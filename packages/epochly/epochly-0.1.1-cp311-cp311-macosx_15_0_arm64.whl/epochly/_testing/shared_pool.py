"""
Canonical session-scoped ProcessPoolExecutor for tests.

Expert guidance: Hardened teardown with lock, shutdown-before-pop, bounded wait.
"""

import atexit
import os
import time
import threading
import signal
import faulthandler
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, Optional

# Python 3.8 compatibility: Use typing.Dict not dict[...]
_POOLS: Dict[str, ProcessPoolExecutor] = {}
_CREATION_PID = None
_LOCK = threading.RLock()


def get_shared_process_pool(n: int = 4, *, key: Optional[str] = None) -> ProcessPoolExecutor:
    """
    Get or create keyed pool. Thread-safe with double-checked locking.

    Expert guidance: Build pool OUTSIDE lock to avoid re-entrant deadlock.
    """
    global _CREATION_PID

    if key is None:
        key = "session"

    # Fast path: check without lock
    pool = _POOLS.get(key)
    if pool is not None:
        return pool

    # Build pool OUTSIDE the lock (expert guidance: avoid re-entrant deadlock)
    ctx_name = os.getenv("EPOCHLY_TEST_POOL_CTX", "spawn")
    ctx = mp.get_context(ctx_name)
    max_tasks = int(os.getenv("EPOCHLY_TEST_MAX_TASKS_PER_CHILD", "256"))

    # Python 3.11+ supports max_tasks_per_child parameter
    import sys
    if sys.version_info >= (3, 11):
        new_pool = ProcessPoolExecutor(
            max_workers=n,
            mp_context=ctx,
            max_tasks_per_child=max_tasks,
        )
    else:
        new_pool = ProcessPoolExecutor(
            max_workers=n,
            mp_context=ctx,
        )
    setattr(new_pool, "_epochly_shared", True)

    # CRITICAL: Register shared pool in global registry for deterministic cleanup
    # This prevents Python 3.13+ non-daemon manager thread from blocking exit
    try:
        from epochly.plugins.executor.sub_interpreter_executor import (
            _PROCESS_POOL_REGISTRY,
            _POOL_REGISTRY_LOCK
        )
        with _POOL_REGISTRY_LOCK:
            _PROCESS_POOL_REGISTRY.add(new_pool)
        print(f"  → Registered shared pool in global registry", flush=True)
    except ImportError:
        pass  # Registry not available in this context

    # Publish atomically under lock
    with _LOCK:
        pool = _POOLS.get(key)
        if pool is None:
            # We won the race, use our pool
            _POOLS[key] = new_pool
            _CREATION_PID = os.getpid()
            print(f"⚠️ CREATED CANONICAL POOL key={key} id={id(new_pool)} pid={_CREATION_PID} "
                  f"start_method={ctx_name} workers={n} max_tasks_per_child={max_tasks}", flush=True)
            return new_pool
        else:
            # Someone else created it, shut down our spare
            try:
                import sys
                if sys.version_info >= (3, 9):
                    new_pool.shutdown(wait=False, cancel_futures=True)
                else:
                    new_pool.shutdown(wait=False)
            except Exception:
                pass
            return pool


def _dump_all_threads(tag=""):
    """
    Dump all thread stacks. Expert guidance: Critical for diagnosing hangs.
    """
    import sys
    import traceback

    print(f"\n==== THREAD DUMP {tag} ====", flush=True)
    frames = sys._current_frames()
    for t in threading.enumerate():
        fr = frames.get(t.ident)
        print(f"--> Thread: {t.name} (daemon={t.daemon}, ident={t.ident})", flush=True)
        if fr:
            traceback.print_stack(fr)
    print("==== END THREAD DUMP ====\n", flush=True)


