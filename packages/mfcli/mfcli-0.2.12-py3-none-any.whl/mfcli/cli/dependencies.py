import os
import subprocess
import sys

from pydantic import ValidationError

from mfcli.utils.config import get_config
from mfcli.utils.directory_manager import app_dirs
from mfcli.utils.logger import get_logger

logger = get_logger(__name__)


def is_playwright_installed() -> bool:
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            path = p.chromium.executable_path
            if path is None or path.strip() == "":
                return False
            if not os.path.exists(path):
                return False
            return True
    except Exception:
        return False


def ensure_playwright_installed():
    if not is_playwright_installed():
        try:
            subprocess.run([sys.executable, "-m", "playwright", "install"], check=True)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to install Playwright automatically.")
            logger.error(f"Error details: {e}")
            logger.error("You can try installing Playwright manually by running:")
            logger.error("    python -m playwright install")
            logger.error("For more information, see https://playwright.dev/python/docs/intro")
            sys.exit(1)
def check_dependencies():
    env_file_path = app_dirs.env_file_path
    logger.debug(f".env file path: {env_file_path}")
    if os.path.exists(env_file_path) and os.access(env_file_path, os.R_OK):
        logger.debug(f".env file found: {env_file_path}")
    else:
        logger.error(f".env file does not exist or cannot be read: {env_file_path}")
        logger.error("Please add your api keys to .env using .env.example in the project folder")
        logger.error(f".env file must be in your home directory: {env_file_path}")
        sys.exit(1)
    try:
        logger.debug(f"Validating .env file: {env_file_path}")
        get_config()
        logger.debug(f".env file validated: {env_file_path}")
    except ValidationError as e:
        logger.exception(e)
        logger.error(f".env file is not formatted properly: {env_file_path}")
    if not is_playwright_installed():
        logger.warning("Playwright is not installed")
        logger.debug("Installing playwright")
        ensure_playwright_installed()
