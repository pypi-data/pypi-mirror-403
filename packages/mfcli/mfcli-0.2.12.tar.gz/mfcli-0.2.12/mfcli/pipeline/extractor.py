from mfcli.constants.file_types import FileTypes
from mfcli.models.file import File
from mfcli.pipeline.extractors.pdf import extract_text_from_pdf
from mfcli.utils.files import is_text_mime_type
from mfcli.utils.logger import get_logger

logger = get_logger(__name__)


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX file using python-docx."""
    try:
        from io import BytesIO
        import docx
        
        doc = docx.Document(BytesIO(file_bytes))
        text_parts = []
        for paragraph in doc.paragraphs:
            text_parts.append(paragraph.text)
        return '\n'.join(text_parts)
    except ImportError:
        logger.warning("python-docx not installed, treating DOCX as binary")
        return file_bytes.decode(errors='ignore')
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {e}")
        return file_bytes.decode(errors='ignore')


def extract_text_from_rtf(file_bytes: bytes) -> str:
    """Extract text from RTF file using striprtf."""
    try:
        from striprtf.striprtf import rtf_to_text
        rtf_string = file_bytes.decode(errors='ignore')
        return rtf_to_text(rtf_string)
    except ImportError:
        logger.warning("striprtf not installed, treating RTF as plain text")
        return file_bytes.decode(errors='ignore')
    except Exception as e:
        logger.error(f"Error extracting text from RTF: {e}")
        return file_bytes.decode(errors='ignore')


def extract_document_text(file: File, file_bytes: bytes) -> str:
    """
    Extract text from a file based on its MIME type.
    
    For PDFs, uses PyMuPDF (fitz) for fast, reliable text extraction.
    For text files, decodes the bytes directly.
    For DOCX files, uses python-docx to extract text.
    For RTF files, uses striprtf to extract text.
    For image files (JPG, PNG), returns empty string (OCR not implemented).
    KiCad schematics and other schematic files are treated as text files.
    
    Args:
        file: File object containing metadata
        file_bytes: Raw file content as bytes
        
    Returns:
        Extracted text content
        
    Raises:
        ValueError: If the file type is not supported
    """
    if is_text_mime_type(file.mime_type):
        return file_bytes.decode(errors='ignore')
    elif file.type == FileTypes.PDF:
        return extract_text_from_pdf(file_bytes)
    elif file.type == FileTypes.DOCX:
        return extract_text_from_docx(file_bytes)
    elif file.type == FileTypes.RTF:
        return extract_text_from_rtf(file_bytes)
    elif file.type == FileTypes.JPG:
        # Image files don't have extractable text without OCR
        # Return empty string for now - file will still be vectorized if it's a PDF-embedded image
        logger.info(f"Image file detected ({file.name}), no text extraction (OCR not implemented)")
        return ""
    elif file.type == FileTypes.CSV:
        # CSV files (including Excel CSV with application/vnd.ms-excel MIME type)
        # are text-based and should be decoded directly
        return file_bytes.decode(errors='ignore')
    elif file.type in (FileTypes.KICAD_SCH, FileTypes.SCH, FileTypes.TXT):
        # KiCad schematics and plain text files are S-expression text files but may have 
        # application/octet-stream MIME type
        return file_bytes.decode(errors='ignore')
    raise ValueError(f"Unsupported MIME type: {file.mime_type}")
