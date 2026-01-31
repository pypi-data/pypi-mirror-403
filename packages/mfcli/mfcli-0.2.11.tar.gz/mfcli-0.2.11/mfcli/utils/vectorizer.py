from pathlib import Path

from mfcli.client.chroma_db import get_chromadb_client_for_project_name
from mfcli.utils.logger import get_logger
from mfcli.utils.orm import Session

logger = get_logger(__name__)


def add_file_to_db(project_name: str, file_path: Path, purpose: str):
    from mfcli.utils.datasheet_vectorizer import DatasheetVectorizer
    if not file_path.exists():
        logger.error(f"File does not exist: {file_path}")
        return

    if not file_path.is_file():
        logger.error(f"Path is not a file: {file_path}")
        return

    try:
        with Session() as db:
            chroma_db = get_chromadb_client_for_project_name(db, project_name)
            vectorizer = DatasheetVectorizer(chroma_db)
        vectorizer.vectorize_local_file(str(file_path), purpose)
        logger.info(f"Successfully added file to ChromaDB: {file_path}")
    except Exception as e:
        logger.error(f"Failed to add file to ChromaDB: {file_path}")
        logger.exception(e)
