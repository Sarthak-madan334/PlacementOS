import re
from datetime import datetime, timezone
from math import floor
from uuid import uuid4

from app.api.v1.schemas.assessment import AssessmentPreviewRequest, FactorResult
from app.services.profile_links import inspect_profile_links


FACTOR_WEIGHTS = {
    "role_skill_coverage": ("Role skill coverage", 0.30),
    "project_evidence": ("Project and work evidence", 0.25),
    "resume_clarity": ("Resume clarity and completeness", 0.20),
    "technical_evidence": ("Technical skill evidence", 0.15),
    "profile_completeness": ("Profile completeness", 0.10),
}

SKILL_ALIASES = {
    "c++": "C++", "cpp": "C++", "c#": "C#", "c sharp": "C#",
    "javascript": "JavaScript", "js": "JavaScript", "typescript": "TypeScript", "ts": "TypeScript",
    "react": "React", "react.js": "React", "next.js": "Next.js", "nextjs": "Next.js",
    "python": "Python", "java": "Java", "sql": "SQL", "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL", "mysql": "MySQL", "mongodb": "MongoDB", "git": "Git",
    "github": "GitHub", "docker": "Docker", "fastapi": "FastAPI", "django": "Django",
    "flask": "Flask", "node.js": "Node.js", "nodejs": "Node.js", "html": "HTML",
    "css": "CSS", "tailwind": "Tailwind CSS", "aws": "AWS", "azure": "Azure",
    "machine learning": "Machine Learning", "pytorch": "PyTorch", "tensorflow": "TensorFlow",
    "pandas": "Pandas", "numpy": "NumPy", "accessibility": "Accessibility",
    "testing": "Testing", "unit testing": "Unit testing", "pytest": "Pytest",
    "rest api": "REST API", "api": "API", "figma": "Figma", "communication": "Communication",
    "leadership": "Leadership", "data analysis": "Data analysis", "excel": "Excel",
}


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _canonical(value: str) -> str | None:
    return SKILL_ALIASES.get(_normalize(value))


def _contains(text: str, term: str) -> bool:
    escaped = re.escape(term)
    return re.search(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])", text, re.IGNORECASE) is not None


def _requirements(request: AssessmentPreviewRequest) -> tuple[list[str], list[str], list[str]]:
    opportunity = request.opportunity
    source = opportunity.required_skills
    if not source and opportunity.description:
        text = opportunity.description
        detected: list[tuple[int, str]] = []
        occupied: list[tuple[int, int]] = []
        for alias in sorted(SKILL_ALIASES, key=len, reverse=True):
            pattern = rf"(?<![A-Za-z0-9]){re.escape(alias)}(?![A-Za-z0-9])"
            for match in re.finditer(pattern, text, re.IGNORECASE):
                if not any(match.start() < end and start < match.end() for start, end in occupied):
                    occupied.append((match.start(), match.end()))
                    detected.append((match.start(), alias))
        source = [alias for _, alias in sorted(detected)]
    required: list[str] = []
    unknown: list[str] = []
    for item in source:
        canonical = _canonical(item)
        target = canonical or item.strip()
        bucket = required if canonical else unknown
        if target and _normalize(target) not in {_normalize(value) for value in bucket}:
            bucket.append(target)
    preferred: list[str] = []
    for item in opportunity.preferred_skills:
        canonical = _canonical(item)
        target = canonical or item.strip()
        if target and _normalize(target) not in {_normalize(value) for value in preferred}:
            preferred.append(target)
    return required, preferred, unknown


