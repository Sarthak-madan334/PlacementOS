"""Resume format extraction adapters."""

from app.adapters.parser.base import ExtractedDocument, PageSegment
from app.adapters.parser.docx_adapter import extract_docx
from app.adapters.parser.pdf_adapter import extract_pdf
from app.adapters.parser.txt_adapter import extract_txt
from app.adapters.parser.validator import ParserException, validate_and_detect_format

__all__ = [
    "ExtractedDocument",
    "PageSegment",
    "ParserException",
    "extract_docx",
    "extract_pdf",
    "extract_txt",
    "validate_and_detect_format",
]
