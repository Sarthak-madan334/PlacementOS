"""PDF text extraction adapter using pypdf."""

import io
from typing import List
from pypdf import PdfReader
from pypdf.errors import PdfReadError, PdfStreamError

from app.adapters.parser.base import ExtractedDocument, PageSegment
from app.adapters.parser.validator import ParserException


def extract_pdf(content: bytes) -> ExtractedDocument:
    """Extract text and page segments from PDF binary content."""
    segments: List[PageSegment] = []
    warnings: List[str] = []
    full_text_parts: List[str] = []

    try:
        stream = io.BytesIO(content)
        reader = PdfReader(stream)

        if len(reader.pages) == 0:
            warnings.append("PDF contains 0 pages")

        for idx, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            cleaned = page_text.strip()
            if cleaned:
                segments.append(PageSegment(page_number=idx, text=cleaned))
                full_text_parts.append(cleaned)
            else:
                warnings.append(f"Page {idx} contains no extractable text (may be image/scanned)")

    except (PdfReadError, PdfStreamError, Exception) as e:
        raise ParserException(
            f"Unable to read or parse PDF document: malformed or corrupt file structure",
            code="corrupt_file",
            status_code=422,
        )

    raw_text = "\n\n".join(full_text_parts)
    if not raw_text.strip() and not warnings:
        warnings.append("No extractable text found in PDF document")

    return ExtractedDocument(
        raw_text=raw_text,
        segments=segments,
        warnings=warnings,
        format_type="pdf",
    )
