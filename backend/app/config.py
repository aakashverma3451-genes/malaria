from __future__ import annotations

import json
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str

    # Redis / Celery
    REDIS_URL: str
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    # MinIO
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str = "genomics-data"
    MINIO_SECURE: bool = False

    # Keycloak
    KEYCLOAK_URL: str
    KEYCLOAK_REALM: str = "malaria"
    KEYCLOAK_CLIENT_ID: str = "malaria-api"

    # App
    SECRET_KEY: str
    DEBUG: bool = False
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Pipeline
    PIPELINE_STAGING_DIR: str = "/staging"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("CELERY_BROKER_URL", mode="before")
    @classmethod
    def default_broker(cls, v: str, info: Any) -> str:
        return v or info.data.get("REDIS_URL", "")

    @field_validator("CELERY_RESULT_BACKEND", mode="before")
    @classmethod
    def default_result_backend(cls, v: str, info: Any) -> str:
        return v or info.data.get("REDIS_URL", "").replace("/0", "/1")

    @property
    def keycloak_jwks_uri(self) -> str:
        return f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}/protocol/openid-connect/certs"

    @property
    def keycloak_issuer(self) -> str:
        return f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}"


settings = Settings()  # type: ignore[call-arg]
