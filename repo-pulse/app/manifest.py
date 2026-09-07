"""GitHub App Manifest registration and credential persistence."""

from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx

from app.config import ENV_PATH, ROOT_DIR, Settings, reload_settings

MANIFEST_STATE_PATH = ROOT_DIR / ".manifest-state"
DEFAULT_APP_DISPLAY_NAME = "RepoPulse-KRYPTON0078"


def public_url(settings: Settings, request_base: str, path: str = "/") -> str:
    base = (settings.public_base_url or request_base).rstrip("/") + "/"
    return urljoin(base, path.lstrip("/"))


def build_manifest(settings: Settings, request_base: str) -> dict[str, Any]:
    homepage = public_url(settings, request_base, "/")
    return {
        "name": DEFAULT_APP_DISPLAY_NAME,
        "url": homepage,
        "hook_attributes": {
            "url": public_url(settings, request_base, "/webhook"),
            "active": True,
        },
        "redirect_url": public_url(settings, request_base, "/setup/callback"),
        "callback_urls": [public_url(settings, request_base, "/setup/callback")],
        "setup_url": public_url(settings, request_base, "/setup/callback"),
        "description": (
            "RepoPulse posts structured pull-request summaries using GitHub REST and GraphQL APIs."
        ),
        "public": False,
        "default_events": ["pull_request"],
        "default_permissions": {
            "pull_requests": "write",
            "checks": "read",
            "metadata": "read",
            "issues": "read",
        },
    }


def new_manifest_state() -> str:
    token = secrets.token_urlsafe(24)
    MANIFEST_STATE_PATH.write_text(token, encoding="utf-8")
    return token


def read_manifest_state() -> str:
    if not MANIFEST_STATE_PATH.is_file():
        return ""
    return MANIFEST_STATE_PATH.read_text(encoding="utf-8").strip()


def persist_app_credentials(payload: dict[str, Any], settings: Settings) -> dict[str, str]:
    pem = payload["pem"]
    key_path = Path(settings.private_key_path)
    key_path.write_text(pem, encoding="utf-8")
    key_path.chmod(0o600)

    values = {
        "APP_ID": str(payload["id"]),
        "APP_SLUG": str(payload.get("slug") or ""),
        "WEBHOOK_SECRET": str(payload.get("webhook_secret") or ""),
        "PRIVATE_KEY_PATH": str(key_path),
        "SUPPORT_EMAIL": settings.support_email,
        "APP_NAME": settings.app_name,
    }
    existing: dict[str, str] = {}
    if ENV_PATH.is_file():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            existing[key] = val
    existing.update(values)
    body = "\n".join(f"{k}={v}" for k, v in existing.items()) + "\n"
    ENV_PATH.write_text(body, encoding="utf-8")
    reload_settings()
    return values


async def convert_manifest_code(code: str, api_base: str) -> dict[str, Any]:
    url = f"{api_base}/app-manifests/{code}/conversions"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        response.raise_for_status()
        return response.json()


def setup_form_html(settings: Settings, request_base: str) -> str:
    state = new_manifest_state()
    manifest = json.dumps(build_manifest(settings, request_base))
    create_url = f"{settings.github_app_create_url}?state={state}"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Register RepoPulse GitHub App</title>
  <style>
    body {{ font-family: system-ui, sans-serif; background:#0d1117; color:#e6edf3;
           display:grid; place-items:center; min-height:100vh; margin:0; }}
    main {{ max-width: 36rem; padding: 2rem; }}
    button {{ background:#238636; color:white; border:0; padding:.8rem 1.2rem;
              border-radius:8px; font-size:1rem; cursor:pointer; }}
  </style>
</head>
<body>
  <main>
    <h1>Create the RepoPulse GitHub App</h1>
    <p>This posts GitHub's official App Manifest. Confirm once on GitHub; RepoPulse stores the App ID, webhook secret, and private key automatically.</p>
    <form id="manifest-form" action="{create_url}" method="post">
      <input type="hidden" name="manifest" id="manifest" />
      <button type="submit">Create GitHub App</button>
    </form>
  </main>
  <script>
    const input = document.getElementById("manifest");
    input.value = JSON.stringify({manifest});
    document.getElementById("manifest-form").submit();
  </script>
</body>
</html>
"""
