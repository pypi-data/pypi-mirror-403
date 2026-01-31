import os
import re
from pathlib import Path
from typing import Literal

AppDataFileTypes = Literal['datasheets', 'files']


def file_access_check(file_path: Path) -> bool:
    if not os.path.exists(file_path) or not os.access(file_path, os.R_OK):
        return False
    return True


def is_text_mime_type(mime_type: str) -> bool:
    return bool(re.match(r"^text/.+$", mime_type))
