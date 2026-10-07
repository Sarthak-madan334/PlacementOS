"""Unit and integration tests for Resume Parser service and API (Phase 03)."""

import io
import os
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from docx import Document
from pypdf import PdfWriter

from app.adapters.parser.validator import ParserException, validate_and_detect_format
from app.services.resume_parser import parse_resume_bytes


def generate_sample_docx(text: str) -> bytes:
    """Generate in-memory DOCX binary bytes."""
    doc = Document()
    for line in text.splitlines():
        if line.strip():
            doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def generate_sample_pdf(text: str) -> bytes:
    """Generate in-memory PDF binary bytes."""
    # Create simple PDF with blank pages or text
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


@pytest.fixture
def sample_resume_text() -> str:
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "resumes", "sample_resume.txt")
    with open(fixture_path, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def minimal_resume_text() -> str:
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "resumes", "minimal_resume.txt")
    with open(fixture_path, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def weak_language_text() -> str:
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "resumes", "weak_language_resume.txt")
    with open(fixture_path, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# 1. File Validation & Error Tests
# ---------------------------------------------------------------------------

def test_validation_empty_file():
    """Empty files raise ParserException with code 'empty_file'."""
    with pytest.raises(ParserException) as exc:
        validate_and_detect_format(b"", filename="resume.pdf")
    assert exc.value.code == "empty_file"


def test_validation_file_too_large():
    """Files exceeding maximum allowed size raise ParserException with code 'file_too_large'."""
    oversized = b"A" * 100
    with pytest.raises(ParserException) as exc:
        validate_and_detect_format(oversized, filename="resume.txt", max_bytes=50)
    assert exc.value.code == "file_too_large"
    assert exc.value.status_code == 413


def test_validation_unsupported_file_type():
    """Unsupported file types raise ParserException with code 'unsupported_type'."""
    # PNG image header
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
    with pytest.raises(ParserException) as exc:
        validate_and_detect_format(png_bytes, filename="photo.png")
    assert exc.value.code == "unsupported_type"


def test_corrupt_pdf_file():
    """Corrupt PDF content raises ParserException with code 'corrupt_file'."""
    corrupt_pdf = b"%PDF-1.4\nCorrupt bytes that cannot be parsed as valid PDF structure..."
    with pytest.raises(ParserException) as exc:
        parse_resume_bytes(corrupt_pdf, filename="corrupt.pdf")
    assert exc.value.code == "corrupt_file"


def test_corrupt_docx_file():
    """Corrupt DOCX content raises ParserException with code 'corrupt_file'."""
    corrupt_docx = b"PK\x03\x04\x14\x00\x00\x00CorruptZipStream"
    with pytest.raises(ParserException) as exc:
        parse_resume_bytes(corrupt_docx, filename="corrupt.docx")
    assert exc.value.code == "corrupt_file"


# ---------------------------------------------------------------------------
# 2. Text, DOCX, and PDF Parsing Tests
# ---------------------------------------------------------------------------

def test_parse_sample_txt_resume(sample_resume_text: str):
    """Parse complete sample TXT resume and verify extracted facts."""
    result = parse_resume_bytes(sample_resume_text.encode("utf-8"), filename="sample_resume.txt")

    # Verify contact
    contact = result.candidate_facts.contact
    assert contact.name == "Aarush Sharma"
    assert contact.email == "aarush.sharma@example.com"
    assert contact.phone == "+1-555-019-2834"
    assert "aarush-sharma" in contact.linkedin
    assert "aarush-sharma" in contact.github

    # Verify education
    education = result.candidate_facts.education
    assert len(education) >= 1
    assert education[0].degree == "B.Tech"
    assert education[0].branch == "Computer Science"
    assert education[0].graduation_year == 2026
    assert education[0].cgpa == 8.75
    assert education[0].cgpa_scale == 10.0

    # Verify skills
    skill_names = [s.normalized_name for s in result.candidate_facts.skills]
    assert "python" in skill_names
    assert "fastapi" in skill_names
    assert "postgresql" in skill_names
    assert "docker" in skill_names

    # Verify projects
    projects = result.candidate_facts.projects
    assert len(projects) >= 2
    proj_titles = [p.title for p in projects]
    assert any("CampusProof" in t for t in proj_titles)
    assert any("Task Worker" in t for t in proj_titles)

    # Verify experience
    exp = result.candidate_facts.experience
    assert len(exp) >= 1
    assert "Acme Cloud Solutions" in exp[0].organization

    # Verify sections detected
    assert "Education" in result.sections_detected
    assert "Skills" in result.sections_detected
    assert "Projects" in result.sections_detected
    assert "Experience" in result.sections_detected


def test_parse_sample_docx_resume(sample_resume_text: str):
    """Parse in-memory DOCX generated from sample text."""
    docx_bytes = generate_sample_docx(sample_resume_text)
    result = parse_resume_bytes(docx_bytes, filename="resume.docx")

    assert result.candidate_facts.contact.email == "aarush.sharma@example.com"
    assert len(result.candidate_facts.skills) > 0
    assert len(result.candidate_facts.projects) > 0
    assert "Education" in result.sections_detected


def test_parse_minimal_resume_missing_sections(minimal_resume_text: str):
    """Parse minimal resume and verify missing section quality signals."""
    result = parse_resume_bytes(minimal_resume_text.encode("utf-8"), filename="minimal.txt")

    assert result.candidate_facts.contact.email == "priya.patel@example.com"
    signals = [s.signal for s in result.quality_signals if s.signal == "missing_section"]
    assert "missing_section" in signals

    # Education and Experience should be noted as missing
    reasons = [s.observed_text for s in result.quality_signals if s.signal == "missing_section"]
    assert any("Education" in r for r in reasons)
    assert any("Experience" in r for r in reasons)


def test_quality_signals_action_verbs_and_quantified_outcomes(sample_resume_text: str):
    """Verify action verbs and quantified impact detection."""
    result = parse_resume_bytes(sample_resume_text.encode("utf-8"), filename="sample.txt")

    signals = result.quality_signals
    signal_types = {s.signal for s in signals}
    assert "action_verb" in signal_types
    assert "quantified_outcome" in signal_types

    # Check specific action verb detected
    action_texts = [s.observed_text for s in signals if s.signal == "action_verb"]
    assert any("Architected" in t or "Developed" in t or "Engineered" in t for t in action_texts)

    # Check specific quantified outcome detected
    quant_texts = [s.observed_text for s in signals if s.signal == "quantified_outcome"]
    assert any("40%" in t or "25%" in t or "10,000+" in t for t in quant_texts)


def test_quality_signals_weak_language(weak_language_text: str):
    """Verify detection of weak/passive language phrases."""
    result = parse_resume_bytes(weak_language_text.encode("utf-8"), filename="weak.txt")

    signals = [s for s in result.quality_signals if s.signal == "weak_language"]
    assert len(signals) >= 3
    observed = [s.observed_text for s in signals]
    assert any("Responsible for" in o or "responsible for" in o for o in observed)
    assert any("Assisted with" in o or "assisted with" in o for o in observed)


# ---------------------------------------------------------------------------
# 3. Determinism Test
# ---------------------------------------------------------------------------

def test_parser_determinism(sample_resume_text: str):
    """Multiple parser invocations on identical input yield byte-equivalent responses."""
    content = sample_resume_text.encode("utf-8")
    run1 = parse_resume_bytes(content, filename="resume.txt")
    run2 = parse_resume_bytes(content, filename="resume.txt")

    assert run1.model_dump() == run2.model_dump()


# ---------------------------------------------------------------------------
# 4. API Endpoint Integration Tests (POST /api/v1/resumes/parse)
# ---------------------------------------------------------------------------

def test_api_parse_resume_success(client: TestClient, sample_resume_text: str):
    """POST /api/v1/resumes/parse returns 200 with ResumeParseResponse without auth required."""
    files = {"file": ("resume.txt", sample_resume_text.encode("utf-8"), "text/plain")}
    response = client.post("/api/v1/resumes/parse", files=files)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "candidate_facts" in data
    assert "sections_detected" in data
    assert "quality_signals" in data
    assert data["candidate_facts"]["contact"]["email"] == "aarush.sharma@example.com"


def test_api_parse_resume_empty_file(client: TestClient):
    """POST /api/v1/resumes/parse returns 422 for empty file."""
    files = {"file": ("empty.txt", b"", "text/plain")}
    response = client.post("/api/v1/resumes/parse", files=files)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["code"] == "empty_file"


def test_api_parse_resume_unsupported_file(client: TestClient):
    """POST /api/v1/resumes/parse returns 422 for unsupported file type."""
    files = {"file": ("image.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 20, "image/png")}
    response = client.post("/api/v1/resumes/parse", files=files)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["code"] == "unsupported_type"
