"""RepoPulse FastAPI entrypoint: homepage, health, setup, and GitHub webhooks."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app import __version__
from app.config import get_settings, reload_settings
from app.manifest import (
    convert_manifest_code,
    persist_app_credentials,
    read_manifest_state,
    setup_form_html,
)
from app.webhook import handle_pull_request_event, verify_signature

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("repopulse")

app = FastAPI(
    title="RepoPulse",
    description="GitHub App that posts structured PR summaries via REST + GraphQL.",
    version=__version__,
)


def _request_base(request: Request) -> str:
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    if host:
        return f"{proto}://{host}"
    return str(request.base_url).rstrip("/")


def _homepage_html(request: Request) -> str:
    settings = get_settings()
    configured = settings.configured
    setup_href = "/setup"
    install_href = f"https://github.com/apps/{settings.app_slug}/installations/new" if settings.app_slug else "/setup"
    status = "configured" if configured else "needs GitHub App registration"
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
    .btn {{
      display: inline-block;
      margin-top: 0.75rem;
      background: #238636;
      color: #fff;
      text-decoration: none;
      padding: 0.55rem 0.9rem;
      border-radius: 8px;
      font-weight: 600;
    }}
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
    <span class="tag">GitHub App · v{__version__} · {status}</span>
    <h1>{settings.app_name}</h1>
    <p class="lead">
      Real-time pull request summaries powered by the GitHub REST and GraphQL APIs.
      Install the app, open a PR, and RepoPulse posts a structured change / risk / CI digest.
    </p>
    <section>
      <h2>Register / install</h2>
      <p style="margin:0 0 .5rem;color:var(--muted)">
        GitHub App names are created from an official Manifest so credentials are stored automatically.
      </p>
      <a class="btn" href="{setup_href}">Create GitHub App</a>
      <a class="btn" href="{install_href}">Install on a repository</a>
      <a class="btn" href="https://github.com/developer/register">Join Developer Program</a>
    </section>
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
        <a href="https://github.com/KRYPTON0078/lucky-cat-gacha/tree/cursor/repo-pulse-github-app-f220/repo-pulse">repo-pulse on GitHub</a>.
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
      Webhook: <code>POST /webhook</code> · Health: <code>GET /health</code> · Status: <code>GET /status</code>
      · Public URL: <code>{_request_base(request)}</code>
    </footer>
  </main>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request) -> HTMLResponse:
    return HTMLResponse(_homepage_html(request))


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "repopulse", "version": __version__}


@app.get("/status")
async def status(request: Request) -> dict[str, object]:
    settings = get_settings()
    return {
        "configured": settings.configured,
        "app_id": settings.app_id or None,
        "app_slug": settings.app_slug or None,
        "support_email": settings.support_email,
        "public_base_url": _request_base(request),
        "install_url": (
            f"https://github.com/apps/{settings.app_slug}/installations/new"
            if settings.app_slug
            else None
        ),
        "developer_program_url": "https://github.com/developer/register",
    }


@app.get("/setup", response_class=HTMLResponse)
async def setup(request: Request) -> HTMLResponse:
    settings = get_settings()
    if settings.configured:
        return HTMLResponse(
            "<html><body style='font-family:system-ui;background:#0d1117;color:#e6edf3;padding:2rem'>"
            "<h1>RepoPulse is already configured</h1>"
            f"<p>App ID {settings.app_id}"
            + (
                f" · <a href='https://github.com/apps/{settings.app_slug}/installations/new'>Install</a>"
                if settings.app_slug
                else ""
            )
            + "</p></body></html>"
        )
    return HTMLResponse(setup_form_html(settings, _request_base(request)))


@app.get("/setup/callback", response_class=HTMLResponse)
async def setup_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> HTMLResponse:
    if error:
        raise HTTPException(status_code=400, detail=error)
    if not code:
        raise HTTPException(status_code=400, detail="Missing manifest conversion code")
    expected = read_manifest_state()
    if expected and state and state != expected:
        raise HTTPException(status_code=400, detail="Invalid setup state")

    settings = get_settings()
    try:
        payload = await convert_manifest_code(code, settings.github_api_base)
        creds = persist_app_credentials(payload, settings)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Manifest conversion failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    slug = creds.get("APP_SLUG") or ""
    install = f"https://github.com/apps/{slug}/installations/new" if slug else "/"
    return HTMLResponse(
        f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>RepoPulse registered</title>
<meta http-equiv="refresh" content="2;url={install}">
</head>
<body style="font-family:system-ui;background:#0d1117;color:#e6edf3;padding:2rem">
  <h1>GitHub App created</h1>
  <p>App ID <strong>{creds["APP_ID"]}</strong> saved. Redirecting to install…</p>
  <p><a href="{install}">Install RepoPulse</a> ·
     <a href="https://github.com/developer/register">Join Developer Program</a></p>
</body></html>
"""
    )


@app.post("/webhook")
async def webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None, alias="X-Hub-Signature-256"),
    x_github_event: str | None = Header(default=None, alias="X-GitHub-Event"),
) -> JSONResponse:
    settings = reload_settings()
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
