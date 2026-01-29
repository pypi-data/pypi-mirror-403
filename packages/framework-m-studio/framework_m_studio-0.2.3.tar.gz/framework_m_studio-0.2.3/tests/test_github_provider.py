"""Tests for GitHub Provider.

Tests the GitHubProvider class with mocked HTTP responses.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from framework_m_studio.git.github_provider import (
    GitHubAuthError,
    GitHubError,
    GitHubProvider,
    PullRequest,
    Repository,
)

# Patch location: where urlopen is used, not where it's defined
URLOPEN_PATCH = "framework_m_studio.git.github_provider.urlopen"


class TestGitHubProvider:
    """Tests for GitHubProvider class."""

    @pytest.fixture
    def provider(self) -> GitHubProvider:
        """Create a GitHubProvider instance."""
        return GitHubProvider(token="ghp_test_token_123")


class TestGetRepository:
    """Tests for get_repository operation."""

    @pytest.fixture
    def provider(self) -> GitHubProvider:
        return GitHubProvider(token="ghp_test_token")

    def test_get_repository_success(self, provider: GitHubProvider) -> None:
        """Test successful repository fetch."""
        mock_response = {
            "full_name": "owner/repo",
            "default_branch": "main",
            "clone_url": "https://github.com/owner/repo.git",
            "private": False,
        }

        with patch(URLOPEN_PATCH) as mock_urlopen:
            mock_fp = MagicMock()
            mock_fp.read.return_value = json.dumps(mock_response).encode()
            mock_fp.__enter__ = MagicMock(return_value=mock_fp)
            mock_fp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_fp

            repo = provider.get_repository("owner", "repo")

            assert isinstance(repo, Repository)
            assert repo.full_name == "owner/repo"
            assert repo.default_branch == "main"
            assert repo.clone_url == "https://github.com/owner/repo.git"
            assert repo.private is False


class TestCreatePullRequest:
    """Tests for create_pull_request operation."""

    @pytest.fixture
    def provider(self) -> GitHubProvider:
        return GitHubProvider(token="ghp_test_token")

    def test_create_pull_request_success(self, provider: GitHubProvider) -> None:
        """Test successful PR creation."""
        mock_response = {
            "number": 42,
            "title": "feat: new feature",
            "html_url": "https://github.com/owner/repo/pull/42",
            "state": "open",
            "head": {"ref": "feature-branch"},
            "base": {"ref": "main"},
        }

        with patch(URLOPEN_PATCH) as mock_urlopen:
            mock_fp = MagicMock()
            mock_fp.read.return_value = json.dumps(mock_response).encode()
            mock_fp.__enter__ = MagicMock(return_value=mock_fp)
            mock_fp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_fp

            pr = provider.create_pull_request(
                owner="owner",
                repo="repo",
                title="feat: new feature",
                head="feature-branch",
                base="main",
            )

            assert isinstance(pr, PullRequest)
            assert pr.number == 42
            assert pr.title == "feat: new feature"
            assert pr.url == "https://github.com/owner/repo/pull/42"
            assert pr.state == "open"
            assert pr.head_branch == "feature-branch"
            assert pr.base_branch == "main"


class TestGetPullRequest:
    """Tests for get_pull_request operation."""

    @pytest.fixture
    def provider(self) -> GitHubProvider:
        return GitHubProvider(token="ghp_test_token")

    def test_get_pull_request_success(self, provider: GitHubProvider) -> None:
        """Test successful PR fetch."""
        mock_response = {
            "number": 42,
            "title": "feat: new feature",
            "html_url": "https://github.com/owner/repo/pull/42",
            "state": "open",
            "head": {"ref": "feature-branch"},
            "base": {"ref": "main"},
        }

        with patch(URLOPEN_PATCH) as mock_urlopen:
            mock_fp = MagicMock()
            mock_fp.read.return_value = json.dumps(mock_response).encode()
            mock_fp.__enter__ = MagicMock(return_value=mock_fp)
            mock_fp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_fp

            pr = provider.get_pull_request("owner", "repo", 42)

            assert pr.number == 42
            assert pr.state == "open"


class TestListPullRequests:
    """Tests for list_pull_requests operation."""

    @pytest.fixture
    def provider(self) -> GitHubProvider:
        return GitHubProvider(token="ghp_test_token")

    def test_list_pull_requests_success(self, provider: GitHubProvider) -> None:
        """Test successful PR list."""
        mock_response = [
            {
                "number": 1,
                "title": "PR 1",
                "html_url": "https://github.com/owner/repo/pull/1",
                "state": "open",
                "head": {"ref": "feature-1"},
                "base": {"ref": "main"},
            },
            {
                "number": 2,
                "title": "PR 2",
                "html_url": "https://github.com/owner/repo/pull/2",
                "state": "open",
                "head": {"ref": "feature-2"},
                "base": {"ref": "main"},
            },
        ]

        with patch(URLOPEN_PATCH) as mock_urlopen:
            mock_fp = MagicMock()
            mock_fp.read.return_value = json.dumps(mock_response).encode()
            mock_fp.__enter__ = MagicMock(return_value=mock_fp)
            mock_fp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_fp

            prs = provider.list_pull_requests("owner", "repo")

            assert len(prs) == 2
            assert prs[0].number == 1
            assert prs[1].number == 2


class TestValidateToken:
    """Tests for validate_token operation."""

    @pytest.fixture
    def provider(self) -> GitHubProvider:
        return GitHubProvider(token="ghp_test_token")

    def test_validate_token_success(self, provider: GitHubProvider) -> None:
        """Test token validation success."""
        mock_response = {"login": "testuser", "name": "Test User"}

        with patch(URLOPEN_PATCH) as mock_urlopen:
            mock_fp = MagicMock()
            mock_fp.read.return_value = json.dumps(mock_response).encode()
            mock_fp.__enter__ = MagicMock(return_value=mock_fp)
            mock_fp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_fp

            assert provider.validate_token() is True


class TestDataClasses:
    """Tests for data classes."""

    def test_pull_request_creation(self) -> None:
        """Test PullRequest dataclass."""
        pr = PullRequest(
            number=42,
            title="Test PR",
            url="https://github.com/owner/repo/pull/42",
            state="open",
            head_branch="feature",
            base_branch="main",
        )
        assert pr.number == 42
        assert pr.title == "Test PR"

    def test_repository_creation(self) -> None:
        """Test Repository dataclass."""
        repo = Repository(
            full_name="owner/repo",
            default_branch="main",
            clone_url="https://github.com/owner/repo.git",
            private=True,
        )
        assert repo.full_name == "owner/repo"
        assert repo.private is True


class TestErrors:
    """Tests for error classes."""

    def test_github_error(self) -> None:
        """Test GitHubError creation."""
        error = GitHubError("API error", status_code=500)
        assert str(error) == "API error"
        assert error.status_code == 500

    def test_github_auth_error(self) -> None:
        """Test GitHubAuthError inheritance."""
        error = GitHubAuthError("Unauthorized", status_code=401)
        assert isinstance(error, GitHubError)
        assert error.status_code == 401
