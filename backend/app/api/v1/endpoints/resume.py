"""Resume parsing endpoint for student review."""

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.v1.schemas.resume import ResumeParseResponse
from app.services.resume_parser import parse_resume_bytes

router = APIRouter(prefix="/resumes", tags=["Resume Parser"])


@router.post(
    "/parse",
    response_model=ResumeParseResponse,
    status_code=status.HTTP_200_OK,
    summary="Parse uploaded resume file",
)
async def parse_resume(
    file: UploadFile = File(..., description="Resume file (PDF, DOCX, or TXT up to 5 MiB)"),
):
    """Parse an uploaded resume file and extract candidate facts, sections, quality signals, and warnings.
    Deterministic and assistive; does not overwrite student profile data.
    """
    content = await file.read()
    filename = file.filename or ""

    result = parse_resume_bytes(content=content, filename=filename)
    return result
