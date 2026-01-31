# Building mfcli Standalone Executable

This document explains how to build a standalone executable for the mfcli CLI tool using PyInstaller.

## Prerequisites

- Python 3.12
- All project dependencies installed (`pip install -e .[dev]`)

## Building on Windows

Run the PowerShell build script:

```powershell
.\build.ps1
```

The script will:
1. Check if PyInstaller is installed (and install it if needed)
2. Clean previous builds
3. Build the executable using PyInstaller
4. Display the executable location and size

**Output:** `dist\mfcli.exe`

## Building on Mac/Linux

First, make the build script executable:

```bash
chmod +x build.sh
```

Then run the build script:

```bash
./build.sh
```

The script will:
1. Check if PyInstaller is installed (and install it if needed)
2. Clean previous builds
3. Build the executable using PyInstaller
4. Make the executable runnable
5. Display the executable location and size

**Output:** `dist/mfcli`

## Manual Build

If you prefer to build manually, you can run PyInstaller directly:

```bash
pyinstaller mfcli.spec
```

## Configuration

The build is configured through `mfcli.spec`, which includes:
- All necessary hidden imports for dependencies
- Data files (YAML configs, INI files, templates)
- Single-file executable output
- Console application settings

## Platform-Specific Dependencies

The `pyproject.toml` automatically handles platform-specific magic library dependencies:
- Windows: `python-magic-bin`
- Mac/Linux: `python-magic`

## Troubleshooting

### Missing Dependencies
If the build fails due to missing dependencies, install the dev dependencies:
```bash
pip install -e .[dev]
```

### Large Executable Size
The executable includes all Python dependencies. This is expected for bundled applications. Typical size is 100-200 MB.

### Runtime Errors
If the built executable fails at runtime, you may need to add additional hidden imports or data files to `mfcli.spec`.

## Distribution

After building, the executable in the `dist/` folder can be distributed as a standalone application. Users don't need Python installed to run it.

### Windows
Distribute `dist\mfcli.exe`

### Mac/Linux
Distribute `dist/mfcli` (ensure it has execute permissions)
