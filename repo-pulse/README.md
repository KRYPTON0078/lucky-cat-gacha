# RepoPulse

**GitHub App** that posts structured pull-request summaries using the GitHub **REST** and **GraphQL** APIs.

Built as a real integration for the [GitHub Developer Program](https://docs.github.com/en/integrations/concepts/github-developer-program).

<p align="center">
  <img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" alt="Works with GitHub" width="64" />
</p>

<p align="center"><em>Works with GitHub</em> — logo usage per <a href="https://github.com/logos">github.com/logos</a></p>

## What it does

When a pull request is opened, reopened, synchronized, or marked ready for review, RepoPulse:

1. Authenticates as a GitHub App (JWT → installation access token)
2. Loads changed files and check runs via **REST**
3. Loads closing-linked issues and review threads via **GraphQL**
4. Creates or updates a single PR comment with a change / risk / CI digest

```text
GitHub webhook (pull_request)
        │
        ▼
   RepoPulse (FastAPI)
        │
        ├─ REST  /pulls/{n}/files
        ├─ REST  /commits/{sha}/check-runs
        ├─ GraphQL linked issues + review threads
        └─ REST  issue comment create/update
```

## Support

**Email:** set `SUPPORT_EMAIL` in `.env` (also shown on `GET /`).  
Default placeholder in `.env.example`: `you@example.com` — replace with an address GitHub users can reach.

## Quick start (development)

### 1. Clone and install

```bash
git clone https://github.com/KRYPTON0078/repo-pulse.git
cd repo-pulse
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Register a GitHub App (manual)

Open [github.com/settings/apps/new](https://github.com/settings/apps/new) and configure:

| Field | Value |
| --- | --- |
| Homepage URL | `https://github.com/KRYPTON0078/repo-pulse` |
| Webhook URL | `https://<public-tunnel>/webhook` |
| Webhook secret | any strong secret → `WEBHOOK_SECRET` |
| Pull requests | Read & write |
| Checks | Read-only |
| Metadata | Read-only |
| Issues | Read-only |
| Events | **Pull request** |

Then:

- Copy **App ID** → `APP_ID`
- Generate and download a **private key** → `private-key.pem`
- Install the app on a test repository

Print the full checklist anytime:

```bash
bash scripts/register-checklist.sh
```

### 3. Configure environment

```bash
cp .env.example .env
# edit APP_ID, WEBHOOK_SECRET, PRIVATE_KEY_PATH, SUPPORT_EMAIL
```

### 4. Run the server + tunnel

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

In another terminal, expose HTTPS (example with ngrok):

```bash
ngrok http 8000
```

Point the GitHub App webhook at `https://<ngrok-host>/webhook`.

### 5. Verify

- `GET /health` → `{"status":"ok",...}`
- `GET /` → product page with support email
- Open a PR on an installed repo → RepoPulse posts a summary comment

## Docker

```bash
docker build -t repopulse .
docker run --rm -p 8000:8000 \
  -e APP_ID=... \
  -e WEBHOOK_SECRET=... \
  -e SUPPORT_EMAIL=you@example.com \
  -e PRIVATE_KEY_PATH=/secrets/private-key.pem \
  -v "$PWD/private-key.pem:/secrets/private-key.pem:ro" \
  repopulse
```

## Project layout

```text
app/
  main.py          # FastAPI: /, /health, /webhook
  config.py        # env settings
  github_auth.py   # App JWT + installation token
  github_api.py    # REST + GraphQL client
  pr_summary.py    # comment markdown builder
  webhook.py       # signature verify + PR handler
scripts/
  register-checklist.sh
  gen-dev-key.sh
tests/
  test_core.py
```

## Join the GitHub Developer Program

Membership needs:

1. An integration in production **or development** using the GitHub API ← RepoPulse
2. A support email where users can contact you ← `SUPPORT_EMAIL`

Register here: **[https://github.com/developer/register](https://github.com/developer/register)**

Use the repo URL or your deployed homepage as the integration URL.

## License

MIT
