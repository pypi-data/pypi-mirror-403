"""
Epochly Jupyter Kernel Installation

Provides functionality to install, manage, and uninstall Epochly-enabled Jupyter kernels.
This allows users to have "Python (Epochly)" available as a kernel option in Jupyter.

Author: Epochly Development Team
"""

import json
import sys
import os
import shutil
from pathlib import Path
from typing import Dict, List, Any
import subprocess


def get_jupyter_kernels_dir() -> Path:
    """Get the Jupyter kernels directory for the current user."""
    try:
        # Try to get from jupyter itself
        result = subprocess.run([sys.executable, '-m', 'jupyter', '--data-dir'], 
                              capture_output=True, text=True, check=True)
        data_dir = Path(result.stdout.strip())
        return data_dir / 'kernels'
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to standard location
        if os.name == 'nt':  # Windows
            return Path.home() / 'AppData' / 'Roaming' / 'jupyter' / 'kernels'
        else:  # Unix-like
            return Path.home() / '.local' / 'share' / 'jupyter' / 'kernels'


def create_epochly_kernel_spec(python_executable: str = None, 
                          display_name: str = "Python (epochly)",
                          kernel_name: str = "epochly") -> Dict[str, Any]:
    """
    Create a Jupyter kernel specification for Epochly.
    
    Args:
        python_executable: Path to Python executable (defaults to current)
        display_name: Display name for the kernel
        kernel_name: Internal kernel name
        
    Returns:
        Dictionary containing kernel specification
    """
    if python_executable is None:
        python_executable = sys.executable
        
    return {
        "argv": [
            python_executable,
            "-m", "ipykernel_launcher",
            "-f", "{connection_file}"
        ],
        "display_name": display_name,
        "language": "python",
        "env": {
            "EPOCHLY_JUPYTER_MODE": "1",
            "EPOCHLY_AUTO_INIT": "1"
        },
        "metadata": {
            "debugger": True,
            "epochly_enabled": True,
            "epochly_version": get_epochly_version()
        }
    }


def get_epochly_version() -> str:
    """Get Epochly version string."""
    try:
        import epochly
        return getattr(epochly, '__version__', 'unknown')
    except ImportError:
        return 'not-installed'


def install_epochly_kernel(kernel_name: str = "epochly",
                      display_name: str = "Python (epochly)",
                      user: bool = True,
                      python_executable: str = None,
                      force: bool = False) -> bool:
    """
    Install Epochly-enabled Jupyter kernel.
    
    Args:
        kernel_name: Internal name for the kernel
        display_name: Display name shown in Jupyter
        user: Install for current user only (vs system-wide)
        python_executable: Python executable to use
        force: Overwrite existing kernel
        
    Returns:
        True if installation successful, False otherwise
    """
    try:
        # Check if ipykernel is available
        try:
            import ipykernel
        except ImportError:
            print("ERROR: ipykernel not found. Please install: pip install ipykernel")
            return False
            
        # Get kernels directory
        if user:
            kernels_dir = get_jupyter_kernels_dir()
        else:
            # System-wide installation
            try:
                result = subprocess.run([sys.executable, '-m', 'jupyter', '--system-data-dir'],
                                      capture_output=True, text=True, check=True)
                kernels_dir = Path(result.stdout.strip()) / 'kernels'
            except:
                print("ERROR: Cannot determine system kernels directory")
                return False
                
        kernel_dir = kernels_dir / kernel_name
        
        # Check if kernel already exists
        if kernel_dir.exists():
            if not force:
                print(f"ERROR: Kernel '{kernel_name}' already exists. Use --force to overwrite.")
                return False
            else:
                print(f"[REMOVING]  Removing existing kernel '{kernel_name}'...")
                shutil.rmtree(kernel_dir)
        
        # Create kernel directory
        kernel_dir.mkdir(parents=True, exist_ok=True)

        # Validate Python executable exists (TDD: test expects failure for invalid Python)
        if python_executable:
            python_path = Path(python_executable)
            if not python_path.exists():
                print(f"ERROR: Python executable not found: {python_executable}")
                # Clean up created directory
                if kernel_dir.exists():
                    shutil.rmtree(kernel_dir)
                return False
            if not python_path.is_file():
                print(f"ERROR: Python executable is not a file: {python_executable}")
                if kernel_dir.exists():
                    shutil.rmtree(kernel_dir)
                return False

        # Create kernel specification
        kernel_spec = create_epochly_kernel_spec(python_executable, display_name, kernel_name)
        
        # Write kernel.json
        kernel_json_path = kernel_dir / 'kernel.json'
        with open(kernel_json_path, 'w') as f:
            json.dump(kernel_spec, f, indent=2)
            
        # Create logo files if they exist
        _install_kernel_logos(kernel_dir)
        
        # Create startup script for Epochly initialization
        _create_kernel_startup_script(kernel_dir)
        
        print(f"SUCCESS: Epochly kernel '{display_name}' installed successfully!")
        print(f"[PATH] Location: {kernel_dir}")
        print(f"[READY] You can now select '{display_name}' in Jupyter Lab/Notebook")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Error installing Epochly kernel: {e}")
        return False


