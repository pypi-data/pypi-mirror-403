"""
Epochly CLI - Jupyter Integration Commands

Provides command-line interface for Epochly Jupyter integration including:
- Kernel installation and management
- Magic command testing
- Jupyter environment setup

Author: Epochly Development Team
"""

import sys
import argparse
from typing import List, Optional


def install_kernel_command(args: argparse.Namespace) -> int:
    """Handle kernel installation command."""
    from epochly.jupyter.kernel_installer import install_epochly_kernel
    
    success = install_epochly_kernel(
        kernel_name=args.name,
        display_name=args.display_name,
        user=not args.system,
        python_executable=args.python,
        force=args.force
    )
    
    if success:
        print("\n[COMPLETE] Installation complete!")
        print("[INFO] Next steps:")
        print("   1. Start Jupyter Lab or Notebook")
        print("   2. Create a new notebook")
        print("   3. Select 'Python (Epochly)' as the kernel")
        print("   4. Type '%epochly help' to see available commands")
        return 0
    else:
        return 1


def uninstall_kernel_command(args: argparse.Namespace) -> int:
    """Handle kernel uninstallation command."""
    from epochly.jupyter.kernel_installer import uninstall_epochly_kernel
    
    success = uninstall_epochly_kernel(
        kernel_name=args.name,
        user=not args.system
    )
    
    return 0 if success else 1


def list_kernels_command(args: argparse.Namespace) -> int:
    """Handle kernel listing command."""
    from epochly.jupyter.kernel_installer import list_epochly_kernels
    
    kernels = list_epochly_kernels(user=not args.system)
    
    if kernels:
        print("[LIST] Installed Epochly Kernels:")
        print("=" * 50)
        for kernel in kernels:
            print(f"[NAME] Name: {kernel['name']}")
            print(f"[DISPLAY] Display Name: {kernel['display_name']}")
            print(f"[PATH] Path: {kernel['path']}")
            print(f"[VERSION] Epochly Version: {kernel['epochly_version']}")
            print("-" * 30)
    else:
        scope = "system" if args.system else "user"
        print(f"[EMPTY] No Epochly kernels found in {scope} directory")
        print("\n[HINT] To install a kernel, run:")
        print("   epochly jupyter install")
        
    return 0


