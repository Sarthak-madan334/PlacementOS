# Phase 07: System, Security, and Data Design Validation

**Owner:** Sejal
**Status:** Completed

## 1. Deployment Decision Record

- **Database:** Supabase PostgreSQL
- **Authentication:** Supabase Auth
- **Storage:** Private Supabase Storage
- **Frontend App:** Next.js deployed on Vercel
- **Backend API:** FastAPI deployed on Render

**Rationale:** This stack fits the MVP requirements for independent development and deployment, avoiding paid API/AI dependencies in the critical path while enabling robust authentication and storage.

## 2. Schema and Data Model Review

The schema described in `ARCHITECTURE.md` has been reviewed against the required MVP journeys:

- **Owner Relationships:** All user-data tables (`student_profiles`, `skills`, `projects`, `opportunities`, `assessments`, `profile_files`) correctly implement a foreign key linking to a user identifier (`user_id`). 
- **Deletion Rules:** The schema implicitly supports explicit cascade/cleanup behavior for account deletion. Deleting a user must cascade to profiles, assessments, opportunities, and storage object metadata.
- **Indexes:** Owner-based indexing must be implemented on the `user_id` foreign keys to ensure performance when filtering by owner.
- **Migration Compatibility:** SQLAlchemy 2.x + Alembic will be used to manage migrations. 

## 3. Security and Privacy Review

- **Auth Validation:** Supabase Auth tokens (JWTs) must be validated by the FastAPI backend for signature, issuer, audience, and expiry before serving or accepting any persisted data.
- **Owner-Scoped Access:** The `users.id` obtained from the validated token must be injected into every database read/write operation as an owner predicate. The client-provided `user_id` is untrusted.
- **Upload Boundaries:** Resume uploads must be limited to PDF, DOCX, and TXT with a maximum size of 5 MiB. Uploads must go to a private storage bucket with short-lived access URLs.
- **CORS:** FastAPI must configure CORS to strictly allow the Vercel frontend domains (preview and production).
- **Secret Handling:** Secrets (database connection strings, service role keys) must only be stored as environment variables on Render. Vercel only receives the public Supabase URL and anon key.
- **Log Redaction:** Sensitive PII (names, emails, resume contents) must not be logged in production.
- **Account Deletion:** An explicit mechanism must exist to hard-delete account data and explicitly delete objects from Supabase Storage.

## 4. Scoring and Eligibility Review

- **No Hidden Eligibility Coupling:** The schema and SRD correctly separate hard eligibility checks (`eligible`, `not_eligible`, `unknown`) from the readiness score arithmetic.
- **Evidence Handling:** Self-reported claims and parsed facts are tracked with confidence levels. Lack of evidence defaults to lower confidence or missing skills, avoiding any "invented evidence" scenarios.
- **Impact Claims:** The `cp-v1` ruleset avoids unjustified numerical outcome guarantees (e.g., probability of getting hired). The recommendations tie back to explicit evidence gaps.

## 5. Risk Register

| Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|
| **Privacy Leak** | Low | High | Restrict storage to private buckets; validate owner on all API reads. | Backend (Aarush) |
| **Cross-Account Access** | Low | High | Never trust client `user_id`. Always derive owner ID from verified JWT. | Backend (Aarush) |
| **Corrupt / Malicious Upload** | Medium | Medium | 5 MiB size limit, strict MIME/extension validation, untrusted parsing boundary. | Backend (Aarush) |
| **Destructive Migration** | Low | High | Use Alembic. Review migrations in PRs. Separate preview/production databases. | System (Sejal) |
| **Stale Results** | Medium | Low | Assessments persist a snapshot of inputs. Changes to profile explicitly prompt for reassessment. | Frontend (Sarthak) |

## 6. Preview Environments

- **Requirement Confirmed:** Vercel (frontend) and Render (backend) preview environments are configured to use separate credentials and isolated databases/storage. 
- **Synthetic Data:** The Next.js frontend has a `NEXT_PUBLIC_DEMO_MODE` to run a full demonstration using synthetic fixtures when the backend is offline or unlinked. No production user data is ever exposed in preview environments.
