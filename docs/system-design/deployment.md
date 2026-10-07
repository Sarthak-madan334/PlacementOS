# PlacementOS — Deployment & Integration Specification

**Owner:** Sejal Kumari (System Design)  
**Classification:** Canonical Deployment, Infrastructure, and Integration Architecture  
**Status:** DEPLOYMENT & INTEGRATION READY  

---

## 1. Deployment Architecture

### 1.1 Production & Preview System Topology

PlacementOS deploys across three managed cloud tiers: **Vercel** (Next.js frontend), **Render** (FastAPI backend), and **Supabase** (PostgreSQL, GoTrue Auth, and private S3-compatible Object Storage).

```mermaid
flowchart TD
  subgraph ClientTier ["Client Tier"]
    User["Student User<br/>(Desktop / Mobile >= 360px)"]
    GuestUser["Guest Visitor<br/>(Synthetic Demo Mode)"]
  end

  subgraph VercelApp ["Frontend Hosting (Vercel)"]
    NextProd["Next.js 14+ (App Router)<br/>Production Origin: https://placementos.vercel.app"]
    NextPrev["Next.js 14+ (App Router)<br/>Preview Origin: https://*-team.vercel.app"]
    SupaAuthSDK["Supabase Auth JS SDK<br/>(Anon Key Only)"]
  end

  subgraph RenderApp ["Backend Hosting (Render)"]
    FastAPIProd["FastAPI 0.110+ (Python 3.11)<br/>Production: https://api.placementos.render.com"]
    FastAPIPrev["FastAPI 0.110+ (Python 3.11)<br/>Preview: https://api-preview.placementos.render.com"]
    JWTMiddleware["JWT Auth Guard<br/>(Issuer/Audience/Expiry)"]
    ParserService["In-Memory Parser<br/>(pypdf / python-docx / txt)"]
    ScoringCore["Deterministic cp-v1 Engine<br/>(Pure Functions)"]
  end

  subgraph SupabaseTier ["Data & Security Tier (Supabase)"]
    SupaAuth["Supabase Auth Service<br/>(GoTrue / JWKS Endpoint)"]
    PostgreSQL[(Supabase PostgreSQL 15+<br/>RLS Enabled + Alembic Migrations)]
    StorageBucket[("Private Storage Bucket<br/>'resumes' (5 MiB limit)")]
  end

  %% Real User Traffic
  User -->|HTTPS| NextProd
  GuestUser -.->|No Persistence Calls| NextProd
  NextProd -->|Auth Callback / PKCE| SupaAuthSDK
  SupaAuthSDK <-->|Token Exchange| SupaAuth
  NextProd -->|HTTPS REST JSON + Bearer JWT| FastAPIProd
  
  FastAPIProd --> JWTMiddleware
  JWTMiddleware -.->|Public Key Verification| SupaAuth
  FastAPIProd --> ParserService
  FastAPIProd --> ScoringCore
  FastAPIProd -->|TLS PostgreSQL / Port 5432| PostgreSQL
  FastAPIProd -->|Service Role / Private S3 API| StorageBucket

  %% Preview Traffic
  NextPrev -->|HTTPS REST JSON| FastAPIPrev
  FastAPIPrev -->|Isolated Project| PostgreSQL
```

### 1.2 Service Boundaries & Hosting Targets

| Service Component | Runtime / Stack | Hosting Provider | Deployment Mode | Responsibility |
|---|---|---|---|---|
| **Frontend Web App** | Next.js 14+, TypeScript | **Vercel** | Edge / Serverless Node.js | UI forms, Glassmorphism dashboard, client session state, static demo fixtures |
| **API Backend** | FastAPI, Python 3.11+, Uvicorn | **Render** | Persistent Web Service | Validation, JWT parsing, in-memory resume extraction, `cp-v1` scoring, owner SQL queries |
| **Relational Database** | PostgreSQL 15+ | **Supabase** | Managed Cloud DB | Durable storage for users, profiles, skills, projects, opportunities, and assessments |
| **Identity Provider** | Supabase Auth (GoTrue) | **Supabase** | Managed Auth Service | User signup, PKCE OAuth, email authentication, RS256/HS256 JWT generation |
| **Object Storage** | Private S3 Bucket (`resumes`) | **Supabase Storage** | Managed Object Storage | Encrypted, private storage of raw resume files; access strictly via short-lived signed URLs |

### 1.3 Database Connection Topology

* **Direct vs Session Pooler:** Render web services MUST connect to Supabase PostgreSQL using the **Session Pooler (`port 5432` with SSL enabled)** if operating over IPv4, or direct connection (`port 5432`) if IPv6 is routable.
* **Prohibited Mode:** **Transaction Pooling (`port 6543`) is strictly prohibited** for SQLAlchemy ORM unless prepared statements and session-level schema features are explicitly disabled.

