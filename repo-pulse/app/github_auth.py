"""GitHub App authentication: JWT → installation access token."""

from __future__ import annotations

import time
from typing import Any

import httpx
import jwt

from app.config import Settings


def build_app_jwt(settings: Settings, *, now: int | None = None) -> str:
    """Create a short-lived JWT signed with the GitHub App private key."""
    issued_at = (now if now is not None else int(time.time())) - 60
    payload = {
        "iat": issued_at,
        "exp": issued_at + 9 * 60,
        "iss": settings.app_id,
    }
    return jwt.encode(payload, settings.private_key_pem, algorithm="RS256")


async def get_installation_token(
    settings: Settings,
    installation_id: int,
    *,
    client: httpx.AsyncClient | None = None,
) -> str:
    """Exchange App JWT for an installation access token."""
    token = build_app_jwt(settings)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    url = f"{settings.github_api_base}/app/installations/{installation_id}/access_tokens"

    owns_client = client is None
    client = client or httpx.AsyncClient(timeout=30.0)
    try:
        response = await client.post(url, headers=headers)
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        return data["token"]
    finally:
        if owns_client:
            await client.aclose()
