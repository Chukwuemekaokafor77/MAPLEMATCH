"""Document processing and OCR text extraction service.

Uses pytesseract (Tesseract OCR) for local text extraction.
Can be extended to use Google Document AI or AWS Textract for production.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


async def extract_text_from_file(file_path: str) -> str | None:
    """Extract text from a document file using OCR.

    Supports images (PNG, JPG, TIFF) and PDFs.
    Returns extracted text or None if extraction fails.

    For production, replace with Google Document AI or AWS Textract call.
    """
    path = Path(file_path)

    if not path.exists():
        logger.warning("File not found for OCR: %s", file_path)
        return None

    suffix = path.suffix.lower()

    try:
        if suffix in {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}:
            return _ocr_image(file_path)
        elif suffix == ".pdf":
            return _ocr_pdf(file_path)
        else:
            logger.warning("Unsupported file type for OCR: %s", suffix)
            return None
    except Exception:
        logger.exception("OCR extraction failed for %s", file_path)
        return None


def _ocr_image(file_path: str) -> str | None:
    """Extract text from an image file using Tesseract."""
    try:
        from PIL import Image

        import pytesseract

        image = Image.open(file_path)
        text = pytesseract.image_to_string(image, lang="eng+fra")
        return text.strip() if text.strip() else None
    except ImportError:
        logger.warning(
            "pytesseract or Pillow not installed. "
            "Install with: pip install pytesseract Pillow"
        )
        return None


def _ocr_pdf(file_path: str) -> str | None:
    """Extract text from a PDF (tries text extraction first, falls back to OCR)."""
    try:
        import pymupdf

        doc = pymupdf.open(file_path)
        text_parts: list[str] = []
        for page in doc:
            text = page.get_text()
            if text.strip():
                text_parts.append(text.strip())
        doc.close()

        if text_parts:
            return "\n\n".join(text_parts)

        # If no text extracted, attempt OCR on rendered pages
        logger.info("No text in PDF, attempting OCR on rendered pages: %s", file_path)
        return _ocr_pdf_with_tesseract(file_path)

    except ImportError:
        logger.warning("pymupdf not installed. Install with: pip install pymupdf")
        return None


def _ocr_pdf_with_tesseract(file_path: str) -> str | None:
    """Render PDF pages to images and run OCR."""
    try:
        import pymupdf
        from PIL import Image

        import pytesseract

        doc = pymupdf.open(file_path)
        text_parts: list[str] = []

        for page in doc:
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            text = pytesseract.image_to_string(img, lang="eng+fra")
            if text.strip():
                text_parts.append(text.strip())

        doc.close()
        return "\n\n".join(text_parts) if text_parts else None

    except ImportError:
        logger.warning("Required OCR dependencies not installed.")
        return None