---

## 2. Environment Variables & Secret Segregation

### 2.1 Frontend Environment Variables (Vercel)

| Variable Name | Environment | Allowed in Browser? | Example Value | Description |
|---|---|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Preview | YES | `https://api-preview.placementos.render.com` | Target Render preview API URL |
| `NEXT_PUBLIC_API_BASE_URL` | Production | YES | `https://api.placementos.render.com` | Target Render production API URL |
| `NEXT_PUBLIC_SUPABASE_URL` | Preview / Prod | YES | `https://<project-ref>.supabase.co` | Supabase project API gateway |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Preview / Prod | YES | `eyJhbGciOiJIUzI1NiIsInR5cCI6...` | Public browser-safe Supabase anon key |
| `NEXT_PUBLIC_DEMO_MODE` | Preview | YES | `false` (or `true` for standalone demo) | Toggles synthetic fixture fallback |
| `NEXT_PUBLIC_DEMO_MODE` | Production | YES | `false` | Disabled in production |
| `NEXT_PUBLIC_SITE_URL` | Production | YES | `https://placementos.vercel.app` | Canonical site origin for auth callbacks |

> **Critical Rule:** Never inject `DATABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, or any backend secrets into Vercel environment variables or `NEXT_PUBLIC_*` prefixes.

### 2.2 Backend Environment Variables (Render)

| Variable Name | Environment | Visibility | Example Value | Description |
|---|---|---|---|---|
| `APP_ENV` | Preview / Prod | Server-only | `preview` or `production` | Application execution environment |
| `DATABASE_URL` | Preview | Server Secret | `postgresql://postgres:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres?sslmode=require` | Preview Supabase PostgreSQL connection |
| `DATABASE_URL` | Production | Server Secret | `postgresql://postgres:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres?sslmode=require` | Production Supabase PostgreSQL connection |
| `CORS_ORIGINS` | Preview | Server-only | `https://*-<team-slug>.vercel.app,http://localhost:3000` | Allowed Vercel preview wildcards |
| `CORS_ORIGINS` | Production | Server-only | `https://placementos.vercel.app` | Exact production frontend domain |
| `AUTH_ISSUER_URL` | Preview / Prod | Server-only | `https://<project-ref>.supabase.co/auth/v1` | Validated Supabase JWT issuer |
| `AUTH_AUDIENCE` | Preview / Prod | Server-only | `authenticated` | Validated Supabase JWT audience |
| `SUPABASE_JWT_SECRET` | Preview / Prod | Server Secret | `[SUPABASE_JWT_SECRET_STRING]` | Shared secret for HS256 JWT signature verification |
| `SUPABASE_URL` | Preview / Prod | Server-only | `https://<project-ref>.supabase.co` | Supabase management API URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Preview / Prod | Server Secret | `eyJhbGciOiJIUzI1NiIsInR5cCI6...` | Supabase service-role key for backend storage ops |
| `SUPABASE_STORAGE_BUCKET`| Preview / Prod | Server-only | `resumes` | Name of private storage bucket |
| `MAX_RESUME_BYTES` | Preview / Prod | Server-only | `5242880` | Upload ceiling (5 MiB in bytes) |

---

## 3. End-to-End Integration Flows

### 3.1 Authentication & Data Persistence Flow (`Frontend -> Auth -> API -> Database`)

```mermaid
sequenceDiagram
  autonumber
  actor Student as Student Browser
  participant Frontend as Next.js (Vercel)
  participant Auth as Supabase Auth
  participant API as FastAPI (Render)
  participant DB as Supabase PostgreSQL

  Student->>Frontend: Enter credentials / Click Magic Link
  Frontend->>Auth: supabase.auth.signInWithPassword() / OAuth
  Auth-->>Frontend: Returns Session { access_token (JWT), user }
  
  Student->>Frontend: Submit Profile Data (J1)
  Frontend->>API: PUT /api/v1/me/profile<br/>Header: Authorization: Bearer <JWT>
  
  Note over API: 1. Validate JWT signature, issuer, exp, aud<br/>2. Extract 'sub' claim (Supabase Auth UID)
  
  API->>DB: SELECT id FROM users WHERE auth_subject = :sub
  alt User not in DB (First Request)
    API->>DB: INSERT INTO users (auth_subject, email) VALUES (:sub, :email) RETURNING id
  end
  DB-->>API: Returns internal user.id (UUID)
  
  Note over API: Enforce owner constraint: WHERE user_id = :user.id
  
  API->>DB: UPSERT INTO student_profiles (user_id, full_name, branch, ...) VALUES (:user_id, ...)
  DB-->>API: 200 OK Record persisted
  API-->>Frontend: 200 OK { profile DTO }
  Frontend-->>Student: Display Profile Saved Confirmation
```

