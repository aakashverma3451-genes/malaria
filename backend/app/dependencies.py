from __future__ import annotations

import uuid
from typing import Annotated

import httpx
from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db

_jwks_cache: dict | None = None


async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(settings.keycloak_jwks_uri, timeout=10)
            resp.raise_for_status()
            _jwks_cache = resp.json()
    return _jwks_cache


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

    try:
        jwks = await _get_jwks()
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=settings.KEYCLOAK_CLIENT_ID,
            issuer=settings.keycloak_issuer,
            options={"verify_exp": True},
        )
    except JWTError as exc:
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
