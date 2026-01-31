import tempfile
from pathlib import Path
from uuid import uuid4

import pikepdf
from io import BytesIO

from mfcli.utils.logger import get_logger

logger = get_logger(__name__)


class PDFSplitter:
    def __init__(self, file_name: str, content: bytes):
        self._name = file_name
        self._content = content

    @staticmethod
    def _head_page_limit(total_pages: int) -> int:
        if total_pages <= 30:
            return 10
        elif total_pages <= 100:
            return 20
        else:
            return 30

    def _open_pdf(self) -> pikepdf.Pdf:
        return pikepdf.open(BytesIO(self._content))

    def split_pdf_head(self) -> Path:
        with self._open_pdf() as src:
            total_pages = len(src.pages)
            page_limit = self._head_page_limit(total_pages)

            dst = pikepdf.Pdf.new()
            dst.pages.extend(src.pages[:page_limit])

            output_path = Path(tempfile.mktemp(suffix=".pdf"))
            dst.save(output_path)

            return output_path

    def extract_range(
            self,
            start_page: int,
            end_page: int,
            output_folder: Path,
    ) -> Path:
        logger.debug(f"Splitting PDF: {self._name}")

        output_folder.mkdir(parents=True, exist_ok=True)

        with self._open_pdf() as src:
            dst = pikepdf.Pdf.new()
            dst.pages.extend(src.pages[start_page:end_page + 1])

            output_path = output_folder / f"{uuid4().hex}.pdf"
            dst.save(output_path)

        logger.debug(f"Output PDF part to: {output_path}")
        logger.debug(f"PDF splitter finished: {self._name}")

        return output_path
