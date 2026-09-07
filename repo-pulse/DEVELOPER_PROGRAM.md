# Joining the GitHub Developer Program with RepoPulse

This document is the operator guide for turning RepoPulse into a registered Developer Program membership.

## Eligibility (current docs)

From [GitHub Developer Program](https://docs.github.com/en/integrations/concepts/github-developer-program):

1. An integration in **production or development** that uses the GitHub API
2. An email address where GitHub users can contact you for support

RepoPulse satisfies (1). Set `SUPPORT_EMAIL` for (2).

## Step A — Publish this repository

If `KRYPTON0078/repo-pulse` does not exist yet:

```bash
cd repo-pulse
gh repo create KRYPTON0078/repo-pulse --public --source=. --remote=origin --push
```

Or create an empty repo in the GitHub UI, then:

```bash
git remote add origin https://github.com/KRYPTON0078/repo-pulse.git
git push -u origin main
```

## Step B — Register the GitHub App

1. Open https://github.com/settings/apps/new
2. Fill fields using `bash scripts/register-checklist.sh`
3. Permissions: Pull requests (R/W), Checks (R), Metadata (R), Issues (R)
4. Event: Pull request
5. Save App ID + webhook secret + private key into `.env`
6. Install the app on one of your repositories

## Step C — Run in development

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
# tunnel, e.g. ngrok http 8000
# set webhook URL to https://<host>/webhook
```

Open a PR → confirm the RepoPulse summary comment appears.

## Step D — Register for the program

1. Go to https://github.com/developer/register
2. Integration name: **RepoPulse**
3. Integration URL: `https://github.com/KRYPTON0078/repo-pulse` (or your deployed homepage)
4. Support email: the same address as `SUPPORT_EMAIL`

## Spreading the word (optional)

- Use the Octocat / GitHub logo per https://github.com/logos
- Blog or short demo video of a PR receiving a RepoPulse comment