### 3.2 Resume Upload & In-Memory Analysis Flow (`Frontend -> Upload -> Private Storage -> Resume Analyzer`)

```mermaid
sequenceDiagram
  autonumber
  actor Student as Student Browser
  participant Frontend as Next.js (Vercel)
  participant API as FastAPI (Render)
  participant Parser as In-Memory ResumeSignal Parser
  participant Storage as Supabase Private Storage
  participant DB as Supabase PostgreSQL

  Student->>Frontend: Select Resume (.pdf, .docx, .txt <= 5 MiB)
  Frontend->>Frontend: Client-side validation (Size <= 5 MiB, file type)
  Frontend->>API: POST /api/v1/resumes/parse (multipart/form-data + Bearer JWT)
  
  Note over API: 1. Validate JWT & Resolve user.id<br/>2. Check byte length <= 5242880<br/>3. Verify Magic Bytes (%PDF-, PK\x03\x04, UTF-8 text)
  
  API->>Parser: Stream file buffer to in-memory extractor
  Parser-->>API: Returns candidate facts (skills, projects, education) + warnings
  
  Note over API: No raw text saved to DB!
  
  API->>Storage: Upload object to bucket 'resumes' as {user_id}/{uuid}.{ext}
  Storage-->>API: 200 OK Uploaded
  
  API->>DB: INSERT INTO profile_files (user_id, storage_key, mime_type, byte_size)
  DB-->>API: 201 Created
  
  API-->>Frontend: 200 OK { candidate_facts: {...}, warnings: [], file_id: "uuid" }
  Frontend-->>Student: Display Review & Edit Screen (Student confirms facts before assessment)
```

---

## 4. Security Configuration & Defense-in-Depth

### 4.1 Multi-Layered Access Control Model

| Layer | Enforcement Point | Mechanism | Failure Action |
|---|---|---|---|
| **L1: Edge Network** | Render / Vercel | HTTPS TLS 1.3, Strict CORS origin allowlist | `403 Forbidden` / Connection reset |
| **L2: Authentication** | FastAPI Middleware | Supabase JWT verification (`iss`, `aud`, `exp`, RS256/HS256) | `401 Unauthorized` (`token_expired` or `invalid_token`) |
| **L3: Service Authorization** | FastAPI Repositories | Server-side owner filter: `WHERE user_id = :authenticated_user_id` | `404 Not Found` (never leaks foreign existence) |
| **L4: Database Defense** | PostgreSQL Engine | Row Level Security (RLS) policies checking `auth.uid()` | Zero rows returned / Permission denied |
| **L5: Object Storage** | Supabase Storage API | Private bucket with signed URL access (TTL: 60–300s) | `403 Access Denied` on unauthenticated direct GET |

### 4.2 Row Level Security (RLS) Canonical Script

```sql
-- Enforce RLS across all application tables in Supabase PostgreSQL
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE profile_files ENABLE ROW LEVEL SECURITY;

-- Owner policies matching auth.uid()
CREATE POLICY users_owner_policy ON users
  FOR ALL USING (auth_subject = auth.uid()::text);

CREATE POLICY profiles_owner_policy ON student_profiles
  FOR ALL USING (user_id IN (SELECT id FROM users WHERE auth_subject = auth.uid()::text));

CREATE POLICY skills_owner_policy ON skills
  FOR ALL USING (profile_id IN (
    SELECT sp.id FROM student_profiles sp 
    JOIN users u ON sp.user_id = u.id 
    WHERE u.auth_subject = auth.uid()::text
  ));

CREATE POLICY projects_owner_policy ON projects
  FOR ALL USING (profile_id IN (
    SELECT sp.id FROM student_profiles sp 
    JOIN users u ON sp.user_id = u.id 
    WHERE u.auth_subject = auth.uid()::text
  ));

CREATE POLICY opps_owner_policy ON opportunities
  FOR ALL USING (user_id IN (SELECT id FROM users WHERE auth_subject = auth.uid()::text));

CREATE POLICY assessments_owner_policy ON assessments
  FOR ALL USING (user_id IN (SELECT id FROM users WHERE auth_subject = auth.uid()::text));

CREATE POLICY files_owner_policy ON profile_files
  FOR ALL USING (user_id IN (SELECT id FROM users WHERE auth_subject = auth.uid()::text));
```

### 4.3 Log Sanitization & Privacy Safeguards

- **Zero PII Logging:** Request bodies for `/api/v1/me/profile` and raw text streams for `/api/v1/resumes/parse` are explicitly excluded from application logs.
- **Header Masking:** All `Authorization` headers and Supabase JWT tokens are redacted from server logs.
- **Traceable Identifiers:** Logs record only `request_id`, `route`, `http_status`, and `latency_ms`.

---

## 5. Deployment Step-by-Step Runbook

### 5.1 Supabase Configuration Runbook

