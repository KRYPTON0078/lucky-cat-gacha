"""Unit tests for signature verification and summary markdown."""

from __future__ import annotations

import hashlib
import hmac

from app.pr_summary import COMMENT_MARKER, build_summary_comment
from app.webhook import verify_signature


def test_verify_signature_valid() -> None:
    secret = "test-secret"
    body = b'{"action":"opened"}'
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_signature(secret, body, f"sha256={digest}") is True


def test_verify_signature_invalid() -> None:
    assert verify_signature("secret", b"body", "sha256=deadbeef") is False
    assert verify_signature("secret", b"body", None) is False
    assert verify_signature("secret", b"body", "sha1=abc") is False


def test_build_summary_comment_contains_marker_and_metrics() -> None:
    files = [
        {"filename": "app/main.py", "additions": 10, "deletions": 2},
        {"filename": ".github/workflows/ci.yml", "additions": 5, "deletions": 0},
    ]
    checks = [{"name": "test", "status": "completed", "conclusion": "success"}]
    linked = {
        "title": "Add feature",
        "linked_issues": [
            {
                "number": 7,
                "title": "Need feature",
                "url": "https://github.com/o/r/issues/7",
                "state": "OPEN",
            }
        ],
        "review_threads": [],
    }
    body = build_summary_comment(
        owner="KRYPTON0078",
        repo="repo-pulse",
        pull_number=1,
        pr_title="Add feature",
        files=files,
        check_runs=checks,
        linked=linked,
    )
    assert COMMENT_MARKER in body
    assert "Files changed | **2**" in body.replace(" ", "") or "**2**" in body
    assert "CI / supply-chain workflow" in body
    assert "#7" in body
    assert "test" in body
