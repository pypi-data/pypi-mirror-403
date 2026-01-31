from pathlib import Path

from mfcli.utils.files import file_access_check
from mfcli.utils.logger import get_logger

logger = get_logger(__name__)


def run_migrations():
    from alembic.config import Config
    from alembic import command

    config_file_path = Path(__file__).parent.parent / "alembic.ini"
    if not file_access_check(config_file_path):
        raise RuntimeError(f"Could not find Alembic config file path: {config_file_path}")

    alembic_cfg = Config(config_file_path)
    command.upgrade(alembic_cfg, "head")
