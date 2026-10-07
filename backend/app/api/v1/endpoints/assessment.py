from fastapi import APIRouter

from app.api.v1.schemas.assessment import AssessmentPreviewRequest, AssessmentPreviewResponse
from app.services.assessment import build_assessment

router = APIRouter(prefix="/assessments", tags=["Assessment"])


@router.post("/preview", response_model=AssessmentPreviewResponse, summary="Build a non-persistent readiness preview")
def preview_assessment(payload: AssessmentPreviewRequest):
    """Assess only the supplied snapshot; do not store the payload or response."""
    return build_assessment(payload)
