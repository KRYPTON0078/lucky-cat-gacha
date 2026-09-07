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

**Email:** `magnedinanevesdina@gmail.com` (override with `SUPPORT_EMAIL`). Shown on `GET /`.

## Automated setup

```bash
cd repo-pulse
bash scripts/bootstrap.sh
# open the printed SETUP URL while logged into GitHub
# GitHub confirms the App Manifest → RepoPulse stores App ID, webhook secret, and PEM
# you are redirected to install the app on a repository
```

Then join the program at [github.com/developer/register](https://github.com/developer/register) with:

- Integration: **RepoPulse**
- URL: this repo or the public homepage from bootstrap
- Support email: `magnedinanevesdina@gmail.com`

Manual field-by-field App creation is still documented in `scripts/register-checklist.sh`.

## Docker

```bash
docker build -t repopulse .
docker run --rm -p 8000:8000 \
  -e APP_ID=... \
  -e WEBHOOK_SECRET=... \
  -e SUPPORT_EMAIL=magnedinanevesdina@gmail.com \
  -e PRIVATE_KEY_PATH=/secrets/private-key.pem \
  -v "$PWD/private-key.pem:/secrets/private-key.pem:ro" \
  repopulse
```

## Project layout

```text
app/
  main.py          # FastAPI: /, /health, /status, /setup, /webhook
  config.py        # env settings
  github_auth.py   # App JWT + installation token
  github_api.py    # REST + GraphQL client
  pr_summary.py    # comment markdown builder
  webhook.py       # signature verify + PR handler
  manifest.py      # GitHub App Manifest create + credential save
scripts/
  bootstrap.sh     # server + public HTTPS tunnel
  register-checklist.sh
  gen-dev-key.sh
tests/
  test_core.py
  test_manifest.py
```

## Join the GitHub Developer Program

Membership needs:

1. An integration in production **or development** using the GitHub API ← RepoPulse
2. A support email where users can contact you ← `SUPPORT_EMAIL`

Register here: **[https://github.com/developer/register](https://github.com/developer/register)**

Use the repo URL or your deployed homepage as the integration URL.

## License

MIT
