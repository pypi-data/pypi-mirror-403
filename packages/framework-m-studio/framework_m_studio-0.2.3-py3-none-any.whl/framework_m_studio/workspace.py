"""Workspace Manager for Studio Cloud Mode.

Manages ephemeral Git workspaces - cloning repos to temporary directories
and tracking sessions for the Studio UI.
"""

from __future__ import annotations

import asyncio
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .git.protocol import GitAdapterProtocol


@dataclass
class WorkspaceSession:
    """Represents an active workspace session."""

    id: str
    """Unique session identifier."""

    repo_url: str
    """Original repository URL (without embedded token)."""

    workspace_path: Path
    """Local path to the cloned repository."""

    created_at: datetime
    """When the session was created."""

    last_accessed: datetime
    """When the session was last accessed."""

    branch: str = "main"
    """Current working branch."""

    auth_token: str | None = None
    """Stored auth token for push operations."""


@dataclass
class WorkspaceInfo:
    """Public workspace info (safe to return to client)."""

    id: str
    repo_url: str
    branch: str
    created_at: datetime
    last_accessed: datetime


class WorkspaceManager:
    """Manages ephemeral Git workspaces.

    Handles the lifecycle of Git workspace sessions:
    - Connect: Clone repo to temp directory
    - Access: Get workspace path for editing
    - Commit: Commit and push changes
    - Disconnect: Cleanup workspace

    Sessions are stored in-memory (suitable for singleton deployment).
    """

    DEFAULT_TTL = timedelta(hours=4)
    """Default session TTL before cleanup."""

    def __init__(
        self,
        git_adapter: GitAdapterProtocol,
        base_dir: Path | None = None,
        session_ttl: timedelta | None = None,
    ):
        """Initialize WorkspaceManager.

        Args:
            git_adapter: Git adapter for operations.
            base_dir: Base directory for workspaces (default: system temp).
            session_ttl: Session TTL before cleanup.
        """
        self._git = git_adapter
        self._base_dir = base_dir or Path(tempfile.gettempdir())
        self._session_ttl = session_ttl or self.DEFAULT_TTL
        self._sessions: dict[str, WorkspaceSession] = {}
        self._lock = asyncio.Lock()

    async def connect(
        self,
        repo_url: str,
        auth_token: str | None = None,
        branch: str | None = None,
    ) -> WorkspaceInfo:
        """Clone a repository and create a workspace session.

        Args:
            repo_url: Repository URL to clone.
            auth_token: Personal access token for authentication.
            branch: Branch to checkout (default: default branch).

        Returns:
            WorkspaceInfo with session ID and metadata.

        Raises:
            GitError: If clone fails.
        """
        session_id = str(uuid.uuid4())
        workspace_path = self._base_dir / f"workspace_{session_id}"

        # Clone the repository
        await self._git.clone(
            repo_url,
            workspace_path,
            auth_token=auth_token,
            branch=branch,
        )

        # Get actual branch name
        actual_branch = await self._git.get_current_branch(workspace_path)

        now = datetime.now(UTC)
        session = WorkspaceSession(
            id=session_id,
            repo_url=repo_url,
            workspace_path=workspace_path,
            created_at=now,
            last_accessed=now,
            branch=actual_branch,
            auth_token=auth_token,
        )

        async with self._lock:
            self._sessions[session_id] = session

        return self._to_info(session)

    async def get_workspace_path(self, session_id: str) -> Path:
        """Get the local path for a workspace.

        Args:
            session_id: Session identifier.

        Returns:
            Path to the workspace directory.

        Raises:
            KeyError: If session not found.
        """
        session = await self._get_session(session_id)
        return session.workspace_path

    async def get_info(self, session_id: str) -> WorkspaceInfo:
        """Get workspace info.

        Args:
            session_id: Session identifier.

        Returns:
            WorkspaceInfo with session metadata.

        Raises:
            KeyError: If session not found.
        """
        session = await self._get_session(session_id)
        return self._to_info(session)

    async def commit(
        self,
        session_id: str,
        message: str,
        *,
        push: bool = True,
    ) -> str:
        """Commit changes in a workspace.

        Args:
            session_id: Session identifier.
            message: Commit message.
            push: If True, push after commit.

        Returns:
            Commit SHA.

        Raises:
            KeyError: If session not found.
            GitError: If commit/push fails.
        """
        session = await self._get_session(session_id)

        result = await self._git.commit(session.workspace_path, message)

        if push and session.auth_token:
            await self._git.push(session.workspace_path, session.branch)

        return result.sha

    async def pull(self, session_id: str) -> None:
        """Pull latest changes for a workspace.

        Args:
            session_id: Session identifier.

        Raises:
            KeyError: If session not found.
            GitError: If pull fails.
        """
        session = await self._get_session(session_id)
        await self._git.pull(session.workspace_path)

    async def create_branch(
        self,
        session_id: str,
        branch_name: str,
    ) -> None:
        """Create and checkout a new branch.

        Args:
            session_id: Session identifier.
            branch_name: Name for the new branch.

        Raises:
            KeyError: If session not found.
            GitError: If branch creation fails.
        """
        session = await self._get_session(session_id)
        await self._git.create_branch(session.workspace_path, branch_name)
        session.branch = branch_name

    async def disconnect(self, session_id: str) -> None:
        """Cleanup a workspace session.

        Args:
            session_id: Session identifier.

        Raises:
            KeyError: If session not found.
        """
        async with self._lock:
            session = self._sessions.pop(session_id, None)

        if session and session.workspace_path.exists():
            shutil.rmtree(session.workspace_path, ignore_errors=True)

    async def cleanup_expired(self) -> int:
        """Remove expired sessions.

        Returns:
            Number of sessions cleaned up.
        """
        now = datetime.now(UTC)
        expired: list[str] = []

        async with self._lock:
            for session_id, session in self._sessions.items():
                if now - session.last_accessed > self._session_ttl:
                    expired.append(session_id)

        for session_id in expired:
            await self.disconnect(session_id)

        return len(expired)

    async def list_sessions(self) -> list[WorkspaceInfo]:
        """List all active sessions.

        Returns:
            List of WorkspaceInfo for all sessions.
        """
        async with self._lock:
            return [self._to_info(s) for s in self._sessions.values()]

    async def _get_session(self, session_id: str) -> WorkspaceSession:
        """Get and update session last_accessed."""
        async with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Workspace session '{session_id}' not found")

            session = self._sessions[session_id]
            session.last_accessed = datetime.now(UTC)
            return session

    def _to_info(self, session: WorkspaceSession) -> WorkspaceInfo:
        """Convert session to public info (without token)."""
        return WorkspaceInfo(
            id=session.id,
            repo_url=session.repo_url,
            branch=session.branch,
            created_at=session.created_at,
            last_accessed=session.last_accessed,
        )
