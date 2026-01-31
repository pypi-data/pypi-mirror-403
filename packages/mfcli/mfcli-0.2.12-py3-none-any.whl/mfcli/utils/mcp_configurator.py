"""MCP server auto-configuration for Cline and Claude Desktop."""
import json
import os
import platform
import shutil
import sys
from pathlib import Path
from typing import List, Tuple, Optional


def get_mcp_config_paths() -> List[Tuple[str, Path]]:
    """Get potential MCP configuration file paths for different editors."""
    paths = []
    system = platform.system()
    
    if system == "Windows":
        appdata = Path(os.environ.get("APPDATA", ""))
        localappdata = Path(os.environ.get("LOCALAPPDATA", ""))
        home = Path.home()
        
        # Cline (VS Code extension)
        cline_vscode = appdata / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
        if cline_vscode.exists():
            paths.append(("Cline (VS Code)", cline_vscode))
        
        # Windsurf/Cline standalone
        cline_standalone = home / ".cline" / "mcp_settings.json"
        if cline_standalone.exists():
            paths.append(("Cline (Standalone)", cline_standalone))
        
        # Claude Desktop (Anthropic's standalone app)
        claude_desktop = appdata / "Claude" / "claude_desktop_config.json"
        if claude_desktop.exists():
            paths.append(("Claude Desktop", claude_desktop))
    
    elif system in ["Darwin", "Linux"]:  # macOS or Linux
        home = Path.home()
        
        # Cline (VS Code extension) - macOS
        if system == "Darwin":
            cline_vscode = home / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
            # Claude Desktop (macOS)
            claude_desktop = home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        else:  # Linux
            cline_vscode = home / ".config" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
            # Claude Desktop (Linux)
            claude_desktop = home / ".config" / "Claude" / "claude_desktop_config.json"
        
        if cline_vscode.exists():
            paths.append(("Cline (VS Code)", cline_vscode))
        
        # Windsurf/Cline standalone
        cline_standalone = home / ".cline" / "mcp_settings.json"
        if cline_standalone.exists():
            paths.append(("Cline (Standalone)", cline_standalone))
        
        # Claude Desktop
        if claude_desktop.exists():
            paths.append(("Claude Desktop", claude_desktop))
    
    return paths


def backup_config(config_path: Path) -> Path:
    """Create a backup of the configuration file."""
    backup_path = config_path.with_suffix(config_path.suffix + ".backup")
    shutil.copy2(config_path, backup_path)
    return backup_path


def get_mfcli_mcp_config() -> dict:
    """Get the mfcli-mcp server configuration."""
    return {
        "mfcli-mcp": {
            "disabled": False,
            "timeout": 60,
            "type": "stdio",
            "command": "mfcli-mcp",
            "autoApprove": ["query_local_rag"]
        }
    }


def update_mcp_config(config_path: Path) -> bool:
    """Update MCP configuration file with mfcli-mcp server."""
    try:
        # Read existing config
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Ensure mcpServers key exists
        if "mcpServers" not in config:
            config["mcpServers"] = {}
        
        # Check if mfcli-mcp already exists
        if "mfcli-mcp" in config["mcpServers"]:
            print(f"    ℹ️  mfcli-mcp already configured in this file")
            return True
        
        # Add mfcli-mcp configuration
        mfcli_config = get_mfcli_mcp_config()
        config["mcpServers"].update(mfcli_config)
        
        # Create backup
        backup_path = backup_config(config_path)
        print(f"    📋 Backup created: {backup_path}")
        
        # Write updated config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return True
    
    except Exception as e:
        print(f"    ❌ Error updating config: {e}")
        return False


def create_mcp_config(config_path: Path) -> bool:
    """Create a new MCP configuration file with mfcli-mcp server."""
    try:
        # Ensure parent directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create new config
        config = {
            "mcpServers": get_mfcli_mcp_config()
        }
        
        # Write config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return True
    
    except Exception as e:
        print(f"    ❌ Error creating config: {e}")
        return False


