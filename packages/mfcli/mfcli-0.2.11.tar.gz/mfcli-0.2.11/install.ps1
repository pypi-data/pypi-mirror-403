# mfcli Installation Script for Windows
# This script installs mfcli using pipx for isolated dependency management

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "======================================================================"
Write-Host "  MFCLI INSTALLATION FOR WINDOWS"
Write-Host "======================================================================"
Write-Host ""

# Check Python version
Write-Host "Checking Python installation..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  Found: $pythonVersion" -ForegroundColor Green
    
    # Extract version numbers
    if ($pythonVersion -match "Python (\d+)\.(\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        
        if ($major -ne 3 -or $minor -ne 12) {
            Write-Host "  Warning: Python 3.12.x is recommended (you have $major.$minor)" -ForegroundColor Yellow
            $continue = Read-Host "  Continue anyway? (y/N)"
            if ($continue -ne "y" -and $continue -ne "Y") {
                Write-Host "  Installation cancelled." -ForegroundColor Red
                exit 1
            }
        }
    }
}
catch {
    Write-Host "  Error: Python not found!" -ForegroundColor Red
    Write-Host "  Please install Python 3.12 from https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Check if pipx is installed
Write-Host ""
Write-Host "Checking pipx installation..." -ForegroundColor Cyan
$pipxInstalled = Get-Command pipx -ErrorAction SilentlyContinue

if (-not $pipxInstalled) {
    Write-Host "  pipx not found. Installing pipx..." -ForegroundColor Yellow
    try {
        python -m pip install --user pipx
        python -m pipx ensurepath
        
        Write-Host "  pipx installed successfully!" -ForegroundColor Green
        Write-Host "  Note: You may need to restart your terminal for PATH changes to take effect." -ForegroundColor Yellow
        
        # Add pipx to current session PATH
        $pipxPath = [System.IO.Path]::Combine($env:USERPROFILE, ".local", "bin")
        if (Test-Path $pipxPath) {
            $env:PATH = "$pipxPath;$env:PATH"
        }
    }
    catch {
        Write-Host "  Error installing pipx: $_" -ForegroundColor Red
        Write-Host "  Please install pipx manually: python -m pip install --user pipx" -ForegroundColor Yellow
        exit 1
    }
}
else {
    Write-Host "  pipx already installed" -ForegroundColor Green
}

# Install mfcli
Write-Host ""
Write-Host "Installing mfcli..." -ForegroundColor Cyan

# Determine installation source
$installFromPyPI = $false
if ($env:MFCLI_INSTALL_SOURCE -eq "pypi") {
    $installFromPyPI = $true
}

try {
    if ($installFromPyPI) {
        Write-Host "  Installing from PyPI..." -ForegroundColor Yellow
        pipx install mfcli
    }
    else {
        Write-Host "  Installing from GitHub..." -ForegroundColor Yellow
        pipx install git+https://github.com/MultifactorAI/multifactor-adk-backend.git
    }
    
    Write-Host "  mfcli installed successfully!" -ForegroundColor Green
}
catch {
    Write-Host "  Error installing mfcli: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Troubleshooting:" -ForegroundColor Yellow
    Write-Host "    1. Ensure Python 3.12 is installed"
    Write-Host "    2. Try: python -m pipx install mfcli"
    Write-Host "    3. Check firewall/network settings if downloading fails"
    exit 1
}

# Create Multifactor directory structure
Write-Host ""
Write-Host "Setting up configuration directory..." -ForegroundColor Cyan

$multifactorDir = Join-Path $env:USERPROFILE "Multifactor"
if (-not (Test-Path $multifactorDir)) {
    New-Item -ItemType Directory -Path $multifactorDir -Force | Out-Null
    Write-Host "  Created: $multifactorDir" -ForegroundColor Green
}
else {
    Write-Host "  Directory already exists: $multifactorDir" -ForegroundColor Green
}

# Check if .env file exists
$envFile = Join-Path $multifactorDir ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "  .env file will be created when you run 'mfcli configure'" -ForegroundColor Yellow
}
else {
    Write-Host "  .env file already exists" -ForegroundColor Green
}

# Verify installation
Write-Host ""
Write-Host "Verifying installation..." -ForegroundColor Cyan

$mfcliPath = Get-Command mfcli -ErrorAction SilentlyContinue
$mfcliMcpPath = Get-Command mfcli-mcp -ErrorAction SilentlyContinue

if ($mfcliPath) {
    Write-Host "  mfcli command: OK" -ForegroundColor Green
}
else {
    Write-Host "  Warning: mfcli command not found in PATH" -ForegroundColor Yellow
    Write-Host "  You may need to restart your terminal" -ForegroundColor Yellow
}

if ($mfcliMcpPath) {
    Write-Host "  mfcli-mcp command: OK" -ForegroundColor Green
}
else {
    Write-Host "  Warning: mfcli-mcp command not found in PATH" -ForegroundColor Yellow
    Write-Host "  You may need to restart your terminal" -ForegroundColor Yellow
}

# Success message
Write-Host ""
Write-Host "======================================================================"
Write-Host "  INSTALLATION COMPLETE!"
Write-Host "======================================================================"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Green
Write-Host ""
Write-Host "  1. Configure API keys:" -ForegroundColor White
Write-Host "       mfcli configure" -ForegroundColor Cyan
Write-Host ""
Write-Host "  2. Navigate to your hardware project directory:" -ForegroundColor White
Write-Host "       cd C:\path\to\your\project" -ForegroundColor Cyan
Write-Host ""
Write-Host "  3. Initialize the project:" -ForegroundColor White
Write-Host "       mfcli init" -ForegroundColor Cyan
Write-Host ""
Write-Host "  4. Run the pipeline:" -ForegroundColor White
Write-Host "       mfcli run" -ForegroundColor Cyan
Write-Host ""
Write-Host "  5. (Optional) Setup MCP server for AI coding assistants:" -ForegroundColor White
Write-Host "       mfcli setup-mcp" -ForegroundColor Cyan
Write-Host ""
Write-Host "For help and documentation:" -ForegroundColor Green
Write-Host "  https://github.com/MultifactorAI/multifactor-adk-backend" -ForegroundColor Cyan
Write-Host ""
Write-Host "To verify your installation:" -ForegroundColor Green
Write-Host "  mfcli doctor" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: If commands are not found, restart your terminal." -ForegroundColor Yellow
Write-Host ""