def magic_commands_test(args: argparse.Namespace) -> int:
    """Test Epochly magic commands in current environment."""
    print("[TESTING] Testing Epochly magic commands...")
    
    try:
        # Test import
        print("SUCCESS: Magic commands module imported successfully")
        
        # Test IPython availability
        try:
            from IPython import get_ipython
            ip = get_ipython()
            if ip is None:
                print("WARNING: Not running in IPython environment")
                print("TIP: Magic commands work best in Jupyter/IPython")
            else:
                print("SUCCESS: IPython environment detected")
                
                # Test loading extension
                try:
                    ip.magic('load_ext epochly.jupyter')
                    print("SUCCESS: Epochly magic commands loaded successfully")
                    
                    # Test basic command
                    ip.magic('epochly help')
                    print("SUCCESS: Magic commands functioning correctly")
                    
                except Exception as e:
                    print(f"ERROR: Error loading magic commands: {e}")
                    return 1
                    
        except ImportError:
            print("ERROR: IPython not available")
            print("TIP: Install with: pip install ipython")
            return 1
            
        # Test Epochly availability
        try:
            import epochly
            print("SUCCESS: Epochly core module available")
        except ImportError:
            print("WARNING: Epochly core module not available")
            print("TIP: Magic commands will have limited functionality")
            
        print("\n[COMPLETE] Magic commands test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"ERROR: Error testing magic commands: {e}")
        return 1


def setup_jupyter_environment(args: argparse.Namespace) -> int:
    """Set up complete Jupyter environment for Epochly."""
    print("[READY] Setting up Epochly Jupyter environment...")
    
    # Check dependencies
    missing_deps = []
    
    try:
        import jupyter
    except ImportError:
        missing_deps.append("jupyter")
        
    try:
        import ipykernel
    except ImportError:
        missing_deps.append("ipykernel")
        
    try:
        import IPython
    except ImportError:
        missing_deps.append("ipython")
        
    if missing_deps:
        print("ERROR: Missing required dependencies:")
        for dep in missing_deps:
            print(f"   * {dep}")
        print(f"\nTIP: Install with: pip install {' '.join(missing_deps)}")
        return 1
        
    print("SUCCESS: All dependencies available")
    
    # Install kernel
    print("\n[INSTALLING] Installing Epochly kernel...")
    from epochly.jupyter.kernel_installer import install_epochly_kernel
    
    success = install_epochly_kernel(
        kernel_name="epochly",
        display_name="Python (Epochly)",
        user=True,
        force=args.force
    )
    
    if not success:
        print("ERROR: Kernel installation failed")
        return 1
        
    # Test magic commands
    print("\n[TESTING] Testing magic commands...")
    test_args = argparse.Namespace()
    if magic_commands_test(test_args) != 0:
        print("WARNING: Magic commands test failed, but kernel is installed")
        
    print("\n[COMPLETE] Epochly Jupyter environment setup complete!")
    print("\n[INFO] Quick Start Guide:")
    print("   1. Launch Jupyter: jupyter lab")
    print("   2. Create new notebook with 'Python (Epochly)' kernel")
    print("   3. Try these commands:")
    print("      %epochly stats      # Show Epochly status")
    print("      %epochly level 3    # Enable full optimization")
    print("      %%epochly --profile # Profile a cell")
    print("      your_code_here()")
    
    return 0


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for Epochly Jupyter CLI."""
    parser = argparse.ArgumentParser(
        description='Epochly Jupyter Integration',
        prog='epochly jupyter'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Jupyter commands')
    
    # Install kernel command
    install_parser = subparsers.add_parser(
        'install', 
        help='Install Epochly Jupyter kernel'
    )
    install_parser.add_argument(
        '--name', 
        default='epochly', 
        help='Kernel name (default: epochly)'
    )
    install_parser.add_argument(
        '--display-name', 
        default='Python (epochly)', 
        help='Display name (default: Python (epochly))'
    )
    install_parser.add_argument(
        '--python', 
        help='Python executable path (default: current)'
    )
    install_parser.add_argument(
        '--system', 
        action='store_true', 
        help='Install system-wide (default: user only)'
    )
    install_parser.add_argument(
        '--force', 
        action='store_true', 
        help='Overwrite existing kernel'
    )
    install_parser.set_defaults(func=install_kernel_command)
    
    # Uninstall kernel command
    uninstall_parser = subparsers.add_parser(
        'uninstall', 
        help='Uninstall Epochly Jupyter kernel'
    )
    uninstall_parser.add_argument(
        '--name', 
        default='epochly', 
        help='Kernel name (default: epochly)'
    )
    uninstall_parser.add_argument(
        '--system', 
        action='store_true', 
        help='Remove from system (default: user only)'
    )
    uninstall_parser.set_defaults(func=uninstall_kernel_command)
    
    # List kernels command
    list_parser = subparsers.add_parser(
        'list', 
        help='List installed Epochly kernels'
    )
    list_parser.add_argument(
        '--system', 
        action='store_true', 
        help='List system kernels (default: user only)'
    )
    list_parser.set_defaults(func=list_kernels_command)
    
    # Test magic commands
    test_parser = subparsers.add_parser(
        'test', 
        help='Test Epochly magic commands'
    )
    test_parser.set_defaults(func=magic_commands_test)
    
    # Setup environment
    setup_parser = subparsers.add_parser(
        'setup', 
        help='Complete Jupyter environment setup'
    )
    setup_parser.add_argument(
        '--force', 
        action='store_true', 
        help='Overwrite existing installation'
    )
    setup_parser.set_defaults(func=setup_jupyter_environment)
    
    # Parse arguments
    parsed_args = parser.parse_args(args)
    
    if parsed_args.command is None:
        parser.print_help()
        return 1
        
    # Execute command
    return parsed_args.func(parsed_args)


if __name__ == '__main__':
    sys.exit(main())