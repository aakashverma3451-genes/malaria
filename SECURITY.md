# Security Notes

## Dependency audit status

Frontend (`npm audit`): **0 vulnerabilities**.

Backend (`pip-audit -r backend/requirements.txt`): **2 packages with known advisories that have no reachable code path in this application** (see below). Everything with an available fix has been upgraded.

To re-run the audits:

```bash
# frontend
cd frontend && npm audit

# backend (needs Python >=3.10 to resolve current pins)
python3.11 -m venv /tmp/pip-audit-venv
/tmp/pip-audit-venv/bin/pip install -U pip pip-audit
/tmp/pip-audit-venv/bin/pip-audit -r backend/requirements.txt
```

## Known dormant advisories (accepted, tracked)

These have **no upstream fix available for our version constraints** and are **not reachable** by the current codebase. Each entry lists the exact trigger that would make it live — re-audit if that condition is ever introduced.

### `ecdsa` 0.19.2 — PYSEC-2026-1325 (Minerva timing attack)

- **What:** Timing side-channel during ECDSA **signing** (`sign_digest`) can leak the private nonce, potentially recovering the private key.
- **Why not fixable:** Pulled in transitively by `python-jose`. The `ecdsa` maintainers have stated they will **not** fix this — a pure-Python library cannot guarantee constant-time execution. `python-jose` still depends on it.
- **Why not reachable:** We only **verify** RS256 (RSA) signatures from Keycloak in `backend/app/dependencies.py`. We never sign anything, and never use ECDSA keys. Signing is done by Keycloak, in a separate process, not by this Python code.
- **Trigger to re-audit:** if this service ever starts *issuing* JWTs itself, or signing with EC keys.
- **Permanent fix (deferred):** migrate JWT verification from `python-jose` to `PyJWT`, which does not depend on `ecdsa`. Deferred because it touches the auth-critical `dependencies.py` and warrants careful end-to-end testing rather than a rushed swap.

### `starlette` 0.52.1 — PYSEC-2026-161 / -248 / -249 / -2280 / -2281 (6 advisories)

- **What (the ones that matter):**
  - `request.form()` DoS on `application/x-www-form-urlencoded` bodies (unbounded fields/memory).
  - "BadHost" — unvalidated `Host` header poisons `request.url.path` / `.hostname`, can bypass path-based checks.
  - Arbitrary HTTP method dispatch via `HTTPEndpoint` + `getattr`.
  - `FileResponse` Range-header O(n²) DoS.
  - `StaticFiles` UNC-path SSRF (Windows only).
- **Why not fixable now:** the fixes require `starlette >= 1.x`, but the **latest FastAPI release still pins `starlette < 1.0.0`**. No FastAPI version currently reaches the fixed starlette line. This resolves itself when FastAPI adopts starlette 1.x upstream — bump both together then.
- **Why not reachable:** verified by grep over `backend/app/` — this codebase uses **none** of the vulnerable surfaces:
  - No `request.form()` / `UploadFile` — file uploads go directly to MinIO via presigned URLs, never through the API.
  - No `FileResponse` — downloads are also presigned MinIO URLs.
  - No raw `HTTPEndpoint` — routing is exclusively FastAPI `APIRouter`.
  - No `request.url.hostname` / `.path` trust — CORS uses a static `allow_origins` list; auth reads only the `Authorization` header.
  - Linux-only Docker deployment — the Windows `StaticFiles` UNC issue cannot apply.
- **Trigger to re-audit:** adding any `UploadFile`/`request.form()` endpoint, using `FileResponse`, mounting `StaticFiles`, or introducing Host-header-dependent logic. **In particular, the Stage 4 file-upload work should re-check the `request.form()` DoS** before shipping.

## Reminder for production (from the Stage 10 gate)

- `DEBUG=false` (disables the dev auth bypass in `dependencies.py`).
- Replace all `BGIBEIJING` dev credentials in `.env` with unique random secrets.
- `SECRET_KEY` / `NEXTAUTH_SECRET` must be long random strings.