def _eligibility(request: AssessmentPreviewRequest) -> dict:
    profile = request.profile
    opportunity = request.opportunity
    reasons: list[dict[str, str]] = []
    failed = False
    criteria = False

    if opportunity.minimum_cgpa is not None:
        criteria = True
        if profile.cgpa is None or profile.cgpa_scale is None:
            reasons.append({"code": "cgpa_missing", "message": "Add your CGPA and grading scale to check this requirement."})
        elif profile.cgpa / profile.cgpa_scale < opportunity.minimum_cgpa / opportunity.cgpa_scale:
            failed = True
            reasons.append({"code": "cgpa_below_minimum", "message": f"Your CGPA is below the stated minimum of {opportunity.minimum_cgpa:g}/{opportunity.cgpa_scale:g}."})
        else:
            reasons.append({"code": "cgpa_meets_minimum", "message": "Your CGPA meets the stated minimum."})

    if opportunity.eligible_branches:
        criteria = True
        if not profile.branch:
            reasons.append({"code": "branch_missing", "message": "Add your branch to check the stated branch criteria."})
        elif not any(_normalize(profile.branch) == _normalize(value) for value in opportunity.eligible_branches):
            failed = True
            reasons.append({"code": "branch_not_eligible", "message": "Your branch is not in the stated eligible-branch list."})
        else:
            reasons.append({"code": "branch_meets_criteria", "message": "Your branch matches the stated criteria."})

    if opportunity.graduation_years:
        criteria = True
        if profile.graduation_year is None:
            reasons.append({"code": "graduation_year_missing", "message": "Add your graduation year to check this requirement."})
        elif profile.graduation_year not in opportunity.graduation_years:
            failed = True
            reasons.append({"code": "graduation_year_not_eligible", "message": "Your graduation year is not in the stated eligible years."})
        else:
            reasons.append({"code": "graduation_year_meets_criteria", "message": "Your graduation year matches the stated criteria."})

    if not criteria:
        return {"status": "unknown", "reasons": [{"code": "criteria_not_provided", "message": "No explicit eligibility criteria were provided, so eligibility cannot be determined."}]}
    status = "not_eligible" if failed else "unknown" if any(reason["code"].endswith("missing") for reason in reasons) else "eligible"
    return {"status": status, "reasons": reasons}