def _install_kernel_logos(kernel_dir: Path):
    """Install kernel logo files if available."""
    # Look for logo files in Epochly package
    try:
        import epochly
        epochly_dir = Path(epochly.__file__).parent
        logos_dir = epochly_dir / 'jupyter' / 'logos'
        
        if logos_dir.exists():
            for logo_file in logos_dir.glob('logo-*.png'):
                shutil.copy2(logo_file, kernel_dir)
                print(f"[LOGO] Installed logo: {logo_file.name}")
    except:
        # Create ASCII logo for Epochly
        
        # Could create a simple PNG logo here if needed
        pass


def _create_kernel_startup_script(kernel_dir: Path):
    """Create IPython startup script for automatic Epochly initialization."""
    startup_script = '''
# Epochly Jupyter Kernel Startup Script
# Automatically loads Epochly magic commands and initializes Epochly

import os
import warnings

try:
    # Initialize Epochly if available
    if os.getenv('EPOCHLY_AUTO_INIT', '0') == '1':
        import epochly
        
        # Load Epochly magic commands
        try:
            from epochly.jupyter import load_ipython_extension
            get_ipython().magic('load_ext epochly.jupyter')
            print("SUCCESS: Epochly initialized successfully! Type '%epochly help' for commands.")
        except Exception as e:
            print(f"WARNING:  Epochly magic commands not loaded: {e}")
            
        # Show welcome message
        print("[READY] Welcome to Python (epochly) - Epochly!")
        print("[INFO] Type '%epochly stats' to see current optimization status")
        print("TIP: Epochly automatically optimizes your code - no changes needed!")
        
except ImportError:
    print("WARNING: Epochly not available in this environment")
except Exception as e:
    warnings.warn(f"Epochly initialization failed: {e}")
'''
    
    startup_dir = kernel_dir / 'startup'
    startup_dir.mkdir(exist_ok=True)
    
    startup_file = startup_dir / '00-epochly-init.py'
    with open(startup_file, 'w') as f:
        f.write(startup_script)


def uninstall_epochly_kernel(kernel_name: str = "epochly", user: bool = True) -> bool:
    """
    Uninstall Epochly Jupyter kernel.
    
    Args:
        kernel_name: Name of kernel to uninstall
        user: Remove from user directory (vs system)
        
    Returns:
        True if uninstallation successful, False otherwise
    """
    try:
        # Get kernels directory
        if user:
            kernels_dir = get_jupyter_kernels_dir()
        else:
            try:
                result = subprocess.run([sys.executable, '-m', 'jupyter', '--system-data-dir'],
                                      capture_output=True, text=True, check=True)
                kernels_dir = Path(result.stdout.strip()) / 'kernels'
            except:
                print("ERROR: Cannot determine system kernels directory")
                return False
                
        kernel_dir = kernels_dir / kernel_name
        
        # Check if kernel exists
        if not kernel_dir.exists():
            print(f"ERROR: Kernel '{kernel_name}' not found")
            return False
            
        # Remove kernel directory
        shutil.rmtree(kernel_dir)
        print(f"SUCCESS: Epochly kernel '{kernel_name}' uninstalled successfully!")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Error uninstalling Epochly kernel: {e}")
        return False


