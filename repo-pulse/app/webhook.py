"""Webhook signature verification and event handling."""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any

from app.config import Settings
from app.github_api import GitHubClient
from app.github_auth import get_installation_token
from app.pr_summary import COMMENT_MARKER, build_summary_comment

logger = logging.getLogger(__name__)

HANDLED_PR_ACTIONS = {"opened", "reopened", "synchronize", "ready_for_review"}


def verify_signature(secret: str, body: bytes, signature_header: str | None) -> bool:
    """Validate X-Hub-Signature-256 from GitHub webhooks."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    received = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, received)


async def handle_pull_request_event(settings: Settings, payload: dict[str, Any]) -> dict[str, Any]:
    action = payload.get("action")
    if action not in HANDLED_PR_ACTIONS:
        return {"status": "ignored", "reason": f"action={action}"}

    installation = payload.get("installation") or {}
    installation_id = installation.get("id")
    if not installation_id:
        return {"status": "error", "reason": "missing installation id"}

    pr = payload.get("pull_request") or {}
    repo = payload.get("repository") or {}
    owner = (repo.get("owner") or {}).get("login")
    repo_name = repo.get("name")
    pull_number = pr.get("number")
    head_sha = (pr.get("head") or {}).get("sha")
    title = pr.get("title") or ""

    if not all([owner, repo_name, pull_number, head_sha]):
        return {"status": "error", "reason": "incomplete PR payload"}

    token = await get_installation_token(settings, int(installation_id))
    async with GitHubClient(settings, token) as gh:
        files = await gh.list_pr_files(owner, repo_name, int(pull_number))
        check_runs = await gh.list_check_runs(owner, repo_name, head_sha)
        linked = await gh.linked_issues_and_threads(owner, repo_name, int(pull_number))
        body = build_summary_comment(
            owner=owner,
            repo=repo_name,
            pull_number=int(pull_number),
            pr_title=title,
            files=files,
            check_runs=check_runs,
            linked=linked,
        )

        existing = await gh.find_existing_bot_comment(
            owner, repo_name, int(pull_number), COMMENT_MARKER
        )
        if existing:
            await gh.update_issue_comment(owner, repo_name, int(existing["id"]), body)
            logger.info("Updated RepoPulse comment on %s/%s#%s", owner, repo_name, pull_number)
            return {"status": "updated", "comment_id": existing["id"]}

        created = await gh.create_issue_comment(owner, repo_name, int(pull_number), body)
        logger.info("Created RepoPulse comment on %s/%s#%s", owner, repo_name, pull_number)
        return {"status": "created", "comment_id": created.get("id")}
