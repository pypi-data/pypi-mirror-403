"""Tests for Git Adapter.

Tests the GitAdapter implementation using mock subprocess calls.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from framework_m_studio.git.adapter import GitAdapter
from framework_m_studio.git.protocol import (
    CommitResult,
    GitAuthError,
    GitError,
    GitNetworkError,
    GitStatus,
)


class TestGitAdapter:
    """Tests for GitAdapter class."""

    @pytest.fixture
    def adapter(self) -> GitAdapter:
        """Create a GitAdapter instance."""
        return GitAdapter()

    @pytest.fixture
    def mock_process(self) -> MagicMock:
        """Create a mock subprocess."""
        proc = MagicMock()
        proc.returncode = 0
        proc.communicate = AsyncMock(return_value=(b"output", b""))
        return proc


class TestClone:
    """Tests for clone operation."""

    @pytest.fixture
    def adapter(self) -> GitAdapter:
        return GitAdapter()

    @pytest.mark.asyncio
    async def test_clone_basic(self, adapter: GitAdapter, tmp_path: Path) -> None:
        """Test basic clone operation."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            proc = MagicMock()
            proc.returncode = 0
            proc.communicate = AsyncMock(return_value=(b"", b""))
            mock_exec.return_value = proc

            target = tmp_path / "repo"
            await adapter.clone("https://github.com/user/repo.git", target)

            # Verify git clone was called
            mock_exec.assert_called_once()
            call_args = mock_exec.call_args[0]
            assert call_args[0] == "git"
            assert "clone" in call_args
            assert str(target) in call_args

    @pytest.mark.asyncio
    async def test_clone_with_branch(self, adapter: GitAdapter, tmp_path: Path) -> None:
        """Test clone with specific branch."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            proc = MagicMock()
            proc.returncode = 0
            proc.communicate = AsyncMock(return_value=(b"", b""))
            mock_exec.return_value = proc

            target = tmp_path / "repo"
            await adapter.clone(
                "https://github.com/user/repo.git",
                target,
                branch="develop",
            )

            call_args = mock_exec.call_args[0]
            assert "--branch" in call_args
            assert "develop" in call_args

    @pytest.mark.asyncio
    async def test_clone_with_token(self, adapter: GitAdapter, tmp_path: Path) -> None:
        """Test clone with auth token."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            proc = MagicMock()
            proc.returncode = 0
            proc.communicate = AsyncMock(return_value=(b"", b""))
            mock_exec.return_value = proc

            target = tmp_path / "repo"
            await adapter.clone(
                "https://github.com/user/repo.git",
                target,
                auth_token="ghp_secret123",
            )

            call_args = mock_exec.call_args[0]
            # Token should be embedded in URL
            url_arg = next(a for a in call_args if "github.com" in a)
            assert "ghp_secret123@github.com" in url_arg

    @pytest.mark.asyncio
    async def test_clone_auth_error(self, adapter: GitAdapter, tmp_path: Path) -> None:
        """Test clone with authentication failure."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            proc = MagicMock()
            proc.returncode = 128
            proc.communicate = AsyncMock(
                return_value=(b"", b"fatal: Authentication failed")
            )
            mock_exec.return_value = proc

            target = tmp_path / "repo"
            with pytest.raises(GitAuthError):
                await adapter.clone("https://github.com/user/repo.git", target)


class TestCommit:
    """Tests for commit operation."""

    @pytest.fixture
    def adapter(self) -> GitAdapter:
        return GitAdapter()

    @pytest.mark.asyncio
    async def test_commit_success(self, adapter: GitAdapter, tmp_path: Path) -> None:
        """Test successful commit."""
        call_count = 0

        async def mock_communicate() -> tuple[bytes, bytes]:
            nonlocal call_count
            call_count += 1
            responses: dict[int, tuple[bytes, bytes]] = {
                1: (b"", b""),  # git add
                2: (b"M file.py", b""),  # git status
                3: (b"", b""),  # git commit
            }
            return responses.get(
                call_count, (b"abc123def456", b"")
            )  # default: rev-parse

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            proc = MagicMock()
            proc.returncode = 0
            proc.communicate = mock_communicate
            mock_exec.return_value = proc

            result = await adapter.commit(tmp_path, "Test commit")

            assert isinstance(result, CommitResult)
            assert result.sha == "abc123def456"
            assert result.message == "Test commit"

    @pytest.mark.asyncio
    async def test_commit_no_changes(self, adapter: GitAdapter, tmp_path: Path) -> None:
        """Test commit with no changes."""
        call_count = 0

        async def mock_communicate() -> tuple[bytes, bytes]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # git add
                return b"", b""
            else:  # git status (empty)
                return b"", b""

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            proc = MagicMock()
            proc.returncode = 0
            proc.communicate = mock_communicate
            mock_exec.return_value = proc

            with pytest.raises(GitError, match="No changes to commit"):
                await adapter.commit(tmp_path, "Test commit")


class TestPush:
    """Tests for push operation."""

    @pytest.fixture
    def adapter(self) -> GitAdapter:
        return GitAdapter()

    @pytest.mark.asyncio
    async def test_push_basic(self, adapter: GitAdapter, tmp_path: Path) -> None:
        """Test basic push operation."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            proc = MagicMock()
            proc.returncode = 0
            proc.communicate = AsyncMock(return_value=(b"", b""))
            mock_exec.return_value = proc

            await adapter.push(tmp_path)

            # Verify git push was called
            mock_exec.assert_called_once()
            call_args = mock_exec.call_args[0]
            assert call_args[0] == "git"
            assert "push" in call_args

    @pytest.mark.asyncio
    async def test_push_with_branch(self, adapter: GitAdapter, tmp_path: Path) -> None:
        """Test push with specific branch."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            proc = MagicMock()
            proc.returncode = 0
            proc.communicate = AsyncMock(return_value=(b"", b""))
            mock_exec.return_value = proc

            await adapter.push(tmp_path, branch="feature")

            call_args = mock_exec.call_args[0]
            assert "origin" in call_args
            assert "feature" in call_args

    @pytest.mark.asyncio
    async def test_push_force(self, adapter: GitAdapter, tmp_path: Path) -> None:
        """Test force push."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            proc = MagicMock()
            proc.returncode = 0
            proc.communicate = AsyncMock(return_value=(b"", b""))
            mock_exec.return_value = proc

            await adapter.push(tmp_path, force=True)

            call_args = mock_exec.call_args[0]
            assert "--force-with-lease" in call_args

    @pytest.mark.asyncio
    async def test_push_auth_error(self, adapter: GitAdapter, tmp_path: Path) -> None:
        """Test push with authentication failure."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            proc = MagicMock()
            proc.returncode = 128
            proc.communicate = AsyncMock(
                return_value=(b"", b"fatal: Authentication failed")
            )
            mock_exec.return_value = proc

            with pytest.raises(GitAuthError):
                await adapter.push(tmp_path)


class TestGetStatus:
    """Tests for get_status operation."""

    @pytest.fixture
    def adapter(self) -> GitAdapter:
        return GitAdapter()

    @pytest.mark.asyncio
    async def test_clean_status(self, adapter: GitAdapter, tmp_path: Path) -> None:
        """Test status with clean working directory."""
        call_count = 0

        async def mock_communicate() -> tuple[bytes, bytes]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # rev-parse --abbrev-ref HEAD
                return b"main", b""
            elif call_count == 2:  # status --porcelain
                return b"", b""
            else:  # rev-list
                return b"0\t0", b""

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            proc = MagicMock()
            proc.returncode = 0
            proc.communicate = mock_communicate
            mock_exec.return_value = proc

            status = await adapter.get_status(tmp_path)

            assert isinstance(status, GitStatus)
            assert status.branch == "main"
            assert status.is_clean is True
            assert status.modified_files == []

    @pytest.mark.asyncio
    async def test_dirty_status(self, adapter: GitAdapter, tmp_path: Path) -> None:
        """Test status with modified files."""
        call_count = 0

        async def mock_communicate() -> tuple[bytes, bytes]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # rev-parse --abbrev-ref HEAD
                return b"feature", b""
            elif call_count == 2:  # status --porcelain
                # Format: XY filename (XY is 2 chars, then space, then filename)
                # "MM" = modified in both index and worktree
                # " M" = modified in worktree only
                # "A " = added to index
                # "??" = untracked
                return b"MM file1.py\nA  file2.py\n?? new.txt", b""
            else:  # rev-list
                return b"2\t1", b""

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            proc = MagicMock()
            proc.returncode = 0
            proc.communicate = mock_communicate
            mock_exec.return_value = proc

            status = await adapter.get_status(tmp_path)

            assert status.branch == "feature"
            assert status.is_clean is False
            # MM means modified in both staging and worktree
            assert "file1.py" in status.modified_files
            assert "file1.py" in status.staged_files
            assert "file2.py" in status.staged_files
            assert "new.txt" in status.untracked_files


class TestTokenEmbedding:
    """Tests for URL token embedding."""

    @pytest.fixture
    def adapter(self) -> GitAdapter:
        return GitAdapter()

    def test_embed_token_https(self, adapter: GitAdapter) -> None:
        """Test token embedding in HTTPS URL."""
        url = "https://github.com/user/repo.git"
        result = adapter._embed_token_in_url(url, "token123")
        assert result == "https://token123@github.com/user/repo.git"

    def test_embed_token_ssh(self, adapter: GitAdapter) -> None:
        """Test token embedding skipped for SSH URL."""
        url = "git@github.com:user/repo.git"
        result = adapter._embed_token_in_url(url, "token123")
        # SSH URLs should remain unchanged
        assert result == url


class TestErrorClassification:
    """Tests for error classification."""

    @pytest.fixture
    def adapter(self) -> GitAdapter:
        return GitAdapter()

    def test_auth_error(self, adapter: GitAdapter) -> None:
        """Test authentication error classification."""
        error = adapter._classify_error("fatal: Authentication failed", 128)
        assert isinstance(error, GitAuthError)

    def test_network_error(self, adapter: GitAdapter) -> None:
        """Test network error classification."""
        error = adapter._classify_error("Could not resolve host: github.com", 128)
        assert isinstance(error, GitNetworkError)

    def test_generic_error(self, adapter: GitAdapter) -> None:
        """Test generic error classification."""
        error = adapter._classify_error("Some other error", 1)
        assert isinstance(error, GitError)
        assert not isinstance(error, GitAuthError)
        assert not isinstance(error, GitNetworkError)
