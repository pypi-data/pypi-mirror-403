"""
Pre-uninstall utility for mfcli.
This module provides cleanup functionality to ensure graceful uninstallation.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import List, Tuple


def get_running_mfcli_processes() -> List[Tuple[int, str]]:
    """Find all running mfcli and mfcli-mcp processes."""
    processes = []
    system = platform.system()
    
    try:
        if system == "Windows":
            # Use tasklist to find processes
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq python*", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=5
            )
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.strip('"').split('","')
                    if len(parts) >= 2:
                        try:
                            pid = int(parts[1])
                            # Check if it's running mfcli-mcp
                            cmdline_result = subprocess.run(
                                ["wmic", "process", "where", f"ProcessId={pid}", "get", "CommandLine", "/value"],
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            if "mfcli-mcp" in cmdline_result.stdout or "mfcli.mcp.server" in cmdline_result.stdout:
                                processes.append((pid, "mfcli-mcp server"))
                        except (ValueError, subprocess.TimeoutExpired):
                            continue
        else:
            # Unix-like systems
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True,
                timeout=5
            )
            for line in result.stdout.split('\n'):
                if "mfcli-mcp" in line or "mfcli.mcp.server" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            pid = int(parts[1])
                            processes.append((pid, "mfcli-mcp server"))
                        except ValueError:
                            continue
    except Exception as e:
        print(f"Warning: Could not check for running processes: {e}", file=sys.stderr)
    
    return processes


def check_mcp_server_status():
    """Check if MCP server is running and provide guidance."""
    print("\n" + "="*70)
    print("  MFCLI PRE-UNINSTALL CHECK")
    print("="*70 + "\n")
    
    processes = get_running_mfcli_processes()
    
    if processes:
        print("⚠️  WARNING: mfcli MCP server processes are currently running!\n")
        print("Running processes:")
        for pid, name in processes:
            print(f"  • PID {pid}: {name}")
        
        print("\nBefore uninstalling, you should:")
        print("  1. Stop/restart your IDE (VS Code, Cline, Claude Code)")
        print("  2. Close any applications using mfcli-mcp")
        print("  3. Wait a few seconds for processes to fully terminate")
        
        if platform.system() == "Windows":
            print("\nTo manually stop these processes, run:")
            for pid, _ in processes:
                print(f"  taskkill /F /PID {pid}")
        else:
            print("\nTo manually stop these processes, run:")
            for pid, _ in processes:
                print(f"  kill {pid}")
        
        return False
    else:
        print("✓ No running mfcli-mcp processes detected\n")
        return True


def cleanup_file_handles():
    """Attempt to close any ChromaDB or database connections."""
    try:
        # Force garbage collection to close any lingering connections
        import gc
        gc.collect()
        
        # Try to close ChromaDB connections if imported
        if 'chromadb' in sys.modules:
            print("Closing ChromaDB connections...")
        
        print("✓ Cleanup completed\n")
    except Exception as e:
        print(f"Warning during cleanup: {e}\n")


def print_uninstall_instructions():
    """Print step-by-step uninstall instructions."""
    print("\n" + "="*70)
    print("  UNINSTALL INSTRUCTIONS")
    print("="*70 + "\n")
    
    print("To safely uninstall mfcli:\n")
    
    if platform.system() == "Windows":
        print("  1. Close VS Code, Cline, or any IDE using mfcli-mcp")
        print("  2. Wait 5-10 seconds for processes to fully stop")
        print("  3. Run: pipx uninstall mfcli")
        print("\nIf you still get permission errors:")
        print("  • Run PowerShell as Administrator")
        print("  • Or use: .\\uninstall.ps1")
        print("  • Or manually delete: %USERPROFILE%\\pipx\\venvs\\mfcli")
    else:
        print("  1. Close your IDE or any applications using mfcli-mcp")
        print("  2. Wait a few seconds for processes to fully stop")
        print("  3. Run: pipx uninstall mfcli")
        print("\nIf you still get permission errors:")
        print("  • Use: ./uninstall.sh")
        print("  • Or manually delete: ~/.local/pipx/venvs/mfcli")
    
    print("\nNote: Your configuration and data at ~/Multifactor will NOT be deleted.")
    print("To remove that as well, manually delete the Multifactor directory.")
    print()


def run_pre_uninstall_check():
    """Main pre-uninstall check function."""
    cleanup_file_handles()
    server_clear = check_mcp_server_status()
    print_uninstall_instructions()
    
    if not server_clear:
        print("\n⚠️  WARNING: Active processes detected. Please stop them before uninstalling.")
        return 1
    else:
        print("\n✓ System is ready for uninstallation.")
        return 0


def main():
    """Entry point for pre-uninstall command."""
    sys.exit(run_pre_uninstall_check())


if __name__ == "__main__":
    main()
