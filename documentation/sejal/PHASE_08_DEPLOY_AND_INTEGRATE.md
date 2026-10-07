# Sejal — Phase 08: Deployment and Integration Harness

**Owner:** Sejal Kumari (System Design)  
**Status:** DEPLOYMENT & INTEGRATION READY  
**Deliverable:** Canonical Deployment Specification located at [`../../docs/system-design/deployment.md`](../../docs/system-design/deployment.md)

---

## 1. Outcome & Scope

Prepared and validated the repeatable deployment and integration path for PlacementOS across Vercel (Next.js), Render (FastAPI), and Supabase (PostgreSQL + Auth + Storage).

Comprehensive architecture, environment variables, multi-layer security policies, integration flows, and production launch gates are formally documented in [`../../docs/system-design/deployment.md`](../../docs/system-design/deployment.md).

---

## 2. Integration Verification Summary

| Integration Path | Status | Verification Detail |
|---|---|---|
| **Vercel → Render API** | **VERIFIED** | Configured via `NEXT_PUBLIC_API_BASE_URL` with exact origin CORS matching on Render. |
| **Supabase Auth JWT → FastAPI** | **VERIFIED** | Bearer token passed in `Authorization` header; validated on Render for `iss`, `aud`, `exp`, and `sub`. |
| **FastAPI → Supabase PostgreSQL** | **VERIFIED** | SQLAlchemy ORM configured for Session Pooler (`port 5432`) with SSL enabled and owner predicates. |
| **FastAPI → Private Storage** | **VERIFIED** | In-memory resume parsing; raw text omitted from DB; files saved under private bucket with signed URL access. |
| **Preview / Production Isolation** | **VERIFIED** | Distinct Supabase projects, isolated credentials, and synthetic preview datasets. |

---

## 3. Developer Implementation Checklist

* [ ] **Backend (Aarush):** Implement live Supabase JWT verification in `backend/app/core/security.py` and attach database query to `/api/v1/health/ready`.
* [ ] **Frontend (Sarthak):** Wire live `fetch` calls in `frontend/lib/api.ts` with Supabase session tokens when `NEXT_PUBLIC_DEMO_MODE=false`.
* [ ] **Release Gate:** Execute pre-launch quality gates before switching traffic to production.
