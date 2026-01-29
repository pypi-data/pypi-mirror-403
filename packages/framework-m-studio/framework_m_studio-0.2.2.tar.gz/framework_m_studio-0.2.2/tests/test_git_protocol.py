"""Tests for Git Protocol.

Tests the dataclasses and error classes defined in the protocol module.
"""

from __future__ import annotations

import pytest

from framework_m_studio.git.protocol import (
    CommitResult,
    GitAuthError,
    GitConflictError,
    GitError,
    GitNetworkError,
    GitStatus,
)


class TestGitStatus:
    """Tests for GitStatus dataclass."""

    def test_git_status_creation(self) -> None:
        """Test basic GitStatus creation."""
        status = GitStatus(
            branch="main",
            is_clean=True,
        )
        assert status.branch == "main"
        assert status.is_clean is True
        assert status.modified_files == []
        assert status.staged_files == []
        assert status.untracked_files == []
        assert status.ahead == 0
        assert status.behind == 0

    def test_git_status_with_changes(self) -> None:
        """Test GitStatus with file changes."""
        status = GitStatus(
            branch="feature/test",
            is_clean=False,
            modified_files=["file1.py", "file2.py"],
            staged_files=["file3.py"],
            untracked_files=["new.txt"],
            ahead=2,
            behind=1,
        )
        assert status.branch == "feature/test"
        assert status.is_clean is False
        assert len(status.modified_files) == 2
        assert "file1.py" in status.modified_files
        assert len(status.staged_files) == 1
        assert len(status.untracked_files) == 1
        assert status.ahead == 2
        assert status.behind == 1

    def test_git_status_defaults(self) -> None:
        """Test that GitStatus has proper defaults."""
        status = GitStatus(branch="main", is_clean=True)
        # All list fields should default to empty lists
        assert isinstance(status.modified_files, list)
        assert isinstance(status.staged_files, list)
        assert isinstance(status.untracked_files, list)


class TestCommitResult:
    """Tests for CommitResult dataclass."""

    def test_commit_result_creation(self) -> None:
        """Test CommitResult creation."""
        result = CommitResult(
            sha="abc123def456",
            message="feat: add new feature",
            files_changed=3,
        )
        assert result.sha == "abc123def456"
        assert result.message == "feat: add new feature"
        assert result.files_changed == 3

    def test_commit_result_minimal(self) -> None:
        """Test CommitResult with minimal data."""
        result = CommitResult(
            sha="a1b2c3",
            message="fix",
            files_changed=1,
        )
        assert result.sha == "a1b2c3"
        assert result.files_changed == 1


class TestGitError:
    """Tests for GitError and subclasses."""

    def test_git_error_creation(self) -> None:
        """Test basic GitError creation."""
        error = GitError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.returncode == 1  # Default

    def test_git_error_with_returncode(self) -> None:
        """Test GitError with custom returncode."""
        error = GitError("Fatal error", returncode=128)
        assert str(error) == "Fatal error"
        assert error.returncode == 128

    def test_git_auth_error_inheritance(self) -> None:
        """Test GitAuthError inherits from GitError."""
        error = GitAuthError("Authentication failed", returncode=128)
        assert isinstance(error, GitError)
        assert isinstance(error, Exception)
        assert str(error) == "Authentication failed"
        assert error.returncode == 128

    def test_git_conflict_error_inheritance(self) -> None:
        """Test GitConflictError inherits from GitError."""
        error = GitConflictError("Merge conflict in file.py")
        assert isinstance(error, GitError)
        assert str(error) == "Merge conflict in file.py"

    def test_git_network_error_inheritance(self) -> None:
        """Test GitNetworkError inherits from GitError."""
        error = GitNetworkError("Could not resolve host")
        assert isinstance(error, GitError)
        assert str(error) == "Could not resolve host"

    def test_error_can_be_raised(self) -> None:
        """Test that errors can be raised and caught."""
        with pytest.raises(GitError):
            raise GitError("Test error")

        with pytest.raises(GitAuthError):
            raise GitAuthError("Auth failed")

    def test_catch_specific_error(self) -> None:
        """Test catching specific error types."""
        try:
            raise GitAuthError("Auth failed")
        except GitAuthError as e:
            assert "Auth" in str(e)
        except GitError:
            pytest.fail("Should have caught GitAuthError specifically")

    def test_catch_base_error(self) -> None:
        """Test catching base GitError catches all subtypes."""
        errors = [
            GitAuthError("auth"),
            GitConflictError("conflict"),
            GitNetworkError("network"),
        ]
        for error in errors:
            try:
                raise error
            except GitError:
                pass  # Should catch all
            except Exception:
                pytest.fail(f"GitError should catch {type(error).__name__}")