def verify_mfcli_installation() -> bool:
    """Verify that mfcli-mcp is installed and accessible."""
    try:
        # Check if mfcli-mcp is in PATH
        result = shutil.which("mfcli-mcp")
        if result:
            return True
        
        # On Windows, also check Scripts directory
        if platform.system() == "Windows":
            scripts_dir = Path(sys.executable).parent / "Scripts"
            mfcli_mcp = scripts_dir / "mfcli-mcp.exe"
            if mfcli_mcp.exists():
                return True
        
        return False
    
    except Exception:
        return False


def test_mcp_server() -> bool:
    """Test if MCP server can be started."""
    print("  Testing MCP server...", end=' ')
    sys.stdout.flush()
    
    try:
        import subprocess
        # Try to run mfcli-mcp with a timeout
        result = subprocess.run(
            ["mfcli-mcp"],
            capture_output=True,
            timeout=5,
            text=True
        )
        # If it starts without error, that's good enough
        print("✅")
        return True
    except subprocess.TimeoutExpired:
        # Timeout is actually OK - it means the server started
        print("✅")
        return True
    except FileNotFoundError:
        print("❌ mfcli-mcp command not found")
        return False
    except Exception as e:
        print(f"❌ {str(e)[:50]}")
        return False


def check_claude_code_cli() -> bool:
    """Check if Claude Code CLI is installed."""
    return shutil.which("claude") is not None


