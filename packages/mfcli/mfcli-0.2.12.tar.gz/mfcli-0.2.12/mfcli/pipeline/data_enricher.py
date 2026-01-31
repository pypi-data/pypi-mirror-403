from typing import TypeVar

from sqlmodel import SQLModel

from mfcli.client.chroma_db import ChromaClient
from mfcli.constants.file_types import FileSubtypes
from mfcli.utils.datasheet_vectorizer import get_datasheets_for_bom_entries
from mfcli.utils.orm import Session

T = TypeVar('T', bound=SQLModel)


async def enrich_data_for_model(db: Session, chroma_db: ChromaClient, subtype: int, instances: list[T]):
    if subtype == FileSubtypes.BOM:
        await get_datasheets_for_bom_entries(db, chroma_db, instances)
