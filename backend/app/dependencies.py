from __future__ import annotations

import json
import uuid
from typing import Annotated

import httpx
import jwt
from fastapi import Depends, Header, HTTPException, status
from jwt.algorithms import RSAAlgorithm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db

_jwks_cache: dict | None = None


async def _get_jwks(force_refresh: bool = False) -> dict:
    global _jwks_cache
    if _jwks_cache is None or force_refresh:
        async with httpx.AsyncClient() as client:
            resp = await client.get(settings.keycloak_jwks_uri, timeout=10)
            resp.raise_for_status()
            _jwks_cache = resp.json()
    return _jwks_cache


def _find_jwk(jwks: dict, kid: str | None) -> dict | None:
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    return None


async def _get_signing_key(token: str):
    """Return the RSA public key matching the token's kid.

    Refreshes the JWKS cache once on a miss, so signing-key rotation in Keycloak
    is handled without a restart.
    """
    try:
        kid = jwt.get_unverified_header(token).get("kid")
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token header: {exc}",
        ) from exc

    jwk = _find_jwk(await _get_jwks(), kid)
    if jwk is None:
        jwk = _find_jwk(await _get_jwks(force_refresh=True), kid)
    if jwk is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No matching signing key for token",
        )
    return RSAAlgorithm.from_jwk(json.dumps(jwk))


class TokenPayload:
    def __init__(self, sub: str, email: str, roles: list[str]) -> None:
        self.sub = sub
        self.email = email
        self.roles = roles

    @property
    def is_admin(self) -> bool:
        return "admin" in self.roles

    @property
    def is_analyst(self) -> bool:
        return "analyst" in self.roles or self.is_admin

    @property
    def is_viewer(self) -> bool:
        return True


async def get_current_token(
    authorization: Annotated[str | None, Header()] = None,
) -> TokenPayload:
    """Validate the Bearer JWT from Keycloak and return extracted claims."""
    if settings.DEBUG and authorization is None:
        # Dev-only bypass: X-Dev-User header allows testing without Keycloak running
        return TokenPayload(
            sub=str(uuid.uuid4()),
            email="dev@localhost",
            roles=["admin"],
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    token = authorization.removeprefix("Bearer ")

    public_key = await _get_signing_key(token)
    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=settings.KEYCLOAK_CLIENT_ID,
            issuer=settings.keycloak_issuer,
            options={"verify_exp": True},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        ) from exc

    realm_roles: list[str] = (
        payload.get("realm_access", {}).get("roles", [])
    )
    return TokenPayload(
        sub=payload["sub"],
        email=payload.get("email", ""),
        roles=realm_roles,
    )


CurrentToken = Annotated[TokenPayload, Depends(get_current_token)]
DB = Annotated[AsyncSession, Depends(get_db)]


def require_analyst(token: CurrentToken) -> TokenPayload:
    if not token.is_analyst:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Analyst role required")
    return token


def require_admin(token: CurrentToken) -> TokenPayload:
    if not token.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return token


RequireAnalyst = Annotated[TokenPayload, Depends(require_analyst)]
RequireAdmin = Annotated[TokenPayload, Depends(require_admin)]
