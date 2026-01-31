import fitz
from io import BytesIO


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract all text from a PDF given as bytes (no temp file needed)."""
    text = []
    # Open from a memory stream instead of file path
    with fitz.open(stream=BytesIO(pdf_bytes), filetype="pdf") as doc:
        for page in doc:
            text.append(page.get_text("text"))
    return "\n".join(text)