def _log_executor_state(pool, tag=""):
    """
    Log ProcessPoolExecutor internal state. Expert guidance: Shows fields that exist in 3.12.
    """
    try:
        # Manager thread
        mt = getattr(pool, "_executor_manager_thread", None)
        mt_alive = bool(mt and mt.is_alive()) if mt else None

        # Processes
        procs = getattr(pool, "_processes", {})
        proc_info = [(p.pid, p.is_alive(), p.exitcode) for p in procs.values()] if procs else []

        # Broken flag
        broken = getattr(pool, "_broken", None)

        # Pending work items
        pend = getattr(pool, "_pending_work_items", None)
        pend_count = len(pend) if pend is not None else "NA"

        print(f"[{tag}] mgr_alive={mt_alive} procs={proc_info} broken={bool(broken)} pending={pend_count}", flush=True)
    except Exception as e:
        print(f"[{tag}] ERROR logging executor state: {e}", flush=True)


def release_shared_process_pool(key: str = "session", *, graceful_timeout: float = 5.0) -> None:
    """
    Idempotent, bounded shutdown. Expert guidance:
    - Log before checking presence
    - Shutdown BEFORE removing from registry
    - Use lock to prevent races
    - Never silently no-op
    """
    # Log early with registry state
    with _LOCK:
        keys = list(_POOLS.keys())
        pool = _POOLS.get(key)

    print(f"⚑ RELEASE REQUEST key={key} present={pool is not None} all_keys={keys}", flush=True)

    if pool is None:
        print(f"⚑ NOTHING TO RELEASE for key={key} (already released or never created)", flush=True)
        return

    print(f"⚠️ SHUTTING DOWN CANONICAL POOL key={key} id={id(pool)}", flush=True)

    # Log executor state before shutdown
    _log_executor_state(pool, "pre-shutdown")

    # Python < 3.11 workaround: Brief sleep before shutdown to drain queues
    # (Prevents deadlock on multiprocessing queues - fixed in Python 3.11+)
    import sys
    if sys.version_info < (3, 11):
        time.sleep(0.001)

    # 1) Begin graceful shutdown (non-blocking)
    try:
        if sys.version_info >= (3, 9):
            pool.shutdown(wait=False, cancel_futures=True)
        else:
            pool.shutdown(wait=False)
    except Exception as e:
        print(f"⚠️ shutdown(wait=False) raised: {e!r}", flush=True)

    _log_executor_state(pool, "post-shutdown-call")

    # 2) Bounded wait by joining worker processes
    processes_dict = getattr(pool, "_processes", None)
    procs = list(processes_dict.values()) if processes_dict else []
    deadline = time.monotonic() + graceful_timeout

    while procs and time.monotonic() < deadline:
        still_alive = []
        for p in procs:
            p.join(timeout=0.1)
            if p.is_alive():
                still_alive.append(p)
        procs = still_alive

    if not procs:
        print(f"⚠️ SHUTDOWN COMPLETE key={key} (graceful)", flush=True)
    else:
        # 3) Hard terminate stragglers
        print(f"⚠️ (key={key}) forcing terminate of {len(procs)} workers after {graceful_timeout}s", flush=True)
        _dump_all_threads(tag=f"key={key} pre-kill")
        for p in procs:
            try:
                p.terminate()
            except Exception:
                pass
        for p in procs:
            p.join(timeout=1.0)

        # Final non-blocking shutdown to stop manager thread
        try:
            import sys
            if sys.version_info >= (3, 9):
                pool.shutdown(wait=False, cancel_futures=True)
            else:
                pool.shutdown(wait=False)
        except Exception:
            pass

        print(f"⚠️ SHUTDOWN FORCED key={key} (terminated {len(procs)} workers)", flush=True)

    # Remove from registry AFTER shutdown completes
    with _LOCK:
        _POOLS.pop(key, None)

    print(f"⚑ RELEASE COMPLETE key={key}", flush=True)


def release_all_pools(graceful_timeout: float = 5.0) -> None:
    """Release all keyed pools (called at process exit)."""
    with _LOCK:
        keys = list(_POOLS.keys())
    for k in keys:
        release_shared_process_pool(k, graceful_timeout=graceful_timeout)


# Single atexit handler for all pools
atexit.register(release_all_pools)
