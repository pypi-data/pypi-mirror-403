from io import BytesIO
from typing import List

import tiktoken
from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker import HybridChunker
from docling_core.transforms.chunker.tokenizer.openai import OpenAITokenizer
from docling_core.types.io import DocumentStream

from mfcli.constants.openai import OPENAI_ENCODING_MODEL
from mfcli.utils.config import get_config
from mfcli.utils.logger import get_logger

logger = get_logger(__name__)


class DoclingChunker:
    def __init__(self):
        self._converter = DocumentConverter()
        self._config = get_config()

    def chunk(self, file_name: str, file_bytes: bytes) -> List[str]:
        logger.debug(f"DoclingChunker: chunking document: {file_name}")
        stream = DocumentStream(
            name=file_name,
            stream=BytesIO(file_bytes)
        )
        doc = self._converter.convert(stream).document
        tokenizer = OpenAITokenizer(
            tokenizer=tiktoken.get_encoding(OPENAI_ENCODING_MODEL),
            max_tokens=self._config.chunk_tokens
        )
        chunker = HybridChunker(
            tokenizer=tokenizer,
            max_tokens=self._config.chunk_tokens,
            merge_peers=True
        )
        chunk_iterator = chunker.chunk(dl_doc=doc)
        logger.debug(f"DoclingChunker: chunking complete: {file_name}")

        chunks = []
        for chunk in chunk_iterator:
            chunks.append(chunker.contextualize(chunk))
        return chunks
