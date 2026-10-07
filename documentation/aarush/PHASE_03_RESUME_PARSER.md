# Aarush — Phase 03: Resume Parsing and Review Contract

**Owner:** Aarush
**Can start:** Immediately, with synthetic sample resumes
**Deployable result:** Stand-alone parser demo/API on Render

## Outcome

A deterministic ResumeSignal-style parser that extracts candidate information for student review. Parsing is assistive; it does not silently certify skills or overwrite profile data.

## Build

- Support PDF, DOCX, and TXT; cap at 5 MiB. Markdown can be accepted in local/demo mode only.
- Separate file validation, format-specific text extraction, normalization, and field/section detection.
- Return candidate contact/education/experience/project/skill facts, section-presence indicators, source snippets or page/section references where feasible, and warnings.
- Detect basic resume quality signals such as missing sections, weak/vague phrasing patterns, action verbs, and quantified outcomes. Each signal must state the observed text or rule.
- Return stable parse error codes for unsupported type, too large, empty, corrupt, and extraction failure.
- Do not use LLMs or paid APIs in the core parser. Do not invent facts or rewrite text in this phase.

## Acceptance

- Unit fixtures cover each supported format, empty/corrupt files, unusual whitespace, and oversized uploads.
- Parser result has the same normalized shape across formats and includes warnings rather than crashing on partial extraction.
- Resume text is treated as untrusted input and is not logged or persisted by the stand-alone demo.
- Extraction does not mark self-reported or parsed skills as externally verified.
- Deploy a demo endpoint or command that accepts sample files without database setup.

## Independence contract

The parser accepts a file and returns candidate facts; it does not require profile CRUD, auth persistence, scoring, or UI. Frontend can render a fixture with the same response contract.

## Implementation Status

- **Status**: COMPLETE
- **Modules Created**:
  - `backend/app/adapters/parser/validator.py`: Format detection (PDF, DOCX, TXT magic bytes), 5 MiB size enforcement, empty and corrupt file handling.
  - `backend/app/adapters/parser/pdf_adapter.py`: PDF text extraction with page tracking via `pypdf`.
  - `backend/app/adapters/parser/docx_adapter.py`: DOCX text and table extraction via `python-docx`.
  - `backend/app/adapters/parser/txt_adapter.py`: Multi-encoding text extraction (UTF-8, Latin-1, CP1252).
  - `backend/app/services/resume_parser.py`: Deterministic pipeline for normalization, section detection, facts extraction (contact, education, skills, projects, experience), and quality signals (`action_verb`, `quantified_outcome`, `weak_language`, `missing_section`).
  - `backend/app/api/v1/schemas/resume.py`: Pydantic response contracts (`ResumeParseResponse`, `CandidateFacts`, `QualitySignal`).
  - `backend/app/api/v1/endpoints/resume.py`: `POST /api/v1/resumes/parse` endpoint.
  - `backend/app/cli/parse_resume.py`: Standalone CLI parsing tool.
  - `backend/fixtures/resumes/`: Synthetic fixtures (`sample_resume.txt`, `minimal_resume.txt`, `weak_language_resume.txt`).
  - `backend/tests/test_resume_parser.py`: Comprehensive test suite verifying formats, validation, errors, quality signals, determinism, and endpoint integration.
