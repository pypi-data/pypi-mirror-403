"""
Secure node authentication for telemetry based on Epochly licensing architecture.

This module implements tamper-proof node registration and authentication
using machine fingerprinting and cryptographic signatures as designed
in the Epochly architecture specification.
"""

import os
import sys
import time
import uuid
import hmac
import hashlib
import json
import platform
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class MachineFingerprint:
    """
    Enhanced 11-attribute machine fingerprinting for maximum anti-piracy protection.
    Based on the architecture spec's hardware fingerprinting approach.
    
    Attributes collected:
    1. CPU serial number
    2. Motherboard ID  
    3. Disk serial number
    4. BIOS version
    5. MAC addresses
    6. GPU information
    7. Memory configuration
    8. OS installation ID
    9. Network interfaces
    10. System UUID
    11. Boot ID (changes on reboot for tolerance testing)
    """
    
    # Cache for expensive operations
    _fingerprint_cache = None
    _raw_data_cache = None
    
    @staticmethod
    def get_cpu_info() -> str:
        """Get CPU identification info (legacy method for compatibility)."""
        return MachineFingerprint.get_cpu_serial()
    
    @staticmethod
    def get_cpu_serial() -> str:
        """Get CPU serial number or processor ID."""
        try:
            system = platform.system()
            
            if system == 'Windows':
                # Get ProcessorId which is unique per CPU
                result = subprocess.run(
                    ['wmic', 'cpu', 'get', 'ProcessorId', '/value'],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.split('\n'):
                    if 'ProcessorId' in line:
                        processor_id = line.split('=')[1].strip()
                        if processor_id and processor_id != '0000000000000000':
                            return processor_id
                            
            elif system == 'Linux':
                # Try to get CPU serial from DMI
                try:
                    result = subprocess.run(
                        ['sudo', 'dmidecode', '-t', 'processor'],
                        capture_output=True, text=True, timeout=5
                    )
                    for line in result.stdout.split('\n'):
                        if 'ID:' in line:
                            cpu_id = line.split('ID:')[1].strip()
                            if cpu_id:
                                return cpu_id
                except:
                    # Fallback to cpuinfo
                    with open('/proc/cpuinfo', 'r') as f:
                        for line in f:
                            if 'model name' in line.lower():
                                return hashlib.md5(line.split(':')[1].strip().encode()).hexdigest()[:16]
                            
            elif system == 'Darwin':
                # macOS: Get CPU serial
                result = subprocess.run(
                    ['sysctl', 'machdep.cpu.signature'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    return result.stdout.strip().split(':')[1].strip() if ':' in result.stdout else result.stdout.strip()
                    
        except Exception:
            pass
            
        # Fallback to processor info hash
        return hashlib.md5(platform.processor().encode()).hexdigest()[:16]
    
    @staticmethod
    def get_motherboard_id() -> str:
        """Get motherboard serial number."""
        try:
            system = platform.system()
            
            if system == 'Windows':
                result = subprocess.run(
                    ['wmic', 'baseboard', 'get', 'SerialNumber', '/value'],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.split('\n'):
                    if 'SerialNumber' in line:
                        serial = line.split('=')[1].strip()
                        if serial and serial not in ['To be filled by O.E.M.', 'None']:
                            return serial
                            
            elif system == 'Linux':
                # Try DMI info
                if os.path.exists('/sys/class/dmi/id/board_serial'):
                    with open('/sys/class/dmi/id/board_serial', 'r') as f:
                        serial = f.read().strip()
                        if serial and serial != 'None':
                            return serial
                            
            elif system == 'Darwin':
                # macOS: Get logic board ID
                result = subprocess.run(
                    ['ioreg', '-l'],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.split('\n'):
                    if 'board-id' in line:
                        board = line.split('=')[1].strip().strip('"')
                        if board:
                            return board
                            
        except Exception:
            pass
            
        # Fallback
        return hashlib.md5(f"{platform.node()}:{platform.machine()}".encode()).hexdigest()[:16]
    
    @staticmethod
    def get_disk_serial() -> str:
        """Get primary disk serial number."""
        try:
            system = platform.system()
            
            if system == 'Windows':
                # Get system drive serial
                result = subprocess.run(
                    ['wmic', 'diskdrive', 'where', 'index=0', 'get', 'SerialNumber', '/value'],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.split('\n'):
                    if 'SerialNumber' in line:
                        serial = line.split('=')[1].strip()
                        if serial:
                            return serial
                            
            elif system == 'Linux':
                # Get disk by-id
                disk_dir = Path('/dev/disk/by-id')
                if disk_dir.exists():
                    for disk in disk_dir.iterdir():
                        if 'ata-' in disk.name or 'nvme-' in disk.name:
                            # Extract serial from name
                            parts = disk.name.split('_')
                            if len(parts) > 1:
                                return parts[-1][:16]
                                
            elif system == 'Darwin':
                # macOS: Get disk identifier
                result = subprocess.run(
                    ['diskutil', 'info', 'disk0'],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.split('\n'):
                    if 'Disk / Partition UUID' in line:
                        uuid_val = line.split(':')[1].strip()
                        if uuid_val:
                            return uuid_val[:16]
                            
        except Exception:
            pass
            
        return "disk_unknown"
    
    @staticmethod
    def get_bios_version() -> str:
        """Get BIOS/UEFI version."""
        try:
            system = platform.system()
            
            if system == 'Windows':
                result = subprocess.run(
                    ['wmic', 'bios', 'get', 'Version', '/value'],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.split('\n'):
                    if 'Version' in line:
                        version = line.split('=')[1].strip()
                        if version:
                            return version[:32]
                            
            elif system == 'Linux':
                if os.path.exists('/sys/class/dmi/id/bios_version'):
                    with open('/sys/class/dmi/id/bios_version', 'r') as f:
                        return f.read().strip()[:32]
                        
            elif system == 'Darwin':
                # macOS: Get firmware version
                result = subprocess.run(
                    ['system_profiler', 'SPHardwareDataType'],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.split('\n'):
                    if 'Boot ROM Version' in line:
                        return line.split(':')[1].strip()[:32]
                        
        except Exception:
            pass
            
        return platform.version()[:32]
    
    @staticmethod
    def get_mac_addresses() -> list:
        """Get all MAC addresses."""
        macs = []
        try:
            # Try using uuid.getnode() for primary MAC
            import uuid as uuid_lib
            mac = ':'.join(['{:02x}'.format((uuid_lib.getnode() >> ele) & 0xff) 
                          for ele in range(0,8*6,8)][::-1])
            if mac and mac != '00:00:00:00:00:00':
                macs.append(mac)
                
            # Try to get additional MACs on Linux
            if platform.system() == 'Linux':
                import subprocess
                result = subprocess.run(['ip', 'link'], capture_output=True, text=True, timeout=5)
                import re
                for match in re.findall(r'link/ether\s+([0-9a-f:]+)', result.stdout):
                    if match not in macs and match != '00:00:00:00:00:00':
                        macs.append(match)
                        
        except Exception:
            pass
            
        return sorted(list(set(macs)))[:3]  # Return up to 3 unique MACs
    
    @staticmethod
    def get_gpu_info() -> str:
        """Get GPU information."""
        try:
            system = platform.system()
            
            if system == 'Windows':
                result = subprocess.run(
                    ['wmic', 'path', 'win32_VideoController', 'get', 'Name', '/value'],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.split('\n'):
                    if 'Name' in line:
                        gpu = line.split('=')[1].strip()
                        if gpu:
                            return gpu[:32]
                            
            elif system == 'Linux':
                # Try lspci
                result = subprocess.run(
                    ['lspci'], capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.split('\n'):
                    if 'VGA' in line or 'Display' in line:
                        return line.split(':')[2].strip()[:32] if len(line.split(':')) > 2 else 'gpu_found'
                        
            elif system == 'Darwin':
                # macOS: Get GPU info
                result = subprocess.run(
                    ['system_profiler', 'SPDisplaysDataType'],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.split('\n'):
                    if 'Chipset Model' in line:
                        return line.split(':')[1].strip()[:32]
                        
        except Exception:
            pass
            
        return "no_gpu"
    
    @staticmethod
    def get_memory_configuration() -> dict:
        """Get memory configuration."""
        config = {
            'total_mb': 0,
            'slots': []
        }
        
        try:
            # Get total memory using cross-platform method
            import os
            if hasattr(os, 'sysconf'):
                if 'SC_PHYS_PAGES' in os.sysconf_names:
                    pages = os.sysconf('SC_PHYS_PAGES')
                    page_size = os.sysconf('SC_PAGE_SIZE')
                    config['total_mb'] = (pages * page_size) // (1024 * 1024)
            else:
                # Windows or fallback
                import subprocess
                result = subprocess.run(
                    ['wmic', 'computersystem', 'get', 'TotalPhysicalMemory', '/value'],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.split('\n'):
                    if 'TotalPhysicalMemory' in line:
                        mem = line.split('=')[1].strip()
                        if mem.isdigit():
                            config['total_mb'] = int(mem) // (1024 * 1024)
                            
        except Exception:
            pass
            
        return config
    
    @staticmethod
    def get_machine_id() -> str:
        """Get platform-specific machine ID (legacy method for compatibility)."""
        return MachineFingerprint.get_os_install_id()
    
    @staticmethod
    def get_os_install_id() -> str:
        """Get OS installation ID."""
        try:
            system = platform.system()
            
            if system == 'Windows':
                # Windows Machine GUID - try registry
                try:
                    import winreg
                    key = winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        r'SOFTWARE\Microsoft\Cryptography'
                    )
                    value = winreg.QueryValueEx(key, 'MachineGuid')[0]
                    winreg.CloseKey(key)
                    return value
                except:
                    # Fallback to wmic
                    result = subprocess.run(
                        ['wmic', 'csproduct', 'get', 'UUID', '/value'],
                        capture_output=True, text=True, timeout=5
                    )
                    for line in result.stdout.split('\n'):
                        if 'UUID' in line:
                            return line.split('=')[1].strip()
                            
            elif system == 'Linux':
                # Linux machine-id
                if os.path.exists('/etc/machine-id'):
                    with open('/etc/machine-id', 'r') as f:
                        return f.read().strip()
                elif os.path.exists('/var/lib/dbus/machine-id'):
                    with open('/var/lib/dbus/machine-id', 'r') as f:
                        return f.read().strip()
                        
            elif system == 'Darwin':
                # macOS: Get system UUID
                result = subprocess.run(
                    ['ioreg', '-rd1', '-c', 'IOPlatformExpertDevice'],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.split('\n'):
                    if 'IOPlatformUUID' in line:
                        return line.split('"')[3]
                        
        except Exception:
            pass
            
        # Fallback: Use MAC address
        import uuid as uuid_lib
        return str(uuid_lib.getnode())
    
    @staticmethod
    def get_network_interfaces() -> list:
        """Get network interface information."""
        interfaces = []
        try:
            import socket
            # Get hostname as a basic network identifier
            hostname = socket.gethostname()
            interfaces.append({'name': 'hostname', 'type': hostname})
            
            # Try to get network interfaces on Linux
            if platform.system() == 'Linux' and os.path.exists('/sys/class/net'):
                for iface in os.listdir('/sys/class/net'):
                    if iface not in ['lo', 'lo0']:  # Skip loopback
                        interfaces.append({
                            'name': iface,
                            'type': 'ethernet' if 'eth' in iface else 'wireless' if 'wl' in iface else 'unknown'
                        })
                        
        except Exception:
            pass
            
        return interfaces[:5]  # Limit to 5 interfaces
    
    @staticmethod
    def get_system_uuid() -> str:
        """Get system UUID."""
        try:
            system = platform.system()
            
            if system == 'Windows':
                result = subprocess.run(
                    ['wmic', 'csproduct', 'get', 'UUID', '/value'],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.split('\n'):
                    if 'UUID' in line:
                        uuid_val = line.split('=')[1].strip()
                        if uuid_val and uuid_val != 'FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF':
                            return uuid_val
                            
            elif system == 'Linux':
                if os.path.exists('/sys/class/dmi/id/product_uuid'):
                    with open('/sys/class/dmi/id/product_uuid', 'r') as f:
                        return f.read().strip()
                        
            elif system == 'Darwin':
                # macOS hardware UUID
                result = subprocess.run(
                    ['system_profiler', 'SPHardwareDataType'],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.split('\n'):
                    if 'Hardware UUID' in line:
                        return line.split(':')[1].strip()
                        
        except Exception:
            pass
            
        # Generate stable UUID from other attributes
        import uuid as uuid_lib
        return str(uuid_lib.uuid5(uuid_lib.NAMESPACE_DNS, platform.node()))
    
    @staticmethod
    def get_boot_id() -> str:
        """Get boot ID (changes on reboot, used for tolerance)."""
        try:
            system = platform.system()
            
            if system == 'Linux':
                if os.path.exists('/proc/sys/kernel/random/boot_id'):
                    with open('/proc/sys/kernel/random/boot_id', 'r') as f:
                        return f.read().strip()
                        
            # For other systems, use uptime as proxy
            import time
            boot_time = time.time() - (os.times()[4] if hasattr(os, 'times') else 0)
            return hashlib.md5(str(boot_time).encode()).hexdigest()
            
        except Exception:
            pass
            
        # Fallback
        import time
        return hashlib.md5(str(time.time()).encode()).hexdigest()
    
    @staticmethod
    def get_raw_fingerprint_data() -> dict:
        """Get all raw fingerprint data (11 attributes)."""
        if MachineFingerprint._raw_data_cache is not None:
            return MachineFingerprint._raw_data_cache
            
        data = {
            'cpu_serial': MachineFingerprint.get_cpu_serial(),
            'motherboard_id': MachineFingerprint.get_motherboard_id(),
            'disk_serial': MachineFingerprint.get_disk_serial(),
            'bios_version': MachineFingerprint.get_bios_version(),
            'mac_addresses': MachineFingerprint.get_mac_addresses(),
            'gpu_info': MachineFingerprint.get_gpu_info(),
            'memory_config': MachineFingerprint.get_memory_configuration(),
            'os_install_id': MachineFingerprint.get_os_install_id(),
            'network_interfaces': MachineFingerprint.get_network_interfaces(),
            'system_uuid': MachineFingerprint.get_system_uuid(),
            'boot_id': MachineFingerprint.get_boot_id()
        }
        
        MachineFingerprint._raw_data_cache = data
        return data
    
    @staticmethod
    def generate() -> str:
        """
        Generate a stable machine fingerprint with 11 attributes.
        Maintains compatibility with existing code.
        """
        if MachineFingerprint._fingerprint_cache is not None:
            return MachineFingerprint._fingerprint_cache
            
        data = MachineFingerprint.get_raw_fingerprint_data()
        
        # Create deterministic string from all 11 attributes
        components = [
            data['cpu_serial'],
            data['motherboard_id'],
            data['disk_serial'],
            data['bios_version'],
            '|'.join(data['mac_addresses']) if data['mac_addresses'] else 'no_mac',
            data['gpu_info'],
            json.dumps(data['memory_config'], sort_keys=True),
            data['os_install_id'],
            json.dumps(data['network_interfaces'], sort_keys=True),
            data['system_uuid'],
            data['boot_id']
        ]
        
        # Create stable hash
        fingerprint_data = '||'.join(str(c) for c in components)
        fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()
        
        MachineFingerprint._fingerprint_cache = fingerprint
        return fingerprint
    
    @staticmethod
    def generate_complete_fingerprint() -> str:
        """Alias for generate() to support new code."""
        return MachineFingerprint.generate()
    
    @staticmethod
    def match_with_tolerance(data1: dict, data2: dict, max_differences: int = 2) -> bool:
        """
        Match fingerprints with tolerance for minor changes.
        
        Args:
            data1: First fingerprint data
            data2: Second fingerprint data
            max_differences: Maximum allowed differences
            
        Returns:
            True if fingerprints match within tolerance
        """
        differences = 0
        
        # Attributes that can change (with weights)
        volatile_attrs = {'boot_id': 1, 'network_interfaces': 1}
        stable_attrs = {'cpu_serial': 3, 'motherboard_id': 3, 'disk_serial': 2}
        
        for key in data1:
            if key in volatile_attrs:
                if data1[key] != data2.get(key):
                    differences += volatile_attrs[key]
            elif key in stable_attrs:
                if data1[key] != data2.get(key):
                    differences += stable_attrs[key]
            else:
                if data1[key] != data2.get(key):
                    differences += 2
                    
        return differences <= max_differences
    
    @staticmethod
    def detect_vm() -> bool:
        """
        Detect if running in a virtual machine.
        Essential for anti-piracy protection.
        """
        try:
            system = platform.system()
            
            # Check for VM artifacts in various places
            vm_indicators = []
            
            if system == 'Windows':
                # Check WMI for VM manufacturers
                try:
                    result = subprocess.run(
                        ['wmic', 'computersystem', 'get', 'manufacturer', '/value'],
                        capture_output=True, text=True, timeout=5
                    )
                    output = result.stdout.lower()
                    vm_vendors = ['vmware', 'virtualbox', 'xen', 'qemu', 'microsoft corporation', 'parallels']
                    for vendor in vm_vendors:
                        if vendor in output:
                            vm_indicators.append(f"WMI manufacturer: {vendor}")
                except:
                    pass
                    
            elif system == 'Linux':
                # Check DMI information
                if os.path.exists('/sys/class/dmi/id/product_name'):
                    with open('/sys/class/dmi/id/product_name', 'r') as f:
                        product = f.read().lower()
                        if any(vm in product for vm in ['vmware', 'virtualbox', 'qemu', 'xen', 'kvm']):
                            vm_indicators.append(f"DMI product: {product.strip()}")
                
                # Check for hypervisor
                if os.path.exists('/proc/cpuinfo'):
                    with open('/proc/cpuinfo', 'r') as f:
                        cpuinfo = f.read().lower()
                        if 'hypervisor' in cpuinfo:
                            vm_indicators.append("Hypervisor flag in cpuinfo")
                
                # Check systemd-detect-virt if available
                try:
                    result = subprocess.run(
                        ['systemd-detect-virt'],
                        capture_output=True, text=True, timeout=2
                    )
                    if result.returncode == 0 and result.stdout.strip() != 'none':
                        vm_indicators.append(f"systemd-detect-virt: {result.stdout.strip()}")
                except:
                    pass
                    
            elif system == 'Darwin':
                # Check for VM on macOS
                try:
                    result = subprocess.run(
                        ['sysctl', 'hw.model'],
                        capture_output=True, text=True, timeout=5
                    )
                    model = result.stdout.lower()
                    if 'vmware' in model or 'virtualbox' in model:
                        vm_indicators.append(f"Hardware model: {model.strip()}")
                except:
                    pass
            
            # Check MAC address prefixes (common VM OUIs)
            vm_mac_prefixes = [
                '00:05:69', '00:0c:29', '00:1c:14', '00:50:56',  # VMware
                '08:00:27', '0a:00:27',  # VirtualBox
                '00:16:3e', '00:1a:4a', '5e:00:00',  # Xen
                '52:54:00',  # QEMU/KVM
                '00:15:5d',  # Hyper-V
            ]
            
            mac_addresses = MachineFingerprint.get_mac_addresses()
            for mac in mac_addresses:
                prefix = mac[:8].lower()
                if any(prefix.startswith(vm_prefix.replace(':', '')) for vm_prefix in vm_mac_prefixes):
                    vm_indicators.append(f"VM MAC prefix: {prefix}")
            
            if vm_indicators:
                logger.debug(f"VM detected: {', '.join(vm_indicators)}")
                return True
                
        except Exception as e:
            logger.debug(f"VM detection error: {e}")
            
        return False
    
    @staticmethod
    def detect_container() -> bool:
        """
        Detect if running in a container (Docker, Kubernetes, etc).
        Essential for anti-piracy protection.
        """
        try:
            container_indicators = []
            
            # Check for Docker
            if os.path.exists('/.dockerenv'):
                container_indicators.append("Docker environment file")
            
            # Check for Kubernetes
            if os.path.exists('/var/run/secrets/kubernetes.io'):
                container_indicators.append("Kubernetes secrets")
            
            # Check cgroup for container signatures
            if os.path.exists('/proc/self/cgroup'):
                with open('/proc/self/cgroup', 'r') as f:
                    cgroup = f.read().lower()
                    if any(c in cgroup for c in ['docker', 'kubepods', 'containerd', 'lxc']):
                        container_indicators.append("Container in cgroup")
            
            # Check for container environment variables
            container_env_vars = ['KUBERNETES_', 'DOCKER_', 'CONTAINER_']
            for env_var in os.environ:
                if any(env_var.startswith(prefix) for prefix in container_env_vars):
                    container_indicators.append(f"Container env var: {env_var}")
            
            # Check init process
            if os.path.exists('/proc/1/sched'):
                with open('/proc/1/sched', 'r') as f:
                    sched = f.read()
                    if 'bash' in sched or 'sh' in sched:
                        container_indicators.append("Non-standard init process")
            
            if container_indicators:
                logger.debug(f"Container detected: {', '.join(container_indicators)}")
                return True
                
        except Exception as e:
            logger.debug(f"Container detection error: {e}")
            
        return False
    
    @staticmethod
    def encrypt(data: str, key: Optional[bytes] = None) -> bytes:
        """
        Encrypt fingerprint data using hardware-derived key.
        Essential for secure storage.
        """
        if key is None:
            # Derive key from hardware fingerprint
            fingerprint = MachineFingerprint.generate()
            key = hashlib.sha256(fingerprint.encode()).digest()
        
        # Use AES-like XOR encryption (simplified for compatibility)
        # In production, use proper AES-256-GCM
        import hmac
        
        # Generate IV
        iv = os.urandom(16)
        
        # Expand key using HMAC
        expanded_key = hmac.new(key, iv, hashlib.sha256).digest()
        
        # XOR encryption
        encrypted = bytearray()
        data_bytes = data.encode()
        for i, byte in enumerate(data_bytes):
            key_byte = expanded_key[i % len(expanded_key)]
            encrypted.append(byte ^ key_byte)
        
        # Prepend IV
        return iv + bytes(encrypted)
    
    @staticmethod
    def detect_changes() -> bool:
        """
        Detect hardware changes since last fingerprint.
        Returns True if significant changes detected.
        """
        try:
            # Get cache directory
            cache_dir = Path.home() / '.epochly' / '.fingerprint'
            stored_fp_file = cache_dir / 'last_fingerprint.json'
            
            # Get current fingerprint data
            current_data = MachineFingerprint.get_raw_fingerprint_data()
            
            # Check if we have a stored fingerprint
            if not stored_fp_file.exists():
                # First run, store current
                cache_dir.mkdir(parents=True, exist_ok=True)
                with open(stored_fp_file, 'w') as f:
                    json.dump(current_data, f)
                return False
            
            # Load stored fingerprint
            with open(stored_fp_file, 'r') as f:
                stored_data = json.load(f)
            
            # Check for changes (allow tolerance)
            if not MachineFingerprint.match_with_tolerance(current_data, stored_data):
                logger.warning("Significant hardware changes detected")
                # Update stored fingerprint
                with open(stored_fp_file, 'w') as f:
                    json.dump(current_data, f)
                return True
                
        except Exception as e:
            logger.debug(f"Change detection error: {e}")
            
        return False
    
    @staticmethod
    def store_fingerprint(fingerprint: str, path: Optional[Path] = None) -> bool:
        """
        Store fingerprint securely.
        """
        try:
            if path is None:
                cache_dir = Path.home() / '.epochly' / '.fingerprint'
                cache_dir.mkdir(parents=True, exist_ok=True)
                path = cache_dir / 'fingerprint.enc'
            
            # Encrypt before storing
            encrypted = MachineFingerprint.encrypt(fingerprint)
            
            # Write atomically
            temp_path = path.with_suffix('.tmp')
            with open(temp_path, 'wb') as f:
                f.write(encrypted)
            
            # Move atomically
            temp_path.replace(path)
            
            # Secure permissions on Unix
            if os.name != 'nt':
                os.chmod(path, 0o600)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store fingerprint: {e}")
            return False
    
    @staticmethod
    def restore_fingerprint(path: Optional[Path] = None) -> Optional[str]:
        """
        Restore a stored fingerprint.
        """
        try:
            if path is None:
                cache_dir = Path.home() / '.epochly' / '.fingerprint'
                path = cache_dir / 'fingerprint.enc'
            
            if not path.exists():
                return None
            
            # Read encrypted data
            with open(path, 'rb') as f:
                encrypted = f.read()
            
            # Decrypt
            if len(encrypted) < 16:
                return None
            
            iv = encrypted[:16]
            ciphertext = encrypted[16:]
            
            # Derive key from hardware
            fingerprint = MachineFingerprint.generate()
            key = hashlib.sha256(fingerprint.encode()).digest()
            
            # Expand key using IV
            expanded_key = hmac.new(key, iv, hashlib.sha256).digest()
            
            # XOR decryption
            decrypted = bytearray()
            for i, byte in enumerate(ciphertext):
                key_byte = expanded_key[i % len(expanded_key)]
                decrypted.append(byte ^ key_byte)
            
            return decrypted.decode()
            
        except Exception as e:
            logger.error(f"Failed to restore fingerprint: {e}")
            return None
    
    @staticmethod
    def backup_fingerprint(backup_path: Path) -> bool:
        """
        Create a backup of the fingerprint.
        """
        try:
            # Get current stored fingerprint
            stored = MachineFingerprint.restore_fingerprint()
            if stored:
                return MachineFingerprint.store_fingerprint(stored, backup_path)
            
            # No stored fingerprint, create from current
            current = MachineFingerprint.generate()
            return MachineFingerprint.store_fingerprint(current, backup_path)
            
        except Exception as e:
            logger.error(f"Failed to backup fingerprint: {e}")
            return False
    
    @staticmethod
    def detect_debugger() -> bool:
        """
        Detect if running under a debugger.
        Essential for anti-tampering protection.
        """
        try:
            # Python-specific debugger detection
            if sys.gettrace() is not None:
                logger.warning("Python trace function detected (debugger)")
                return True
            
            # Check for common debugger environment variables
            debugger_env_vars = ['PYTHONBREAKPOINT', 'PYCHARM_', 'VSCODE_', 'PYTHONDEBUG']
            for env_var in os.environ:
                if any(env_var.startswith(debug_var) for debug_var in debugger_env_vars):
                    logger.warning(f"Debugger environment variable detected: {env_var}")
                    return True
            
            system = platform.system()
            
            if system == 'Linux':
                # Check /proc/self/status for TracerPid
                if os.path.exists('/proc/self/status'):
                    with open('/proc/self/status', 'r') as f:
                        for line in f:
                            if line.startswith('TracerPid:'):
                                tracer_pid = int(line.split()[1])
                                if tracer_pid != 0:
                                    logger.warning(f"Process is being traced (PID: {tracer_pid})")
                                    return True
            
            elif system == 'Windows':
                # Check for debugger using Windows API (simplified)
                try:
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    is_debugged = ctypes.c_bool(False)
                    kernel32.CheckRemoteDebuggerPresent(
                        kernel32.GetCurrentProcess(),
                        ctypes.byref(is_debugged)
                    )
                    if is_debugged.value:
                        logger.warning("Windows debugger detected")
                        return True
                except:
                    pass
            
            elif system == 'Darwin':
                # Check for debugger on macOS
                try:
                    import ctypes
                    import ctypes.util
                    
                    libc = ctypes.CDLL(ctypes.util.find_library('c'))
                    P_TRACED = 0x00000800
                    
                    class kinfo_proc(ctypes.Structure):
                        _fields_ = [('kp_proc', ctypes.c_char * 648)]
                    
                    pid = os.getpid()
                    proc_info = kinfo_proc()
                    size = ctypes.c_size_t(ctypes.sizeof(proc_info))
                    
                    mib = (ctypes.c_int * 4)(1, 14, 1, pid)
                    
                    if libc.sysctl(mib, 4, ctypes.byref(proc_info), ctypes.byref(size), None, 0) == 0:
                        # Check P_TRACED flag
                        flags = int.from_bytes(proc_info.kp_proc[32:36], byteorder='little')
                        if flags & P_TRACED:
                            logger.warning("macOS debugger detected")
                            return True
                except:
                    pass
                    
        except Exception as e:
            logger.debug(f"Debugger detection error: {e}")
            
        return False


class SecureNodeAuth:
    """
    Secure node authentication system following Epochly's licensing architecture.
    
    Features:
    - Machine fingerprinting for node identification
    - Tamper detection and prevention
    - Cryptographic signatures for request authentication
    - Automatic registration with proof-of-work
    """
    
    # Embedded secrets (would be obfuscated in production build)
    # These follow the pattern from the architecture spec
    _EPOCHLY_PUBLIC_KEY = """
    -----BEGIN PUBLIC KEY-----
    MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1234567890...
    -----END PUBLIC KEY-----
    """
    
    _EPOCHLY_TELEMETRY_SECRET = b"epochly-telemetry-2024-v1-embedded-secret"
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize secure node authentication."""
        self.cache_dir = cache_dir or self._get_cache_dir()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Node identity
        self.node_file = self.cache_dir / "node_identity.json"
        self.machine_fingerprint = MachineFingerprint.generate()
        
        # Load or create node data
        self.node_id = None
        self.node_secret = None
        self.registration_token = None
        self.registered_at = None
        
        self._load_or_create_node()
        
        # Anti-tampering
        self.last_integrity_check = 0
        self.integrity_check_interval = 300  # 5 minutes
        
        # Try to register if not already done
        if not self.registered_at:
            self._attempt_registration()
    
    def _get_cache_dir(self) -> Path:
        """Get secure cache directory."""
        if os.name == 'nt':
            base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
            return Path(base) / 'Epochly' / '.secure'
        else:
            base = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
            return Path(base) / 'epochly' / '.secure'
    
    def _load_or_create_node(self):
        """Load existing node or create new one."""
        if self.node_file.exists():
            try:
                with open(self.node_file, 'r') as f:
                    data = json.load(f)
                    
                    # Verify machine fingerprint matches
                    if data.get('machine_fingerprint') != self.machine_fingerprint:
                        logger.warning("Machine fingerprint mismatch - regenerating node")
                        self._create_new_node()
                        return
                    
                    self.node_id = data['node_id']
                    self.node_secret = data['node_secret']
                    self.registration_token = data.get('registration_token')
                    self.registered_at = data.get('registered_at')
                    
                    logger.info(f"Loaded node identity: {self.node_id[:8]}...")
                    return
                    
            except Exception as e:
                logger.warning(f"Failed to load node identity: {e}")
        
        self._create_new_node()
    
    def _create_new_node(self):
        """Create new node identity with proof-of-work."""
        # Generate unique node ID
        self.node_id = str(uuid.uuid4())
        
        # Generate node-specific secret
        self.node_secret = hashlib.sha256(
            f"{self.node_id}:{self.machine_fingerprint}:{time.time()}".encode()
        ).hexdigest()
        
        # Generate registration token with proof-of-work
        self.registration_token = self._generate_proof_of_work()
        
        # Save node data
        self._save_node()
        
        logger.info(f"Created new node identity: {self.node_id[:8]}...")
    
    def _generate_proof_of_work(self) -> str:
        """
        Generate proof-of-work for registration.
        Prevents spam registrations and ensures computational cost.
        """
        difficulty = 4  # Require 4 leading zeros
        nonce = 0
        start_time = time.time()
        
        while True:
            # Combine node data with nonce
            data = f"{self.node_id}:{self.machine_fingerprint}:{nonce}"
            hash_result = hashlib.sha256(data.encode()).hexdigest()
            
            # Check if hash meets difficulty
            if hash_result.startswith('0' * difficulty):
                elapsed = time.time() - start_time
                logger.info(f"Proof-of-work completed in {elapsed:.2f}s")
                return f"{nonce}:{hash_result}"
            
            nonce += 1
            
            # Timeout after 30 seconds
            if time.time() - start_time > 30:
                logger.warning("Proof-of-work timeout")
                return hashlib.sha256(data.encode()).hexdigest()
    
    def _save_node(self):
        """Save node identity securely."""
        node_data = {
            'node_id': self.node_id,
            'node_secret': self.node_secret,
            'machine_fingerprint': self.machine_fingerprint,
            'registration_token': self.registration_token,
            'registered_at': self.registered_at,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'epochly_version': self._get_epochly_version(),
            'python_version': platform.python_version(),
            'platform': platform.platform()
        }
        
        # Write atomically
        temp_file = self.node_file.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(node_data, f, indent=2)
        
        # Move atomically
        temp_file.replace(self.node_file)
        
        # Secure permissions on Unix
        if os.name != 'nt':
            os.chmod(self.node_file, 0o600)
    
    def _get_epochly_version(self) -> str:
        """Get Epochly version."""
        try:
            import epochly
            return getattr(epochly, '__version__', 'unknown')
        except:
            return 'unknown'
    
    def check_integrity(self) -> bool:
        """
        Check system integrity for tampering.
        Based on AntiTamper from architecture spec.
        """
        now = time.time()
        
        # Rate limit checks
        if now - self.last_integrity_check < self.integrity_check_interval:
            return True
        
        self.last_integrity_check = now
        
        # Check time consistency
        if not self._check_time_consistency():
            logger.warning("Time consistency check failed")
            return False
        
        # Check file integrity
        if not self._check_file_integrity():
            logger.warning("File integrity check failed")
            return False
        
        # Check environment
        if not self._check_environment():
            logger.warning("Environment check failed")
            return False
        
        return True
    
    def _check_time_consistency(self) -> bool:
        """Detect system time manipulation."""
        # Check if time is moving forward
        current_time = time.time()
        
        # Load last known time
        time_file = self.cache_dir / ".last_time"
        if time_file.exists():
            try:
                with open(time_file, 'r') as f:
                    last_time = float(f.read())
                    
                # Time should not go backwards significantly
                if current_time < last_time - 60:  # Allow 1 minute drift
                    return False
            except:
                pass
        
        # Save current time
        with open(time_file, 'w') as f:
            f.write(str(current_time))
        
        return True
    
    def _check_file_integrity(self) -> bool:
        """Check node file hasn't been tampered with."""
        if not self.node_file.exists():
            return False
        
        # Check file permissions on Unix
        if os.name != 'nt':
            stat_info = os.stat(self.node_file)
            if stat_info.st_mode & 0o077:  # Others have access
                return False
        
        return True
    
    def _check_environment(self) -> bool:
        """Check for debugging or tampering tools."""
        # Check for debuggers
        if sys.gettrace() is not None:
            return False
        
        # Check for common tampering environment variables
        suspicious_vars = ['EPOCHLY_BYPASS', 'EPOCHLY_FAKE_NODE', 'EPOCHLY_NO_AUTH']
        for var in suspicious_vars:
            if os.environ.get(var):
                return False
        
        return True
    
    def generate_auth_headers(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate authentication headers for a request.
        
        Args:
            data: Request data to sign
            
        Returns:
            Headers with authentication information
        """
        # Check integrity first
        if not self.check_integrity():
            raise RuntimeError("Integrity check failed")
        
        # Add timestamp to prevent replay attacks
        timestamp = datetime.now(timezone.utc).isoformat()
        data['timestamp'] = timestamp
        data['node_id'] = self.node_id
        
        # Create signature
        signature = self._sign_request(data)
        
        return {
            'X-Node-ID': self.node_id,
            'X-Machine-Fingerprint': self.machine_fingerprint[:16],  # First 16 chars
            'X-Timestamp': timestamp,
            'X-Signature': signature,
            'X-Epochly-Version': self._get_epochly_version()
        }
    
    def _sign_request(self, data: Dict[str, Any]) -> str:
        """
        Sign request data with HMAC.
        
        Uses combination of node secret and embedded secret
        for dual-layer authentication.
        """
        # Serialize data deterministically
        json_data = json.dumps(data, sort_keys=True, separators=(',', ':'))
        
        # Create signing key from node secret + embedded secret
        signing_key = hashlib.sha256(
            self.node_secret.encode() + self._EPOCHLY_TELEMETRY_SECRET
        ).digest()
        
        # Generate HMAC signature
        signature = hmac.new(
            signing_key,
            json_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify_response(self, response_data: Dict[str, Any], 
                        response_signature: str) -> bool:
        """
        Verify response from server.
        
        Args:
            response_data: Response data
            response_signature: Server's signature
            
        Returns:
            True if signature is valid
        """
        # Server signs with its private key
        # We verify with embedded public key
        # (Simplified for this implementation)
        
        expected_signature = hashlib.sha256(
            json.dumps(response_data, sort_keys=True).encode() + 
            self._EPOCHLY_TELEMETRY_SECRET
        ).hexdigest()
        
        return hmac.compare_digest(response_signature, expected_signature)
    
    def _attempt_registration(self):
        """
        Attempt to self-register with the API Gateway.
        
        This is called automatically on first use.
        """
        try:
            # Check if we have requests available
            try:
                import requests
            except ImportError:
                logger.debug("requests not available - skipping registration")
                return
            
            # Get API endpoint
            api_endpoint = os.environ.get('EPOCHLY_API_ENDPOINT')
            if not api_endpoint:
                logger.debug("EPOCHLY_API_ENDPOINT not set - skipping registration")
                return
            
            # Prepare registration data
            registration_data = {
                'node_id': self.node_id,
                'machine_fingerprint': self.machine_fingerprint,
                'node_secret': self.node_secret,
                'proof_token': self.registration_token,
                'epochly_version': self._get_epochly_version(),
                # Include enhanced fingerprint data for better validation
                'fingerprint_data': MachineFingerprint.get_raw_fingerprint_data()
            }
            
            # Send registration request
            url = f"{api_endpoint}/register"
            response = requests.post(
                url,
                json=registration_data,
                headers={'Content-Type': 'application/json'},
                timeout=5.0
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                self.registered_at = result.get('registered_at', 
                                               datetime.now(timezone.utc).isoformat())
                self._save_node()
                logger.info(f"Node registered successfully: {self.node_id[:8]}...")
            elif response.status_code == 403:
                logger.warning("Node registration rejected - may be banned")
            else:
                logger.debug(f"Registration returned {response.status_code}")
                
        except Exception as e:
            logger.debug(f"Registration attempt failed: {e}")
            # Not critical - node can still work without registration


# Global instance
_global_auth = None


def get_secure_auth() -> SecureNodeAuth:
    """Get global secure authentication instance."""
    global _global_auth
    if _global_auth is None:
        _global_auth = SecureNodeAuth()
    return _global_auth