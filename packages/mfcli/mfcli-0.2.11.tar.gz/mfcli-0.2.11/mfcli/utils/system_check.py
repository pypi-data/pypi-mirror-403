"""System health check and diagnostics for mfcli."""
import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Tuple, Optional

from mfcli.utils.directory_manager import app_dirs


def check_python_version() -> Tuple[bool, str]:
    """Check Python version."""
    version = sys.version_info
    if version.major == 3 and version.minor == 12:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    else:
        return False, f"Python {version.major}.{version.minor}.{version.micro} (requires 3.12.x)"


def check_pipx_installation() -> Tuple[bool, str]:
    """Check if pipx is installed."""
    pipx_path = shutil.which("pipx")
    if pipx_path:
        return True, f"Found at {pipx_path}"
    else:
        return False, "Not installed"


def check_mfcli_installation() -> Tuple[bool, str]:
    """Check if mfcli is properly installed."""
    mfcli_path = shutil.which("mfcli")
    mfcli_mcp_path = shutil.which("mfcli-mcp")
    
    if mfcli_path and mfcli_mcp_path:
        return True, f"Both mfcli and mfcli-mcp found"
    elif mfcli_path:
        return False, "mfcli found but mfcli-mcp missing"
    else:
        return False, "Not found in PATH"


def check_env_file() -> Tuple[bool, str]:
    """Check if .env file exists and has required keys."""
    env_path = app_dirs.env_file_path
    
    if not env_path.exists():
        return False, f"Not found at {env_path}"
    
    # Read and check for required keys
    required_keys = ["google_api_key", "openai_api_key",
                     "digikey_client_id", "digikey_client_secret"]
    
    with open(env_path, 'r') as f:
        content = f.read()
    
    missing_keys = []
    for key in required_keys:
        if key not in content or f"{key}=your_" in content:
            missing_keys.append(key)
    
    if missing_keys:
        return False, f"Missing or unconfigured: {', '.join(missing_keys)}"
    
    return True, f"Found at {env_path}"


def test_google_api() -> Tuple[bool, str]:
    """Test Google Gemini API connection."""
    try:
        from mfcli.utils.config import get_config
        config = get_config()
        
        if not config.google_api_key or config.google_api_key.startswith("your_"):
            return False, "API key not configured"
        
        import google.generativeai as genai
        genai.configure(api_key=config.google_api_key)
        
        # Try to list models
        models = list(genai.list_models())
        if models:
            return True, f"Connected (found {len(models)} models)"
        else:
            return False, "No models found"
    
    except Exception as e:
        return False, f"Error: {str(e)[:60]}"


def test_openai_api() -> Tuple[bool, str]:
    """Test OpenAI API connection."""
    try:
        from mfcli.utils.config import get_config
        config = get_config()
        
        if not config.openai_api_key or config.openai_api_key.startswith("your_"):
            return False, "API key not configured"
        
        from openai import OpenAI
        client = OpenAI(api_key=config.openai_api_key)
        
        # Try to list models
        models = client.models.list()
        return True, "Connected"
    
    except Exception as e:
        return False, f"Error: {str(e)[:60]}"


def check_chromadb() -> Tuple[bool, str]:
    """Check ChromaDB setup."""
    try:
        chroma_dir = app_dirs.chroma_db_dir
        
        if not chroma_dir.exists():
            return False, f"Directory not found: {chroma_dir}"
        
        import chromadb
        from chromadb.utils import embedding_functions
        from mfcli.utils.config import get_config
        
        config = get_config()
        client = chromadb.PersistentClient(path=str(chroma_dir))
        
        # Try to get collection
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=config.openai_api_key,
            model_name=config.embedding_model
        )
        collection = client.get_or_create_collection("engineering_docs", embedding_function=openai_ef)
        
        count = collection.count()
        return True, f"Connected ({count} documents)"
    
    except Exception as e:
        return False, f"Error: {str(e)[:60]}"


def check_ssl_certificates() -> Tuple[bool, str]:
    """Check if SSL certificates are properly installed (macOS-specific)."""
    # Only relevant on macOS
    if platform.system() != "Darwin":
        return True, "Not applicable (non-macOS system)"
    
    try:
        import ssl
        import urllib.request
        
        # Try to make a simple HTTPS request
        urllib.request.urlopen('https://www.google.com', timeout=5)
        return True, "Working correctly"
    
    except Exception as e:
        error_msg = str(e)
        if "CERTIFICATE_VERIFY_FAILED" in error_msg:
            return False, "Certificate verification failed - run automatic fix"
        else:
            return False, f"Error: {error_msg[:60]}"


