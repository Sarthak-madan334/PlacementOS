# PlacementOS — Backend Service (Aarush)

FastAPI service for profile evidence, resume analysis, deterministic readiness, and role matching.

## Architecture

- **Framework**: FastAPI (Python 3.10+)
- **ORM & DB**: SQLAlchemy 2.x, PostgreSQL (production) / SQLite (local / testing)
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Auth**: Managed JWT verification (Supabase Auth / RFC 7519)

## Setup & Running Locally

### 1. Install Dependencies

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and set environment variables:

```bash
cp .env.example .env
```

`ALLOW_MOCK_AUTH=true` is included only for local synthetic profile API tests. The backend ignores mock authentication outside `APP_ENV=local` or `test`. Never enable it on a deployed service.

### 3. Run Database Migrations

```bash
python -m alembic -c alembic.ini upgrade head
```

### 4. Start the Development Server

```bash
python -m uvicorn app.main:app --reload --port 8000
```

OpenAPI docs will be available at: `http://localhost:8000/api/v1/docs`.

---

## API Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/health/live` | Process liveness check | No |
| `GET` | `/health/ready` | Database readiness check | No |
| `GET` | `/api/v1/me/profile` | Get current authenticated student's profile | Yes (`Bearer <token>`) |
| `PUT` | `/api/v1/me/profile` | Idempotently create/update profile, skills, projects | Yes (`Bearer <token>`) |
| `DELETE` | `/api/v1/me/profile` | Delete profile and associated evidence records | Yes (`Bearer <token>`) |
| `POST` | `/api/v1/resumes/parse` | Parse uploaded resume (PDF, DOCX, TXT) for review | No |
| `POST` | `/api/v1/assessments/preview` | Compute a non-persistent guest assessment from supplied synthetic profile/role data | No |

---

## Standalone Resume Parser CLI

You can parse resume files directly via the command line without starting the web server:

```bash
python -m app.cli.parse_resume fixtures/resumes/sample_resume.txt
```

---

## Testing

Run the automated test suite from the repository root:

```bash
python -m pytest backend/tests -v
```

The assessment preview is intentionally not persisted and has no account-history endpoint. Use synthetic data in guest/preview mode; authenticated profile persistence and saved assessment history are separate release work.

---

## Example cURL Requests

### Check Liveness
```bash
curl -X GET http://localhost:8000/health/live
```

### Check Database Readiness
```bash
curl -X GET http://localhost:8000/health/ready
```

### Create / Update Profile (PUT)
```bash
curl -X PUT http://localhost:8000/api/v1/me/profile \
  -H "Authorization: Bearer mock-student-01" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Aarush Sharma",
    "branch": "Computer Science",
    "graduation_year": 2026,
    "cgpa": 8.75,
    "cgpa_scale": 10.0,
    "target_role": "Backend Engineer",
    "skills": [
      {
        "display_name": "Python",
        "self_reported_level": "advanced",
        "source": "self_reported"
      },
      {
        "display_name": "FastAPI",
        "self_reported_level": "advanced",
        "source": "self_reported"
      }
    ],
    "projects": [
      {
        "title": "PlacementOS",
        "description": "Backend readiness engine and profile evidence service",
        "url": "https://github.com/Sarthak-madan334/PlacementOS",
        "start_date": "2025-01-01",
        "end_date": "2025-05-01"
      }
    ]
  }'
```

### Read Profile (GET)
```bash
curl -X GET http://localhost:8000/api/v1/me/profile \
  -H "Authorization: Bearer mock-student-01"
```

### Delete Profile (DELETE)
```bash
curl -X DELETE http://localhost:8000/api/v1/me/profile \
  -H "Authorization: Bearer mock-student-01"
```
