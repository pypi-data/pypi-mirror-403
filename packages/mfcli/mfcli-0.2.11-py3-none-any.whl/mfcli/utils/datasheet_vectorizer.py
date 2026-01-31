import os
import re
from urllib.parse import urlparse, unquote

from playwright.async_api import async_playwright, Browser
from requests import RequestException
from sqlmodel import select

from mfcli.client.chroma_db import ChromaClient
from mfcli.client.docling import DoclingChunker
from mfcli.client.vector_db import DocumentVectorizer
from mfcli.constants.file_types import PDFMimeTypes
from mfcli.digikey.digikey import DigiKey
from mfcli.models.bom import BOM
from mfcli.models.datasheet import Datasheet
from mfcli.pipeline.extractors.pdf import extract_text_from_pdf
from mfcli.utils.directory_manager import app_dirs
from mfcli.utils.http_requests import http_request
from mfcli.utils.logger import get_logger
from mfcli.utils.orm import Session
from mfcli.utils.tools import get_mime_type_from_bytes

logger = get_logger(__name__)


class DatasheetVectorizer:
    def __init__(self, chroma_db: ChromaClient):
        self._vectorizer = DocumentVectorizer(chroma_db)
        self._docling = DoclingChunker()

    def _vectorize_text(self, text: str, file_name: str, purpose: str, additional_metadata: dict = None):
        """
        Shared method to vectorize text with metadata
        :param text: Extracted text content
        :param file_name: Name of the file
        :param purpose: Purpose of the vectorization (e.g., 'datasheet', 'bom', 'errata')
        :param additional_metadata: Optional additional metadata to include
        """
        metadata = {"file_name": file_name, "purpose": purpose}
        if additional_metadata:
            metadata.update(additional_metadata)
        self._vectorizer.vectorize(text, metadata)
        logger.debug(f"File vectorized: {file_name} (purpose: {purpose})")

    @staticmethod
    async def _fetch_with_playwright(browser: Browser, url: str):
        context = await browser.new_context()
        response = await context.request.get(url)
        body = await response.body()
        return body

    @staticmethod
    def _parse_ti_url(url: str) -> str:
        """
        Texas Instruments URLs may have goTo param which is the real URL of the PDF
        :param url: TI URL
        :return: URL from goTo param
        """
        url_query_params = urlparse(url).query
        if not url_query_params:
            return url
        params = url_query_params.split('&')
        for param in params:
            name = param.split('=')[0]
            value = param.split('=')[1]
            if not name == 'gotoUrl':
                continue
            return unquote(value)
        return url

    @staticmethod
    def _save_datasheet(name: str, content: bytes):
        file_path = app_dirs.data_sheets_dir / name
        with open(file_path, "wb") as f:
            f.write(content)

    async def _download(self, browser: Browser, url: str, purpose: str = "datasheet"):
        logger.debug(f"Fetching datasheet: {url}")
        try:
            ti_url_regex = r"^https?://www.ti.com/.+$"
            if re.match(ti_url_regex, url, re.I):
                logger.debug(f"URL is a TI URL: {url}")
                url = self._parse_ti_url(url)
                logger.debug(f"Parsed TI URL: {url}")
            url_path = urlparse(url).path
        except ValueError as e:
            logger.debug(f"Unable to parse datasheet URL: {url}")
            logger.debug(e)
            return
        file_name = os.path.basename(url_path)
        if not file_name.endswith(".pdf"):
            file_name = f"{file_name}.pdf"
        try:
            content = http_request(method='GET', url=url).content
            mime_type = get_mime_type_from_bytes(content, file_name)
            if mime_type not in PDFMimeTypes:
                logger.debug(f"Retrieved PDF is not PDF MIME type: {url}")
                logger.debug(f"Retrying with playwright: {url}")
                content = await self._fetch_with_playwright(browser, url)
        except RequestException as e:
            logger.debug(e)
            logger.debug(f"HTTP error fetching PDF: {url}")
            logger.debug(f"Retrying with playwright: {url}")
            content = await self._fetch_with_playwright(browser, url)
        except Exception as e:
            logger.debug(f"Unhandled error fetching datasheet URL: {url}")
            logger.debug(e)
            return
        mime_type = get_mime_type_from_bytes(content, file_name)
        if mime_type not in PDFMimeTypes:
            logger.debug(f"Could not fetch PDF even with playwright: {url}")
            return
        try:
            self._save_datasheet(file_name, content)
        except Exception as e:
            logger.debug(e)
            logger.debug(f"Error saving datasheet: {file_name}")

    async def download(self, urls: list[str], purpose: str = "datasheet"):
        if not urls:
            logger.debug(f"No datasheets to vectorize, exiting")
            return
        logger.debug(f"Vectorizing {len(urls)} documents (purpose: {purpose})")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                for url in urls:
                    try:
                        await self._download(browser, url, purpose)
                    except Exception as e:
                        logger.debug(e)
                        logger.debug(f"Error processing document: {url}")
            finally:
                await browser.close()

    def vectorize_local_file(self, file_path: str, purpose: str, additional_metadata: dict = None):
        """
        Vectorize a local file (e.g., generated by agents)
        :param file_path: Path to the local file
        :param purpose: Purpose of the vectorization (e.g., 'bom', 'errata', 'functional_blocks')
        :param additional_metadata: Optional additional metadata to include
        """
        try:
            logger.debug(f"Vectorizing local file: {file_path} (purpose: {purpose})")
            file_name = os.path.basename(file_path)

            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"File does not exist: {file_path}")
                return

            # Extract text based on file type
            with open(file_path, 'rb') as f:
                content = f.read()

            mime_type = get_mime_type_from_bytes(content, file_name)

            if mime_type in PDFMimeTypes:
                text = extract_text_from_pdf(content)
            else:
                # For non-PDF files, decode as text
                text = content.decode(errors='ignore')

            logger.debug(f"Text extracted from local file: {file_path}")
            self._vectorize_text(text, file_name, purpose, additional_metadata)

        except Exception as e:
            logger.error(f"Error vectorizing local file: {file_path}")
            logger.exception(e)
            raise

    def vectorize_local_files(self, file_paths: list[str], purpose: str, additional_metadata: dict = None):
        """
        Vectorize multiple local files
        :param file_paths: List of paths to local files
        :param purpose: Purpose of the vectorization (e.g., 'bom', 'errata', 'functional_blocks')
        :param additional_metadata: Optional additional metadata to include
        """
        if not file_paths:
            logger.debug(f"No files to vectorize, exiting")
            return

        logger.debug(f"Vectorizing {len(file_paths)} local files (purpose: {purpose})")
        for file_path in file_paths:
            try:
                self.vectorize_local_file(file_path, purpose, additional_metadata)
            except Exception as e:
                logger.exception(e)
                logger.error(f"Error processing local file: {file_path}")
        logger.debug(f"Finished vectorizing {len(file_paths)} local files")

    def vectorize_text_content(self, text: str, file_name: str, purpose: str, additional_metadata: dict = None):
        """
        Vectorize text content directly (e.g., from agent output)
        :param text: Text content to vectorize
        :param file_name: Name to associate with this content
        :param purpose: Purpose of the vectorization (e.g., 'bom', 'errata', 'functional_blocks')
        :param additional_metadata: Optional additional metadata to include
        """
        try:
            logger.debug(f"Vectorizing text content: {file_name} (purpose: {purpose})")
            self._vectorize_text(text, file_name, purpose, additional_metadata)
        except Exception as e:
            logger.error(f"Error vectorizing text content: {file_name}")
            logger.exception(e)
            raise

    def vectorize_file_buf(
            self,
            file_bytes: bytes,
            file_name: str,
            purpose: str,
            additional_metadata: dict = None
    ) -> None:
        """
        Vectorize a file from a buffer. This vectorizer uses DoclingChunker.
        :param file_bytes: file bytes
        :param file_name: file name
        :param purpose: file purpose
        :param additional_metadata: dict of metadata
        :return: None
        """
        chunks = self._docling.chunk(file_name, file_bytes)
        metadata = {"file_name": file_name, "purpose": purpose}
        if additional_metadata:
            metadata.update(additional_metadata)
        self._vectorizer.vectorize_chunks(chunks, metadata)


