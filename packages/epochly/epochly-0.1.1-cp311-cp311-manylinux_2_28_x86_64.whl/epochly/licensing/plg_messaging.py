"""
PLG (Product-Led Growth) messaging system for Epochly.

Delivers contextual, non-intrusive messages about trials and upgrades
across different environments (CLI, REPL, Jupyter).
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class PLGMessenger:
    """
    Manages product-led growth messaging across all Epochly touchpoints.
    
    Design principles:
    - Non-intrusive: Never block or slow down user work
    - Contextual: Show relevant messages based on user actions
    - Respectful: Limit frequency to avoid annoyance
    - Valuable: Focus on what users gain, not what they lose
    """
    
    # Message display intervals (seconds)
    SESSION_REMINDER_INTERVAL = 3600  # Once per hour max
    STARTUP_MESSAGE_INTERVAL = 86400  # Once per day for startup messages
    
    def __init__(self):
        self._message_cache_dir = self._get_cache_dir()
        self._message_cache_dir.mkdir(parents=True, exist_ok=True)
        self._session_start = time.time()
        self._last_reminder_time = 0
        self._messages_shown = set()
        
        # Detect environment
        self._environment = self._detect_environment()
        
        # Load message history
        self._load_message_history()
    
    def _get_cache_dir(self) -> Path:
        """Get directory for message history tracking."""
        if os.name == 'nt':
            base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
            return Path(base) / 'Epochly' / '.plg'
        else:
            base = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
            return Path(base) / 'epochly' / '.plg'
    
    def _detect_environment(self) -> str:
        """Detect current execution environment."""
        # Check for Jupyter
        try:
            from IPython import get_ipython
            if get_ipython() is not None:
                if 'IPKernelApp' in get_ipython().config:
                    return 'jupyter'
                elif 'TerminalIPythonApp' in get_ipython().config:
                    return 'ipython'
        except:
            pass
        
        # Check for interactive Python
        if hasattr(sys, 'ps1'):
            return 'repl'
        
        # Default to CLI
        return 'cli'
    
    def _load_message_history(self):
        """Load history of shown messages to avoid repetition."""
        history_file = self._message_cache_dir / 'message_history.json'
        if history_file.exists():
            try:
                with open(history_file) as f:
                    data = json.load(f)
                    self._last_reminder_time = data.get('last_reminder', 0)
                    self._messages_shown = set(data.get('shown_today', []))
                    
                    # Reset daily messages if new day
                    last_date = data.get('date', '')
                    today = datetime.now().date().isoformat()
                    if last_date != today:
                        self._messages_shown.clear()
            except:
                pass
    
    def _save_message_history(self):
        """Save message history to prevent repetition."""
        history_file = self._message_cache_dir / 'message_history.json'
        try:
            with open(history_file, 'w') as f:
                json.dump({
                    'date': datetime.now().date().isoformat(),
                    'last_reminder': self._last_reminder_time,
                    'shown_today': list(self._messages_shown)
                }, f)
        except:
            pass
    
    def show_startup_message(self, license_info: Dict[str, Any]):
        """Show appropriate message at Epochly startup."""
        tier = license_info.get('tier', 'community')
        
        # Only show once per day
        if 'startup' in self._messages_shown:
            return
        
        if tier == 'community':
            # Check if they ever had a trial
            had_trial = license_info.get('had_trial', False)
            
            if not had_trial:
                # First time user - welcome them
                self._show_community_welcome()
            elif self._should_show_upgrade_nudge():
                # Occasional gentle reminder about upgrading
                self._show_community_reminder()
        
        elif tier == 'trial':
            # Show trial status
            days_remaining = license_info.get('days_remaining', 30)
            self._show_trial_status(days_remaining)
        
        # Mark as shown
        self._messages_shown.add('startup')
        self._save_message_history()
    
    def show_core_limit_message(self, requested: int, allowed: int, total: int):
        """Show message when user hits core limit."""
        # Rate limit these messages
        now = time.time()
        if now - self._last_reminder_time < self.SESSION_REMINDER_INTERVAL:
            return
        
        self._last_reminder_time = now
        
        # Craft message based on environment
        if self._environment == 'jupyter':
            self._show_jupyter_message(
                f"🔸 Core limit: Using {allowed} of {total} available cores "
                f"(Community Edition)\n"
                f"   Unlock all cores: Run `epochly trial --email` in terminal"
            )
        elif self._environment == 'repl':
            print(f"\n[Epochly] Request for {requested} cores exceeds Community limit ({allowed} cores)")
            print(f"[Epochly] Unlock all {total} cores with: epochly trial --email your@email.com")
        else:  # CLI
            logger.info(f"Core limit: {allowed}/{total} cores (Community Edition)")
            if 'trial_hint' not in self._messages_shown:
                logger.info(f"Unlock all cores: epochly trial --email")
                self._messages_shown.add('trial_hint')
    
    def show_trial_expiration_warning(self, days_remaining: int):
        """Show trial expiration warning at appropriate urgency."""
        # Only show these at startup or once per session
        if f'trial_warning_{days_remaining}' in self._messages_shown:
            return
        
        if days_remaining == 15:
            message = (
                "📊 Halfway through your Epochly trial!\n"
                "   You've been using all CPU cores for 15 days.\n"
                "   15 days remaining to decide on a license."
            )
        elif days_remaining == 7:
            message = (
                "One week left in your Epochly trial\n"
                "   After expiration: Limited to 4 cores, no GPU\n"
                "   Keep full performance: epochly.com/pricing"
            )
        elif days_remaining == 1:
            message = (
                "Last day of your Epochly trial!\n"
                "   Tomorrow: Back to Community Edition (4 cores, no GPU)\n"
                "   Maintain full access: epochly.com/pricing"
            )
        elif days_remaining == 0:
            message = (
                "Trial expired - Now using Community Edition\n"
                "   Current: 4 cores maximum, no GPU\n"
                "   Upgrade for all cores + GPU: epochly.com/pricing"
            )
        else:
            return  # Only show at key intervals
        
        self._display_message(message)
        self._messages_shown.add(f'trial_warning_{days_remaining}')
        self._save_message_history()
    
    def _show_community_welcome(self):
        """Welcome message for new community users."""
        message = (
            "Welcome to Epochly Community Edition! 🚀\n"
            "  • Free forever with 4 CPU cores\n"
            f"  • Your system has {os.cpu_count()} cores total\n"
            "  • Get 30-day trial for all cores: epochly trial --email"
        )
        self._display_message(message)
    
    def _show_community_reminder(self):
        """Gentle upgrade reminder for community users."""
        # Only show occasionally (e.g., once a week)
        message = (
            f"Epochly Community: Using 4 of {os.cpu_count()} available cores\n"
            "  Unlock full performance at epochly.com/pricing"
        )
        self._display_message(message, priority='low')
    
    def _show_trial_status(self, days_remaining: int):
        """Show current trial status."""
        if days_remaining > 20:
            emoji = "🚀"
            urgency = "enjoy"
        elif days_remaining > 7:
            emoji = "📊"
            urgency = "track"
        elif days_remaining > 1:
            emoji = "⏰"
            urgency = "decide"
        else:
            emoji = "🔔"
            urgency = "urgent"
        
        message = (
            f"{emoji} Epochly Trial: {days_remaining} days remaining\n"
            f"  - All {os.cpu_count()} CPU cores enabled\n"
            f"  - GPU acceleration enabled\n"
        )

        if urgency in ['decide', 'urgent']:
            message += "  - Maintain access: epochly.com/pricing"
        
        self._display_message(message)
    
    def _should_show_upgrade_nudge(self) -> bool:
        """Determine if we should show an upgrade reminder."""
        # Check if enough time has passed since last nudge
        nudge_file = self._message_cache_dir / 'last_nudge'
        
        if nudge_file.exists():
            try:
                last_nudge = float(nudge_file.read_text())
                # Show max once per week
                if time.time() - last_nudge < 604800:
                    return False
            except:
                pass
        
        # Mark nudge as shown
        nudge_file.write_text(str(time.time()))
        return True
    
    def _display_message(self, message: str, priority: str = 'normal'):
        """Display message appropriately for the environment."""
        if priority == 'low' and self._environment != 'cli':
            # Skip low priority messages in interactive environments
            return
        
        if self._environment == 'jupyter':
            self._show_jupyter_message(message)
        elif self._environment == 'ipython':
            # IPython terminal - use clean formatting
            print(f"\n{message}\n")
        elif self._environment == 'repl':
            # Standard Python REPL
            print(f"\n[Epochly] {message}\n")
        else:
            # CLI - use logger
            for line in message.split('\n'):
                if line.strip():
                    logger.info(line.strip())
    
    def _show_jupyter_message(self, message: str):
        """Display message in Jupyter notebook."""
        try:
            from IPython.display import display, HTML
            
            # Create styled HTML message
            html = f"""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px 16px;
                border-radius: 8px;
                margin: 10px 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 14px;
                line-height: 1.5;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">
                <div style="opacity: 0.95;">
                    {message.replace(chr(10), '<br>')}
                </div>
            </div>
            """
            display(HTML(html))
        except:
            # Fallback to print
            print(message)
    
    def show_performance_achievement(self, metric: str, value: float):
        """Show performance achievements to reinforce value."""
        # Only show significant achievements
        if metric == 'speedup' and value >= 2.0:
            if 'achievement_shown' not in self._messages_shown:
                message = f"⚡ Epochly achieved {value:.1f}x speedup on this workload!"
                self._display_message(message, priority='low')
                self._messages_shown.add('achievement_shown')
    
    def show_feature_blocked(self, feature: str):
        """Show message when a paid feature is requested."""
        feature_messages = {
            'gpu': (
                "GPU acceleration requires a paid license\n"
                "  Available in Instance ($16/month) and higher tiers\n"
                "  Learn more: epochly.com/pricing"
            ),
            'unlimited_cores': (
                "This operation requires more than 4 cores\n"
                "  Get 30-day trial: epochly trial --email\n"
                "  Or upgrade: epochly.com/pricing"
            ),
            'advanced_jit': (
                "Advanced JIT compilation requires trial or paid license\n"
                "  Start trial: epochly trial --email"
            )
        }
        
        message = feature_messages.get(feature)
        if message and feature not in self._messages_shown:
            self._display_message(message)
            self._messages_shown.add(feature)


# Global messenger instance
_messenger: Optional[PLGMessenger] = None


def get_plg_messenger() -> PLGMessenger:
    """Get the global PLG messenger instance."""
    global _messenger
    if _messenger is None:
        _messenger = PLGMessenger()
    return _messenger


def show_startup_message(license_info: Dict[str, Any]):
    """Show appropriate startup message based on license."""
    messenger = get_plg_messenger()
    messenger.show_startup_message(license_info)


def show_core_limit_message(requested: int, allowed: int):
    """Show message when core limit is hit."""
    messenger = get_plg_messenger()
    total = os.cpu_count() or 8
    messenger.show_core_limit_message(requested, allowed, total)


def show_trial_warning(days_remaining: int):
    """Show trial expiration warning."""
    messenger = get_plg_messenger()
    messenger.show_trial_expiration_warning(days_remaining)


def show_performance_achievement(metric: str, value: float):
    """Celebrate performance wins with the user."""
    messenger = get_plg_messenger()
    messenger.show_performance_achievement(metric, value)


def show_feature_blocked(feature: str):
    """Inform user about feature licensing requirements."""
    messenger = get_plg_messenger()
    messenger.show_feature_blocked(feature)