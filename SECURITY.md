# Security Notes

## Dependency audit status

Both audits are **clean** as of the latest commit:

- Frontend (`npm audit`): **0 vulnerabilities**
- Backend (`pip-audit -r backend/requirements.txt`): **No known vulnerabilities found**

To re-run:

```bash
# frontend
cd frontend && npm audit

# backend (needs Python >=3.10 to resolve current pins)
python3.11 -m venv /tmp/pip-audit-venv
/tmp/pip-audit-venv/bin/pip install -U pip pip-audit
/tmp/pip-audit-venv/bin/pip-audit -r backend/requirements.txt
```

## Notable hardening decisions

### JWT library: PyJWT, not python-jose

Auth token validation (`backend/app/dependencies.py`) uses **PyJWT**, not `python-jose`.
`python-jose` transitively depends on `ecdsa`, which carries an **unfixable** advisory
(PYSEC-2026-1325, the "Minerva" timing side-channel — the `ecdsa` maintainers have
stated a pure-Python library cannot guarantee constant-time execution and will not
fix it). PyJWT depends only on `cryptography`, so switching removed `ecdsa` from the
dependency tree entirely. PyJWT is also the more actively maintained choice for
verifying third-party OIDC tokens.

We verify RS256 signatures against Keycloak's JWKS (fetched and cached, refreshed
once on a `kid` miss to survive Keycloak signing-key rotation). Validation is tested
for both acceptance (valid token → 200) and rejection (malformed and tampered-signature
tokens → 401).

### FastAPI / Starlette version floor

`fastapi>=0.135` dropped the old `starlette<1.0.0` cap. We pin `fastapi==0.139.0` so
`starlette` resolves to `1.3.1`, which patches the 2026 Starlette advisories
(BadHost host-header path poisoning, `request.form()` DoS, `FileResponse` Range DoS,
etc.). Earlier FastAPI releases capped Starlette below the patched line — do not pin
FastAPI back under 0.135 without re-checking `pip-audit`.

## Reminder for production (from the Stage 10 gate)

- `DEBUG=false` (disables the dev auth bypass in `dependencies.py`).
- Replace all `BGIBEIJING` dev credentials in `.env` with unique random secrets.
- `SECRET_KEY` / `NEXTAUTH_SECRET` must be long random strings.
