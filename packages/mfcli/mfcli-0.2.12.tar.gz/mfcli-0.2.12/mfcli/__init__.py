"""mfcli - AI-powered CLI for analyzing hardware engineering documents"""

try:
    from importlib.metadata import version, PackageNotFoundError
    try:
        __version__ = version("mfcli")
    except PackageNotFoundError:
        # Package is not installed, fallback to a default version
        __version__ = "0.2.3"
except ImportError:
    # Python < 3.8
    __version__ = "0.2.3"

__all__ = ["__version__"]
