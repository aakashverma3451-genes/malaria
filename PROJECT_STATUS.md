# Malaria Genomics Platform — Implementation Status

_Last updated: 2026-07-05_

This document maps what was originally planned against what is actually built and running today. It is a working reference, not a spec — update it as work lands.

> **Note on the "original plan":** the stage numbers below (Stage 1–6) are reconstructed from `Placeholder — full implementation in Stage N` comments left in the code and from the tech-stack/workflow documents shared at the start of this build, not copied verbatim from an original prompt file. If you have the original 6-prompt document, paste it in and I'll replace this reconstruction with the literal text.

---

## 1. Infrastructure — done

- Docker Compose stack: postgres, redis, minio, keycloak, backend, frontend, celery-worker, celery-beat, flower — all 9 services build and run (`make up`)
- Alembic migrations wired for async SQLAlchemy, initial schema applied (11 tables)
- MinIO bucket (`genomics-data`) created and reachable
- Keycloak realm `malaria` configured: roles (`admin`/`analyst`/`viewer`), clients (`malaria-api`, `malaria-web` with an audience mapper), verified end-to-end with a real minted JWT
- `.env` / `.env.example`, `.gitignore`, `Makefile`, pre-commit config all in place

## 2. Backend (FastAPI) — status by module

| Module | State | Notes |
|---|---|---|
| `auth` (JWT validation, `dependencies.py`) | **Done** | JWKS-based, realm-role based authorization (`RequireAdmin`/`RequireAnalyst`), dev bypass when `DEBUG=true` |
| `users` router | **Done** | `/me` GET/PUT, admin list — tested end-to-end |
| `projects` router | **Built, untested** | CRUD scaffolded; not exercised against real data yet |
| `samples` router | **Built, untested** | CRUD scaffolded |
| `files` router (upload) | **Built, untested** | Presigned MinIO PUT/GET flow implemented; never actually driven through a real upload |
| `jobs` router | **Built, untested** | Creates `AnalysisJob` + `AnalysisJobSample` rows, dispatches to Celery — but see Pipeline below |
| `results` router | **Built, untested** | CRUD scaffolded |
| `reports` | **Not started** | `Report` model + Pydantic schema exist; **no router** — no API endpoints at all |
| `health` router | **Done** | Live, checked by `docker compose ps` healthchecks indirectly and manually |

## 3. Pipeline execution — mostly not started

This is the biggest gap. The platform can *record* that a job was submitted, but cannot *run* one yet.

- `celery/tasks/pipeline.py` → `run_pipeline`: **stub**, just returns `{"status": "queued"}`, does not invoke Nextflow
- `celery/tasks/maintenance.py` → `cleanup_expired_uploads`: **stub**, returns `{"cleaned": 0}`
- `docs/pipeline-comparison/single_sample.nf`: a **reference/comparison sketch** (fastp → BWA-MEM → GATK → SnpEff for P. falciparum), explicitly marked illustrative — not wired into the app, no container images built for it
- `WorkflowType` enum already models 7 workflow kinds (single-sample QC/full, population joint-calling/structure/phylogenetics/selection/full) — schema is ready, execution is not

## 4. Frontend (Next.js) — status by page

| Page | State |
|---|---|
| `/login` | **Done** — dark BioVis theme, Keycloak SSO button, verified working |
| `/dashboard` | **Built, static data only** — KPI cards/resource bars/tables render but are hardcoded placeholder arrays, not fetched from the backend |
| `/dashboard/samples` | **Not started** — linked from the sidebar, page doesn't exist (404) |
| `/dashboard/projects` | **Not started** — same |
| `/dashboard/pipelines` | **Not started** — same |
| `/dashboard/jobs` | **Not started** — same |
| `/dashboard/results` | **Not started** — same |
| `/dashboard/settings` | **Not started** — same |

The Axios client (`lib/api.ts`) with the auth-token interceptor exists, but **nothing in the frontend actually calls a backend endpoint yet** besides NextAuth's own token handling. The dashboard is a visual shell, not a connected one.

## 5. What's fully working end-to-end today

- Sign in via Keycloak → NextAuth session → JWT with correct `iss`/`aud`/roles → backend validates it → `GET /api/v1/users/me` returns real Postgres data (auto-provisioning a `users` row on first login)
- Docker stack boots clean, migrations apply, healthchecks pass

## 6. Suggested next priorities

Roughly in the order they'd unblock the most:

1. **Wire the dashboard to real data** — replace the static arrays in `dashboard/page.tsx` with calls to `/api/v1/projects`, `/api/v1/samples`, `/api/v1/jobs`
2. **Build the missing sidebar pages** — at minimum samples and jobs, since those routers already exist server-side
3. **Test the upload flow live** — presigned URL code exists but has never been exercised through a real file
4. **Reports router** — add the missing API layer for the `Report` model
5. **Pipeline execution** — this is the core value of the product and is currently 0% implemented; needs a real Celery→Nextflow bridge, container images for the tools in `single_sample.nf`, and a way to track job progress back into `AnalysisJob.progress_percent`
