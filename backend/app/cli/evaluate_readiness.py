"""CLI tool for evaluating deterministic student readiness (cp-v1)."""

import argparse
import json
import sys
from pathlib import Path

from app.services.readiness_engine import (
    OpportunityRequirement,
    ProjectEvidence,
    ReadinessEngine,
    ResumeEvidence,
    SkillEvidence,
    StudentProfileEvidence,
)
from app.services.resume_parser import parse_resume_bytes


def main():
    parser = argparse.ArgumentParser(description="Evaluate student readiness deterministically (cp-v1)")
    parser.add_argument("--profile", required=False, help="Path to profile JSON file")
    parser.add_argument("--opportunity", required=False, help="Path to opportunity requirement JSON file")
    parser.add_argument("--resume", required=False, help="Path to resume file (PDF, DOCX, or TXT)")
    args = parser.parse_args()

    # Load profile data
    profile_data = {}
    if args.profile:
        profile_path = Path(args.profile)
        if not profile_path.exists():
            print(f"Error: Profile file '{args.profile}' not found", file=sys.stderr)
            sys.exit(1)
        with open(profile_path, "r", encoding="utf-8") as f:
            raw_json = json.load(f)
            if isinstance(raw_json, list):
                profile_data = raw_json[0] if raw_json else {}
            elif isinstance(raw_json, dict):
                profile_data = raw_json.get("profile", raw_json)

    # Load opportunity data
    opportunity_data = {}
    if args.opportunity:
        opp_path = Path(args.opportunity)
        if not opp_path.exists():
            print(f"Error: Opportunity file '{args.opportunity}' not found", file=sys.stderr)
            sys.exit(1)
        with open(opp_path, "r", encoding="utf-8") as f:
            opportunity_data = json.load(f)

    # Load and parse resume if provided
    resume_evidence = None
    if args.resume:
        res_path = Path(args.resume)
        if not res_path.exists():
            print(f"Error: Resume file '{args.resume}' not found", file=sys.stderr)
            sys.exit(1)
        data = res_path.read_bytes()
        parsed = parse_resume_bytes(data, filename=res_path.name)
        facts = parsed.candidate_facts
        has_contact = bool(facts.contact.email or facts.contact.phone or facts.contact.name)
        has_education = len(facts.education) > 0
        has_skills = len(facts.skills) > 0
        has_experience = len(facts.experience) > 0 or len(facts.projects) > 0

        action_verbs_count = sum(1 for q in parsed.quality_signals if q.signal == "action_verb")
        quantified_count = sum(1 for q in parsed.quality_signals if q.signal == "quantified_outcome")
        weak_count = sum(1 for q in parsed.quality_signals if q.signal == "weak_language")

        resume_evidence = ResumeEvidence(
            sections_present=parsed.sections_detected,
            contact_present=has_contact,
            education_present=has_education,
            skills_present=has_skills,
            experience_present=has_experience,
            extracted_skills=[s.display_name for s in facts.skills],
            action_verbs_count=action_verbs_count,
            quantified_outcomes_count=quantified_count,
            weak_language_count=weak_count,
            raw_text=data.decode("utf-8", errors="ignore"),
        )

    # Build domain objects
    skills_evidence = [
        SkillEvidence(
            name=s.get("display_name", s.get("name", "")),
            normalized_name=s.get("normalized_name", ""),
            source=s.get("source", "self_reported"),
            self_reported_level=s.get("self_reported_level"),
        )
        for s in profile_data.get("skills", [])
    ]

    projects_evidence = [
        ProjectEvidence(
            title=p.get("title", ""),
            description=p.get("description", ""),
            url=p.get("url"),
            start_date=p.get("start_date"),
            end_date=p.get("end_date"),
        )
        for p in profile_data.get("projects", [])
    ]

    profile_evidence = StudentProfileEvidence(
        full_name=profile_data.get("full_name"),
        branch=profile_data.get("branch"),
        graduation_year=profile_data.get("graduation_year"),
        cgpa=profile_data.get("cgpa"),
        cgpa_scale=profile_data.get("cgpa_scale"),
        target_role=profile_data.get("target_role"),
        skills=skills_evidence,
        projects=projects_evidence,
        resume=resume_evidence,
    )

    opp_req = None
    if opportunity_data:
        opp_req = OpportunityRequirement(
            role_title=opportunity_data.get("role_title"),
            company=opportunity_data.get("company"),
            jd_text=opportunity_data.get("jd_text"),
            required_skills=opportunity_data.get("required_skills", []),
            preferred_skills=opportunity_data.get("preferred_skills", []),
            explicit_criteria=opportunity_data.get("explicit_criteria", {}),
        )

    # Evaluate
    report = ReadinessEngine.evaluate(profile_evidence, opp_req)

    # Format output dictionary
    out = {
        "scoring_version": report.scoring_version,
        "created_at": report.created_at,
        "eligibility": {
            "status": report.eligibility.status,
            "reasons": [{"code": r.code, "message": r.message} for r in report.eligibility.reasons],
        },
        "readiness": {
            "score": report.readiness.score,
            "confidence": report.readiness.confidence,
            "factors": [
                {
                    "key": f.key,
                    "name": f.name,
                    "score": f.score,
                    "weight": f.weight,
                    "available": f.available,
                    "evidence": f.evidence,
                    "explanation": f.explanation,
                }
                for f in report.readiness.factors
            ],
            "excluded_factors": report.readiness.excluded_factors,
        },
        "role_match": {
            "score": report.role_match.score,
            "matched": report.role_match.matched,
            "missing": report.role_match.missing,
            "unknown": report.role_match.unknown,
        } if report.role_match else None,
        "strengths": [{"label": s.label, "evidence": s.evidence, "confidence": s.confidence} for s in report.strengths],
        "gaps": [{"label": g.label, "importance": g.importance, "reason": g.reason} for g in report.gaps],
        "next_actions": [
            {"title": a.title, "rationale": a.rationale, "completion_evidence": a.completion_evidence}
            for a in report.next_actions
        ],
    }

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
