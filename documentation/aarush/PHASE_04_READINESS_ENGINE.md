# Aarush — Phase 04: Explainable Readiness Engine

**Owner:** Aarush
**Can start:** Immediately, with hand-authored fixture inputs
**Deployable result:** Deterministic CLI/API demo with tests

## Outcome

A pure, repeatable `cp-v1` readiness calculation that explains every output and does not make hiring predictions.

## Build

- Implement `cp-v1` factor weights exactly as in [`../shared/SRD.md`](../shared/SRD.md): role skill coverage 30%, demonstrated project/work evidence 25%, resume clarity/completeness 20%, technical skill evidence 15%, profile completeness 10%.
- Each factor returns score, weight, availability, evidence references, and an explanation. If unavailable, exclude and renormalize over available factor weights; list excluded factors and reduce confidence.
- Keep hard eligibility separate from readiness arithmetic. CGPA affects eligibility only when explicit criteria are provided.
- Define confidence from evidence source quality; missing data yields unknown/unavailable, not a fabricated zero or confirmed inability.
- Version rule tables, aliases, and output with `cp-v1`; put the deterministic domain logic in pure functions without web/database dependencies.
- Return up to three recommendations tied to concrete gaps and completion evidence. Do not predict guaranteed score lift or job chances.

## Acceptance

- Same normalized inputs always produce byte-equivalent meaningful results, apart from generated IDs/timestamps.
- Tests cover each factor, renormalization, rounding, no assessable factors, empty profile, conflicting evidence, and score bounds.
- Explanation values sum consistently with the returned total within the documented rounding rule.
- Readiness may be high or low independently of eligibility; a failed eligibility rule is visible separately.
- Demo runs with fixture JSON and no database or paid service.

## Independence contract

Use normalized in-memory profile/evidence/opportunity objects. This workstream does not wait for parser output or persisted data; fixtures can represent confirmed data from any source.
