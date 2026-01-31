import hashlib
import mimetypes
import os
from pathlib import Path

import pandas as pd

from werkzeug.utils import secure_filename

from mfcli.constants.file_types import SupportedFileTypes, FileTypes
from mfcli.models.file_metadata import FileMetadata
from mfcli.utils.logger import get_logger

MAX_FILE_GB = 1
MAX_FILE_SIZE = 1024 * 1024 * 1024 * MAX_FILE_GB

logger = get_logger(__name__)


def is_csv(file_path):
    pd.read_csv(file_path, nrows=5, encoding_errors='ignore')


def validate_file(metadata: FileMetadata):
    logger.debug(f"Validating file: {metadata.name}")
    try:
        if metadata.type_id == FileTypes.CSV:
            is_csv(metadata.path)
        else:
            logger.debug(f"File type has no validator: {metadata.type_name}")
    except Exception as e:
        raise ValueError(f"The file is not a valid {metadata.type_name} file: {e}")


def get_file_metadata(file_path: str, is_datasheet: bool) -> tuple[FileMetadata, bytes]:
    logger.debug(f"Starting categorize_and_validate_file tool: {file_path}")
    file_name = os.path.basename(file_path)
    file_name = secure_filename(file_name).lower().strip()

    file_ext = os.path.splitext(file_name)[1]
    file_type_name = file_ext.replace('.', '').upper()
    if not file_type_name:
        raise ValueError("File requires an extension")
    if file_type_name not in SupportedFileTypes:
        raise ValueError(f"File extension is not supported: {file_type_name}")
    file_type_id = FileTypes[file_type_name].value
    logger.debug(f"File type id: {file_type_id}")

    path = Path(file_path)
    if not path.exists():
        raise ValueError("File does not exist")
    if not os.access(path, os.R_OK):
        raise ValueError("File is not readable")

    file_bytes = os.stat(file_path).st_size
    if file_bytes == 0:
        raise ValueError(f"File is empty: {file_name}")
    if file_bytes > MAX_FILE_SIZE:
        raise ValueError(f"File size exceeds limit: {file_bytes}")

    logger.debug(f"File validated: {file_path}")
    with open(file_path, "rb") as fp:
        content = fp.read()
        md5_sum = hashlib.md5(content).hexdigest()
        
        # Define file types that should always be treated as text/plain
        # These are text-based formats that may be incorrectly detected as binary
        text_file_types = {'NET', 'KICAD_SCH', 'SCH', 'ASC', 'CIR'}
        
        if file_type_name in text_file_types:
            # Force text/plain MIME type for known text-based schematic/netlist files
            mime_type = 'text/plain'
            logger.debug(f"Forcing text/plain MIME type for {file_type_name}")
        else:
            # Use mimetypes module to guess MIME type from file extension
            mime_type, _ = mimetypes.guess_type(file_path)
            
            # If mimetypes can't detect it, use default based on file type
            if mime_type is None:
                # Use the first supported MIME type as default
                mime_types = SupportedFileTypes[file_type_name]["mime_types"]
                mime_type = list(mime_types)[0] if mime_types else 'application/octet-stream'
            
            # Validate MIME type matches expected types for this file extension
            if mime_type not in SupportedFileTypes[file_type_name]["mime_types"]:
                logger.warning(f"Extension {file_type_name} has unexpected MIME type: {mime_type}. Expected one of: {SupportedFileTypes[file_type_name]['mime_types']}")
                # Use the first supported MIME type as default instead of failing
                mime_type = list(SupportedFileTypes[file_type_name]["mime_types"])[0]
        
        file_metadata = FileMetadata(
            name=file_name,
            size=file_bytes,
            md5=md5_sum,
            path=file_path,
            mime=mime_type,
            ext=file_ext,
            type_id=file_type_id,
            type_name=file_type_name,
            is_datasheet=is_datasheet
        )
        logger.debug(file_metadata)
        return file_metadata, content