def check_mcp_config() -> Tuple[bool, str]:
    """Check if MCP server is configured."""
    try:
        from mfcli.utils.mcp_configurator import get_mcp_config_paths
        
        config_paths = get_mcp_config_paths()
        
        if not config_paths:
            return False, "No MCP config files found"
        
        # Check if mfcli-mcp is configured in any of them
        import json
        configured_editors = []
        
        for name, path in config_paths:
            try:
                with open(path, 'r') as f:
                    config = json.load(f)
                
                if "mcpServers" in config and "mfcli-mcp" in config["mcpServers"]:
                    configured_editors.append(name)
            except:
                pass
        
        if configured_editors:
            return True, f"Configured in: {', '.join(configured_editors)}"
        else:
            return False, f"Found {len(config_paths)} config(s) but mfcli-mcp not configured"
    
    except Exception as e:
        return False, f"Error: {str(e)[:60]}"


def check_sqlite_db() -> Tuple[bool, str]:
    """Check SQLite database."""
    try:
        from mfcli.utils.config import get_config
        config = get_config()
        
        db_path = Path(config.sqlite_db_path)
        
        if not db_path.exists():
            return False, f"Database not found: {db_path}"
        
        # Try to connect
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        
        if tables:
            return True, f"Connected ({len(tables)} tables)"
        else:
            return False, "Database has no tables"
    
    except Exception as e:
        return False, f"Error: {str(e)[:60]}"


def print_check_result(component: str, passed: bool, message: str, indent: int = 2) -> None:
    """Print a check result with formatting."""
    indent_str = " " * indent
    status = "✅" if passed else "❌"
    print(f"{indent_str}{status} {component}: {message}")


def run_system_check() -> None:
    """Run comprehensive system health check."""
    print("\n" + "="*70)
    print("  MFCLI SYSTEM HEALTH CHECK")
    print("="*70)
    
    print("\n  System Information:")
    print(f"    OS: {platform.system()} {platform.release()}")
    print(f"    Architecture: {platform.machine()}")
    
    all_checks = []
    
    # Python version
    print("\n  Python Environment:")
    passed, msg = check_python_version()
    print_check_result("Python Version", passed, msg)
    all_checks.append(passed)
    
    # pipx installation
    passed, msg = check_pipx_installation()
    print_check_result("pipx", passed, msg)
    
    # mfcli installation
    passed, msg = check_mfcli_installation()
    print_check_result("mfcli Installation", passed, msg)
    all_checks.append(passed)
    
    # Configuration
    print("\n  Configuration:")
    passed, msg = check_env_file()
    print_check_result("Environment File", passed, msg)
    all_checks.append(passed)
    
    # SSL certificates (macOS only)
    if platform.system() == "Darwin":
        print("\n  macOS SSL Certificates:")
        passed, msg = check_ssl_certificates()
        print_check_result("SSL Certificates", passed, msg)
        if not passed:
            print(f"    💡 Tip: mfcli will automatically attempt to fix this on next run")
            print(f"    Or manually run: /Applications/Python 3.12/Install Certificates.command")
    
    # API connections
    print("\n  API Connections:")
    passed, msg = test_google_api()
    print_check_result("Google Gemini API", passed, msg)
    all_checks.append(passed)
    
    passed, msg = test_openai_api()
    print_check_result("OpenAI API", passed, msg)
    all_checks.append(passed)
    
    # Data storage
    print("\n  Data Storage:")
    passed, msg = check_sqlite_db()
    print_check_result("SQLite Database", passed, msg)
    all_checks.append(passed)
    
    passed, msg = check_chromadb()
    print_check_result("ChromaDB", passed, msg)
    all_checks.append(passed)
    
    # MCP configuration
    print("\n  MCP Server:")
    passed, msg = check_mcp_config()
    print_check_result("MCP Configuration", passed, msg)
    
    # Summary
    print("\n" + "="*70)
    critical_checks_passed = sum(all_checks)
    total_critical = len(all_checks)
    
    if critical_checks_passed == total_critical:
        print("  ✅ ALL CRITICAL CHECKS PASSED")
        print("  Your mfcli installation is healthy and ready to use!")
    else:
        print(f"  ⚠️  {critical_checks_passed}/{total_critical} CRITICAL CHECKS PASSED")
        print("\n  Recommendations:")
        
        if not all_checks[0]:  # Python version
            print("    - Install Python 3.12.x")
        
        if not all_checks[1]:  # mfcli installation
            print("    - Install mfcli: pipx install mfcli")
        
        if not all_checks[2]:  # env file
            print("    - Configure mfcli: mfcli configure")
        
        if not all_checks[3]:  # Google API
            print("    - Check Google API key in configuration")
        
        if not all_checks[4]:  # OpenAI API
            print("    - Check OpenAI API key in configuration")
        
        if not all_checks[5]:  # SQLite
            print("    - Run: mfcli init (in a project directory)")
        
        if not all_checks[6]:  # ChromaDB
            print("    - Run: mfcli run (to process documents and create database)")
    
    print("="*70)
    print("\n  For more help:")
    print("    - Configuration: mfcli configure")
    print("    - MCP Setup: mfcli setup-mcp")
    print("    - Check config: mfcli configure --check")
    print("\n")
