"""Tests for Workspace Manager.

Tests the WorkspaceManager for session management and lifecycle.
"""

from __future__ import annotations

import asyncio
from datetime import timedelta
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from framework_m_studio.git.protocol import CommitResult, GitStatus
from framework_m_studio.workspace import (
    WorkspaceInfo,
    WorkspaceManager,
)


class MockGitAdapter:
    """Mock GitAdapter for testing."""

    def __init__(self) -> None:
        self.clone = AsyncMock()
        self.commit = AsyncMock(
            return_value=CommitResult(sha="abc123", message="test", files_changed=1)
        )
        self.push = AsyncMock()
        self.pull = AsyncMock()
        self.create_branch = AsyncMock()
        self.checkout = AsyncMock()
        self.get_status = AsyncMock(
            return_value=GitStatus(
                branch="main",
                is_clean=True,
                modified_files=[],
                staged_files=[],
                untracked_files=[],
            )
        )
        self.get_current_branch = AsyncMock(return_value="main")


class TestWorkspaceManager:
    """Tests for WorkspaceManager class."""

    @pytest.fixture
    def git_adapter(self) -> MockGitAdapter:
        """Create a mock git adapter."""
        return MockGitAdapter()

    @pytest.fixture
    def manager(self, git_adapter: MockGitAdapter, tmp_path: Path) -> WorkspaceManager:
        """Create a WorkspaceManager instance."""
        return WorkspaceManager(
            git_adapter=git_adapter,  # type: ignore
            base_dir=tmp_path,
            session_ttl=timedelta(hours=1),
        )


class TestConnect:
    """Tests for connect operation."""

    @pytest.fixture
    def git_adapter(self) -> MockGitAdapter:
        return MockGitAdapter()

    @pytest.fixture
    def manager(self, git_adapter: MockGitAdapter, tmp_path: Path) -> WorkspaceManager:
        return WorkspaceManager(git_adapter=git_adapter, base_dir=tmp_path)  # type: ignore

    @pytest.mark.asyncio
    async def test_connect_creates_session(
        self, manager: WorkspaceManager, git_adapter: MockGitAdapter
    ) -> None:
        """Test that connect creates a new session."""
        info = await manager.connect(
            repo_url="https://github.com/user/repo.git",
            auth_token="token123",
        )

        assert isinstance(info, WorkspaceInfo)
        assert info.repo_url == "https://github.com/user/repo.git"
        assert info.branch == "main"
        assert info.id is not None

        # Verify git clone was called
        git_adapter.clone.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_with_branch(
        self, manager: WorkspaceManager, git_adapter: MockGitAdapter
    ) -> None:
        """Test connect with specific branch."""
        git_adapter.get_current_branch.return_value = "develop"

        info = await manager.connect(
            repo_url="https://github.com/user/repo.git",
            branch="develop",
        )

        assert info.branch == "develop"

    @pytest.mark.asyncio
    async def test_connect_stores_session(self, manager: WorkspaceManager) -> None:
        """Test that connect stores session in manager."""
        info = await manager.connect(
            repo_url="https://github.com/user/repo.git",
        )

        # Should be able to retrieve session
        retrieved = await manager.get_info(info.id)
        assert retrieved.id == info.id


class TestGetWorkspacePath:
    """Tests for get_workspace_path operation."""

    @pytest.fixture
    def git_adapter(self) -> MockGitAdapter:
        return MockGitAdapter()

    @pytest.fixture
    def manager(self, git_adapter: MockGitAdapter, tmp_path: Path) -> WorkspaceManager:
        return WorkspaceManager(git_adapter=git_adapter, base_dir=tmp_path)  # type: ignore

    @pytest.mark.asyncio
    async def test_get_workspace_path(self, manager: WorkspaceManager) -> None:
        """Test getting workspace path for session."""
        info = await manager.connect(repo_url="https://github.com/user/repo.git")
        path = await manager.get_workspace_path(info.id)

        assert isinstance(path, Path)
        assert info.id in str(path)

    @pytest.mark.asyncio
    async def test_get_workspace_path_not_found(
        self, manager: WorkspaceManager
    ) -> None:
        """Test getting path for non-existent session."""
        with pytest.raises(KeyError):
            await manager.get_workspace_path("non-existent-id")


