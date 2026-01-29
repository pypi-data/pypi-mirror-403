"""GitHub Provider for Studio Cloud Mode.

Provides GitHub-specific API operations like creating pull requests,
managing branches, and repository operations using the GitHub REST API.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


@dataclass
class PullRequest:
    """GitHub Pull Request data."""

    number: int
    """PR number."""

    title: str
    """PR title."""

    url: str
    """Web URL to the PR."""

    state: str
    """PR state: open, closed, merged."""

    head_branch: str
    """Source branch name."""

    base_branch: str
    """Target branch name."""


@dataclass
class Repository:
    """GitHub Repository data."""

    full_name: str
    """Full repo name (owner/repo)."""

    default_branch: str
    """Default branch name."""

    clone_url: str
    """HTTPS clone URL."""

    private: bool
    """Whether the repo is private."""


class GitHubError(Exception):
    """GitHub API error."""

    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code


class GitHubAuthError(GitHubError):
    """Authentication failed."""

    pass


class GitHubProvider:
    """GitHub API provider.

    Provides GitHub-specific operations using the REST API.
    Uses personal access tokens for authentication.
    """

    API_BASE = "https://api.github.com"

    def __init__(self, token: str):
        """Initialize GitHubProvider.

        Args:
            token: GitHub personal access token.
        """
        self._token = token

    def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated request to GitHub API.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE).
            endpoint: API endpoint (e.g., /repos/owner/repo).
            data: Request body data.

        Returns:
            Response JSON as dict.

        Raises:
            GitHubError: If request fails.
        """
        url = urljoin(self.API_BASE, endpoint)
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        body = None
        if data:
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = Request(url, data=body, headers=headers, method=method)

        try:
            with urlopen(request, timeout=30) as response:
                response_body = response.read().decode("utf-8")
                if response_body:
                    result: dict[str, Any] = json.loads(response_body)
                    return result
                return {}
        except HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            if e.code == 401:
                raise GitHubAuthError(
                    f"Authentication failed: {error_body}", e.code
                ) from e
            raise GitHubError(f"GitHub API error: {error_body}", e.code) from e

    def get_repository(self, owner: str, repo: str) -> Repository:
        """Get repository information.

        Args:
            owner: Repository owner (user or org).
            repo: Repository name.

        Returns:
            Repository data.
        """
        data = self._request("GET", f"/repos/{owner}/{repo}")
        return Repository(
            full_name=data["full_name"],
            default_branch=data["default_branch"],
            clone_url=data["clone_url"],
            private=data["private"],
        )

    def create_branch(
        self,
        owner: str,
        repo: str,
        branch_name: str,
        from_ref: str = "HEAD",
    ) -> str:
        """Create a new branch.

        Args:
            owner: Repository owner.
            repo: Repository name.
            branch_name: New branch name.
            from_ref: Base reference (branch, tag, or SHA).

        Returns:
            The created ref name.
        """
        # Get the SHA of the base ref
        ref_data = self._request(
            "GET", f"/repos/{owner}/{repo}/git/ref/heads/{from_ref}"
        )
        sha = ref_data["object"]["sha"]

        # Create new branch
        self._request(
            "POST",
            f"/repos/{owner}/{repo}/git/refs",
            data={"ref": f"refs/heads/{branch_name}", "sha": sha},
        )
        return f"refs/heads/{branch_name}"

    def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        head: str,
        base: str,
        body: str = "",
        draft: bool = False,
    ) -> PullRequest:
        """Create a pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            title: PR title.
            head: Source branch.
            base: Target branch.
            body: PR description.
            draft: Create as draft PR.

        Returns:
            Created PullRequest.
        """
        data = self._request(
            "POST",
            f"/repos/{owner}/{repo}/pulls",
            data={
                "title": title,
                "head": head,
                "base": base,
                "body": body,
                "draft": draft,
            },
        )
        return PullRequest(
            number=data["number"],
            title=data["title"],
            url=data["html_url"],
            state=data["state"],
            head_branch=data["head"]["ref"],
            base_branch=data["base"]["ref"],
        )

    def get_pull_request(
        self,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> PullRequest:
        """Get a pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pr_number: PR number.

        Returns:
            PullRequest data.
        """
        data = self._request("GET", f"/repos/{owner}/{repo}/pulls/{pr_number}")
        return PullRequest(
            number=data["number"],
            title=data["title"],
            url=data["html_url"],
            state=data["state"],
            head_branch=data["head"]["ref"],
            base_branch=data["base"]["ref"],
        )

    def list_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        head: str | None = None,
    ) -> list[PullRequest]:
        """List pull requests.

        Args:
            owner: Repository owner.
            repo: Repository name.
            state: Filter by state (open, closed, all).
            head: Filter by head branch (owner:branch).

        Returns:
            List of PullRequests.
        """
        endpoint = f"/repos/{owner}/{repo}/pulls?state={state}"
        if head:
            endpoint += f"&head={head}"

        data = self._request("GET", endpoint)
        # data is a list of dicts, but mypy sees it as dict[str, Any]
        if not isinstance(data, list):
            return []
        return [
            PullRequest(
                number=int(pr["number"])
                if isinstance(pr.get("number"), (int, str))
                else 0,
                title=str(pr["title"]) if "title" in pr else "",
                url=str(pr["html_url"]) if "html_url" in pr else "",
                state=str(pr["state"]) if "state" in pr else "",
                head_branch=str(pr["head"]["ref"])
                if "head" in pr and "ref" in pr["head"]
                else "",
                base_branch=str(pr["base"]["ref"])
                if "base" in pr and "ref" in pr["base"]
                else "",
            )
            for pr in data
        ]

    def get_authenticated_user(self) -> dict[str, Any]:
        """Get the authenticated user.

        Returns:
            User data including login, name, email.
        """
        return self._request("GET", "/user")

    def validate_token(self) -> bool:
        """Validate the access token.

        Returns:
            True if token is valid.

        Raises:
            GitHubAuthError: If token is invalid.
        """
        try:
            self.get_authenticated_user()
            return True
        except GitHubAuthError:
            return False
