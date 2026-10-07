"""Deterministic Resume Parser service implementing evidence extraction and quality heuristics."""

import re
from typing import Dict, List, Optional, Set, Tuple

from app.adapters.parser.base import ExtractedDocument, PageSegment
from app.adapters.parser.docx_adapter import extract_docx
from app.adapters.parser.pdf_adapter import extract_pdf
from app.adapters.parser.txt_adapter import extract_txt
from app.adapters.parser.validator import ParserException, validate_and_detect_format
from app.api.v1.schemas.resume import (
    CandidateFacts,
    ContactFacts,
    EducationFact,
    ExperienceFact,
    ProjectFact,
    QualitySignal,
    ResumeParseResponse,
    SkillFact,
)

# Deterministic Skill Vocabulary (normalized_name -> display_name)
TECHNICAL_SKILLS: Dict[str, str] = {
    "python": "Python",
    "java": "Java",
    "c++": "C++",
    "c": "C",
    "c#": "C#",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "go": "Go",
    "rust": "Rust",
    "ruby": "Ruby",
    "php": "PHP",
    "swift": "Swift",
    "kotlin": "Kotlin",
    "sql": "SQL",
    "html": "HTML",
    "css": "CSS",
    "react": "React",
    "next.js": "Next.js",
    "vue": "Vue.js",
    "angular": "Angular",
    "node.js": "Node.js",
    "express": "Express.js",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "django": "Django",
    "spring boot": "Spring Boot",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "sqlite": "SQLite",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "aws": "AWS",
    "azure": "Azure",
    "gcp": "Google Cloud",
    "git": "Git",
    "github": "GitHub",
    "linux": "Linux",
    "rest api": "REST API",
    "graphql": "GraphQL",
    "ci/cd": "CI/CD",
    "tailwind": "Tailwind CSS",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "scikit-learn": "Scikit-Learn",
    "machine learning": "Machine Learning",
    "data science": "Data Science",
}

# Strong action verbs commonly used in high-impact resume bullets
ACTION_VERBS: Set[str] = {
    "architected", "built", "created", "deployed", "designed", "developed",
    "engineered", "implemented", "integrated", "launched", "led", "optimized",
    "orchestrated", "refactored", "resolved", "spearheaded", "transformed",
    "automated", "scaled", "reduced", "increased", "generated", "authored"
}

# Weak or vague phrases
WEAK_PHRASES: List[Tuple[str, str]] = [
    ("responsible for", "Passive duty description instead of active achievement"),
    ("assisted with", "Vague participation without clearly defined ownership"),
    ("helped to", "Vague participation without measurable contribution"),
    ("worked on", "Generic phrasing without indicating outcome or role"),
    ("handled", "Vague operational task phrasing"),
]

# Section header regex patterns
SECTION_PATTERNS: Dict[str, re.Pattern] = {
    "Education": re.compile(r"^(?:education|academic background|academics|qualifications|academic history)\b", re.I),
    "Experience": re.compile(r"^(?:work experience|professional experience|experience|employment history|internships)\b", re.I),
    "Projects": re.compile(r"^(?:projects|academic projects|key projects|personal projects|technical projects)\b", re.I),
    "Skills": re.compile(r"^(?:technical skills|skills & tools|skills|technologies|core competencies|toolset)\b", re.I),
    "Certifications": re.compile(r"^(?:certifications|licenses & certifications|certificates)\b", re.I),
    "Achievements": re.compile(r"^(?:achievements|honors & awards|awards|accomplishments)\b", re.I),
    "Contact": re.compile(r"^(?:contact|contact information|personal details)\b", re.I),
}


def normalize_text(text: str) -> str:
    """Normalize whitespace and linebreaks while preserving line structure."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace non-breaking spaces
    text = text.replace("\xa0", " ").replace("\u200b", "")
    return text


def detect_sections(text: str) -> Dict[str, List[str]]:
    """Split text lines into detected standard resume sections."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    sections: Dict[str, List[str]] = {"Header": []}
    current_section = "Header"

    for line in lines:
        cleaned_line = line.strip(" :-\t#*").strip()
        matched_section = None

        if len(cleaned_line) < 40:
            for sec_name, pattern in SECTION_PATTERNS.items():
                if pattern.match(cleaned_line):
                    matched_section = sec_name
                    break

        if matched_section:
            current_section = matched_section
            if current_section not in sections:
                sections[current_section] = []
        else:
            sections.setdefault(current_section, []).append(line)

    return sections