async def get_datasheets_for_bom_entries(db: Session, chroma_db: ChromaClient, entries: list[BOM]):
    logger.info(f"Fetching datasheets for {len(entries)} BOM entries")
    part_numbers = {entry.value for entry in entries}
    logger.debug("Fetching existing datasheets for part numbers")

    # Fetch existing datasheets
    stmt = select(Datasheet).where(Datasheet.part_number.in_(part_numbers))
    datasheets: list[Datasheet] = db.execute(stmt).scalars().all()
    datasheet_map = {d.part_number: d.datasheet for d in datasheets}

    logger.debug(f"Datasheet map: {datasheet_map}")
    client = DigiKey()
    new_datasheets: list[Datasheet] = []
    datasheet_urls: list[str] = []
    for entry in entries:
        try:
            logger.debug(f"Processing BOM entry: {entry.value}")

            # Skip resistors, capacitors and inductors
            ref = entry.reference
            if ref.startswith('R') \
            or ref.startswith('C') \
            or ref.startswith('L') \
            or ref.startswith('J') \
            or ref.startswith('T') \
            or ref.startswith('D'):
                logger.debug(f"Skipping BOM entry {entry.value} with reference: {ref}")
                continue

            existing_datasheet = datasheet_map.get(entry.value)
            if not existing_datasheet:
                logger.debug(f"Datasheet does not exist for {entry.value}")
            entry.datasheet = existing_datasheet or client.datasheet(entry.value)

            # If datasheet is new create it in DB
            if not existing_datasheet and entry.datasheet:
                logger.debug(f"Adding new datasheet for {entry.value}: {entry.datasheet}")
                new_datasheets.append(Datasheet(part_number=entry.value, datasheet=entry.datasheet))
                datasheet_urls.append(entry.datasheet)
        except Exception as e:
            logger.error(f"Error adding datasheet for BOM entry: {entry.value}")
            logger.exception(e)
    if new_datasheets:
        db.add_all(new_datasheets)
        logger.debug(f"Adding new data sheets: {new_datasheets}")
    if datasheet_urls:
        logger.debug(f"About to download datasheets: {datasheet_urls}")
        try:
            await DatasheetVectorizer(chroma_db).download(datasheet_urls)
        except Exception as e:
            logger.error("Error vectorizing datasheets for BOM")
            raise e
    logger.debug("Finished adding datasheets")
