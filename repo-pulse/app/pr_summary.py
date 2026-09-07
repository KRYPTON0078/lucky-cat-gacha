"""Build the structured PR summary markdown comment."""

from __future__ import annotations

from typing import Any

COMMENT_MARKER = "<!-- repopulse-summary -->"

RISKY_PATH_HINTS = (
    ("Dockerfile", "Container build / runtime surface"),
    (".github/workflows/", "CI / supply-chain workflow"),
    ("requirements", "Python dependency lock surface"),
    ("package-lock.json", "JS dependency lock surface"),
    ("Cargo.lock", "Rust dependency lock surface"),
    ("auth", "Auth-related path"),
    ("secret", "Secret-related path"),
    ("crypto", "Crypto-related path"),
    ("migrate", "Database migration"),
    ("infra/", "Infrastructure"),
    ("terraform", "Infrastructure as code"),
)


def _risk_hints(filenames: list[str]) -> list[str]:
    hints: list[str] = []
    seen: set[str] = set()
    for name in filenames:
        lower = name.lower()
        for needle, label in RISKY_PATH_HINTS:
            if needle.lower() in lower and label not in seen:
                hints.append(f"`{name}` → {label}")
                seen.add(label)
    return hints[:8]


def _format_checks(check_runs: list[dict[str, Any]]) -> str:
    if not check_runs:
        return "_No check runs reported yet for the head SHA._"
    lines = []
    for run in check_runs[:15]:
        name = run.get("name", "check")
        status = run.get("status", "unknown")
        conclusion = run.get("conclusion") or "—"
        lines.append(f"- **{name}**: `{status}` / `{conclusion}`")
    if len(check_runs) > 15:
        lines.append(f"- _…and {len(check_runs) - 15} more_")
    return "\n".join(lines)


def _format_linked_issues(issues: list[dict[str, Any]]) -> str:
    if not issues:
        return "_No closing-linked issues found via GraphQL._"
    lines = []
    for issue in issues:
        lines.append(
            f"- [#{issue['number']}]({issue['url']}) {issue.get('title', '')} "
            f"(`{issue.get('state', '?')}`)"
        )
    return "\n".join(lines)


def _format_threads(threads: list[dict[str, Any]]) -> str:
    if not threads:
        return "_No review threads._"
    unresolved = [t for t in threads if not t.get("isResolved")]
    resolved = len(threads) - len(unresolved)
    lines = [f"- Resolved: **{resolved}** · Unresolved: **{len(unresolved)}**"]
    for thread in unresolved[:5]:
        comments = (thread.get("comments") or {}).get("nodes") or []
        if not comments:
            continue
        author = ((comments[0].get("author") or {}) or {}).get("login", "user")
        body = (comments[0].get("body") or "").strip().splitlines()[0][:120]
        lines.append(f"- @{author}: {body}")
    return "\n".join(lines)


def build_summary_comment(
    *,
    owner: str,
    repo: str,
    pull_number: int,
    pr_title: str,
    files: list[dict[str, Any]],
    check_runs: list[dict[str, Any]],
    linked: dict[str, Any],
) -> str:
    filenames = [f.get("filename", "") for f in files]
    additions = sum(int(f.get("additions") or 0) for f in files)
    deletions = sum(int(f.get("deletions") or 0) for f in files)
    top_files = filenames[:12]
    file_list = "\n".join(f"- `{name}`" for name in top_files) or "_No files listed._"
    if len(filenames) > 12:
        file_list += f"\n- _…and {len(filenames) - 12} more files_"

    risks = _risk_hints(filenames)
    risk_block = "\n".join(f"- {h}" for h in risks) if risks else "_No heuristic risk paths matched._"

    return f"""{COMMENT_MARKER}
## RepoPulse PR summary

**{owner}/{repo}#{pull_number}** — {pr_title or linked.get('title') or '(untitled)'}

### Change snapshot (REST)
| Metric | Value |
| --- | --- |
| Files changed | **{len(files)}** |
| Additions | **+{additions}** |
| Deletions | **−{deletions}** |

<details>
<summary>Changed paths</summary>

{file_list}

</details>

### Risk hints
{risk_block}

### CI / checks (REST)
{_format_checks(check_runs)}

### Linked issues (GraphQL)
{_format_linked_issues(linked.get("linked_issues") or [])}

### Review threads (GraphQL)
{_format_threads(linked.get("review_threads") or [])}

---
_Posted by [RepoPulse](https://github.com/KRYPTON0078/repo-pulse) · GitHub App using REST + GraphQL APIs_
"""
