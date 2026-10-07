"""Deterministic, explainable readiness calculation engine (cp-v1).

Pure scoring domain module independent of web, database, or LLM services.
Calculates factor scores, renormalizes weights over available evidence,
determines eligibility separately from readiness, and provides actionable recommendations.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional, Set, Tuple


# Scoring model version identifier
SCORING_VERSION = "cp-v1"

# Factor keys and standard weights
FACTOR_WEIGHTS: Dict[str, float] = {
    "role_skill_coverage": 0.30,
    "project_evidence": 0.25,
    "resume_clarity": 0.20,
    "technical_skills": 0.15,
    "profile_completeness": 0.10,
}

# Versioned skill alias vocabulary (cp-v1)
SKILL_ALIASES_V1: Dict[str, str] = {
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "python3": "python",
    "react.js": "react",
    "reactjs": "react",
    "node": "nodejs",
    "node.js": "nodejs",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "pg": "postgresql",
    "mongo": "mongodb",
    "mongodb": "mongodb",
    "golang": "go",
    "k8s": "kubernetes",
    "kubernetes": "kubernetes",
    "aws": "amazon web services",
    "amazon web services": "amazon web services",
    "gcp": "google cloud platform",
    "google cloud": "google cloud platform",
    "docker": "docker",
    "rest": "rest api",
    "rest api": "rest api",
    "restful": "rest api",
    "fastapi": "fastapi",
    "django": "django",
    "flask": "flask",
    "sql": "sql",
    "nosql": "nosql",
    "c++": "cpp",
    "cpp": "cpp",
    "c#": "csharp",
    "csharp": "csharp",
    ".net": "dotnet",
    "dotnet": "dotnet",
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "html5": "html",
    "css3": "css",
}


def normalize_skill_name(name: str) -> str:
    """Normalize a skill name using lowercasing, whitespace trimming, and versioned alias map."""
    cleaned = re.sub(r"\s+", " ", name.lower().strip())
    # Strip leading/trailing punctuation if not part of name like c++ / c#
    cleaned = re.sub(r"^[^\w+#]+|[^\w+#]+$", "", cleaned)
    return SKILL_ALIASES_V1.get(cleaned, cleaned)


@dataclass
class SkillEvidence:
    name: str
    normalized_name: str
    source: str = "self_reported"  # self_reported, resume, project
    self_reported_level: Optional[str] = None


@dataclass
class ProjectEvidence:
    title: str
    description: str
    url: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@dataclass
class ResumeEvidence:
    sections_present: List[str] = field(default_factory=list)
    contact_present: bool = False
    education_present: bool = False
    skills_present: bool = False
    experience_present: bool = False
    extracted_skills: List[str] = field(default_factory=list)
    action_verbs_count: int = 0
    quantified_outcomes_count: int = 0
    weak_language_count: int = 0
    raw_text: Optional[str] = None


@dataclass
class StudentProfileEvidence:
    full_name: Optional[str] = None
    branch: Optional[str] = None
    graduation_year: Optional[int] = None
    cgpa: Optional[float] = None
    cgpa_scale: Optional[float] = None
    target_role: Optional[str] = None
    skills: List[SkillEvidence] = field(default_factory=list)
    projects: List[ProjectEvidence] = field(default_factory=list)
    resume: Optional[ResumeEvidence] = None


@dataclass
class OpportunityRequirement:
    role_title: Optional[str] = None
    company: Optional[str] = None
    jd_text: Optional[str] = None
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    explicit_criteria: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FactorEvaluation:
    key: str
    name: str
    score: int
    weight: float
    available: bool
    evidence: List[str]
    explanation: str


@dataclass
class EligibilityReason:
    code: str
    message: str


@dataclass
class EligibilityResult:
    status: str  # eligible, not_eligible, unknown
    reasons: List[EligibilityReason] = field(default_factory=list)


@dataclass
class RoleMatchResult:
    score: Optional[int]
    matched: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)
    unknown: List[str] = field(default_factory=list)


@dataclass
class StrengthItem:
    label: str
    evidence: str
    confidence: str = "medium"


@dataclass
class GapItem:
    label: str
    importance: str  # required, preferred, improvement
    reason: str


@dataclass
class NextAction:
    title: str
    rationale: str
    completion_evidence: str


@dataclass
class ReadinessResult:
    score: Optional[int]
    confidence: str  # low, medium, high
    scoring_version: str
    factors: List[FactorEvaluation]
    excluded_factors: List[str]


@dataclass
class AssessmentReport:
    eligibility: EligibilityResult
    readiness: ReadinessResult
    role_match: Optional[RoleMatchResult]
    strengths: List[StrengthItem]
    gaps: List[GapItem]
    next_actions: List[NextAction]
    scoring_version: str
    created_at: str


class ReadinessEngine:
    """Pure deterministic implementation of cp-v1 scoring rules."""

    @staticmethod
    def evaluate_eligibility(
        profile: StudentProfileEvidence,
        opportunity: Optional[OpportunityRequirement],
    ) -> EligibilityResult:
        """Evaluate hard eligibility criteria (CGPA, Branch, Graduation Year) strictly separated from readiness score."""
        if not opportunity or not opportunity.explicit_criteria:
            return EligibilityResult(status="eligible", reasons=[])

        criteria = opportunity.explicit_criteria
        reasons: List[EligibilityReason] = []
        has_hard_fail = False

        # 1. Minimum CGPA check
        min_cgpa = criteria.get("min_cgpa")
        if min_cgpa is not None:
            try:
                min_val = float(min_cgpa)
                if profile.cgpa is None:
                    reasons.append(EligibilityReason(
                        code="cgpa_missing",
                        message="Add CGPA to check this requirement."
                    ))
                elif profile.cgpa < min_val:
                    has_hard_fail = True
                    reasons.append(EligibilityReason(
                        code="cgpa_below_minimum",
                        message=f"CGPA ({profile.cgpa}) is below the required minimum of {min_val}."
                    ))
            except (ValueError, TypeError):
                pass

        # 2. Eligible branches check
        allowed_branches = criteria.get("allowed_branches")
        if allowed_branches and isinstance(allowed_branches, list):
            allowed_norm = [b.lower().strip() for b in allowed_branches if isinstance(b, str)]
            if allowed_norm:
                if not profile.branch or not profile.branch.strip():
                    reasons.append(EligibilityReason(
                        code="branch_missing",
                        message="Add branch of study to verify eligibility."
                    ))
                else:
                    stud_branch = profile.branch.lower().strip()
                    matched = any(ab in stud_branch or stud_branch in ab for ab in allowed_norm)
                    if not matched:
                        has_hard_fail = True
                        reasons.append(EligibilityReason(
                            code="branch_not_eligible",
                            message=f"Branch '{profile.branch}' is not in the eligible branches list."
                        ))

        # 3. Graduation year check
        allowed_years = criteria.get("allowed_years")
        if allowed_years and isinstance(allowed_years, list):
            if profile.graduation_year is None:
                reasons.append(EligibilityReason(
                    code="grad_year_missing",
                    message="Add graduation year to verify eligibility."
                ))
            elif profile.graduation_year not in allowed_years:
                has_hard_fail = True
                reasons.append(EligibilityReason(
                    code="grad_year_mismatch",
                    message=f"Graduation year {profile.graduation_year} is not eligible for this opportunity."
                ))

        if has_hard_fail:
            return EligibilityResult(status="not_eligible", reasons=reasons)
        elif len(reasons) > 0:
            return EligibilityResult(status="unknown", reasons=reasons)
        else:
            return EligibilityResult(status="eligible", reasons=[])

    @staticmethod
    def _evaluate_role_skill_coverage(
        profile: StudentProfileEvidence,
        opportunity: Optional[OpportunityRequirement],
    ) -> Tuple[FactorEvaluation, Optional[RoleMatchResult]]:
        """Factor 1: Role skill coverage (30%). Evaluates coverage of required JD skills."""
        weight = FACTOR_WEIGHTS["role_skill_coverage"]

        # Collect all student skills from profile and resume
        student_skills_map: Dict[str, str] = {}
        for s in profile.skills:
            norm = s.normalized_name or normalize_skill_name(s.name)
            student_skills_map[norm] = s.name

        if profile.resume and profile.resume.extracted_skills:
            for r_skill in profile.resume.extracted_skills:
                norm = normalize_skill_name(r_skill)
                if norm not in student_skills_map:
                    student_skills_map[norm] = r_skill

        # Project text search for technologies
        project_text = " ".join(f"{p.title} {p.description}" for p in profile.projects).lower()

        # If no opportunity or no role requirements are provided, factor is UNAVAILABLE
        if not opportunity or (not opportunity.required_skills and not opportunity.jd_text and not opportunity.role_title):
            eval_res = FactorEvaluation(
                key="role_skill_coverage",
                name="Role Skill Coverage",
                score=0,
                weight=weight,
                available=False,
                evidence=[],
                explanation="No target role or JD requirements provided to evaluate skill coverage.",
            )
            return eval_res, None

        required_skills = [s.strip() for s in opportunity.required_skills if s and s.strip()]

        if not required_skills:
            # Opportunity provided with title/JD but no explicit required skill list
            eval_res = FactorEvaluation(
                key="role_skill_coverage",
                name="Role Skill Coverage",
                score=0,
                weight=weight,
                available=False,
                evidence=[],
                explanation="No explicit required skills specified in the target role.",
            )
            return eval_res, RoleMatchResult(score=None, matched=[], missing=[], unknown=[])

        matched_skills: List[str] = []
        missing_skills: List[str] = []

        for req in required_skills:
            req_norm = normalize_skill_name(req)
            # Check direct match in student skills
            if req_norm in student_skills_map:
                matched_skills.append(req)
            elif req_norm in project_text:
                matched_skills.append(req)
            else:
                missing_skills.append(req)

        coverage_ratio = len(matched_skills) / len(required_skills)
        score = int(round(coverage_ratio * 100))

        evidence_list = [f"skill:{s}" for s in matched_skills]
        explanation = f"Matched {len(matched_skills)} of {len(required_skills)} required role skill(s)."

        eval_res = FactorEvaluation(
            key="role_skill_coverage",
            name="Role Skill Coverage",
            score=max(0, min(100, score)),
            weight=weight,
            available=True,
            evidence=evidence_list,
            explanation=explanation,
        )

        role_match = RoleMatchResult(
            score=max(0, min(100, score)),
            matched=matched_skills,
            missing=missing_skills,
            unknown=[],
        )

        return eval_res, role_match

    @staticmethod
    def _evaluate_project_evidence(
        profile: StudentProfileEvidence,
    ) -> FactorEvaluation:
        """Factor 2: Demonstrated project / work evidence (25%)."""
        weight = FACTOR_WEIGHTS["project_evidence"]

        if not profile.projects and (not profile.resume or not profile.resume.experience_present):
            return FactorEvaluation(
                key="project_evidence",
                name="Demonstrated Project / Work Evidence",
                score=0,
                weight=weight,
                available=True,
                evidence=[],
                explanation="No project or work evidence demonstrated.",
            )

        score = 0
        evidence: List[str] = []
        num_projects = len(profile.projects)

        # Base score by project count
        if num_projects == 1:
            score += 40
        elif num_projects == 2:
            score += 65
        elif num_projects >= 3:
            score += 80

        # Substantive descriptions and URLs
        has_substantive_desc = False
        has_url = False
        for p in profile.projects:
            evidence.append(p.title)
            if len(p.description.strip()) >= 50:
                has_substantive_desc = True
            if p.url and p.url.strip().startswith(("http://", "https://")):
                has_url = True

        if has_substantive_desc:
            score += 10
        if has_url:
            score += 10

        # Experience from resume
        if profile.resume and profile.resume.experience_present:
            score = max(score, score + 10)

        final_score = max(0, min(100, score))
        explanation = f"{num_projects} project(s) demonstrated with technical descriptions."
        if has_url:
            explanation += " Includes verifiable repository / live links."

        return FactorEvaluation(
            key="project_evidence",
            name="Demonstrated Project / Work Evidence",
            score=final_score,
            weight=weight,
            available=True,
            evidence=evidence,
            explanation=explanation,
        )

    @staticmethod
    def _evaluate_resume_clarity(
        profile: StudentProfileEvidence,
    ) -> FactorEvaluation:
        """Factor 3: Resume clarity and completeness (20%)."""
        weight = FACTOR_WEIGHTS["resume_clarity"]

        if not profile.resume or (
            not profile.resume.sections_present
            and not profile.resume.contact_present
            and not profile.resume.education_present
            and not profile.resume.skills_present
            and not profile.resume.experience_present
        ):
            return FactorEvaluation(
                key="resume_clarity",
                name="Resume Clarity and Completeness",
                score=0,
                weight=weight,
                available=False,
                evidence=[],
                explanation="No parsed resume provided; factor excluded from readiness assessment.",
            )

        resume = profile.resume
        points = 0
        evidence: List[str] = []

        # Structural sections check (20 points each, up to 80)
        if resume.contact_present:
            points += 20
            evidence.append("section:contact")
        if resume.education_present:
            points += 20
            evidence.append("section:education")
        if resume.skills_present:
            points += 20
            evidence.append("section:skills")
        if resume.experience_present:
            points += 20
            evidence.append("section:experience")

        # Quality signals adjustment (+10 for strong verbs/quantified, -10 for weak language)
        if resume.quantified_outcomes_count > 0 or resume.action_verbs_count >= 2:
            points += 20
            evidence.append("signals:quantified_and_action_verbs")
        elif resume.action_verbs_count > 0:
            points += 10
            evidence.append("signals:action_verbs")

        if resume.weak_language_count >= 2:
            points -= 10
            evidence.append("signals:weak_language_penalty")

        final_score = max(0, min(100, points))
        explanation = f"Structured resume parsed with {len(evidence)} verified section and quality components."

        return FactorEvaluation(
            key="resume_clarity",
            name="Resume Clarity and Completeness",
            score=final_score,
            weight=weight,
            available=True,
            evidence=evidence,
            explanation=explanation,
        )

    @staticmethod
    def _evaluate_technical_skills(
        profile: StudentProfileEvidence,
    ) -> FactorEvaluation:
        """Factor 4: Technical skill evidence (15%)."""
        weight = FACTOR_WEIGHTS["technical_skills"]

        # Distinct normalized skills from profile and resume
        skill_names: Set[str] = set()
        evidence: List[str] = []
        for s in profile.skills:
            norm = s.normalized_name or normalize_skill_name(s.name)
            if norm not in skill_names:
                skill_names.add(norm)
                evidence.append(s.name)

        if profile.resume:
            for r_skill in profile.resume.extracted_skills:
                norm = normalize_skill_name(r_skill)
                if norm not in skill_names:
                    skill_names.add(norm)
                    evidence.append(r_skill)

        num_skills = len(skill_names)
        if num_skills == 0:
            return FactorEvaluation(
                key="technical_skills",
                name="Technical Skill Evidence",
                score=0,
                weight=weight,
                available=True,
                evidence=[],
                explanation="No technical skills reported or demonstrated.",
            )

        score = 0
        if num_skills <= 2:
            score = 45
        elif num_skills <= 4:
            score = 70
        elif num_skills <= 7:
            score = 85
        else:
            score = 95

        # Cross-reference with project descriptions for verified depth
        project_text = " ".join(p.description.lower() for p in profile.projects)
        verified_count = sum(1 for norm in skill_names if norm in project_text)
        if verified_count >= 2:
            score = min(100, score + 10)

        final_score = max(0, min(100, score))
        explanation = f"{num_skills} technical skill(s) supported by evidence."
        if verified_count > 0:
            explanation += f" {verified_count} skill(s) corroborated by project descriptions."

        return FactorEvaluation(
            key="technical_skills",
            name="Technical Skill Evidence",
            score=final_score,
            weight=weight,
            available=True,
            evidence=evidence[:10],
            explanation=explanation,
        )

    @staticmethod
    def _evaluate_profile_completeness(
        profile: StudentProfileEvidence,
    ) -> FactorEvaluation:
        """Factor 5: Profile completeness (10%)."""
        weight = FACTOR_WEIGHTS["profile_completeness"]

        points = 0
        evidence: List[str] = []

        if profile.full_name and profile.full_name.strip():
            points += 20
            evidence.append("field:full_name")
        if profile.branch and profile.branch.strip():
            points += 20
            evidence.append("field:branch")
        if profile.graduation_year is not None and profile.graduation_year > 0:
            points += 20
            evidence.append("field:graduation_year")
        if profile.target_role and profile.target_role.strip():
            points += 20
            evidence.append("field:target_role")
        if profile.skills:
            points += 10
            evidence.append(f"skills_count:{len(profile.skills)}")
        if profile.projects:
            points += 10
            evidence.append(f"projects_count:{len(profile.projects)}")

        final_score = max(0, min(100, points))
        explanation = f"Profile completeness is {final_score}% across core identity and evidence fields."

        return FactorEvaluation(
            key="profile_completeness",
            name="Profile Completeness",
            score=final_score,
            weight=weight,
            available=True,
            evidence=evidence,
            explanation=explanation,
        )

    @staticmethod
    def _calculate_confidence(
        assessable_weight: float,
        profile: StudentProfileEvidence,
        has_role_match: bool,
    ) -> str:
        """Derive confidence based strictly on evidence source quality and completeness."""
        if assessable_weight < 0.40:
            return "low"
        elif assessable_weight >= 0.85 and profile.resume is not None and profile.projects:
            return "high"
        elif assessable_weight >= 0.60:
            return "medium"
        else:
            return "low"

    @staticmethod
    def _generate_strengths_and_gaps(
        profile: StudentProfileEvidence,
        factors: List[FactorEvaluation],
        role_match: Optional[RoleMatchResult],
    ) -> Tuple[List[StrengthItem], List[GapItem]]:
        """Identify concrete observable strengths and evidence gaps."""
        strengths: List[StrengthItem] = []
        gaps: List[GapItem] = []

        # Role match gaps & strengths
        if role_match and role_match.score is not None:
            for s in role_match.matched:
                strengths.append(StrengthItem(
                    label=s,
                    evidence="Matched to target role requirements with profile/project evidence",
                    confidence="medium" if len(profile.projects) > 0 else "low",
                ))
            for m in role_match.missing:
                gaps.append(GapItem(
                    label=m,
                    importance="required",
                    reason="Required in target role description but missing from evidence.",
                ))

        # Project evidence
        proj_factor = next((f for f in factors if f.key == "project_evidence"), None)
        if proj_factor and proj_factor.score >= 70:
            strengths.append(StrengthItem(
                label="Project Portfolio",
                evidence=f"{len(profile.projects)} demonstrated project(s) with descriptions",
                confidence="high",
            ))
        elif not profile.projects:
            gaps.append(GapItem(
                label="Project Evidence",
                importance="required",
                reason="No projects or practical implementations demonstrated.",
            ))

        # Technical skills
        skills_factor = next((f for f in factors if f.key == "technical_skills"), None)
        if skills_factor and skills_factor.score >= 80:
            strengths.append(StrengthItem(
                label="Technical Breadth",
                evidence=f"{len(profile.skills)} technical skills reported and corroborated",
                confidence="high",
            ))

        # Resume clarity
        resume_factor = next((f for f in factors if f.key == "resume_clarity"), None)
        if not resume_factor or not resume_factor.available:
            gaps.append(GapItem(
                label="Resume Evidence",
                importance="preferred",
                reason="No parsed resume provided; upload a resume to verify structured sections.",
            ))

        return strengths[:5], gaps

    @staticmethod
    def _generate_recommendations(
        gaps: List[GapItem],
        profile: StudentProfileEvidence,
        role_match: Optional[RoleMatchResult],
    ) -> List[NextAction]:
        """Generate up to 3 prioritized, evidence-based recommendations."""
        actions: List[NextAction] = []

        # 1. Missing required role skill
        if role_match and role_match.missing:
            top_missing = role_match.missing[0]
            actions.append(NextAction(
                title=f"Demonstrate {top_missing} in a project",
                rationale=f"{top_missing} is a required role skill without demonstrated project evidence.",
                completion_evidence=f"Build a project demonstrating {top_missing} and provide a descriptive summary and URL.",
            ))

        # 2. Missing project links / evidence
        if not profile.projects:
            actions.append(NextAction(
                title="Add demonstrated project evidence",
                rationale="Practical projects validate technical skills beyond self-reported claims.",
                completion_evidence="Add at least one detailed project with title, description, and repository URL.",
            ))
        elif any(not (p.url and p.url.strip()) for p in profile.projects):
            actions.append(NextAction(
                title="Add verifiable repository / live links to projects",
                rationale="Direct links increase evidence confidence and verify project authenticity.",
                completion_evidence="Attach active GitHub or deployment URLs to your existing project entries.",
            ))

        # 3. Missing resume
        if not profile.resume and len(actions) < 3:
            actions.append(NextAction(
                title="Upload and parse resume",
                rationale="A structured resume validates formatting, experience dates, and quality signals.",
                completion_evidence="Upload a PDF or DOCX resume to assess resume clarity and section completeness.",
            ))

        # 4. Profile completeness gaps
        if (not profile.target_role or not profile.branch) and len(actions) < 3:
            actions.append(NextAction(
                title="Complete target role and academic profile",
                rationale="Complete profile fields enable tailored eligibility checks and role matching.",
                completion_evidence="Fill in target role, branch, and graduation year in your profile.",
            ))

        return actions[:3]

    @classmethod
    def evaluate(
        cls,
        profile: StudentProfileEvidence,
        opportunity: Optional[OpportunityRequirement] = None,
    ) -> AssessmentReport:
        """Execute full cp-v1 assessment deterministically across all factors."""
        # 1. Eligibility evaluation
        eligibility = cls.evaluate_eligibility(profile, opportunity)

        # 2. Individual factor evaluations
        factor_role, role_match = cls._evaluate_role_skill_coverage(profile, opportunity)
        factor_project = cls._evaluate_project_evidence(profile)
        factor_resume = cls._evaluate_resume_clarity(profile)
        factor_skills = cls._evaluate_technical_skills(profile)
        factor_profile = cls._evaluate_profile_completeness(profile)

        factors = [
            factor_role,
            factor_project,
            factor_resume,
            factor_skills,
            factor_profile,
        ]

        # 3. Weight renormalization over assessable factors
        assessable_factors = [f for f in factors if f.available]
        excluded_factors = [f.key for f in factors if not f.available]
        total_assessable_weight = sum(f.weight for f in assessable_factors)

        if total_assessable_weight == 0:
            final_readiness_score: Optional[int] = None
            confidence = "low"
        else:
            weighted_sum = sum(f.score * f.weight for f in assessable_factors)
            normalized = weighted_sum / total_assessable_weight
            final_readiness_score = max(0, min(100, int(round(normalized))))
            confidence = cls._calculate_confidence(
                total_assessable_weight,
                profile,
                has_role_match=(role_match is not None and role_match.score is not None),
            )

        readiness = ReadinessResult(
            score=final_readiness_score,
            confidence=confidence,
            scoring_version=SCORING_VERSION,
            factors=factors,
            excluded_factors=excluded_factors,
        )

        # 4. Strengths, gaps, and recommendations
        strengths, gaps = cls._generate_strengths_and_gaps(profile, factors, role_match)
        next_actions = cls._generate_recommendations(gaps, profile, role_match)

        now_utc = datetime.now(timezone.utc).isoformat()

        return AssessmentReport(
            eligibility=eligibility,
            readiness=readiness,
            role_match=role_match,
            strengths=strengths,
            gaps=gaps,
            next_actions=next_actions,
            scoring_version=SCORING_VERSION,
            created_at=now_utc,
        )
