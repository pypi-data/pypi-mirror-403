#!/usr/bin/env python3
"""
Windows Service Entry Point for pyWATS Client

This module provides the entry point for running pyWATS Client as a Windows Service.
It's used by the frozen executable (pywats-service.exe) created by cx_Freeze.

Usage:
    # Install service
    pywats-service.exe install
    
    # Start service
    pywats-service.exe start
    
    # Stop service
    pywats-service.exe stop
    
    # Remove service
    pywats-service.exe remove
    
    # Debug mode (run in console)
    pywats-service.exe debug
"""

import sys
import os

# Ensure the frozen app can find its modules
if getattr(sys, 'frozen', False):
    # Running as frozen executable
    app_dir = os.path.dirname(sys.executable)
    sys.path.insert(0, app_dir)
    sys.path.insert(0, os.path.join(app_dir, 'lib'))

def main():
    """Main entry point for Windows Service."""
    try:
        from pywats_client.control.windows_native_service import PyWATSService, HAS_PYWIN32
        
        if not HAS_PYWIN32:
            print("ERROR: pywin32 is not available")
            print("Windows Service requires pywin32 package")
            sys.exit(1)
        
        import win32serviceutil
        
        # Handle command line
        if len(sys.argv) == 1:
            # No arguments - try to start service dispatcher
            try:
                import servicemanager
                servicemanager.Initialize()
                servicemanager.PrepareToHostSingle(PyWATSService)
                servicemanager.StartServiceCtrlDispatcher()
            except Exception as e:
                print(f"Service dispatcher failed: {e}")
                print("\nUsage: pywats-service.exe [install|start|stop|remove|debug]")
                sys.exit(1)
        else:
            # Handle service commands
            win32serviceutil.HandleCommandLine(PyWATSService)
            
    except ImportError as e:
        print(f"Import error: {e}")
        print("\nMake sure pyWATS Client is properly installed")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