def build_assessment(request: AssessmentPreviewRequest) -> dict:
    profile = request.profile
    required, preferred, unknown_required = _requirements(request)
    profile_skills: dict[str, str] = {}
    for item in profile.skills:
        canonical = _canonical(item)
        if canonical:
            profile_skills[_normalize(canonical)] = canonical
    project_text = " ".join(f"{project.title} {project.description}" for project in profile.projects)
    matched = [skill for skill in required if any(_normalize(value) == _normalize(skill) for value in profile_skills.values()) or _contains(project_text, skill)]
    missing = [skill for skill in required if skill not in matched]
    role_score = round(100 * len(matched) / len(required)) if required else None
    role_match = {
        "score": role_score,
        "matched": matched,
        "missing": missing,
        "unknown": unknown_required,
        "preferred": preferred,
        "explanation": "Required terms found in profile skills or project descriptions." if required else "No supported required skills were provided; add explicit skills to compare.",
    }

    factors: list[FactorResult] = []
    role_evidence = [f"required_skill:{skill}" for skill in required]
    factors.append(FactorResult(key="role_skill_coverage", label=FACTOR_WEIGHTS["role_skill_coverage"][0], score=role_score, weight=.30, available=role_score is not None, evidence=role_evidence, explanation="Matched required role skills divided by supported required skills; project descriptions can support a skill." if role_score is not None else "Unavailable because no supported required role skills were supplied."))

    project_score = None
    project_refs: list[str] = []
    if profile.projects:
        scores = []
        for index, project in enumerate(profile.projects):
            description_words = len(project.description.split())
            score = 35 + (20 if description_words >= 20 else 0) + (20 if project.url else 0)
            score += 15 if re.search(r"\b\d+(?:%|\+|\s*(?:users|requests|records|ms))\b", project.description, re.IGNORECASE) else 0
            score += 10 if any(_contains(project.description, skill) for skill in profile_skills.values()) else 0
            scores.append(min(score, 100))
            project_refs.append(f"project:{index + 1}:{project.title}")
        project_score = round(sum(scores) / len(scores))
    factors.append(FactorResult(key="project_evidence", label=FACTOR_WEIGHTS["project_evidence"][0], score=project_score, weight=.25, available=project_score is not None, evidence=project_refs, explanation="Project evidence uses explicit signals: a described project, a detailed description, a link, a quantified result, and a listed skill mention." if project_score is not None else "Unavailable because no project or work description was provided."))

    resume_score = None
    resume_refs: list[str] = []
    if profile.resume_sections is not None:
        sections = {_normalize(section) for section in profile.resume_sections}
        expected = {"education", "experience", "projects", "skills"}
        present = expected.intersection(sections)
        resume_score = round(100 * len(present) / len(expected))
        resume_refs = [f"resume_section:{section}" for section in sorted(present)]
    factors.append(FactorResult(key="resume_clarity", label=FACTOR_WEIGHTS["resume_clarity"][0], score=resume_score, weight=.20, available=resume_score is not None, evidence=resume_refs, explanation="Based only on the presence of Education, Experience, Projects, and Skills sections in a reviewed parse." if resume_score is not None else "Unavailable because no reviewed resume parse was supplied; resume is optional."))

    technical_score = None
    technical_refs: list[str] = []
    if profile.skills or profile.projects:
        project_supported = [skill for skill in profile_skills.values() if _contains(project_text, skill)]
        technical_score = min(100, 40 + 20 * len(project_supported)) if profile.skills else min(60, 20 + 20 * len(project_supported))
        technical_refs = [f"self_reported_skill:{skill}" for skill in profile_skills.values()] + [f"project_mentioned_skill:{skill}" for skill in project_supported]
    factors.append(FactorResult(key="technical_evidence", label=FACTOR_WEIGHTS["technical_evidence"][0], score=technical_score, weight=.15, available=technical_score is not None, evidence=technical_refs, explanation="Self-reported skills start at 40; each one also mentioned in a project description adds 20, capped at 100. This is not independent verification." if technical_score is not None else "Unavailable because no skill or project evidence was provided."))

    completed = sum(bool(value) for value in (profile.target_role, profile.branch, profile.graduation_year, profile.skills))
    completeness_score = round(100 * completed / 4) if completed else None
    completeness_refs = [name for name, present in (("target_role", bool(profile.target_role)), ("branch", bool(profile.branch)), ("graduation_year", profile.graduation_year is not None), ("skills", bool(profile.skills))) if present]
    factors.append(FactorResult(key="profile_completeness", label=FACTOR_WEIGHTS["profile_completeness"][0], score=completeness_score, weight=.10, available=completeness_score is not None, evidence=completeness_refs, explanation="One quarter each for target role, branch, graduation year, and at least one skill; CGPA and resume are optional." if completeness_score is not None else "Unavailable because no profile information was supplied."))

    available = [factor for factor in factors if factor.available and factor.score is not None]
    weight_total = sum(factor.weight for factor in available)
    score = floor(sum(factor.score * factor.weight for factor in available) / weight_total + .5) if weight_total else None
    excluded = [factor.key for factor in factors if not factor.available]
    provenance_count = int(bool(profile.skills)) + int(bool(profile.projects)) + int(profile.resume_sections is not None)
    confidence = "high" if len(available) >= 4 and provenance_count >= 3 else "medium" if len(available) >= 3 and provenance_count >= 2 else "low"
    readiness = {"score": score, "confidence": confidence, "scoring_version": "cp-v1", "factors": [factor.model_dump() for factor in factors], "excluded_factors": excluded}

    strengths = [{"label": skill, "evidence": "Listed as a self-reported skill" + (" and mentioned in a project description" if _contains(project_text, skill) else "."), "confidence": "medium" if _contains(project_text, skill) else "low"} for skill in profile_skills.values()]
    if profile.projects:
        strengths.extend({"label": project.title, "evidence": "Project description supplied by the student.", "confidence": "medium" if project.url else "low"} for project in profile.projects[:2])
    gaps = [{"label": skill, "importance": "required", "reason": "This explicit required skill was not shown in the profile skills or project descriptions."} for skill in missing]
    gaps.extend({"label": skill, "importance": "unknown", "reason": "This required term is outside the supported skill vocabulary; review or clarify it."} for skill in unknown_required)
    actions: list[dict[str, str]] = []
    eligibility = _eligibility(request)
    for reason in eligibility["reasons"]:
        if reason["code"].endswith("missing"):
            actions.append({"title": "Add the missing eligibility detail", "rationale": reason["message"], "completion_evidence": "Enter the requested value, if you’re comfortable sharing it."})
            break
    for skill in missing:
        actions.append({"title": f"Show evidence for {skill}", "rationale": f"{skill} is explicitly required but not shown in your profile.", "completion_evidence": f"Add a relevant project, work example, or resume detail mentioning {skill}."})
    for skill in unknown_required:
        actions.append({"title": f"Review the requirement: {skill}", "rationale": "This requirement could not be matched to the supported skill vocabulary.", "completion_evidence": "Clarify the requirement or map it to a supported skill."})
    if not profile.projects:
        actions.append({"title": "Add a project example", "rationale": "A concrete example gives context to self-reported skills.", "completion_evidence": "Describe what you built and your contribution; a link is optional."})
    if not actions and profile.skills:
        actions.append({"title": "Keep your profile current", "rationale": "A recent project or role description can make the next snapshot more specific.", "completion_evidence": "Add a new project or compare against a specific opportunity."})

    return {
        "id": uuid4(),
        "eligibility": eligibility,
        "readiness": readiness,
        "role_match": role_match,
        "profile_links": inspect_profile_links(profile.github_profile_url, profile.linkedin_profile_url),
        "strengths": strengths[:5],
        "gaps": gaps,
        "next_actions": actions[:3],
        "created_at": datetime.now(timezone.utc),
    }
