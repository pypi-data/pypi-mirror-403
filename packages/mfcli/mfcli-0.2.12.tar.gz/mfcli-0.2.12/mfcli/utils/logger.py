import logging
import sys

from mfcli.utils.config import get_config


def setup_logging():
    config = get_config()
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(config.log_level)
    logger.addHandler(handler)
    logger.propagate = False

    logging.getLogger("google_genai").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging.getLogger("docling").setLevel(logging.ERROR)


def get_logger(name=None):
    return logging.getLogger(name or __name__)
