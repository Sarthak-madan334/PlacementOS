"""Deterministic, explainable opportunity and role matching engine (rm-v1).

Pure matching domain module independent of web, database, or external LLM services.
Extracts requirements from job descriptions, normalizes skills using a versioned alias vocabulary,
performs 3-state evidence matching (matched/missing/unknown), evaluates hard eligibility criteria,
and computes deterministic role-match scores.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional, Set, Tuple


# Matching engine version identifier
MATCHING_VERSION = "rm-v1"

# Versioned skill alias vocabulary (rm-v1)
# Maps variants, abbreviations, and common naming differences to canonical skill identifiers
SKILL_ALIASES_RM_V1: Dict[str, str] = {
    # Programming Languages
    "python": "python",
    "py": "python",
    "python3": "python",
    "python 3": "python",
    "js": "javascript",
    "javascript": "javascript",
    "ecmascript": "javascript",
    "ts": "typescript",
    "typescript": "typescript",
    "go": "go",
    "golang": "go",
    "go lang": "go",
    "c++": "cpp",
    "cpp": "cpp",
    "c#": "csharp",
    "csharp": "csharp",
    ".net": "dotnet",
    "dotnet": "dotnet",
    "rb": "ruby",
    "ruby": "ruby",
    "rust": "rust",
    "java": "java",
    "kotlin": "kotlin",
    "swift": "swift",
    "scala": "scala",
    "r": "r",

    # Web & Frameworks
    "react": "react",
    "reactjs": "react",
    "react.js": "react",
    "react native": "react native",
    "vue": "vue",
    "vuejs": "vue",
    "vue.js": "vue",
    "angular": "angular",
    "angularjs": "angular",
    "angular.js": "angular",
    "nextjs": "next.js",
    "next.js": "next.js",
    "node": "nodejs",
    "nodejs": "nodejs",
    "node.js": "nodejs",
    "express": "express",
    "expressjs": "express",
    "fastapi": "fastapi",
    "fast api": "fastapi",
    "django": "django",
    "flask": "flask",
    "spring": "spring",
    "spring boot": "spring boot",
    "springboot": "spring boot",
    "html": "html",
    "html5": "html",
    "css": "css",
    "css3": "css",
    "tailwind": "tailwind css",
    "tailwindcss": "tailwind css",
    "tailwind css": "tailwind css",
    "bootstrap": "bootstrap",
    "graphql": "graphql",
    "rest": "rest api",
    "rest api": "rest api",
    "restful": "rest api",
    "restful api": "rest api",

    # Databases & Storage
    "sql": "sql",
    "nosql": "nosql",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "pg": "postgresql",
    "mysql": "mysql",
    "sqlite": "sqlite",
    "mongo": "mongodb",
    "mongodb": "mongodb",
    "redis": "redis",
    "cassandra": "cassandra",
    "dynamodb": "dynamodb",
    "oracle": "oracle db",
    "oracle db": "oracle db",

    # Cloud & DevOps
    "docker": "docker",
    "k8s": "kubernetes",
    "kubernetes": "kubernetes",
    "aws": "amazon web services",
    "amazon web services": "amazon web services",
    "gcp": "google cloud platform",
    "google cloud": "google cloud platform",
    "google cloud platform": "google cloud platform",
    "azure": "microsoft azure",
    "microsoft azure": "microsoft azure",
    "ci/cd": "ci/cd",
    "cicd": "ci/cd",
    "git": "git",
    "github": "git",
    "gitlab": "git",
    "linux": "linux",
    "unix": "unix",
    "terraform": "terraform",
    "ansible": "ansible",

    # Data Science, AI & Machine Learning
    "ml": "machine learning",
    "machine learning": "machine learning",
    "ai": "artificial intelligence",
    "artificial intelligence": "artificial intelligence",
    "dl": "deep learning",
    "deep learning": "deep learning",
    "nlp": "natural language processing",
    "natural language processing": "natural language processing",
    "cv": "computer vision",
    "computer vision": "computer vision",
    "statistics": "statistics",
    "data analysis": "data analysis",
    "data analytics": "data analysis",
    "pandas": "pandas",
    "numpy": "numpy",
    "scipy": "scipy",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "pytorch": "pytorch",
    "torch": "pytorch",
    "tensorflow": "tensorflow",
    "tf": "tensorflow",
    "keras": "keras",
    "power bi": "power bi",
    "powerbi": "power bi",
    "tableau": "tableau",
    "excel": "excel",
    "ms excel": "excel",
    "microsoft excel": "excel",
    "spark": "apache spark",
    "apache spark": "apache spark",
    "hadoop": "hadoop",
}

# Branch normalization mapping for eligibility checking
BRANCH_ALIASES: Dict[str, str] = {
    "cs": "computer science",
    "cse": "computer science and engineering",
    "computer science": "computer science",
    "computer science and engineering": "computer science and engineering",
    "computer science & engineering": "computer science and engineering",
    "it": "information technology",
    "information technology": "information technology",
    "information science": "information science",
    "ise": "information science and engineering",
    "ece": "electronics and communication engineering",
    "electronics and communication": "electronics and communication engineering",
    "electronics and communication engineering": "electronics and communication engineering",
    "electronics & communication": "electronics and communication engineering",
    "ee": "electrical engineering",
    "eee": "electrical and electronics engineering",
    "electrical engineering": "electrical engineering",
    "mech": "mechanical engineering",
    "mechanical engineering": "mechanical engineering",
    "civil": "civil engineering",
    "civil engineering": "civil engineering",
    "ai": "artificial intelligence",
    "ai & ds": "artificial intelligence and data science",
    "aids": "artificial intelligence and data science",
    "artificial intelligence and data science": "artificial intelligence and data science",
    "data science": "data science",
}


def normalize_skill_name(name: str) -> str:
    """Normalize a skill name string using lowercasing, whitespace trimming, and versioned rm-v1 alias map."""
    cleaned = re.sub(r"\s+", " ", name.lower().strip())
    # Strip non-alphanumeric punctuation from boundaries, preserving +, #, ., / inside/around names
    cleaned = re.sub(r"^[^\w+#./]+|[^\w+#./]+$", "", cleaned)
    return SKILL_ALIASES_RM_V1.get(cleaned, cleaned)


def normalize_branch_name(branch: str) -> str:
    """Normalize academic branch string for comparison against eligibility criteria."""
    cleaned = re.sub(r"\s+", " ", branch.lower().strip())
    # Remove common degree prefixes like 'b.tech', 'b.e.', 'm.tech', 'bachelor of technology in'
    cleaned = re.sub(r"^(b\.?tech|b\.?e\.?|m\.?tech|bachelor of technology in|bachelor of engineering in)\s+", "", cleaned)
    cleaned = re.sub(r"^[^\w&]+|[^\w&]+$", "", cleaned)
    return BRANCH_ALIASES.get(cleaned, cleaned)


@dataclass
class ExtractedRequirement:
    """A requirement extracted from an opportunity or job description."""
    original_phrase: str
    normalized_skill: str
    category: str  # "required", "preferred", "unspecified"
    source_context: str = ""


@dataclass
class RequirementMatchItem:
    """Detailed evaluation of a single requirement against candidate evidence."""
    original_phrase: str
    normalized_skill: str
    category: str  # "required", "preferred", "unspecified"
    status: str  # "matched", "missing", "unknown"
    evidence_source: Optional[str] = None
    matched_text: Optional[str] = None
    explanation: str = ""


@dataclass
class EligibilityReason:
    code: str
    message: str


@dataclass
class EligibilityResult:
    status: str  # "eligible", "not_eligible", "unknown"
    reasons: List[EligibilityReason] = field(default_factory=list)


@dataclass
class StrengthItem:
    label: str
    evidence: str
    importance: str = "required"  # "required", "preferred"
    confidence: str = "medium"


@dataclass
class GapItem:
    label: str
    importance: str  # "required", "preferred", "unspecified"
    reason: str


@dataclass
class RoleMatchSummary:
    score: Optional[int]  # 0-100 or None if no assessable requirements
    matched_required: List[str] = field(default_factory=list)
    missing_required: List[str] = field(default_factory=list)
    unknown_required: List[str] = field(default_factory=list)
    matched_preferred: List[str] = field(default_factory=list)
    missing_preferred: List[str] = field(default_factory=list)
    total_required: int = 0
    total_preferred: int = 0
    explanation: str = ""
    reason_code: Optional[str] = None  # e.g. "NO_ASSESSABLE_REQUIREMENTS"


@dataclass
class MatchReport:
    matching_version: str
    eligibility: EligibilityResult
    role_match: RoleMatchSummary
    requirements: List[RequirementMatchItem]
    strengths: List[StrengthItem]
    gaps: List[GapItem]
    created_at: str


class RequirementExtractor:
    """Rule-based, deterministic extractor that classifies skills into required, preferred, and unspecified."""

    REQUIRED_SECTION_PATTERNS = [
        re.compile(r"(?:requirements|required|must have|mandatory|essential|minimum qualifications|what we are looking for|what you will need|basic qualifications)", re.IGNORECASE),
    ]

    PREFERRED_SECTION_PATTERNS = [
        re.compile(r"(?:preferred|nice to have|good to have|bonus|plus|desired|preferred qualifications|bonus points|optional)", re.IGNORECASE),
    ]

    REQUIRED_LINE_MARKERS = [
        re.compile(r"\b(?:required|must|mandatory|essential|minimum of|proficiency in|strong knowledge of|expertise in)\b", re.IGNORECASE),
    ]

    PREFERRED_LINE_MARKERS = [
        re.compile(r"\b(?:preferred|nice to have|good to have|bonus|plus|desired|optional|familiarity with|advantageous)\b", re.IGNORECASE),
    ]

    @classmethod
    def extract_from_text(cls, jd_text: str) -> List[ExtractedRequirement]:
        """Parse raw job description text and return classified skill requirements."""
        if not jd_text or not jd_text.strip():
            return []

        results: List[ExtractedRequirement] = []
        seen_normalized: Set[str] = set()

        lines = [line.strip() for line in jd_text.splitlines() if line.strip()]
        current_section_category = "unspecified"

        for line in lines:
            # 1. Check if line is a section heading
            is_heading = False
            for req_pat in cls.REQUIRED_SECTION_PATTERNS:
                if req_pat.search(line) and len(line) < 60:
                    current_section_category = "required"
                    is_heading = True
                    break

            if not is_heading:
                for pref_pat in cls.PREFERRED_SECTION_PATTERNS:
                    if pref_pat.search(line) and len(line) < 60:
                        current_section_category = "preferred"
                        is_heading = True
                        break

            if not is_heading:
                # Generic headings like "About the team:", "Responsibilities:", "Overview:" reset category to unspecified
                if (line.endswith(":") and len(line) < 60 and not line.startswith(("-", "•", "*"))) or re.match(r"^(about|responsibilities|overview|role|who we are|description)", line, re.IGNORECASE):
                    current_section_category = "unspecified"
                    is_heading = True

            if is_heading:
                continue

            # 2. Determine line category from explicit line markers or active section
            line_category = current_section_category

            for req_marker in cls.REQUIRED_LINE_MARKERS:
                if req_marker.search(line):
                    line_category = "required"
                    break

            for pref_marker in cls.PREFERRED_LINE_MARKERS:
                if pref_marker.search(line):
                    line_category = "preferred"
                    break

            # 3. Look for known skills in the line
            # Clean bullet symbols and punctuation
            cleaned_line = re.sub(r"^[\s*•\-–—\d.)]+", "", line).strip()
            if not cleaned_line:
                continue

            # Check known alias keys against line using word boundary matches
            # Sort alias keys by length descending to match multi-word phrases first (e.g. "machine learning" before "c")
            sorted_aliases = sorted(SKILL_ALIASES_RM_V1.keys(), key=lambda x: len(x), reverse=True)
            line_lower = cleaned_line.lower()

            for alias in sorted_aliases:
                # Use word boundaries for alphabetic aliases, literal matching for symbols like c++, c#
                if re.match(r"^[a-z0-9\s]+$", alias):
                    pattern = rf"\b{re.escape(alias)}\b"
                else:
                    pattern = rf"(?:^|\s|[(\[,]){re.escape(alias)}(?:$|\s|[)\],.:;])"

                match = re.search(pattern, line_lower)
                if match:
                    norm = SKILL_ALIASES_RM_V1[alias]
                    if norm not in seen_normalized:
                        seen_normalized.add(norm)
                        # Extract the exact phrase as written in the JD
                        orig_start = match.start()
                        orig_end = match.end()
                        orig_phrase = cleaned_line[orig_start:orig_end].strip(" (),.:;")
                        if not orig_phrase:
                            orig_phrase = alias

                        results.append(ExtractedRequirement(
                            original_phrase=orig_phrase,
                            normalized_skill=norm,
                            category=line_category,
                            source_context=cleaned_line[:120],
                        ))

        return results

    @classmethod
    def from_lists_and_text(
        cls,
        required_skills: Optional[List[str]] = None,
        preferred_skills: Optional[List[str]] = None,
        jd_text: Optional[str] = None,
    ) -> List[ExtractedRequirement]:
        """Combine explicit required/preferred skill lists with requirements extracted from JD text."""
        results: List[ExtractedRequirement] = []
        seen_normalized: Set[str] = set()

        # 1. Add explicitly declared required skills
        if required_skills:
            for s in required_skills:
                cleaned = s.strip()
                if not cleaned:
                    continue
                norm = normalize_skill_name(cleaned)
                if norm not in seen_normalized:
                    seen_normalized.add(norm)
                    results.append(ExtractedRequirement(
                        original_phrase=cleaned,
                        normalized_skill=norm,
                        category="required",
                        source_context="Explicitly specified in opportunity requirements",
                    ))

        # 2. Add explicitly declared preferred skills
        if preferred_skills:
            for s in preferred_skills:
                cleaned = s.strip()
                if not cleaned:
                    continue
                norm = normalize_skill_name(cleaned)
                if norm not in seen_normalized:
                    seen_normalized.add(norm)
                    results.append(ExtractedRequirement(
                        original_phrase=cleaned,
                        normalized_skill=norm,
                        category="preferred",
                        source_context="Explicitly specified in opportunity preferred skills",
                    ))

        # 3. Extract any additional skills from JD text
        if jd_text and jd_text.strip():
            extracted = cls.extract_from_text(jd_text)
            for item in extracted:
                if item.normalized_skill not in seen_normalized:
                    seen_normalized.add(item.normalized_skill)
                    results.append(item)

        return results


class MatchingEngine:
    """Pure, deterministic matching and eligibility engine implementing rm-v1 rules."""

    @staticmethod
    def evaluate_eligibility(
        profile_data: Dict[str, Any],
        explicit_criteria: Optional[Dict[str, Any]],
    ) -> EligibilityResult:
        """Evaluate hard eligibility constraints (CGPA, Branch, Graduation Year) strictly separated from role match."""
        if not explicit_criteria:
            return EligibilityResult(status="eligible", reasons=[])

        reasons: List[EligibilityReason] = []
        has_hard_fail = False

        # 1. Minimum CGPA check
        min_cgpa = explicit_criteria.get("min_cgpa")
        if min_cgpa is not None:
            try:
                min_val = float(min_cgpa)
                student_cgpa = profile_data.get("cgpa")
                if student_cgpa is None:
                    reasons.append(EligibilityReason(
                        code="CGPA_MISSING",
                        message="Add CGPA to verify this requirement."
                    ))
                else:
                    cgpa_val = float(student_cgpa)
                    if cgpa_val < min_val:
                        has_hard_fail = True
                        reasons.append(EligibilityReason(
                            code="CGPA_BELOW_MINIMUM",
                            message=f"CGPA ({cgpa_val}) is below the required minimum of {min_val}."
                        ))
            except (ValueError, TypeError):
                pass

        # 2. Eligible branches check
        allowed_branches = explicit_criteria.get("allowed_branches")
        if allowed_branches and isinstance(allowed_branches, list):
            norm_allowed = [normalize_branch_name(b) for b in allowed_branches if isinstance(b, str) and b.strip()]
            if norm_allowed:
                student_branch = profile_data.get("branch")
                if not student_branch or not str(student_branch).strip():
                    reasons.append(EligibilityReason(
                        code="BRANCH_MISSING",
                        message="Add branch of study to verify eligibility."
                    ))
                else:
                    norm_student_branch = normalize_branch_name(str(student_branch))
                    # Check if student branch matches any allowed branch
                    matched_branch = any(
                        norm_student_branch == ab or norm_student_branch in ab or ab in norm_student_branch
                        for ab in norm_allowed
                    )
                    if not matched_branch:
                        has_hard_fail = True
                        reasons.append(EligibilityReason(
                            code="BRANCH_NOT_ELIGIBLE",
                            message=f"Branch '{student_branch}' is not in the eligible branches list: {', '.join(allowed_branches)}."
                        ))

        # 3. Graduation year check
        allowed_years = explicit_criteria.get("allowed_years") or explicit_criteria.get("graduation_years")
        if allowed_years and isinstance(allowed_years, list):
            valid_years = [int(y) for y in allowed_years if isinstance(y, (int, str)) and str(y).isdigit()]
            if valid_years:
                student_year = profile_data.get("graduation_year")
                if student_year is None:
                    reasons.append(EligibilityReason(
                        code="GRADUATION_YEAR_MISSING",
                        message="Add graduation year to verify eligibility."
                    ))
                else:
                    try:
                        student_yr_val = int(student_year)
                        if student_yr_val not in valid_years:
                            has_hard_fail = True
                            reasons.append(EligibilityReason(
                                code="GRADUATION_YEAR_NOT_ELIGIBLE",
                                message=f"Graduation year {student_yr_val} is not in eligible batches: {', '.join(str(y) for y in valid_years)}."
                            ))
                    except (ValueError, TypeError):
                        pass

        # Final eligibility aggregation
        if has_hard_fail:
            status = "not_eligible"
        elif reasons:
            status = "unknown"
        else:
            status = "eligible"

        return EligibilityResult(status=status, reasons=reasons)

    @classmethod
    def match_evidence(
        cls,
        candidate_evidence: Dict[str, Any],
        requirements: List[ExtractedRequirement],
    ) -> List[RequirementMatchItem]:
        """Compare candidate evidence against extracted requirements and produce 3-state matched/missing/unknown results."""
        results: List[RequirementMatchItem] = []

        # 1. Aggregate candidate evidence by normalized skill key
        # skill_key -> list of evidence descriptions
        evidence_map: Dict[str, List[Dict[str, str]]] = {}

        # a. Explicit profile skills
        profile_skills = candidate_evidence.get("skills", [])
        for s in profile_skills:
            name = s if isinstance(s, str) else s.get("name", "")
            if name and name.strip():
                norm = normalize_skill_name(name)
                evidence_map.setdefault(norm, []).append({
                    "source": "profile_skill",
                    "text": name,
                    "detail": "Listed in profile skills",
                })

        # b. Parsed resume skills
        resume_skills = candidate_evidence.get("resume_skills", [])
        for rs in resume_skills:
            if isinstance(rs, str) and rs.strip():
                norm = normalize_skill_name(rs)
                evidence_map.setdefault(norm, []).append({
                    "source": "resume_skill",
                    "text": rs,
                    "detail": "Extracted from resume skills section",
                })

        # c. Project descriptions and titles
        projects = candidate_evidence.get("projects", [])
        project_corpus = []
        for p in projects:
            title = p.get("title", "") if isinstance(p, dict) else getattr(p, "title", "")
            desc = p.get("description", "") if isinstance(p, dict) else getattr(p, "description", "")
            url = p.get("url", "") if isinstance(p, dict) else getattr(p, "url", "")
            combined_text = f"{title} {desc}".lower()
            project_corpus.append((title, combined_text, url))

        # 2. Evaluate each requirement against the evidence map and corpus
        for req in requirements:
            norm = req.normalized_skill
            matched_sources: List[str] = []
            matched_texts: List[str] = []

            # Direct hit in evidence map
            if norm in evidence_map:
                for ev in evidence_map[norm]:
                    matched_sources.append(ev["source"])
                    matched_texts.append(ev["text"])

            # Check project corpus for corroborating mentions
            for proj_title, proj_text, proj_url in project_corpus:
                # Match normalized skill or original phrase in project text
                if norm in proj_text or req.original_phrase.lower() in proj_text:
                    link_info = " (with repository link)" if proj_url else ""
                    matched_sources.append(f"project:{proj_title}{link_info}")
                    matched_texts.append(proj_title)

            # Determine 3-state match status
            if matched_sources:
                status = "matched"
                source_summary = ", ".join(dict.fromkeys(matched_sources))
                text_summary = ", ".join(dict.fromkeys(matched_texts))
                explanation = f"Demonstrated in student evidence ({source_summary})."
            else:
                # "Missing" in the evidence: not demonstrated, not "cannot do"
                status = "missing"
                source_summary = None
                text_summary = None
                explanation = f"'{req.original_phrase}' was not demonstrated in the available evidence."

            results.append(RequirementMatchItem(
                original_phrase=req.original_phrase,
                normalized_skill=req.normalized_skill,
                category=req.category,
                status=status,
                evidence_source=source_summary,
                matched_text=text_summary,
                explanation=explanation,
            ))

        return results

    @classmethod
    def evaluate(
        cls,
        candidate_evidence: Dict[str, Any],
        opportunity_data: Dict[str, Any],
    ) -> MatchReport:
        """Perform end-to-end matching evaluation between candidate evidence and opportunity."""
        # 1. Extract requirements
        required_skills = opportunity_data.get("required_skills", [])
        preferred_skills = opportunity_data.get("preferred_skills", [])
        jd_text = opportunity_data.get("jd_text", "")
        explicit_criteria = opportunity_data.get("explicit_criteria", {})

        requirements = RequirementExtractor.from_lists_and_text(
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            jd_text=jd_text,
        )

        # 2. Evaluate hard eligibility
        eligibility = cls.evaluate_eligibility(
            profile_data=candidate_evidence,
            explicit_criteria=explicit_criteria,
        )

        # 3. Match evidence against requirements
        evaluated_requirements = cls.match_evidence(
            candidate_evidence=candidate_evidence,
            requirements=requirements,
        )

        # 4. Compute role-match score across assessable required skills
        required_items = [r for r in evaluated_requirements if r.category == "required"]
        preferred_items = [r for r in evaluated_requirements if r.category == "preferred"]

        matched_req = [r.original_phrase for r in required_items if r.status == "matched"]
        missing_req = [r.original_phrase for r in required_items if r.status == "missing"]
        unknown_req = [r.original_phrase for r in required_items if r.status == "unknown"]

        matched_pref = [r.original_phrase for r in preferred_items if r.status == "matched"]
        missing_pref = [r.original_phrase for r in preferred_items if r.status == "missing"]

        assessable_required_count = len(matched_req) + len(missing_req)

        if assessable_required_count == 0:
            score = None
            reason_code = "NO_ASSESSABLE_REQUIREMENTS"
            explanation = "No usable required skills were specified or extracted from the opportunity."
        else:
            score = round((len(matched_req) / assessable_required_count) * 100)
            reason_code = None
            explanation = f"Matched {len(matched_req)} of {assessable_required_count} assessable required skill(s) ({score}%)."

        role_match_summary = RoleMatchSummary(
            score=score,
            matched_required=sorted(matched_req),
            missing_required=sorted(missing_req),
            unknown_required=sorted(unknown_req),
            matched_preferred=sorted(matched_pref),
            missing_preferred=sorted(missing_pref),
            total_required=len(required_items),
            total_preferred=len(preferred_items),
            explanation=explanation,
            reason_code=reason_code,
        )

        # 5. Extract explainable strengths and gaps
        strengths: List[StrengthItem] = []
        gaps: List[GapItem] = []

        for req in evaluated_requirements:
            if req.status == "matched":
                strengths.append(StrengthItem(
                    label=req.original_phrase,
                    evidence=req.explanation,
                    importance=req.category,
                    confidence="high" if req.evidence_source and "project" in req.evidence_source else "medium",
                ))
            elif req.status == "missing":
                gaps.append(GapItem(
                    label=req.original_phrase,
                    importance=req.category,
                    reason=f"Required in the opportunity description." if req.category == "required" else f"Preferred skill for this role.",
                ))

        # Sort strengths and gaps deterministically
        strengths.sort(key=lambda s: (0 if s.importance == "required" else 1, s.label.lower()))
        gaps.sort(key=lambda g: (0 if g.importance == "required" else 1, g.label.lower()))

        now_iso = datetime.now(timezone.utc).isoformat()

        return MatchReport(
            matching_version=MATCHING_VERSION,
            eligibility=eligibility,
            role_match=role_match_summary,
            requirements=evaluated_requirements,
            strengths=strengths,
            gaps=gaps,
            created_at=now_iso,
        )
