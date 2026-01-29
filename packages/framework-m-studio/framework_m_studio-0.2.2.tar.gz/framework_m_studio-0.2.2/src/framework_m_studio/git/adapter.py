"""Git Adapter Implementation.

Uses the `git` CLI via asyncio subprocess for all Git operations.
No external Python dependencies (gitpython, dulwich) required.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from .protocol import (
    CommitResult,
    GitAdapterProtocol,
    GitAuthError,
    GitConflictError,
    GitError,
    GitNetworkError,
    GitStatus,
)


class GitAdapter:
    """Git adapter using the git CLI.

    Implements GitAdapterProtocol using asyncio subprocess to call git commands.
    This approach has no Python dependencies and works with any git version.
    """

    def __init__(self, git_binary: str = "git"):
        """Initialize GitAdapter.

        Args:
            git_binary: Path to git binary (default: "git" from PATH).
        """
        self.git_binary = git_binary

    async def _run_git(
        self,
        args: list[str],
        cwd: Path | None = None,
        *,
        check: bool = True,
        env: dict[str, str] | None = None,
    ) -> tuple[str, str]:
        """Run a git command asynchronously.

        Args:
            args: Git command arguments (without 'git' prefix).
            cwd: Working directory for the command.
            check: If True, raise GitError on non-zero exit.
            env: Additional environment variables.

        Returns:
            Tuple of (stdout, stderr).

        Raises:
            GitError: If command fails and check=True.
        """
        import os

        full_env = os.environ.copy()
        if env:
            full_env.update(env)

        # Disable interactive prompts
        full_env["GIT_TERMINAL_PROMPT"] = "0"

        proc = await asyncio.create_subprocess_exec(
            self.git_binary,
            *args,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=full_env,
        )

        stdout, stderr = await proc.communicate()
        stdout_str = stdout.decode("utf-8", errors="replace").strip()
        stderr_str = stderr.decode("utf-8", errors="replace").strip()

        if check and proc.returncode != 0:
            error_msg = stderr_str or stdout_str or "Unknown git error"
            raise self._classify_error(error_msg, proc.returncode or 0)

        return stdout_str, stderr_str

    def _classify_error(self, message: str, returncode: int) -> GitError:
        """Classify a git error into a specific exception type."""
        lower_msg = message.lower()

        if "authentication" in lower_msg or "permission denied" in lower_msg:
            return GitAuthError(message, returncode)
        if "conflict" in lower_msg or "merge conflict" in lower_msg:
            return GitConflictError(message, returncode)
        if (
            "could not resolve host" in lower_msg
            or "connection refused" in lower_msg
            or "network" in lower_msg
        ):
            return GitNetworkError(message, returncode)

        return GitError(message, returncode)

    def _embed_token_in_url(self, url: str, token: str) -> str:
        """Embed auth token in HTTPS URL.

        Converts: https://github.com/user/repo.git
        To:       https://token@github.com/user/repo.git
        """
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return url  # SSH URLs don't use token embedding

        # Replace or add username with token
        netloc = f"{token}@{parsed.hostname}"
        if parsed.port:
            netloc += f":{parsed.port}"

        return urlunparse(parsed._replace(netloc=netloc))

    async def clone(
        self,
        repo_url: str,
        target_dir: Path,
        *,
        auth_token: str | None = None,
        branch: str | None = None,
    ) -> None:
        """Clone a repository to the target directory."""
        url = repo_url
        if auth_token:
            url = self._embed_token_in_url(repo_url, auth_token)

        args = ["clone", "--depth", "1"]  # Shallow clone for speed
        if branch:
            args.extend(["--branch", branch])
        args.extend([url, str(target_dir)])

        await self._run_git(args)

    async def commit(
        self,
        workspace: Path,
        message: str,
        *,
        author: str | None = None,
    ) -> CommitResult:
        """Stage all changes and create a commit."""
        # Stage all changes
        await self._run_git(["add", "-A"], cwd=workspace)

        # Check if there's anything to commit
        status_out, _ = await self._run_git(
            ["status", "--porcelain"], cwd=workspace, check=False
        )
        if not status_out:
            raise GitError("No changes to commit", 0)

        # Count files
        files_changed = len(status_out.strip().split("\n"))

        # Build commit command
        args = ["commit", "-m", message]
        if author:
            args.extend(["--author", author])

        await self._run_git(args, cwd=workspace)

        # Get commit SHA
        sha, _ = await self._run_git(["rev-parse", "HEAD"], cwd=workspace)

        return CommitResult(sha=sha, message=message, files_changed=files_changed)

    async def push(
        self,
        workspace: Path,
        branch: str | None = None,
        *,
        force: bool = False,
    ) -> None:
        """Push commits to remote."""
        args = ["push"]
        if force:
            args.append("--force-with-lease")
        if branch:
            args.extend(["origin", branch])

        await self._run_git(args, cwd=workspace)

    async def pull(
        self,
        workspace: Path,
        *,
        rebase: bool = True,
    ) -> None:
        """Pull latest changes from remote."""
        args = ["pull"]
        if rebase:
            args.append("--rebase")

        await self._run_git(args, cwd=workspace)

    async def create_branch(
        self,
        workspace: Path,
        name: str,
        *,
        checkout: bool = True,
    ) -> None:
        """Create a new branch."""
        if checkout:
            await self._run_git(["checkout", "-b", name], cwd=workspace)
        else:
            await self._run_git(["branch", name], cwd=workspace)

    async def checkout(
        self,
        workspace: Path,
        ref: str,
    ) -> None:
        """Checkout a branch or commit."""
        await self._run_git(["checkout", ref], cwd=workspace)

    async def get_status(
        self,
        workspace: Path,
    ) -> GitStatus:
        """Get the current status of the workspace."""
        # Get current branch
        branch = await self.get_current_branch(workspace)

        # Get status
        status_out, _ = await self._run_git(
            ["status", "--porcelain"], cwd=workspace, check=False
        )

        modified: list[str] = []
        staged: list[str] = []
        untracked: list[str] = []

        for line in status_out.split("\n"):
            if not line:
                continue
            status_code = line[:2]
            filepath = line[3:]

            if status_code[0] == "?":
                untracked.append(filepath)
            elif status_code[0] != " ":
                staged.append(filepath)

            if status_code[1] == "M":
                modified.append(filepath)

        is_clean = not (modified or staged or untracked)

        # Get ahead/behind counts
        ahead, behind = await self._get_ahead_behind(workspace, branch)

        return GitStatus(
            branch=branch,
            is_clean=is_clean,
            modified_files=modified,
            staged_files=staged,
            untracked_files=untracked,
            ahead=ahead,
            behind=behind,
        )

    async def get_current_branch(
        self,
        workspace: Path,
    ) -> str:
        """Get the name of the current branch."""
        branch, _ = await self._run_git(
            ["rev-parse", "--abbrev-ref", "HEAD"], cwd=workspace
        )
        return branch

    async def _get_ahead_behind(self, workspace: Path, branch: str) -> tuple[int, int]:
        """Get number of commits ahead/behind remote."""
        try:
            out, _ = await self._run_git(
                ["rev-list", "--left-right", "--count", f"origin/{branch}...HEAD"],
                cwd=workspace,
                check=False,
            )
            if out:
                parts = out.split()
                if len(parts) == 2:
                    behind = int(parts[0])
                    ahead = int(parts[1])
                    return ahead, behind
        except (ValueError, GitError):
            pass
        return 0, 0

    async def fetch(
        self,
        workspace: Path,
    ) -> None:
        """Fetch updates from remote without merging."""
        await self._run_git(["fetch", "--quiet"], cwd=workspace)


# Type assertion to verify protocol compliance
_: GitAdapterProtocol = GitAdapter()
