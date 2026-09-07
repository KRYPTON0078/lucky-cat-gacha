# Joining the GitHub Developer Program with RepoPulse

## Eligibility

From [GitHub Developer Program](https://docs.github.com/en/integrations/concepts/github-developer-program):

1. An integration in production **or development** using the GitHub API
2. A support email — **magnedinanevesdina@gmail.com**

## Automated path

```bash
bash scripts/bootstrap.sh
```

This starts FastAPI and a public HTTPS tunnel, then:

1. Open the printed **SETUP** URL while signed into GitHub
2. Confirm the App Manifest (one GitHub screen)
3. Callback `/setup/callback` stores `APP_ID`, `WEBHOOK_SECRET`, and `private-key.pem`
4. Redirect installs the app on a repository
5. Register at https://github.com/developer/register

Register form values:

- Name: **RepoPulse**
- URL: the public homepage from bootstrap, or this GitHub tree
- Email: **magnedinanevesdina@gmail.com**

GitHub does not expose an API to create personal repositories or to submit Developer Program membership. Those two GitHub website steps still require a logged-in GitHub session.

## Logo

https://github.com/logos