def extract_contact_info(text: str, sections: Dict[str, List[str]]) -> ContactFacts:
    """Extract contact information (email, phone, linkedin, github, name) from text."""
    contact = ContactFacts()

    # 1. Email extraction
    email_match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b", text)
    if email_match:
        contact.email = email_match.group(0).lower()

    # 2. Phone extraction (international and local formats)
    phone_match = re.search(
        r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        text,
    )
    if phone_match:
        contact.phone = phone_match.group(0).strip()

    # 3. LinkedIn extraction
    linkedin_match = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/in/([A-Za-z0-9_-]+)", text, re.I)
    if linkedin_match:
        contact.linkedin = linkedin_match.group(0)

    # 4. GitHub extraction
    github_match = re.search(r"(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9_-]+)", text, re.I)
    if github_match:
        contact.github = github_match.group(0)

    # 5. Name extraction (from Header lines before any section)
    header_lines = sections.get("Header", [])
    for line in header_lines[:3]:
        cleaned = re.sub(r"[^A-Za-z\s]", "", line).strip()
        words = cleaned.split()
        if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
            contact.name = " ".join(words)
            break

    return contact


def extract_education(sections: Dict[str, List[str]]) -> List[EducationFact]:
    """Extract education items from the Education section."""
    edu_lines = sections.get("Education", [])
    if not edu_lines:
        return []

    edu_facts: List[EducationFact] = []
    current_text = " ".join(edu_lines)

    # Detect degree
    degree = None
    if re.search(r"\b(?:B\.Tech|B\.E\.|Bachelor of Technology|Bachelor of Engineering|B\.S\.|B\.Sc)\b", current_text, re.I):
        degree = "B.Tech"
    elif re.search(r"\b(?:M\.Tech|M\.E\.|Master of Technology|M\.S\.|M\.Sc)\b", current_text, re.I):
        degree = "M.Tech"
    elif re.search(r"\b(?:BCA|MCA|Ph\.D|Diploma)\b", current_text, re.I):
        degree = "BCA"

    # Detect branch
    branch = None
    if re.search(r"\b(?:Computer Science|CSE|Information Technology|IT|Software Engineering)\b", current_text, re.I):
        branch = "Computer Science"
    elif re.search(r"\b(?:Electrical|Electronics|ECE|Mechanical|Civil)\b", current_text, re.I):
        branch = "Electronics and Communication"

    # Detect graduation year (if year range like 2022-2026, pick end year; otherwise pick max year)
    all_years = [int(y) for y in re.findall(r"\b(20[0-3][0-9])\b", current_text)]
    grad_year = max(all_years) if all_years else None

    # Detect CGPA/GPA if explicitly stated
    cgpa = None
    cgpa_scale = None
    cgpa_match = re.search(r"\b(?:CGPA|GPA|Score)[\s:]*([0-9]+(?:\.[0-9]+)?)(?:\s*/\s*([0-9]+(?:\.[0-9]+)?))?\b", current_text, re.I)
    if cgpa_match:
        try:
            cgpa = float(cgpa_match.group(1))
            if cgpa_match.group(2):
                cgpa_scale = float(cgpa_match.group(2))
            else:
                cgpa_scale = 10.0 if cgpa <= 10.0 else 100.0
        except ValueError:
            pass

    # Detect institution from first prominent line in education
    institution = edu_lines[0] if edu_lines else None

    edu_facts.append(
        EducationFact(
            institution=institution,
            degree=degree,
            branch=branch,
            graduation_year=grad_year,
            cgpa=cgpa,
            cgpa_scale=cgpa_scale,
            source_snippet="\n".join(edu_lines[:4]),
        )
    )

    return edu_facts


