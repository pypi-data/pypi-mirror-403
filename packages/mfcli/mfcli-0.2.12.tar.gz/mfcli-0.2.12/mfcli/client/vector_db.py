from typing import List
from uuid import uuid4

import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI

from mfcli.client.chroma_db import ChromaClient, ChunkMetadata, VectorDBChunk
from mfcli.utils.config import get_config
from mfcli.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentVectorizer:
    def __init__(self, chroma_db: ChromaClient):
        self._config = get_config()
        self._client: OpenAI = OpenAI(api_key=self._config.openai_api_key)
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._config.chunk_size,
            chunk_overlap=self._config.chunk_overlap,
            length_function=len
        )
        self._chroma_db = chroma_db

    def _batch_texts(self, texts: list[str]) -> list[list[str]]:
        max_request_chunks = 2048
        max_request_tokens = 300000

        encoding = tiktoken.encoding_for_model(self._config.embedding_model)

        request_batches = []
        for i in range(0, len(texts), max_request_chunks):
            request_batches.append(texts[i:i + max_request_chunks])

        batches = []
        for request_batch in request_batches:
            total_tokens = 0
            batch = []
            for text in request_batch:
                tokens = len(encoding.encode(text))
                # if adding this text would exceed the token limit, push the current batch
                if total_tokens + tokens > max_request_tokens:
                    batches.append(batch)
                    batch = [text]
                    total_tokens = tokens  # reset with current text
                else:
                    batch.append(text)
                    total_tokens += tokens
            if batch:
                batches.append(batch)
        return batches

    def _get_embeddings(self, texts: list[str]) -> list[list[float]]:
        batches = self._batch_texts(texts)
        embeddings = []
        for batch in batches:
            response = self._client.embeddings.create(
                model=self._config.embedding_model,
                input=batch
            )
            embeddings += [row.embedding for row in response.data]
        return embeddings

    def _chunk_document(self, text: str) -> list[str]:
        return self._splitter.split_text(text)

    def vectorize_chunks(self, chunks: List[str], metadata: ChunkMetadata) -> list[VectorDBChunk]:
        # Generate embeddings ourselves instead of letting ChromaDB do it
        logger.debug("Generating embeddings")
        embeddings = self._get_embeddings(chunks)
        logger.debug(f"Generated {len(embeddings)} embeddings")

        vectors = [
            VectorDBChunk(
                id=uuid4().hex,
                document=chunk,
                metadata=metadata,
                embedding=embedding
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]
        logger.debug("Adding vectors")
        self._chroma_db.add(vectors)
        logger.debug("Vectors added")
        return vectors

    def vectorize(self, text: str, metadata: ChunkMetadata) -> list[VectorDBChunk]:
        logger.debug("Vectorize document")
        chunks = self._chunk_document(text)
        logger.debug(f"Document split into {len(chunks)} chunks")

        return self.vectorize_chunks(chunks, metadata)
