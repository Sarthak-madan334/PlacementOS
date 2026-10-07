"""Validation and format detection for untrusted resume input."""

from typing import Tuple
from app.core.config import settings
from app.core.exceptions import AppException


class ParserException(AppException):
    """Exception raised during resume validation or extraction with stable error code."""
    def __init__(self, detail: str, code: str, status_code: int = 422):
        super().__init__(detail=detail, code=code, status_code=status_code)


def validate_and_detect_format(
    content: bytes,
    filename: str = "",
    max_bytes: int = settings.MAX_RESUME_BYTES,
) -> str:
    """Validate file size and magic signature, returning detected format string ('pdf', 'docx', 'txt').
    Raises ParserException with stable codes: 'empty_file', 'file_too_large', 'unsupported_type'.
    """
    if not content or len(content) == 0:
        raise ParserException("The uploaded resume file is empty", code="empty_file", status_code=422)

    if len(content) > max_bytes:
        raise ParserException(
            f"File size ({len(content)} bytes) exceeds the maximum limit of {max_bytes} bytes (5 MiB)",
            code="file_too_large",
            status_code=413,
        )

    lower_name = filename.lower()

    # 1. PDF magic bytes check
    if content.startswith(b"%PDF"):
        return "pdf"

    # 2. DOCX magic bytes check (ZIP header with Word document indicators or .docx extension)
    if content.startswith(b"PK\x03\x04"):
        # If it has a .docx extension or zip structure
        if lower_name.endswith(".docx") or b"word/" in content:
            return "docx"
        else:
            raise ParserException(
                "ZIP archive detected without valid DOCX document structure",
                code="unsupported_type",
                status_code=422,
            )

    # 3. Explicit extension fallback for text/markdown
    if lower_name.endswith((".txt", ".md", ".text")):
        return "txt"

    # 4. Check if content is plain printable text (UTF-8 / ASCII)
    try:
        sample = content[:4096].decode("utf-8")
        # Check ratio of printable text characters
        printable_count = sum(1 for c in sample if c.isprintable() or c in "\n\r\t")
        if len(sample) > 0 and (printable_count / len(sample)) > 0.90:
            return "txt"
    except UnicodeDecodeError:
        pass

    raise ParserException(
        "Unsupported resume file type. Please upload a PDF, DOCX, or TXT file",
        code="unsupported_type",
        status_code=422,
    )
