from typing import Optional

from pydantic import BaseModel, Field

from mfcli.constants.file_types import FileSubtypes, FileTypes


class FileMetadata(BaseModel):
    name: str
    size: int
    md5: str
    path: str
    mime: str
    ext: str
    type_id: FileTypes
    type_name: str
    subtype_id: Optional[FileSubtypes] = Field(None)
    subtype_name: Optional[str] = Field(None)
    is_datasheet: bool
