"""GitHub API adapter.

Implements GitHubProtocol using httpx for the GitHub REST API.
"""

from __future__ import annotations

import asyncio
import base64
import os
from datetime import datetime
from typing import Any

import httpx

from ._exceptions import (
    AuthenticationError,
    FileNotFoundError,
    GitHubAPIError,
    PRNotFoundError,
    RateLimitedError,
    RepoNotFoundError,
)
from ._types import (
    CodeSearchResult,
    Commit,
    CommitAuthor,
    FileContent,
    PullRequest,
    PullRequestUser,
    RepoInfo,
    TreeEntry,
)

# GitHub API base URL
GITHUB_API_BASE = "https://api.github.com"


class GitHubAdapter:
    """GitHub API adapter implementing GitHubProtocol.

    Uses httpx.AsyncClient for efficient HTTP requests with:
    - Automatic rate limit handling with exponential backoff
    - Token authentication from environment or constructor
    - Connection pooling for performance

    Example:
        ```python
        # Use token from environment
        adapter = GitHubAdapter()

        # Or provide token explicitly
        adapter = GitHubAdapter(token="ghp_...")

        # Use the adapter
        repo = await adapter.get_repo("facebook", "react")
        print(repo.description)
        ```
    """

    def __init__(
        self,
        token: str | None = None,
        base_url: str = GITHUB_API_BASE,
        max_retries: int = 3,
    ) -> None:
        """Initialize the adapter.

        Args:
            token: GitHub personal access token. Falls back to GITHUB_TOKEN env var.
            base_url: GitHub API base URL (for GitHub Enterprise).
            max_retries: Maximum retries for rate-limited requests.
        """
        self._token = token or os.environ.get("GITHUB_TOKEN")
        self._base_url = base_url.rstrip("/")
        self._max_retries = max_retries
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            headers: dict[str, str] = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "bond-agent/0.1",
            }
            if self._token:
                headers["Authorization"] = f"Bearer {self._token}"

            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers=headers,
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Make an API request with rate limit handling.

        Args:
            method: HTTP method.
            path: API path.
            params: Query parameters.

        Returns:
            Parsed JSON response.

        Raises:
            GitHubError: On API errors.
        """
        client = await self._get_client()
        retries = 0

        while True:
            response = await client.request(method, path, params=params)

            # Handle rate limiting
            if response.status_code == 403:
                remaining = response.headers.get("X-RateLimit-Remaining", "0")
                if remaining == "0":
                    if retries >= self._max_retries:
                        reset_at = response.headers.get("X-RateLimit-Reset")
                        raise RateLimitedError(int(reset_at) if reset_at else None)

                    # Exponential backoff
                    wait_time = 2**retries
                    await asyncio.sleep(wait_time)
                    retries += 1
                    continue

            # Handle authentication errors
            if response.status_code == 401:
                raise AuthenticationError()

            # Handle not found
            if response.status_code == 404:
                return {"_status": 404}

            # Handle other errors
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    message = error_data.get("message", "Unknown error")
                except Exception:
                    message = response.text or "Unknown error"
                raise GitHubAPIError(response.status_code, message)

            return response.json()  # type: ignore[no-any-return]

    def _parse_datetime(self, value: str | None) -> datetime:
        """Parse ISO 8601 datetime string."""
        if not value:
            return datetime.min
        # Handle Z suffix and remove microseconds if present
        value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value)

    async def get_repo(self, owner: str, repo: str) -> RepoInfo:
        """Get repository metadata."""
        data = await self._request("GET", f"/repos/{owner}/{repo}")

        if isinstance(data, dict) and data.get("_status") == 404:
            raise RepoNotFoundError(owner, repo)

        if not isinstance(data, dict):
            raise GitHubAPIError(500, "Unexpected response format")

        return RepoInfo(
            owner=data["owner"]["login"],
            name=data["name"],
            full_name=data["full_name"],
            description=data.get("description"),
            default_branch=data["default_branch"],
            topics=tuple(data.get("topics", [])),
            language=data.get("language"),
            stars=data.get("stargazers_count", 0),
            forks=data.get("forks_count", 0),
            is_private=data.get("private", False),
            created_at=self._parse_datetime(data.get("created_at")),
            updated_at=self._parse_datetime(data.get("updated_at")),
        )

    async def list_tree(
        self,
        owner: str,
        repo: str,
        path: str = "",
        ref: str | None = None,
    ) -> list[TreeEntry]:
        """List directory contents at path."""
        # Build the path
        api_path = f"/repos/{owner}/{repo}/contents/{path.lstrip('/')}"
        params: dict[str, str] = {}
        if ref:
            params["ref"] = ref

        data = await self._request("GET", api_path, params=params or None)

        if isinstance(data, dict) and data.get("_status") == 404:
            raise FileNotFoundError(owner, repo, path)

        # Single file returns dict, directory returns list
        if isinstance(data, dict):
            # It's a file, not a directory
            return [
                TreeEntry(
                    path=data["path"],
                    name=data["name"],
                    type=data["type"],
                    size=data.get("size"),
                    sha=data["sha"],
                )
            ]

        return [
            TreeEntry(
                path=item["path"],
                name=item["name"],
                type=item["type"],
                size=item.get("size"),
                sha=item["sha"],
            )
            for item in data
        ]

    async def get_file(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: str | None = None,
    ) -> FileContent:
        """Read file content."""
        api_path = f"/repos/{owner}/{repo}/contents/{path.lstrip('/')}"
        params: dict[str, str] = {}
        if ref:
            params["ref"] = ref

        data = await self._request("GET", api_path, params=params or None)

        if isinstance(data, dict) and data.get("_status") == 404:
            raise FileNotFoundError(owner, repo, path)

        if not isinstance(data, dict):
            raise GitHubAPIError(500, "Unexpected response format")

        if data.get("type") != "file":
            raise GitHubAPIError(400, f"Path is not a file: {path}")

        # Decode base64 content
        content = data.get("content", "")
        encoding = data.get("encoding", "base64")

        if encoding == "base64":
            # GitHub returns base64 with newlines
            content = base64.b64decode(content.replace("\n", "")).decode("utf-8")

        return FileContent(
            path=data["path"],
            content=content,
            encoding=encoding,
            size=data.get("size", 0),
            sha=data["sha"],
        )

    async def search_code(
        self,
        query: str,
        owner: str | None = None,
        repo: str | None = None,
        limit: int = 10,
    ) -> list[CodeSearchResult]:
        """Search code within repository or across GitHub."""
        # Build search query
        search_query = query
        if owner and repo:
            search_query = f"{query} repo:{owner}/{repo}"
        elif owner:
            search_query = f"{query} user:{owner}"

        params = {
            "q": search_query,
            "per_page": str(min(limit, 100)),
        }

        # Request text matches
        headers = {"Accept": "application/vnd.github.text-match+json"}
        client = await self._get_client()

        response = await client.request(
            "GET",
            "/search/code",
            params=params,
            headers=headers,
        )

        if response.status_code == 403:
            raise RateLimitedError()
        if response.status_code >= 400:
            raise GitHubAPIError(response.status_code, response.text)

        data = response.json()
        items = data.get("items", [])

        return [
            CodeSearchResult(
                path=item["path"],
                repository=item["repository"]["full_name"],
                html_url=item["html_url"],
                text_matches=tuple(
                    match.get("fragment", "") for match in item.get("text_matches", [])
                ),
            )
            for item in items
        ]

    async def get_commits(
        self,
        owner: str,
        repo: str,
        path: str | None = None,
        ref: str | None = None,
        limit: int = 10,
    ) -> list[Commit]:
        """Get recent commits for file or repository."""
        params: dict[str, str] = {
            "per_page": str(min(limit, 100)),
        }
        if path:
            params["path"] = path
        if ref:
            params["sha"] = ref

        data = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/commits",
            params=params,
        )

        if isinstance(data, dict) and data.get("_status") == 404:
            raise RepoNotFoundError(owner, repo)

        if not isinstance(data, list):
            raise GitHubAPIError(500, "Unexpected response format")

        return [
            Commit(
                sha=item["sha"],
                message=item["commit"]["message"],
                author=CommitAuthor(
                    name=item["commit"]["author"]["name"],
                    email=item["commit"]["author"]["email"],
                    date=self._parse_datetime(item["commit"]["author"]["date"]),
                ),
                committer=CommitAuthor(
                    name=item["commit"]["committer"]["name"],
                    email=item["commit"]["committer"]["email"],
                    date=self._parse_datetime(item["commit"]["committer"]["date"]),
                ),
                html_url=item["html_url"],
            )
            for item in data
        ]

    async def get_pr(
        self,
        owner: str,
        repo: str,
        number: int,
    ) -> PullRequest:
        """Get pull request details by number."""
        data = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/pulls/{number}",
        )

        if isinstance(data, dict) and data.get("_status") == 404:
            raise PRNotFoundError(owner, repo, number)

        if not isinstance(data, dict):
            raise GitHubAPIError(500, "Unexpected response format")

        return PullRequest(
            number=data["number"],
            title=data["title"],
            body=data.get("body"),
            state=data["state"],
            user=PullRequestUser(
                login=data["user"]["login"],
                html_url=data["user"]["html_url"],
            ),
            html_url=data["html_url"],
            created_at=self._parse_datetime(data.get("created_at")),
            updated_at=self._parse_datetime(data.get("updated_at")),
            merged_at=self._parse_datetime(data.get("merged_at"))
            if data.get("merged_at")
            else None,
            base_branch=data["base"]["ref"],
            head_branch=data["head"]["ref"],
        )
