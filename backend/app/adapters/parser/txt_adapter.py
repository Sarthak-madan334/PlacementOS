"""Plain text / Markdown text extraction adapter."""

from typing import List
from app.adapters.parser.base import ExtractedDocument, PageSegment
from app.adapters.parser.validator import ParserException


def extract_txt(content: bytes) -> ExtractedDocument:
    """Decode and extract text from plain text or markdown files with encoding fallbacks."""
    warnings: List[str] = []
    text = ""

    # Attempt decodings in order
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            text = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ParserException(
            "Unable to decode text file with standard character encodings",
            code="extraction_failure",
            status_code=422,
        )

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    segments = [PageSegment(page_number=1, text=line) for line in lines]

    if not text.strip():
        warnings.append("Text file is empty or contains only whitespace")

    return ExtractedDocument(
        raw_text=text,
        segments=segments,
        warnings=warnings,
        format_type="txt",
    )
