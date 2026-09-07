"""Tests for GitHub App Manifest helpers."""

from __future__ import annotations

from app.config import Settings
from app.manifest import build_manifest, persist_app_credentials


def test_build_manifest_includes_webhook_and_permissions() -> None:
    settings = Settings(public_base_url="https://example.test")
    manifest = build_manifest(settings, "https://example.test")
    assert manifest["hook_attributes"]["url"] == "https://example.test/webhook"
    assert manifest["redirect_url"] == "https://example.test/setup/callback"
    assert manifest["default_permissions"]["pull_requests"] == "write"
    assert "pull_request" in manifest["default_events"]


def test_persist_app_credentials(tmp_path, monkeypatch) -> None:
    key = tmp_path / "private-key.pem"
    env = tmp_path / ".env"
    monkeypatch.setattr("app.manifest.ENV_PATH", env)
    settings = Settings(private_key_path=str(key), support_email="magnedinanevesdina@gmail.com")
    values = persist_app_credentials(
        {
            "id": 42,
            "slug": "repopulse-krypton0078",
            "webhook_secret": "whsec",
            "pem": "-----BEGIN RSA PRIVATE KEY-----\nTEST\n-----END RSA PRIVATE KEY-----\n",
        },
        settings,
    )
    assert values["APP_ID"] == "42"
    assert "BEGIN RSA PRIVATE KEY" in key.read_text()
    text = env.read_text()
    assert "WEBHOOK_SECRET=whsec" in text
    assert "APP_SLUG=repopulse-krypton0078" in text
