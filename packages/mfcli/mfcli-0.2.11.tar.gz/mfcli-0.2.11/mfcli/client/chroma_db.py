from typing import Mapping, List

import chromadb
import tiktoken
import unicodedata
from chromadb import SparseVector
from chromadb.utils import embedding_functions
from pydantic import BaseModel

from mfcli.constants.openai import (
    OPENAI_ENCODING_MODEL,
    OPENAI_MAX_ENCODING_REQUEST_TOKENS,
    OPENAI_MAX_TOKENS_PER_CHUNK
)
from mfcli.crud.project import get_project_by_name
from mfcli.utils.config import get_config
from mfcli.utils.directory_manager import app_dirs
from mfcli.utils.logger import get_logger
from mfcli.utils.orm import Session

logger = get_logger(__name__)

ChunkMetadata = Mapping[str, str | int | float | bool | SparseVector | None]


class VectorDBChunk(BaseModel):
    id: str
    document: str
    metadata: ChunkMetadata
    embedding: list[float] | None = None


class ChromaClient:
    def __init__(self, index_name: str):
        self._index_name = index_name
        self._config = get_config()
        self._client = chromadb.PersistentClient(
            path=app_dirs.chroma_db_dir
        )
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=self._config.openai_api_key,
            model_name=self._config.embedding_model
        )
        self._collection = self._client.get_or_create_collection(
            name=index_name,
            embedding_function=openai_ef
        )
        self._enc = tiktoken.get_encoding(OPENAI_ENCODING_MODEL)

    def delete_collection(self):
        self._client.delete_collection(self._index_name)

    @staticmethod
    def _sanitize_chunk(text: str):
        if not isinstance(text, str):
            raise TypeError(f"Chunk is not a string: {type(text)}")

        # Remove ASCII control characters except newline/tab
        text = ''.join(
            ch for ch in text
            if (32 <= ord(ch) <= 0x10FFFF) or ch in "\n\t\r"
        )
        return text.strip()

    def _validate_chunk_for_embedding(self, text: str) -> None:
        """
        Raises an error if the chunk cannot be embedded.
        """
        if not isinstance(text, str):
            raise TypeError(f"Chunk is not a string: {type(text)}")

        if not text.strip():
            raise ValueError("Chunk is empty or whitespace only")

        try:
            text.encode("utf-8")
        except UnicodeEncodeError as e:
            raise ValueError(f"Chunk contains invalid Unicode: {e}")

        # Check for illegal control characters (other than \n, \t, \r)
        for ch in text:
            if unicodedata.category(ch) == "Cc" and ch not in "\n\t\r":
                raise ValueError(f"Chunk contains control character: {repr(ch)}")

        # Check token length
        token_count = len(self._enc.encode(text))
        if token_count > OPENAI_MAX_TOKENS_PER_CHUNK:
            raise ValueError(f"Chunk too long: {token_count} tokens (> {OPENAI_MAX_TOKENS_PER_CHUNK})")

    def _batch_chunks(self, chunks: List[VectorDBChunk]) -> List[List[VectorDBChunk]]:
        batches = []
        current_batch = []
        total_tokens = 0
        failed_count = 0

        for chunk in chunks:
            try:
                text = self._sanitize_chunk(chunk.document)
                self._validate_chunk_for_embedding(text)
                chunk.document = text
            except (TypeError, ValueError) as e:
                failed_count += 1
                chunk_preview = chunk.document[:100] if len(chunk.document) > 100 else chunk.document
                logger.warning(f"Chunk validation failed ({type(e).__name__}): {str(e)}")
                logger.debug(f"Failed chunk preview: {repr(chunk_preview)}")
                continue
            chunk_tokens = len(self._enc.encode(chunk.document))
            if current_batch and (total_tokens + chunk_tokens > OPENAI_MAX_ENCODING_REQUEST_TOKENS):
                batches.append(current_batch)
                current_batch = []
                total_tokens = 0
            current_batch.append(chunk)
            total_tokens += chunk_tokens

        if current_batch:
            batches.append(current_batch)

        if failed_count > 0:
            logger.warning(f"Failed to process {failed_count} out of {len(chunks)} chunks during batching")

        return batches

    def add(self, chunks: list[VectorDBChunk]):
        logger.debug(f"Adding {len(chunks)} embeddings")
        chunk_batches = self._batch_chunks(chunks)

        if not chunk_batches:
            logger.warning("No valid chunks to add after batching - all chunks failed validation")
            return

        valid_chunk_count = sum(len(batch) for batch in chunk_batches)
        logger.debug(
            f"Processed {len(chunks)} chunks into {len(chunk_batches)} batches ({valid_chunk_count} valid chunks)")

        for batch_idx, batch in enumerate(chunk_batches):
            if not batch:
                logger.warning("Skipping empty batch")
                continue
            try:
                logger.debug(f"Adding batch {batch_idx + 1}/{len(chunk_batches)} with {len(batch)} chunks")

                # If embeddings are pre-generated, use them; otherwise let ChromaDB generate them
                if batch[0].embedding is not None:
                    self._collection.add(
                        ids=[chunk.id for chunk in batch],
                        documents=[chunk.document for chunk in batch],
                        embeddings=[chunk.embedding for chunk in batch],
                        metadatas=[chunk.metadata for chunk in batch]
                    )
                else:
                    self._collection.add(
                        ids=[chunk.id for chunk in batch],
                        documents=[chunk.document for chunk in batch],
                        metadatas=[chunk.metadata for chunk in batch]
                    )
                logger.debug(f"Batch {batch_idx + 1}/{len(chunk_batches)} added successfully")
            except Exception as e:
                logger.error(f"Failed to add batch {batch_idx + 1}/{len(chunk_batches)}")
                logger.error(
                    f"Batch details: {len(batch)} chunks, first chunk length: {len(batch[0].document) if batch else 0}")
                logger.error(f"First chunk preview: {batch[0].document[:200] if batch else 'N/A'}")
                raise
        logger.debug("All embeddings added successfully")

    def query(self, text: str) -> list[VectorDBChunk]:
        logger.debug(f"Querying vector DB: {text}")
        results = self._collection.query(
            query_texts=[text],
            n_results=8
        )
        logger.debug(f"Query results: {results}")
        return [
            VectorDBChunk(
                id=chunk_id,
                document=results["documents"][0][i],
                metadata=results["metadatas"][0][i]
            )
            for i, chunk_id in enumerate(results["ids"][0])
        ]


def get_chromadb_client_for_project_name(db: Session, project_name: str) -> ChromaClient:
    project = get_project_by_name(db, project_name)
    return ChromaClient(project.index_id)
