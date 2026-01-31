"""SSL Certificate installer for macOS."""
import platform
import subprocess
import sys
from pathlib import Path
from typing import Optional

from mfcli.utils.logger import get_logger

logger = get_logger(__name__)


def is_macos() -> bool:
    """Check if running on macOS."""
    return platform.system() == "Darwin"


def check_ssl_certificates() -> bool:
    """
    Check if SSL certificates are properly installed.
    
    Returns:
        True if certificates are working, False otherwise
    """
    try:
        import ssl
        import urllib.request
        
        # Try to make a simple HTTPS request
        urllib.request.urlopen('https://www.google.com', timeout=5)
        return True
    except Exception as e:
        logger.debug(f"SSL certificate check failed: {e}")
        return False


def find_python_cert_installer() -> Optional[Path]:
    """
    Find the Python certificate installer script.
    
    Returns:
        Path to Install Certificates.command if found, None otherwise
    """
    # Common locations for Python installations
    possible_paths = [
        Path(f"/Applications/Python {sys.version_info.major}.{sys.version_info.minor}/Install Certificates.command"),
        Path(f"/Library/Frameworks/Python.framework/Versions/{sys.version_info.major}.{sys.version_info.minor}/Install Certificates.command"),
        Path(sys.prefix) / "Install Certificates.command",
    ]
    
    for path in possible_paths:
        if path.exists():
            logger.debug(f"Found certificate installer at: {path}")
            return path
    
    return None


def install_certifi_package() -> bool:
    """
    Install/upgrade certifi package as a fallback solution.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Installing certifi package...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "certifi"],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("✅ certifi package installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install certifi: {e.stderr}")
        return False


def run_certificate_installer(cert_script_path: Path) -> bool:
    """
    Run the Python certificate installer script.
    
    Args:
        cert_script_path: Path to the Install Certificates.command script
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Running Python certificate installer...")
        result = subprocess.run(
            ["bash", str(cert_script_path)],
            check=True,
            capture_output=True,
            text=True
        )
        logger.debug(f"Certificate installer output: {result.stdout}")
        logger.info("✅ SSL certificates installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run certificate installer: {e.stderr}")
        return False


def install_ssl_certificates(silent: bool = False) -> bool:
    """
    Install SSL certificates on macOS if needed.
    
    Args:
        silent: If True, don't print informational messages to console
        
    Returns:
        True if certificates are working (or were successfully installed), False otherwise
    """
    # Only run on macOS
    if not is_macos():
        return True
    
    # Check if certificates are already working
    if check_ssl_certificates():
        logger.debug("SSL certificates are already working")
        return True
    
    if not silent:
        print("\n" + "="*70)
        print("  macOS SSL Certificate Setup")
        print("="*70)
        print("\n  Detecting SSL certificate issue...")
        print("  Installing certificates to enable API connections...\n")
    
    # Try to find and run Python's certificate installer
    cert_installer = find_python_cert_installer()
    if cert_installer:
        if not silent:
            print(f"  Found certificate installer: {cert_installer}")
        if run_certificate_installer(cert_installer):
            # Verify it worked
            if check_ssl_certificates():
                if not silent:
                    print("\n  ✅ SSL certificates installed successfully!")
                    print("="*70 + "\n")
                return True
    
    # Fallback: install certifi package
    if not silent:
        print("  Trying alternative method (certifi package)...")
    
    if install_certifi_package():
        # Verify it worked
        if check_ssl_certificates():
            if not silent:
                print("\n  ✅ SSL certificates configured successfully!")
                print("="*70 + "\n")
            return True
    
    # If we got here, automatic installation failed
    if not silent:
        print("\n  ⚠️  Automatic SSL certificate installation failed.")
        print("="*70)
        print("\n  Please install SSL certificates manually:")
        print("\n  Option 1: Run Python's certificate installer")
        if cert_installer:
            print(f"    {cert_installer}")
        else:
            print(f"    /Applications/Python {sys.version_info.major}.{sys.version_info.minor}/Install Certificates.command")
        print("\n  Option 2: Install via Homebrew")
        print("    brew reinstall python@3.12")
        print("\n  Option 3: Install certifi manually")
        print("    pip3 install --upgrade certifi")
        print("\n  See INSTALL.md for detailed instructions.")
        print("="*70 + "\n")
    
    return False


def check_and_install_ssl_certificates() -> None:
    """
    Check SSL certificates and install if needed (main entry point).
    Only runs on macOS, silently succeeds on other platforms.
    """
    if not is_macos():
        return
    
    # Check if certificates are working
    if check_ssl_certificates():
        return
    
    # Try to install automatically
    logger.info("SSL certificate issue detected on macOS, attempting automatic fix...")
    success = install_ssl_certificates(silent=False)
    
    if not success:
        logger.warning("Could not automatically install SSL certificates. Manual installation may be required.")


if __name__ == "__main__":
    # Allow running as a standalone script for testing
    print("Checking SSL certificates...")
    if check_ssl_certificates():
        print("✅ SSL certificates are working correctly")
    else:
        print("❌ SSL certificate issue detected")
        install_ssl_certificates(silent=False)
