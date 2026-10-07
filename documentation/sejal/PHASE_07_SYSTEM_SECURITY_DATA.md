# Sejal — Phase 07: System, Security, and Data Design Validation

**Owner:** Sejal
**Can start:** Immediately from Phase Zero documents
**Deployable result:** Versioned design and review artifact

## Outcome

Validate that the architecture, data model, privacy safeguards, contracts, and deployment choices are internally consistent and practical for the MVP.

## Work

- Review the schema against profile, resume evidence, opportunity, and assessment journeys; verify owner relationships, deletion rules, indexes, and migration compatibility.
- Record the deployment decision: Supabase PostgreSQL + Supabase Auth + private Supabase Storage, with Next.js on Vercel and FastAPI on Render.
- Review auth issuer/audience validation, owner-scoped access, upload boundaries, CORS, secret handling, log redaction, and account deletion.
- Review score factors and ensure no hidden eligibility coupling, invented evidence, or unjustified numerical impact claims.
- Maintain a compact risk list with likelihood, impact, mitigation, and owner. Prioritize privacy leak, cross-account access, corrupt upload, and destructive migration risks.
- Verify that preview environments use synthetic data and separate credentials from production.

## Acceptance

- Architecture and SRD conflicts are identified and resolved in the documents before implementation depends on them.
- A reviewer can trace every persisted field to a product feature and owner.
- All personal-data paths have an owner check and a deletion behavior.
- Provider choice, auth setup, migration owner, retention/deletion plan, and production launch gate are recorded.
- Deliverable is a reviewable Markdown checklist/decision record; no application code is required for this phase to finish.

## Independence contract

This phase needs only the agreed product and interface documents. It can complete without frontend or backend implementation.