def list_epochly_kernels(user: bool = True) -> List[Dict[str, Any]]:
    """
    List installed Epochly kernels.
    
    Args:
        user: Check user directory (vs system)
        
    Returns:
        List of kernel information dictionaries
    """
    epochly_kernels = []
    
    try:
        # Get kernels directory
        if user:
            kernels_dir = get_jupyter_kernels_dir()
        else:
            try:
                result = subprocess.run([sys.executable, '-m', 'jupyter', '--system-data-dir'],
                                      capture_output=True, text=True, check=True)
                kernels_dir = Path(result.stdout.strip()) / 'kernels'
            except:
                return epochly_kernels
                
        if not kernels_dir.exists():
            return epochly_kernels
            
        # Check each kernel directory
        for kernel_dir in kernels_dir.iterdir():
            if kernel_dir.is_dir():
                kernel_json = kernel_dir / 'kernel.json'
                if kernel_json.exists():
                    try:
                        with open(kernel_json) as f:
                            spec = json.load(f)
                            
                        # Check if it's an Epochly kernel
                        metadata = spec.get('metadata', {})
                        if metadata.get('epochly_enabled', False):
                            epochly_kernels.append({
                                'name': kernel_dir.name,
                                'display_name': spec.get('display_name', 'Unknown'),
                                'path': str(kernel_dir),
                                'epochly_version': metadata.get('epochly_version', 'unknown'),
                                'language': spec.get('language', 'python')
                            })
                            
                    except (json.JSONDecodeError, KeyError):
                        continue
                        
    except Exception:
        pass
        
    return epochly_kernels


def main():
    """Command-line interface for kernel management."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Epochly Jupyter Kernel Management')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Install command
    install_parser = subparsers.add_parser('install', help='Install Epochly kernel')
    install_parser.add_argument('--name', default='epochly', help='Kernel name')
    install_parser.add_argument('--display-name', default='Python (Epochly)', help='Display name')
    install_parser.add_argument('--python', help='Python executable path')
    install_parser.add_argument('--system', action='store_true', help='Install system-wide')
    install_parser.add_argument('--force', action='store_true', help='Overwrite existing')
    
    # Uninstall command
    uninstall_parser = subparsers.add_parser('uninstall', help='Uninstall Epochly kernel')
    uninstall_parser.add_argument('--name', default='epochly', help='Kernel name')
    uninstall_parser.add_argument('--system', action='store_true', help='Remove from system')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List Epochly kernels')
    list_parser.add_argument('--system', action='store_true', help='List system kernels')
    
    args = parser.parse_args()
    
    if args.command == 'install':
        success = install_epochly_kernel(
            kernel_name=args.name,
            display_name=args.display_name,
            user=not args.system,
            python_executable=args.python,
            force=args.force
        )
        sys.exit(0 if success else 1)
        
    elif args.command == 'uninstall':
        success = uninstall_epochly_kernel(
            kernel_name=args.name,
            user=not args.system
        )
        sys.exit(0 if success else 1)
        
    elif args.command == 'list':
        kernels = list_epochly_kernels(user=not args.system)
        if kernels:
            print("[LIST] Installed Epochly Kernels:")
            for kernel in kernels:
                print(f"  * {kernel['display_name']} ({kernel['name']})")
                print(f"    Path: {kernel['path']}")
                print(f"    Epochly Version: {kernel['epochly_version']}")
                print()
        else:
            print("[EMPTY] No Epochly kernels found")
            
    else:
        parser.print_help()


if __name__ == '__main__':
    main()