"""CLI utility to evaluate opportunity and role matching (rm-v1).

Usage:
    python -m app.cli.evaluate_match [--fixtures-path PATH]
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict

from app.services.matching_engine import MatchingEngine, RequirementExtractor


def evaluate_match_cli(fixtures_path: Path) -> int:
    """Run deterministic role matching across synthetic fixtures and print explainable reports."""
    if not fixtures_path.exists():
        print(f"Error: Fixtures file not found at {fixtures_path}", file=sys.stderr)
        return 1

    with open(fixtures_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    opportunities = data.get("opportunities", {})
    profiles = data.get("candidate_profiles", {})

    print("=" * 80)
    print("PLACEMENTOS — PHASE 05 ROLE MATCHING ENGINE (rm-v1) CLI EVALUATION")
    print("=" * 80)

    # 1. Test Software Engineer with strong candidate
    swe_opp = opportunities.get("software_engineer", {})
    swe_cand = profiles.get("strong_swe_candidate", {})
    print("\n--- SCENARIO 1: Software Engineer vs Strong Candidate ---")
    report1 = MatchingEngine.evaluate(swe_cand, swe_opp)
    _print_report_summary(report1, swe_cand, swe_opp)

    # 2. Test AI/ML Intern with partial candidate (missing statistics, CGPA 7.8 < min 8.0)
    aiml_opp = opportunities.get("ai_ml_intern", {})
    aiml_cand = profiles.get("partial_aiml_candidate", {})
    print("\n--- SCENARIO 2: AI/ML Intern vs Partial Candidate (Hard Fail on CGPA) ---")
    report2 = MatchingEngine.evaluate(aiml_cand, aiml_opp)
    _print_report_summary(report2, aiml_cand, aiml_opp)

    # 3. Test Software Engineer with Unrelated Branch (Civil Eng vs CSE/IT)
    branch_cand = profiles.get("unrelated_branch_candidate", {})
    print("\n--- SCENARIO 3: Software Engineer vs Unrelated Branch (Branch Ineligible) ---")
    report3 = MatchingEngine.evaluate(branch_cand, swe_opp)
    _print_report_summary(report3, branch_cand, swe_opp)

    # 4. Test Data Analyst with No CGPA (Unknown CGPA status)
    da_opp = opportunities.get("data_analyst", {})
    no_cgpa_cand = profiles.get("no_cgpa_candidate", {})
    print("\n--- SCENARIO 4: Data Analyst vs Missing CGPA (Unknown Status) ---")
    report4 = MatchingEngine.evaluate(no_cgpa_cand, da_opp)
    _print_report_summary(report4, no_cgpa_cand, da_opp)

    # 5. Test Opportunity with No Usable Requirements
    empty_opp = opportunities.get("unspecified_requirements", {})
    print("\n--- SCENARIO 5: Opportunity with No Usable Skill Requirements ---")
    report5 = MatchingEngine.evaluate(swe_cand, empty_opp)
    _print_report_summary(report5, swe_cand, empty_opp)

    print("\n" + "=" * 80)
    print("ALL EVALUATION SCENARIOS COMPLETED DETERMINISTICALLY.")
    print("=" * 80)
    return 0


def _print_report_summary(report: Any, profile: Dict[str, Any], opp: Dict[str, Any]) -> None:
    print(f"Candidate: {profile.get('full_name')} ({profile.get('branch')}, CGPA: {profile.get('cgpa')})")
    print(f"Opportunity: {opp.get('role_title')} at {opp.get('company')}")
    print(f"Matching Version: {report.matching_version}")
    print(f"Eligibility Status: {report.eligibility.status.upper()}")
    for reason in report.eligibility.reasons:
        print(f"  - [{reason.code}] {reason.message}")
    print(f"Role Match Score: {report.role_match.score if report.role_match.score is not None else 'null'} ({report.role_match.explanation})")
    if report.role_match.reason_code:
        print(f"  Reason Code: {report.role_match.reason_code}")
    print(f"  Matched Required: {report.role_match.matched_required}")
    print(f"  Missing Required: {report.role_match.missing_required}")
    print(f"  Matched Preferred: {report.role_match.matched_preferred}")
    print(f"  Missing Preferred: {report.role_match.missing_preferred}")
    print("Requirements Breakdown:")
    for req in report.requirements:
        status_symbol = "MATCH" if req.status == "matched" else ("MISS" if req.status == "missing" else "UNKNOWN")
        print(f"  [{status_symbol}] {req.original_phrase} ({req.category.upper()} -> {req.normalized_skill}): {req.status} - {req.explanation}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate role matching against opportunities")
    default_fixtures = Path(__file__).resolve().parent.parent.parent / "fixtures" / "role_matching_fixtures.json"
    parser.add_argument("--fixtures-path", type=Path, default=default_fixtures, help="Path to fixtures JSON file")
    args = parser.parse_args()
    sys.exit(evaluate_match_cli(args.fixtures_path))