class TestCommit:
    """Tests for commit operation."""

    @pytest.fixture
    def git_adapter(self) -> MockGitAdapter:
        return MockGitAdapter()

    @pytest.fixture
    def manager(self, git_adapter: MockGitAdapter, tmp_path: Path) -> WorkspaceManager:
        return WorkspaceManager(git_adapter=git_adapter, base_dir=tmp_path)  # type: ignore

    @pytest.mark.asyncio
    async def test_commit_success(
        self, manager: WorkspaceManager, git_adapter: MockGitAdapter
    ) -> None:
        """Test successful commit."""
        info = await manager.connect(
            repo_url="https://github.com/user/repo.git",
            auth_token="token123",
        )

        sha = await manager.commit(info.id, "Test commit message")

        assert sha == "abc123"
        git_adapter.commit.assert_called_once()
        git_adapter.push.assert_called_once()

    @pytest.mark.asyncio
    async def test_commit_without_push(
        self, manager: WorkspaceManager, git_adapter: MockGitAdapter
    ) -> None:
        """Test commit without push."""
        info = await manager.connect(
            repo_url="https://github.com/user/repo.git",
            auth_token="token123",
        )

        sha = await manager.commit(info.id, "Test commit", push=False)

        assert sha == "abc123"
        git_adapter.commit.assert_called_once()
        git_adapter.push.assert_not_called()

    @pytest.mark.asyncio
    async def test_commit_not_found(self, manager: WorkspaceManager) -> None:
        """Test commit for non-existent session."""
        with pytest.raises(KeyError):
            await manager.commit("non-existent-id", "Test")


class TestDisconnect:
    """Tests for disconnect operation."""

    @pytest.fixture
    def git_adapter(self) -> MockGitAdapter:
        return MockGitAdapter()

    @pytest.fixture
    def manager(self, git_adapter: MockGitAdapter, tmp_path: Path) -> WorkspaceManager:
        return WorkspaceManager(git_adapter=git_adapter, base_dir=tmp_path)  # type: ignore

    @pytest.mark.asyncio
    async def test_disconnect_removes_session(self, manager: WorkspaceManager) -> None:
        """Test that disconnect removes session."""
        info = await manager.connect(repo_url="https://github.com/user/repo.git")

        await manager.disconnect(info.id)

        with pytest.raises(KeyError):
            await manager.get_info(info.id)

    @pytest.mark.asyncio
    async def test_disconnect_cleans_directory(
        self, manager: WorkspaceManager, tmp_path: Path
    ) -> None:
        """Test that disconnect cleans up workspace directory."""
        info = await manager.connect(repo_url="https://github.com/user/repo.git")
        workspace_path = await manager.get_workspace_path(info.id)

        # Create workspace dir to simulate clone
        workspace_path.mkdir(parents=True, exist_ok=True)
        (workspace_path / "test.txt").write_text("content")

        await manager.disconnect(info.id)

        assert not workspace_path.exists()


class TestCleanupExpired:
    """Tests for cleanup_expired operation."""

    @pytest.fixture
    def git_adapter(self) -> MockGitAdapter:
        return MockGitAdapter()

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(
        self, git_adapter: MockGitAdapter, tmp_path: Path
    ) -> None:
        """Test cleanup of expired sessions."""
        # Create manager with short TTL
        manager = WorkspaceManager(
            git_adapter=git_adapter,  # type: ignore
            base_dir=tmp_path,
            session_ttl=timedelta(seconds=1),
        )

        info = await manager.connect(repo_url="https://github.com/user/repo.git")

        # Wait for session to expire
        await asyncio.sleep(1.1)

        # Session should now be expired
        cleaned = await manager.cleanup_expired()

        assert cleaned == 1

        with pytest.raises(KeyError):
            await manager.get_info(info.id)


class TestListSessions:
    """Tests for list_sessions operation."""

    @pytest.fixture
    def git_adapter(self) -> MockGitAdapter:
        return MockGitAdapter()

    @pytest.fixture
    def manager(self, git_adapter: MockGitAdapter, tmp_path: Path) -> WorkspaceManager:
        return WorkspaceManager(git_adapter=git_adapter, base_dir=tmp_path)  # type: ignore

    @pytest.mark.asyncio
    async def test_list_empty(self, manager: WorkspaceManager) -> None:
        """Test listing with no sessions."""
        sessions = await manager.list_sessions()
        assert sessions == []

    @pytest.mark.asyncio
    async def test_list_multiple_sessions(self, manager: WorkspaceManager) -> None:
        """Test listing multiple sessions."""
        await manager.connect(repo_url="https://github.com/user/repo1.git")
        await manager.connect(repo_url="https://github.com/user/repo2.git")

        sessions = await manager.list_sessions()

        assert len(sessions) == 2
        urls = {s.repo_url for s in sessions}
        assert "https://github.com/user/repo1.git" in urls
        assert "https://github.com/user/repo2.git" in urls
