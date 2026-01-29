from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from dotenv import find_dotenv, load_dotenv

# The generated client will live in this module after `ariadne-codegen` runs.
# It is intentionally a separate top-level package so it won't overwrite
# handwritten wrapper code.
from netrise_turbine_sdk_graphql import Client as GeneratedClient


@dataclass(frozen=True)
class TurbineClientConfig:
    endpoint: str

    # Client credentials
    domain: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    audience: Optional[str] = None
    organization_id: Optional[str] = None

    # Manual token override
    turbine_api_token: Optional[str] = None

    @staticmethod
    def from_env(load_env_file: bool = True) -> "TurbineClientConfig":
        """Load config from environment variables.

        If `load_env_file` is True, automatically loads a `.env` file from:
        - Current working directory (most common)
        - Parent directories (walks up the directory tree)

        Environment variables can also be set directly without a `.env` file.
        Set `load_env_file=False` to disable automatic `.env` file loading.
        """
        if load_env_file:
            # Prioritize .env file in current working directory
            # This ensures local .env files take precedence over parent directories
            current_dir_env = Path.cwd() / ".env"
            if current_dir_env.exists():
                load_dotenv(current_dir_env, override=False)
            else:
                # If no .env in current directory, search parent directories
                dotenv_path = find_dotenv(usecwd=True)
                if dotenv_path:
                    load_dotenv(dotenv_path, override=False)
                else:
                    # Fallback to default behavior if find_dotenv doesn't find anything
                    load_dotenv(override=False)

        endpoint = (os.getenv("endpoint") or "").strip()
        if not endpoint:
            raise ValueError(
                "endpoint is required (e.g. https://apollo.turbine.netrise.io/graphql/v3)"
            )

        return TurbineClientConfig(
            endpoint=endpoint,
            domain=_strip_or_none(os.getenv("domain")),
            client_id=_strip_or_none(os.getenv("client_id")),
            client_secret=_strip_or_none(os.getenv("client_secret")),
            audience=_strip_or_none(os.getenv("audience")),
            organization_id=_strip_or_none(os.getenv("organization_id")),
            turbine_api_token=_strip_or_none(os.getenv("TURBINE_API_TOKEN")),
        )


class TurbineClient:
    """Sync-first Turbine GraphQL client.

    - Uses `TURBINE_API_TOKEN` if provided.
    - Otherwise uses client credentials to fetch a token.

    The underlying request execution is provided by the generated client from
    `ariadne-codegen`.
    """

    def __init__(
        self,
        config: TurbineClientConfig,
        *,
        timeout: float = 30.0,
        httpx_client: Optional[httpx.Client] = None,
    ) -> None:
        self._config = config
        self._timeout = timeout
        self._httpx_client = httpx_client

        self._cached_token: Optional[str] = None
        self._cached_token_expires_at: float = 0.0

    @property
    def config(self) -> TurbineClientConfig:
        return self._config

    def _get_auth_header(self) -> Dict[str, str]:
        token = self._get_token()
        if not token.startswith("Bearer "):
            token = f"Bearer {token}"
        return {"Authorization": token}

    def _get_token(self) -> str:
        # 1) Manual token override
        if self._config.turbine_api_token:
            return self._config.turbine_api_token

        # 2) Cached token
        now = time.time()
        if self._cached_token and now < self._cached_token_expires_at:
            return self._cached_token

        # 3) Fetch via client credentials
        token, expires_in = _fetch_token(
            domain=self._config.domain,
            client_id=self._config.client_id,
            client_secret=self._config.client_secret,
            audience=self._config.audience,
            organization_id=self._config.organization_id,
            timeout=self._timeout,
        )

        # Cache with a small safety buffer.
        self._cached_token = token
        self._cached_token_expires_at = time.time() + max(0, expires_in - 30)
        return token

    def graphql(self) -> GeneratedClient:
        """Return a generated client instance (sync)."""
        headers = self._get_auth_header()

        # Prefer reusing caller-provided httpx client.
        if self._httpx_client is not None:
            self._httpx_client.headers.update(headers)
            return GeneratedClient(
                url=self._config.endpoint,
                http_client=self._httpx_client,
            )

        http_client = httpx.Client(timeout=self._timeout, headers=headers)
        return GeneratedClient(
            url=self._config.endpoint,
            http_client=http_client,
        )


def _strip_or_none(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    v = v.strip()
    return v or None


def _fetch_token(
    *,
    domain: Optional[str],
    client_id: Optional[str],
    client_secret: Optional[str],
    audience: Optional[str],
    organization_id: Optional[str],
    timeout: float,
) -> tuple[str, int]:
    if not domain:
        raise ValueError("domain is required when TURBINE_API_TOKEN is not set")
    if not client_id or not client_secret:
        raise ValueError(
            "client_id and client_secret are required when TURBINE_API_TOKEN is not set"
        )
    if not audience:
        raise ValueError("audience is required when TURBINE_API_TOKEN is not set")

    domain = domain.rstrip("/")
    token_url = f"{domain}/oauth/token"

    payload: Dict[str, Any] = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": audience,
    }

    # Organizations support depends on the client grant settings.
    if organization_id:
        payload["organization"] = organization_id

    with httpx.Client(timeout=timeout) as c:
        r = c.post(token_url, json=payload)
        r.raise_for_status()
        data = r.json()

    token = data.get("access_token")
    expires_in = int(data.get("expires_in", 3600))

    if not token:
        raise RuntimeError(f"Token response missing access_token: {data}")

    return token if token.startswith("Bearer ") else f"Bearer {token}", expires_in
