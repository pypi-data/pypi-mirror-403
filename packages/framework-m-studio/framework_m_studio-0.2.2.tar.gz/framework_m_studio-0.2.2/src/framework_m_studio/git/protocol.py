"""Git Adapter Protocol.

Defines the interface for Git operations following Hexagonal Architecture.
The core logic depends on this protocol, not on specific implementations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass
class GitStatus:
    """Status of a Git workspace."""

    branch: str
    """Current branch name."""

    is_clean: bool
    """True if working directory has no changes."""

    modified_files: list[str] = field(default_factory=list)
    """List of modified file paths relative to workspace root."""

    staged_files: list[str] = field(default_factory=list)
    """List of staged file paths."""

    untracked_files: list[str] = field(default_factory=list)
    """List of untracked file paths."""

    ahead: int = 0
    """Number of commits ahead of remote."""

    behind: int = 0
    """Number of commits behind remote."""


@dataclass
class CommitResult:
    """Result of a commit operation."""

    sha: str
    """The commit SHA."""

    message: str
    """The commit message."""

    files_changed: int
    """Number of files changed in this commit."""


class GitAdapterProtocol(Protocol):
    """Port for Git operations.

    Implementations can use git CLI, dulwich, gitpython, etc.
    This protocol abstracts the Git implementation details.
    """

    async def clone(
        self,
        repo_url: str,
        target_dir: Path,
        *,
        auth_token: str | None = None,
        branch: str | None = None,
    ) -> None:
        """Clone a repository to the target directory.

        Args:
            repo_url: The repository URL (HTTPS or SSH).
            target_dir: Local path to clone into.
            auth_token: Personal access token for HTTPS auth.
            branch: Specific branch to clone (default: default branch).

        Raises:
            GitError: If clone fails (auth, network, etc.).
        """
        ...

    async def commit(
        self,
        workspace: Path,
        message: str,
        *,
        author: str | None = None,
    ) -> CommitResult:
        """Stage all changes and create a commit.

        Args:
            workspace: Path to the Git workspace.
            message: Commit message.
            author: Author string (default: from git config).

        Returns:
            CommitResult with SHA and metadata.

        Raises:
            GitError: If commit fails or no changes to commit.
        """
        ...

    async def push(
        self,
        workspace: Path,
        branch: str | None = None,
        *,
        force: bool = False,
    ) -> None:
        """Push commits to remote.

        Args:
            workspace: Path to the Git workspace.
            branch: Branch to push (default: current branch).
            force: Force push (use with caution).

        Raises:
            GitError: If push fails (auth, conflicts, etc.).
        """
        ...

    async def pull(
        self,
        workspace: Path,
        *,
        rebase: bool = True,
    ) -> None:
        """Pull latest changes from remote.

        Args:
            workspace: Path to the Git workspace.
            rebase: If True, use --rebase (default).

        Raises:
            GitError: If pull fails (conflicts, etc.).
        """
        ...

    async def create_branch(
        self,
        workspace: Path,
        name: str,
        *,
        checkout: bool = True,
    ) -> None:
        """Create a new branch.

        Args:
            workspace: Path to the Git workspace.
            name: Branch name.
            checkout: If True, switch to the new branch.

        Raises:
            GitError: If branch creation fails.
        """
        ...

    async def checkout(
        self,
        workspace: Path,
        ref: str,
    ) -> None:
        """Checkout a branch or commit.

        Args:
            workspace: Path to the Git workspace.
            ref: Branch name, tag, or commit SHA.

        Raises:
            GitError: If checkout fails.
        """
        ...

    async def get_status(
        self,
        workspace: Path,
    ) -> GitStatus:
        """Get the current status of the workspace.

        Args:
            workspace: Path to the Git workspace.

        Returns:
            GitStatus with branch info and file changes.
        """
        ...

    async def get_current_branch(
        self,
        workspace: Path,
    ) -> str:
        """Get the name of the current branch.

        Args:
            workspace: Path to the Git workspace.

        Returns:
            Branch name.
        """
        ...

    async def fetch(
        self,
        workspace: Path,
    ) -> None:
        """Fetch updates from remote without merging.

        Used to check for available updates (Updates Available indicator).

        Args:
            workspace: Path to the Git workspace.

        Raises:
            GitError: If fetch fails (auth, network, etc.).
        """
        ...


class GitError(Exception):
    """Base exception for Git operations."""

    def __init__(self, message: str, returncode: int = 1):
        """Initialize GitError.

        Args:
            message: Error description.
            returncode: Git command exit code.
        """
        super().__init__(message)
        self.returncode = returncode


class GitAuthError(GitError):
    """Authentication failed."""

    pass


class GitConflictError(GitError):
    """Merge/rebase conflict occurred."""

    pass


class GitNetworkError(GitError):
    """Network-related error (timeout, DNS, etc.)."""

    pass
