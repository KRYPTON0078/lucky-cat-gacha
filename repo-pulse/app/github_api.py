"""GitHub REST + GraphQL helpers used by RepoPulse."""

from __future__ import annotations

from typing import Any

import httpx

from app.config import Settings


class GitHubClient:
    def __init__(
        self,
        settings: Settings,
        access_token: str,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings
        self.access_token = access_token
        self._client = client
        self._owns_client = client is None

    async def __aenter__(self) -> GitHubClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("GitHubClient must be used as an async context manager")
        return self._client

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def rest_get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.settings.github_api_base}{path}"
        response = await self.client.get(url, headers=self._headers(), params=params)
        response.raise_for_status()
        return response.json()

    async def rest_post(self, path: str, *, json: dict[str, Any]) -> Any:
        url = f"{self.settings.github_api_base}{path}"
        response = await self.client.post(url, headers=self._headers(), json=json)
        response.raise_for_status()
        return response.json()

    async def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.settings.github_api_base}/graphql"
        payload = {"query": query, "variables": variables or {}}
        response = await self.client.post(url, headers=self._headers(), json=payload)
        response.raise_for_status()
        data = response.json()
        if "errors" in data:
            raise RuntimeError(f"GraphQL errors: {data['errors']}")
        return data["data"]

    async def list_pr_files(self, owner: str, repo: str, pull_number: int) -> list[dict[str, Any]]:
        files: list[dict[str, Any]] = []
        page = 1
        while True:
            batch = await self.rest_get(
                f"/repos/{owner}/{repo}/pulls/{pull_number}/files",
                params={"per_page": 100, "page": page},
            )
            if not batch:
                break
            files.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        return files

    async def list_check_runs(self, owner: str, repo: str, ref: str) -> list[dict[str, Any]]:
        data = await self.rest_get(
            f"/repos/{owner}/{repo}/commits/{ref}/check-runs",
            params={"per_page": 50},
        )
        return list(data.get("check_runs", []))

    async def create_issue_comment(
        self, owner: str, repo: str, issue_number: int, body: str
    ) -> dict[str, Any]:
        return await self.rest_post(
            f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
            json={"body": body},
        )

    async def find_existing_bot_comment(
        self, owner: str, repo: str, issue_number: int, marker: str
    ) -> dict[str, Any] | None:
        comments = await self.rest_get(
            f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
            params={"per_page": 100},
        )
        for comment in comments:
            body = comment.get("body") or ""
            if marker in body:
                return comment
        return None

    async def update_issue_comment(self, owner: str, repo: str, comment_id: int, body: str) -> Any:
        url = f"{self.settings.github_api_base}/repos/{owner}/{repo}/issues/comments/{comment_id}"
        response = await self.client.patch(url, headers=self._headers(), json={"body": body})
        response.raise_for_status()
        return response.json()

    async def linked_issues_and_threads(
        self, owner: str, repo: str, pull_number: int
    ) -> dict[str, Any]:
        query = """
        query($owner: String!, $repo: String!, $number: Int!) {
          repository(owner: $owner, name: $repo) {
            pullRequest(number: $number) {
              title
              body
              closingIssuesReferences(first: 10) {
                nodes {
                  number
                  title
                  url
                  state
                }
              }
              reviewThreads(first: 20) {
                nodes {
                  isResolved
                  comments(first: 1) {
                    nodes {
                      body
                      author { login }
                    }
                  }
                }
              }
            }
          }
        }
        """
        data = await self.graphql(
            query,
            {"owner": owner, "repo": repo, "number": pull_number},
        )
        pr = data["repository"]["pullRequest"]
        return {
            "title": pr.get("title"),
            "body": pr.get("body") or "",
            "linked_issues": pr.get("closingIssuesReferences", {}).get("nodes", []),
            "review_threads": pr.get("reviewThreads", {}).get("nodes", []),
        }
