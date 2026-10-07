"""Base definitions and data classes for resume extraction adapters."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PageSegment:
    """Represents text extracted from a specific page or paragraph segment."""
    page_number: int
    text: str


@dataclass
class ExtractedDocument:
    """Normalized raw document text with location segments and warnings."""
    raw_text: str
    segments: List[PageSegment] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    format_type: str = "unknown"