def extract_skills(
    full_text: str,
    sections: Dict[str, List[str]],
    segments: List[PageSegment],
) -> List[SkillFact]:
    """Extract mentioned technical skills with deterministic dictionary matching."""
    extracted: List[SkillFact] = []
    seen_skills: Set[str] = set()
    lowered_full_text = full_text.lower()

    # Determine skills section text for contextual snippet
    skills_lines = sections.get("Skills", [])
    skills_section_text = " ".join(skills_lines)

    for norm_name, display_name in TECHNICAL_SKILLS.items():
        # Match as whole word / token
        pattern = r"(?<![a-zA-Z0-9_\-\.])" + re.escape(norm_name) + r"(?![a-zA-Z0-9_\-\.])"
        if re.search(pattern, lowered_full_text, re.I):
            if norm_name not in seen_skills:
                seen_skills.add(norm_name)

                # Determine section and page where skill was found
                found_section = "Skills" if re.search(pattern, skills_section_text.lower(), re.I) else "Body"
                page_num = 1
                for seg in segments:
                    if re.search(pattern, seg.text.lower(), re.I):
                        page_num = seg.page_number
                        break

                # Create concise snippet
                snippet = None
                match = re.search(r"([^.\n]*?" + re.escape(norm_name) + r"[^.\n]*)", full_text, re.I)
                if match:
                    snippet = match.group(1).strip()

                extracted.append(
                    SkillFact(
                        display_name=display_name,
                        normalized_name=norm_name,
                        source_snippet=snippet,
                        section=found_section,
                        page=page_num,
                    )
                )

    # Return in deterministic order (by normalized_name)
    return sorted(extracted, key=lambda s: s.normalized_name)


def extract_projects(sections: Dict[str, List[str]]) -> List[ProjectFact]:
    """Extract projects from Projects section."""
    proj_lines = sections.get("Projects", [])
    if not proj_lines:
        return []

    projects: List[ProjectFact] = []
    current_title: Optional[str] = None
    current_desc_lines: List[str] = []
    current_url: Optional[str] = None

    for line in proj_lines:
        cleaned = line.strip()
        if not cleaned:
            continue

        # Check if line contains a URL
        url_match = re.search(r"(https?://[^\s]+)", cleaned)
        if url_match:
            current_url = url_match.group(1)

        # Heuristic for project header (e.g. bold or bullet start or short line)
        if (len(cleaned) < 60 and not cleaned.startswith(("-", "•", "*", "–"))) or current_title is None:
            if current_title and current_desc_lines:
                projects.append(
                    ProjectFact(
                        title=current_title,
                        description=" ".join(current_desc_lines),
                        url=current_url,
                        source_snippet=f"{current_title}: {' '.join(current_desc_lines[:2])}",
                    )
                )
                current_desc_lines = []
                current_url = None
            current_title = cleaned.split("|")[0].strip()
        else:
            current_desc_lines.append(cleaned.lstrip("-•*– "))

    if current_title:
        projects.append(
            ProjectFact(
                title=current_title,
                description=" ".join(current_desc_lines) if current_desc_lines else current_title,
                url=current_url,
                source_snippet=f"{current_title}: {' '.join(current_desc_lines[:2])}",
            )
        )

    return projects


def extract_experience(sections: Dict[str, List[str]]) -> List[ExperienceFact]:
    """Extract experience records from Experience section."""
    exp_lines = sections.get("Experience", [])
    if not exp_lines:
        return []

    experiences: List[ExperienceFact] = []
    current_org: Optional[str] = None
    current_role: str = "Software Developer"
    current_dates: Optional[str] = None
    current_desc: List[str] = []

    for line in exp_lines:
        cleaned = line.strip()
        if not cleaned:
            continue

        date_match = re.search(
            r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d{4}|\d{4}\s*-\s*(?:\d{4}|Present))\b",
            cleaned,
            re.I,
        )

        is_bullet = cleaned.startswith(("-", "•", "*", "–"))

        if is_bullet:
            current_desc.append(cleaned.lstrip("-•*– "))
        elif "|" in cleaned:
            # New experience entry like "Company | Role" or "Company | Role | Dates"
            if current_org and (current_desc or current_dates):
                experiences.append(
                    ExperienceFact(
                        organization=current_org,
                        role=current_role,
                        dates=current_dates,
                        description=" ".join(current_desc) if current_desc else "Work experience",
                        source_snippet=f"{current_org} - {current_role}",
                    )
                )
                current_desc = []
                current_dates = None

            parts = [p.strip() for p in cleaned.split("|")]
            current_org = parts[0]
            current_role = parts[1] if len(parts) > 1 else "Software Developer"
            if len(parts) > 2 and date_match:
                current_dates = parts[2]
        elif date_match and len(cleaned) < 60:
            # Line is solely or primarily a date range like "May 2025 - July 2025"
            current_dates = cleaned
        else:
            if not current_org:
                current_org = cleaned
            else:
                current_desc.append(cleaned)

    if current_org:
        experiences.append(
            ExperienceFact(
                organization=current_org,
                role=current_role,
                dates=current_dates,
                description=" ".join(current_desc) if current_desc else "Work experience",
                source_snippet=f"{current_org} - {current_role}",
            )
        )

    return experiences


