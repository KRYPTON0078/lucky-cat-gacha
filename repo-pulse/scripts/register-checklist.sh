#!/usr/bin/env bash
# Print the checklist for GitHub App + Developer Program registration.
set -euo pipefail
cat <<'EOF'
RepoPulse — registration checklist
==================================

1) Create the GitHub App (manual UI)
   https://github.com/settings/apps/new

   Suggested values:
   - GitHub App name: RepoPulse (or RepoPulse-<yourhandle>)
   - Homepage URL: https://github.com/KRYPTON0078/repo-pulse
   - Callback URL: http://localhost:8000/  (dev)
   - Webhook URL: https://<your-tunnel>/webhook
   - Webhook secret: same value as WEBHOOK_SECRET in .env
   - Permissions:
       Pull requests: Read & write
       Checks: Read-only
       Metadata: Read-only
       Issues: Read-only
   - Subscribe to events: Pull request
   - Where can this GitHub App be installed?: Only on this account (dev) or Any account

2) After create
   - Note the App ID → APP_ID in .env
   - Generate a private key → save as private-key.pem → PRIVATE_KEY_PATH
   - Install the app on a test repository

3) Run locally with a tunnel
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env   # fill APP_ID, WEBHOOK_SECRET, SUPPORT_EMAIL
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   # separate terminal:
   ngrok http 8000   # or cloudflared tunnel --url http://localhost:8000
   # paste the HTTPS URL + /webhook into the App webhook settings

4) Verify
   Open a PR on the installed repo → RepoPulse posts/updates a summary comment
   GET /health → {"status":"ok",...}
   GET / → product homepage with support email

5) Join the GitHub Developer Program
   https://github.com/developer/register
   Provide:
   - Integration name: RepoPulse
   - Integration URL: repo README or deployed homepage
   - Support email: the SUPPORT_EMAIL you configured

Logo guidelines: https://github.com/logos
Program docs: https://docs.github.com/en/integrations/concepts/github-developer-program
EOF