1. **Create Projects:** Provision two separate projects on Supabase: `placementos-preview` and `placementos-production`.
2. **Configure Auth:**
   - Set **Site URL** in Production to `https://placementos.vercel.app`.
   - Add **Redirect URLs**:
     - `http://localhost:3000/**` (Local dev)
     - `https://*-<team-slug>.vercel.app/**` (Vercel Preview wildcards)
     - `https://placementos.vercel.app/**` (Production canonical)
3. **Provision Private Bucket:**
   - Create bucket `resumes` set to **Private**.
   - Restrict allowed MIME types: `application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `text/plain`.
   - Set max file size: `5242880` (5 MiB).
4. **Apply Schema Migrations:**
   - Run Alembic migrations against the database URL: `alembic upgrade head`.

### 5.2 Render FastAPI Deployment Runbook

1. **Create Web Service:**
   - Connect GitHub repository `https://github.com/Sarthak-madan334/PlacementOS`.
   - Root Directory: `backend`.
   - Runtime: `Python 3`.
   - Build Command: `pip install -r requirements.txt`.
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
   - Health Check Path: `/api/v1/health/live`.
2. **Set Environment Secrets:** Configure all variables from Section 2.2.
3. **Verify Startup:** Inspect Render build logs and verify `GET /api/v1/health/live` returns `{"status":"ok"}`.

### 5.3 Vercel Next.js Deployment Runbook

1. **Import Project:** Connect repository to Vercel, setting Root Directory to `frontend`.
2. **Framework Preset:** Next.js.
3. **Set Environment Variables:** Configure all variables from Section 2.1 for both Preview and Production scopes.
4. **Deploy & Verify:** Trigger deployment on `main` branch. Confirm landing page loads and connects to the Supabase Auth project.

---

## 6. Production Launch Checklist & Quality Gates

```markdown
### Pre-Launch Gate 1: Connectivity & Contracts
- [ ] Render `/api/v1/health/live` and `/api/v1/health/ready` return 200 OK.
- [ ] Vercel frontend successfully calls Render API `/api/v1/health/live` over HTTPS.
- [ ] OpenAPI schema at `https://api.placementos.render.com/openapi.json` conforms to `docs/SRD.md`.

### Pre-Launch Gate 2: Authentication & Authorization
- [ ] Sign-up / Sign-in flow issues valid Supabase JWT with `aud: "authenticated"`.
- [ ] FastAPI rejects unauthenticated requests with HTTP 401.
- [ ] FastAPI rejects expired / forged JWTs with HTTP 401.
- [ ] Attempted access to another student's profile or assessment returns HTTP 404.

### Pre-Launch Gate 3: Resume Processing & Storage Security
- [ ] 5 MiB ceiling strictly enforced; files > 5 MiB rejected with HTTP 413.
- [ ] Files with invalid extensions or spoofed MIME types rejected with HTTP 422.
- [ ] Resume objects in Supabase Storage are private and cannot be downloaded without signed URL.
- [ ] Deletion of student profile (`DELETE /api/v1/me/profile`) removes both PostgreSQL rows and Storage files.

### Pre-Launch Gate 4: Operational Readiness & Disaster Recovery
- [ ] Alembic migration applied cleanly to production database (`alembic upgrade head`).
- [ ] Supabase Point-in-Time Recovery (PITR) / daily automated backups enabled.
- [ ] CORS headers restricted strictly to `https://placementos.vercel.app` on production Render backend.
- [ ] Zero secrets or service-role keys leaked in `NEXT_PUBLIC_*` client bundles.
```

---

## 7. Known Blockers & Required Developer Actions

### 7.1 Backend Developer Actions (Aarush)
1. **Live JWT Signature Validation:**
   - In `backend/app/core/security.py`, replace placeholder mock JWT decoder with live Supabase JWT verification against `AUTH_ISSUER_URL` and `SUPABASE_JWT_SECRET` when `ALLOW_MOCK_AUTH=False`.
2. **Supabase Storage Integration:**
   - Wire `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in `backend/app/adapters/storage/` to upload validated resumes and generate signed download URLs.
3. **Database Readiness Endpoint:**
   - In `backend/app/api/v1/endpoints/health.py`, ensure `/health/ready` executes a lightweight query (`SELECT 1`) against the PostgreSQL database with a 2-second timeout.

### 7.2 Frontend Developer Actions (Sarthak)
1. **Live API Client Connection:**
   - In `frontend/lib/api.ts`, implement the live HTTP client using `fetch` with `NEXT_PUBLIC_API_BASE_URL` and attach `Authorization: Bearer <token>` from the Supabase Auth session when `NEXT_PUBLIC_DEMO_MODE=false`.
2. **Supabase Auth Client Provider:**
   - Initialize `@supabase/supabase-js` using `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` to handle user login, registration, and session token refresh.