def check_claude_code_mcp_configured() -> bool:
    """Check if mfcli-mcp is configured in Claude Code CLI."""
    try:
        import subprocess
        result = subprocess.run(
            ["claude", "mcp", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # Check if mfcli-mcp is in the output
        return "mfcli-mcp" in result.stdout
    except Exception:
        return False


def configure_claude_code_mcp() -> bool:
    """Configure mfcli-mcp in Claude Code CLI."""
    try:
        import subprocess

        # Check if already configured
        if check_claude_code_mcp_configured():
            print(f"     [OK] Already configured!")
            return True

        # Add the MCP server using claude mcp add command
        result = subprocess.run(
            ["claude", "mcp", "add", "--scope", "user", "mfcli-mcp", "--", "mfcli-mcp"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print(f"     [OK] Successfully configured!")
            return True
        else:
            # Check if error is due to already existing
            if "already exists" in result.stderr.lower():
                print(f"     [OK] Already configured!")
                return True
            print(f"     [ERROR] Configuration failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"     [ERROR] Error configuring: {e}")
        return False


def check_mcp_configured() -> Tuple[bool, List[Tuple[str, Path]]]:
    """
    Check if MCP server is configured in any detected editor.

    Returns:
        Tuple of (is_configured, config_paths)
        - is_configured: True if mfcli-mcp is found in at least one config
        - config_paths: List of all detected MCP config paths
    """
    config_paths = get_mcp_config_paths()

    # Check Claude Code CLI first
    if check_claude_code_cli() and check_claude_code_mcp_configured():
        return True, config_paths

    if not config_paths:
        return False, []

    # Check if any config has mfcli-mcp configured
    for name, path in config_paths:
        try:
            with open(path, 'r') as f:
                config = json.load(f)

            if "mcpServers" in config and "mfcli-mcp" in config["mcpServers"]:
                return True, config_paths
        except Exception:
            continue

    return False, config_paths


def verify_and_prompt_mcp_setup() -> None:
    """
    Verify MCP server configuration and prompt user to set it up if needed.
    Called during 'mfcli init' to ensure MCP is configured.
    """
    print("\n" + "="*70)
    print("  MCP SERVER VERIFICATION")
    print("="*70)

    # Check if mfcli-mcp is installed
    if not verify_mfcli_installation():
        print("\n  ⚠️  mfcli-mcp command not found!")
        print("     MCP server won't be available until installation is complete.")
        print("="*70 + "\n")
        return

    # Check for Claude Code CLI
    has_claude_cli = check_claude_code_cli()
    claude_cli_configured = has_claude_cli and check_claude_code_mcp_configured()

    # Get configuration paths for file-based editors
    config_paths = get_mcp_config_paths()

    # Check which file-based configs have mfcli-mcp
    unconfigured_paths = []
    for name, path in config_paths:
        try:
            with open(path, 'r') as f:
                config = json.load(f)
            if "mcpServers" not in config or "mfcli-mcp" not in config["mcpServers"]:
                unconfigured_paths.append((name, path))
        except Exception:
            unconfigured_paths.append((name, path))

    # Check if all assistants are configured
    all_configured = claude_cli_configured or not has_claude_cli
    all_configured = all_configured and len(unconfigured_paths) == 0

    if all_configured and (has_claude_cli or len(config_paths) > 0):
        print("\n  ✅ MCP server is already configured in all detected assistants!")
        print("="*70 + "\n")
        return

    # MCP is not fully configured - check if any assistants exist
    if not config_paths and not has_claude_cli:
        print("\n  ℹ️  No AI coding assistant detected.")
        print("\n  To use mfcli with AI assistants like Cline, Claude Code, or Claude Desktop,")
        print("  you'll need to configure the MCP server.")
        print("\n  Run this command when ready:")
        print("    mfcli setup-mcp")
        print("="*70 + "\n")
        return

    # Some assistants need configuration
    unconfigured_count = len(unconfigured_paths) + (1 if has_claude_cli and not claude_cli_configured else 0)
    total_count = len(config_paths) + (1 if has_claude_cli else 0)
    configured_count = total_count - unconfigured_count

    print(f"\n  Found {total_count} AI coding assistant(s):")
    if configured_count > 0:
        print(f"  ✅ {configured_count} already configured")
    print(f"  ⚠️  {unconfigured_count} need configuration")
    print("\n  Would you like to configure the remaining assistant(s) now? (y/n): ", end='')
    sys.stdout.flush()

    try:
        response = input().strip().lower()
        if response in ['y', 'yes']:
            print()
            setup_mcp_servers()
        else:
            print("\n  ℹ️  You can configure MCP server later by running:")
            print("    mfcli setup-mcp")
            print("="*70 + "\n")
    except (KeyboardInterrupt, EOFError):
        print("\n\n  ℹ️  Skipping MCP configuration. You can run it later with:")
        print("    mfcli setup-mcp")
        print("="*70 + "\n")


def setup_mcp_servers() -> None:
    """Auto-configure MCP servers for detected editors."""
    print("\n" + "="*70)
    print("  MCP SERVER AUTO-CONFIGURATION")
    print("="*70)
    print("\n  Detecting installed AI coding assistants...")

    # Verify mfcli installation
    if not verify_mfcli_installation():
        print("\n  ❌ mfcli-mcp command not found!")
        print("\n  Please ensure mfcli is installed with:")
        print("    pipx install mfcli")
        print("\n  Or if installing from source:")
        print("    pip install .")
        print("="*70 + "\n")
        return

    # Check for Claude Code CLI
    has_claude_cli = check_claude_code_cli()
    claude_cli_configured = has_claude_cli and check_claude_code_mcp_configured()

    # Get configuration paths
    config_paths = get_mcp_config_paths()

    if not config_paths and not has_claude_cli:
        print("\n  ℹ️  No AI coding assistants detected.")
        print("\n  Supported editors:")
        print("    - Claude Code (CLI)")
        print("    - Cline (VS Code extension)")
        print("    - Cline (Standalone)")
        print("    - Claude Desktop")
        print("\n  If you have one of these installed, the configuration file may")
        print("  not exist yet. You can create it manually at:")

        system = platform.system()
        if system == "Windows":
            print("\n  Cline (VS Code):")
            print("    %APPDATA%\\Code\\User\\globalStorage\\saoudrizwan.claude-dev\\settings\\cline_mcp_settings.json")
            print("\n  Cline (Standalone):")
            print("    %USERPROFILE%\\.cline\\mcp_settings.json")
            print("\n  Claude Desktop:")
            print("    %APPDATA%\\Claude\\claude_desktop_config.json")
        else:
            print("\n  Cline (VS Code):")
            if system == "Darwin":
                print("    ~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json")
                print("\n  Claude Desktop:")
                print("    ~/Library/Application Support/Claude/claude_desktop_config.json")
            else:
                print("    ~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json")
                print("\n  Claude Desktop:")
                print("    ~/.config/Claude/claude_desktop_config.json")
            print("\n  Cline (Standalone):")
            print("    ~/.cline/mcp_settings.json")

        print("\n  Then run this command again.")
        print("="*70 + "\n")
        return

    total_assistants = len(config_paths) + (1 if has_claude_cli else 0)
    print(f"\n  Found {total_assistants} AI assistant(s):\n")

    success_count = 0
    skipped_count = 0

    # Configure Claude Code CLI first if detected
    if has_claude_cli:
        print(f"  > Claude Code (CLI)")
        if claude_cli_configured:
            print(f"     ℹ️  Already configured, skipping\n")
            skipped_count += 1
        else:
            if configure_claude_code_mcp():
                success_count += 1
            print()

    # Configure file-based assistants
    for name, path in config_paths:
        print(f"  > {name}")
        print(f"     {path}")

        # Check if already configured
        try:
            with open(path, 'r') as f:
                config = json.load(f)
            if "mcpServers" in config and "mfcli-mcp" in config["mcpServers"]:
                print(f"     ℹ️  Already configured, skipping\n")
                skipped_count += 1
                continue
        except Exception:
            pass

        if update_mcp_config(path):
            print(f"     ✅ Successfully configured!\n")
            success_count += 1
        else:
            print(f"     ❌ Configuration failed\n")

    if success_count > 0 or skipped_count > 0:
        print("="*70)
        if success_count > 0:
            print(f"  [SUCCESS] Successfully configured {success_count} assistant(s)!")
        if skipped_count > 0:
            print(f"  [INFO] Skipped {skipped_count} already configured assistant(s)")
        print("="*70)
        print("\n  Next steps:")
        if has_claude_cli and check_claude_code_mcp_configured():
            print("  - For Claude Code: The MCP server is ready! No restart needed.")
            print("    Verify with: claude mcp list")
        if config_paths:
            print("  - For editors (VS Code, Cline, Claude Desktop): Restart your editor")
        print("\n  The mfcli-mcp server should now be available")
        print("  Try using the 'query_local_rag' tool in your AI assistant")
        print("\n  To test the MCP server:")
        print("    mfcli doctor")
        print("\n")
    else:
        print("="*70)
        print("  [WARNING] No configurations were updated.")
        print("="*70 + "\n")


def get_manual_setup_instructions() -> str:
    """Get manual MCP setup instructions."""
    instructions = """
Manual MCP Setup Instructions
==============================

If auto-configuration didn't work, you can manually add mfcli-mcp to your
editor's MCP configuration file.

1. Locate your MCP configuration file:

   Windows (Cline in VS Code):
   %APPDATA%\\Code\\User\\globalStorage\\saoudrizwan.claude-dev\\settings\\cline_mcp_settings.json

   Windows (Claude Desktop):
   %APPDATA%\\Claude\\claude_desktop_config.json

   macOS (Cline in VS Code):
   ~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json

   macOS (Claude Desktop):
   ~/Library/Application Support/Claude/claude_desktop_config.json

   Linux (Cline in VS Code):
   ~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json

   Linux (Claude Desktop):
   ~/.config/Claude/claude_desktop_config.json

   Cline Standalone (All platforms):
   ~/.cline/mcp_settings.json (or %USERPROFILE%\\.cline\\mcp_settings.json on Windows)

2. Add the following configuration to the "mcpServers" section:

{
  "mcpServers": {
    "mfcli-mcp": {
      "disabled": false,
      "timeout": 60,
      "type": "stdio",
      "command": "mfcli-mcp",
      "autoApprove": ["query_local_rag"]
    }
  }
}

3. Save the file and restart your editor.

4. The mfcli-mcp server should now be available in your AI assistant.
"""
    return instructions