def analyze_quality_signals(
    full_text: str,
    sections: Dict[str, List[str]],
) -> List[QualitySignal]:
    """Analyze observable quality signals (action verbs, quantified outcomes, weak language, missing sections)."""
    signals: List[QualitySignal] = []

    # 1. Missing essential sections
    detected_section_keys = set(sections.keys()) - {"Header"}
    essential_sections = ["Education", "Skills", "Projects", "Experience"]
    for essential in essential_sections:
        if essential not in detected_section_keys or not sections[essential]:
            signals.append(
                QualitySignal(
                    signal="missing_section",
                    category="completeness",
                    observed_text=f"Section '{essential}' was not detected",
                    rule_or_reason=f"Recommended section '{essential}' is absent or not labeled clearly",
                )
            )

    # 2. Action verbs and Quantified outcomes analysis on bullet points
    lines = [line.strip() for line in full_text.splitlines() if line.strip()]
    for line in lines:
        cleaned = line.lstrip("-•*–0123456789.) \t")
        if not cleaned:
            continue
        first_word = cleaned.split()[0].lower() if cleaned.split() else ""

        # Check action verbs
        if first_word in ACTION_VERBS:
            signals.append(
                QualitySignal(
                    signal="action_verb",
                    category="language",
                    observed_text=line[:100],
                    rule_or_reason=f"Bullet begins with strong action verb '{first_word.capitalize()}'",
                )
            )

        # Check quantified outcomes (percentages, metrics, multipliers, numbers with +, $)
        quant_match = re.search(r"(\b\d+(?:\.\d+)?%|\b\d+\s*(?:ms|sec|x|users|clients|requests|\+)\b|\$\d+)", line, re.I)
        if quant_match:
            signals.append(
                QualitySignal(
                    signal="quantified_outcome",
                    category="impact",
                    observed_text=line[:100],
                    rule_or_reason=f"Contains measurable metric or quantified impact '{quant_match.group(0)}'",
                )
            )

        # Check weak phrasing
        for weak_term, reason in WEAK_PHRASES:
            if weak_term in line.lower():
                signals.append(
                    QualitySignal(
                        signal="weak_language",
                        category="language",
                        observed_text=line[:100],
                        rule_or_reason=f"Contains passive or vague phrasing '{weak_term}': {reason}",
                    )
                )

    return signals


def parse_resume_bytes(content: bytes, filename: str = "") -> ResumeParseResponse:
    """End-to-end resume parser pipeline.
    Validates, extracts, normalizes, detects sections, extracts facts, and computes quality signals.
    Does not persist or overwrite database profiles.
    """
    # 1. Validation and format detection
    fmt = validate_and_detect_format(content, filename=filename)

    # 2. Text Extraction
    if fmt == "pdf":
        extracted_doc = extract_pdf(content)
    elif fmt == "docx":
        extracted_doc = extract_docx(content)
    elif fmt == "txt":
        extracted_doc = extract_txt(content)
    else:
        raise ParserException(f"Unsupported format '{fmt}'", code="unsupported_type", status_code=422)

    # 3. Normalization
    normalized_full_text = normalize_text(extracted_doc.raw_text)

    # 4. Section Detection
    sections = detect_sections(normalized_full_text)
    detected_section_names = [s for s in sections.keys() if s != "Header" and sections[s]]

    # 5. Field / Evidence Extraction
    contact = extract_contact_info(normalized_full_text, sections)
    education = extract_education(sections)
    skills = extract_skills(normalized_full_text, sections, extracted_doc.segments)
    projects = extract_projects(sections)
    experience = extract_experience(sections)

    candidate_facts = CandidateFacts(
        contact=contact,
        education=education,
        skills=skills,
        projects=projects,
        experience=experience,
    )

    # 6. Quality Signals
    quality_signals = analyze_quality_signals(normalized_full_text, sections)

    # 7. Warnings compilation
    warnings = list(extracted_doc.warnings)
    if not skills:
        warnings.append("No technical skills were identified from the standard vocabulary")
    if not education:
        warnings.append("No explicit education degrees were identified")

    return ResumeParseResponse(
        candidate_facts=candidate_facts,
        sections_detected=detected_section_names,
        quality_signals=quality_signals,
        warnings=warnings,
    )
