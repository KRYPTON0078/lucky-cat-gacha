"""RepoPulse FastAPI entrypoint: homepage, health, and GitHub webhooks."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app import __version__
from app.config import get_settings
from app.webhook import handle_pull_request_event, verify_signature

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("repopulse")

app = FastAPI(
    title="RepoPulse",
    description="GitHub App that posts structured PR summaries via REST + GraphQL.",
    version=__version__,
)


def _homepage_html() -> str:
    settings = get_settings()
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>RepoPulse — GitHub App</title>
  <style>
    :root {{
      --bg: #0d1117;
      --panel: #161b22;
      --text: #e6edf3;
      --muted: #8b949e;
      --accent: #3fb950;
      --border: #30363d;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", system-ui, sans-serif;
      background:
        radial-gradient(1200px 600px at 10% -10%, #1f6feb33, transparent),
        radial-gradient(900px 500px at 100% 0%, #3fb95022, transparent),
        var(--bg);
      color: var(--text);
      min-height: 100vh;
      line-height: 1.55;
    }}
    main {{
      max-width: 720px;
      margin: 0 auto;
      padding: 3.5rem 1.25rem 4rem;
    }}
    h1 {{
      font-size: clamp(2rem, 4vw, 2.75rem);
      letter-spacing: -0.03em;
      margin: 0 0 0.5rem;
    }}
    .tag {{
      display: inline-block;
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 0.2rem 0.7rem;
      color: var(--muted);
      font-size: 0.85rem;
      margin-bottom: 1rem;
    }}
    p.lead {{ color: var(--muted); font-size: 1.1rem; }}
    section {{
      margin-top: 2rem;
      padding: 1.25rem 1.35rem;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 12px;
    }}
    h2 {{ margin: 0 0 0.75rem; font-size: 1.1rem; }}
    ul {{ margin: 0; padding-left: 1.2rem; color: var(--muted); }}
    a {{ color: var(--accent); }}
    code {{
      background: #0d1117;
      padding: 0.1rem 0.35rem;
      border-radius: 4px;
      font-size: 0.92em;
    }}
    footer {{
      margin-top: 2.5rem;
      color: var(--muted);
      font-size: 0.9rem;
    }}
  </style>
</head>
<body>
  <main>
    <span class="tag">GitHub App · v{__version__}</span>
    <h1>{settings.app_name}</h1>
    <p class="lead">
      Real-time pull request summaries powered by the GitHub REST and GraphQL APIs.
      Install the app, open a PR, and RepoPulse posts a structured change / risk / CI digest.
    </p>
    <section>
      <h2>What it does</h2>
      <ul>
        <li>Listens for <code>pull_request</code> webhooks</li>
        <li>Fetches changed files and check runs via <strong>REST</strong></li>
        <li>Fetches linked issues and review threads via <strong>GraphQL</strong></li>
        <li>Creates or updates a single PR comment with the summary</li>
      </ul>
    </section>
    <section>
      <h2>Works with GitHub</h2>
      <p style="margin:0;color:var(--muted)">
        Built for the
        <a href="https://docs.github.com/en/integrations/concepts/github-developer-program">GitHub Developer Program</a>.
        Source:
        <a href="https://github.com/KRYPTON0078/repo-pulse">KRYPTON0078/repo-pulse</a>.
      </p>
    </section>
    <section>
      <h2>Support</h2>
      <p style="margin:0;color:var(--muted)">
        Questions or issues:
        <a href="mailto:{settings.support_email}">{settings.support_email}</a>
      </p>
    </section>
    <footer>
      Webhook endpoint: <code>POST /webhook</code> · Health: <code>GET /health</code>
    </footer>
  </main>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def homepage() -> HTMLResponse:
    return HTMLResponse(_homepage_html())


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "repopulse", "version": __version__}


@app.post("/webhook")
async def webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None, alias="X-Hub-Signature-256"),
    x_github_event: str | None = Header(default=None, alias="X-GitHub-Event"),
) -> JSONResponse:
    settings = get_settings()
    body = await request.body()

    if not settings.webhook_secret:
        raise HTTPException(status_code=500, detail="WEBHOOK_SECRET is not configured")

    if not verify_signature(settings.webhook_secret, body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()
    event = x_github_event or ""

    if event == "ping":
        return JSONResponse({"status": "pong", "zen": payload.get("zen")})

    if event == "pull_request":
        if not settings.app_id:
            raise HTTPException(status_code=500, detail="APP_ID is not configured")
        try:
            result = await handle_pull_request_event(settings, payload)
        except FileNotFoundError as exc:
            logger.exception("Missing private key")
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001 — surface to operator logs
            logger.exception("Failed to handle pull_request")
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return JSONResponse(result)

    return JSONResponse({"status": "ignored", "event": event})


def run() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    run()
