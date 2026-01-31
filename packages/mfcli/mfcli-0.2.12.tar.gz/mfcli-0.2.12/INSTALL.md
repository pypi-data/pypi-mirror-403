# mfcli Installation Guide

Comprehensive installation instructions for mfcli on Windows, Linux, and macOS.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Install](#quick-install)
- [Manual Installation](#manual-installation)
- [Installation Methods Comparison](#installation-methods-comparison)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Upgrading](#upgrading)
- [Uninstallation](#uninstallation)

## Prerequisites

### Required

- **Python 3.12.x** - mfcli requires Python 3.12
  - Download from [python.org](https://www.python.org/downloads/)
  - Verify: `python --version` or `python3 --version`

### Recommended

- **pipx** - For isolated installation (automatically installed by our scripts)
- **Git** - For installing from source (optional)

## Quick Install

The fastest way to get started:

### Windows

Open PowerShell and run:

```powershell
iwr -useb https://raw.githubusercontent.com/MultifactorAI/multifactor-adk-backend/main/install.ps1 | iex
```

### Linux/macOS

Open Terminal and run:

```bash
curl -fsSL https://raw.githubusercontent.com/MultifactorAI/multifactor-adk-backend/main/install.sh | bash
```

### What the Script Does

1. ✅ Checks Python 3.12 installation
2. ✅ Installs pipx if not present
3. ✅ Installs mfcli in an isolated environment
4. ✅ Makes `mfcli` and `mfcli-mcp` commands globally available
5. ✅ Creates configuration directory structure
6. ✅ Provides next steps guidance

**After installation**, you may need to restart your terminal for PATH changes to take effect.

## Manual Installation

### Method 1: Using pipx (Recommended)

pipx installs Python CLI tools in isolated environments while making them globally available.

#### Install pipx

**Windows:**
```powershell
python -m pip install --user pipx
python -m pipx ensurepath
```

**Linux/macOS:**
```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

Or on Debian/Ubuntu:
```bash
sudo apt-get install pipx
```

Or on macOS with Homebrew:
```bash
brew install pipx
```

#### Install mfcli

**From GitHub (current):**
```bash
pipx install git+https://github.com/MultifactorAI/multifactor-adk-backend.git
```

**From PyPI (once published):**
```bash
pipx install mfcli
```

### Method 2: Using pip

This method is suitable for development or if pipx is not available.

```bash
# Create virtual environment
python -m venv mfcli-env

# Activate virtual environment
# Windows:
mfcli-env\Scripts\activate
# Linux/macOS:
source mfcli-env/bin/activate

# Install from GitHub
pip install git+https://github.com/MultifactorAI/multifactor-adk-backend.git

# Or install from source
git clone https://github.com/MultifactorAI/multifactor-adk-backend.git
cd multifactor-adk-backend
pip install .
```

**Note**: When using pip with a virtual environment, you must activate the environment each time you want to use mfcli. For MCP server usage, pipx is strongly recommended.

### Method 3: Development Installation

For contributors and developers:

```bash
# Clone repository
git clone https://github.com/MultifactorAI/multifactor-adk-backend.git
cd multifactor-adk-backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

## Installation Methods Comparison

| Method | Global Access | Isolated Deps | MCP Compatible | Updates | Best For |
|--------|---------------|---------------|----------------|---------|----------|
| **pipx** | ✅ | ✅ | ✅ | `pipx upgrade mfcli` | Most users |
| **pip (venv)** | ❌ | ✅ | ❌ | Manual reinstall | Testing |
| **pip (global)** | ✅ | ❌ | ✅ | `pip install --upgrade` | Legacy systems |
| **Development** | ❌ | ✅ | ❌ | Git pull + reinstall | Contributors |

**Recommendation**: Use pipx for the best experience.

## Verification

After installation, verify everything is working:

### Check Installation

```bash
# Verify mfcli is installed
mfcli --help

# Verify mfcli-mcp is installed
mfcli-mcp --help
```

### Run System Check

```bash
mfcli doctor
```

This will check:
- Python version
- Package installation
- Configuration file
- API credentials
- Database connections
- MCP setup

### Test Configuration

```bash
# Check configuration
mfcli configure --check
```

## Troubleshooting

### Command Not Found

**Symptom**: `mfcli: command not found` or `'mfcli' is not recognized`

**Solutions**:

1. **Restart your terminal** - PATH changes require a new terminal session

2. **Check pipx PATH** (if using pipx):
   ```bash
   pipx ensurepath
   ```

3. **Manually add to PATH** (Windows):
   - Add `C:\Users\<username>\.local\bin` to your PATH environment variable
   - Or `C:\Users\<username>\AppData\Roaming\Python\Python312\Scripts`

4. **Manually add to PATH** (Linux/macOS):
   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```

### Python Version Mismatch

**Symptom**: Installation fails with Python version error

**Solution**:
- Install Python 3.12.x from [python.org](https://www.python.org/downloads/)
- Ensure `python --version` shows 3.12.x
- On systems with multiple Python versions, use `python3.12` explicitly

### Permission Errors

**Symptom**: Permission denied during installation

**Solutions**:

- **Never use sudo with pipx** - pipx installs in user space
- If using pip globally, consider using pipx instead
- On Windows, run PowerShell as Administrator only if necessary

### Installation Hangs

**Symptom**: Installation appears to freeze

**Solutions**:

- Check internet connection
- Try with verbose output: `pipx install -v ...`
- Check firewall/proxy settings
- Try a different network

### pipx Not Found After Install

**Symptom**: pipx installed but command not found

**Solution**:
```bash
python -m pipx ensurepath
# Then restart terminal
```

### Conflicting Dependencies

**Symptom**: Dependency conflicts during installation

**Solution**:
- pipx automatically handles this by isolating dependencies
- If using pip, create a fresh virtual environment
- Clear pip cache: `pip cache purge`

### macOS SSL Certificate Error

**Symptom**: `[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate`

This is a common macOS issue where Python doesn't have access to SSL certificates needed to connect to external APIs (Google Gemini, OpenAI, etc.).

**Automatic Fix (v0.2.1+):**

Starting with version 0.2.1, mfcli automatically detects and attempts to fix SSL certificate issues on macOS when you run any command. If the automatic fix doesn't work, try the manual solutions below.

**Manual Solutions:**

**Option 1: Install Python SSL Certificates (Recommended)**

Run the certificate installation script that comes with Python:

```bash
# Find your Python 3.12 installation
# Common locations:
# - /Applications/Python\ 3.12/Install\ Certificates.command
# - /Library/Frameworks/Python.framework/Versions/3.12/Install\ Certificates.command

# Run the installer
/Applications/Python\ 3.12/Install\ Certificates.command
```

Or manually:
```bash
# Install certifi package
pip3 install --upgrade certifi

# Link certifi certificates to Python
cd /Applications/Python\ 3.12/
./Install\ Certificates.command
```

**Option 2: Install via Homebrew Python**

If you installed Python via Homebrew:

```bash
# Reinstall Python with certificates
brew reinstall python@3.12

# Or install certifi
pip3 install --upgrade certifi
```

**Option 3: Use certifi Package**

```bash
# Install certifi in the pipx environment
pipx inject mfcli certifi

# Or if using pip
pip install --upgrade certifi
```

**Option 4: Manual Certificate Installation**

```bash
# Download and install certificates
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade certifi
python3 -c "import certifi; print(certifi.where())"
```

**After applying any solution, test with:**
```bash
# Test SSL connection
python3 -c "import ssl; import urllib.request; urllib.request.urlopen('https://www.google.com')"

# If successful, try mfcli again
mfcli run
```

**Why this happens:**
- macOS no longer includes OpenSSL by default
- Python needs explicit SSL certificate configuration
- This affects all HTTPS connections to external APIs

**Note:** This is NOT related to environment variable case (lowercase vs uppercase).

## Upgrading

### Using pipx

```bash
# Upgrade to latest version
pipx upgrade mfcli

# Reinstall (if upgrade fails)
pipx reinstall mfcli
```

### Using pip

```bash
# Activate virtual environment first
pip install --upgrade git+https://github.com/MultifactorAI/multifactor-adk-backend.git
```

### From PyPI (once published)

```bash
pipx upgrade mfcli
# or
pip install --upgrade mfcli
```

## Uninstallation

### Using pipx

```bash
# Complete removal
pipx uninstall mfcli

# Optional: Remove configuration
# Windows: Remove C:\Users\<username>\Multifactor
# Linux/macOS: rm -rf ~/Multifactor
```

### Using pip

```bash
# Activate virtual environment first
pip uninstall mfcli

# Remove virtual environment
rm -rf mfcli-env  # or venv
```

### Clean Removal

To completely remove all mfcli data:

```bash
# Uninstall package
pipx uninstall mfcli

# Remove configuration (optional)
# Windows:
Remove-Item -Recurse -Force $env:USERPROFILE\Multifactor
# Linux/macOS:
rm -rf ~/Multifactor

# Remove application data (optional)
# Windows:
Remove-Item -Recurse -Force $env:LOCALAPPDATA\Multifactor
# Linux:
rm -rf ~/.local/share/Multifactor
# macOS:
rm -rf ~/Library/Application\ Support/Multifactor
```

## Next Steps

After successful installation:

1. **Configure API keys**:
   ```bash
   mfcli configure
   ```

2. **Setup MCP server** (optional):
   ```bash
   mfcli setup-mcp
   ```

3. **Initialize a project**:
   ```bash
   cd /path/to/your/hardware/project
   mfcli init
   ```

4. **Process documents**:
   ```bash
   mfcli run
   ```

## Getting Help

- **Documentation**: [README.md](README.md)
- **MCP Setup**: [MCP_SETUP.md](MCP_SETUP.md)
- **Configuration**: [CONFIGURATION.md](CONFIGURATION.md)
- **Issues**: [GitHub Issues](https://github.com/MultifactorAI/multifactor-adk-backend/issues)

## Platform-Specific Notes

### Windows

- PowerShell 5.1 or later recommended
- May need to enable script execution: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`
- Antivirus may flag installation - add exception if needed

### macOS

- May need to install Command Line Tools: `xcode-select --install`
- Homebrew installation of Python recommended
- ARM (M1/M2) and Intel both supported

### Linux

- Ubuntu/Debian: May need `python3-venv` package
- Some distributions require `python3-dev` for building dependencies
- SELinux may require policy adjustments

---

For more detailed information, see the main [README.md](README.md).
