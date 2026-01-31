import mimetypes
import subprocess
from pathlib import Path


def get_git_root(repo_dir: Path | str = None) -> Path | None:
    """
    Get the root directory of the git repository.
    
    :param repo_dir: Path to start searching from (defaults to current directory)
    :return: Path to git root or None if not a git repo or error occurs
    """
    try:
        if not repo_dir:
            repo_dir = Path.cwd()
        else:
            repo_dir = Path(repo_dir)
        
        # Get the git root directory
        result = subprocess.run(
            ["git", "-C", str(repo_dir), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
        
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return None


def get_git_repo_name(repo_dir: Path | str = None) -> str | None:
    """
    Get the name of the git repository from the remote URL.
    
    :param repo_dir: Path to the repository directory (defaults to current directory)
    :return: Repository name or None if not a git repo or error occurs
    """
    try:
        if not repo_dir:
            repo_dir = Path.cwd()
        else:
            repo_dir = Path(repo_dir)
        
        # Get the remote URL
        result = subprocess.run(
            ["git", "-C", str(repo_dir), "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            url = result.stdout.strip()
            # Extract repo name from URL
            # Handle various formats: https://github.com/user/repo.git, git@github.com:user/repo.git, etc.
            repo_name = url.rstrip('/').split('/')[-1]
            # Remove .git extension if present
            if repo_name.endswith('.git'):
                repo_name = repo_name[:-4]
            return repo_name
        
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return None


def get_mime_type_from_bytes(file_bytes: bytes, filename: str = None):
    """
    Get MIME type from file bytes using Python's built-in mimetypes module
    and file signature detection.
    
    :param file_bytes: Bytes of the file
    :param filename: Optional filename to help with detection
    :return: MIME type string
    """
    # Check for common file signatures
    if len(file_bytes) >= 5 and file_bytes.startswith(b'%PDF-'):
        return 'application/pdf'
    elif len(file_bytes) >= 4 and file_bytes.startswith(b'PK\x03\x04'):
        # ZIP-based formats (could be various formats)
        return 'application/zip'
    elif len(file_bytes) >= 8 and file_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    elif len(file_bytes) >= 3 and file_bytes.startswith(b'\xff\xd8\xff'):
        return 'image/jpeg'
    
    # If filename is provided, try to guess from extension
    if filename:
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type:
            return mime_type
    
    # Default fallback
    return 'application/octet-stream'
