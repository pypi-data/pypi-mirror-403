"""Git operations for twshtd."""

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

_log = logging.getLogger(__name__)


@dataclass
class GitResult:
    """Result of a git operation."""

    repo_path: Path
    operation: str  # "cleanup", "pull", "fetch"
    success: bool
    message: str
    changes: str | None = None  # git status --porcelain output


@dataclass
class RepoStatus:
    """Comprehensive status of a repository."""

    repo_path: Path
    exists: bool
    is_git_repo: bool
    dirty: bool  # Has uncommitted changes (staged or unstaged)
    behind: int  # Commits behind remote
    ahead: int  # Commits ahead of remote
    untracked: int  # Untracked files count
    error: str | None = None
    fetch_failed: bool = False  # True if fetch was attempted but failed


class GitOperations:
    """Git operations for a single repository."""

    def __init__(self, repo_path: Path) -> None:
        """Initialize GitOperations for a repository."""
        self.repo_path = repo_path

    def _run_git(
        self, *args: str, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        """Run a git command in the repository directory."""
        _log.debug("Running: git %s (in %s)", " ".join(args), self.repo_path)
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=check,
        )
        if result.stdout.strip():
            _log.debug("stdout: %s", result.stdout.strip()[:200])
        if result.stderr.strip():
            _log.debug("stderr: %s", result.stderr.strip()[:200])
        return result

    def _get_status_porcelain(self) -> str:
        """Get git status --porcelain output."""
        result = self._run_git("status", "--porcelain", check=False)
        return result.stdout.strip()

    def _has_changes(self) -> bool:
        """Check if there are uncommitted changes."""
        return bool(self._get_status_porcelain())

    def _add_and_commit(self) -> tuple[bool, str, str | None]:
        """
        Add all changes and commit with status as message.

        Returns:
            Tuple of (committed, message, changes)
        """
        # Stage all changes
        self._run_git("add", ".", check=False)

        # Get status for commit message
        status = self._get_status_porcelain()
        if not status:
            return False, "No changes to commit", None

        # Commit with status as message
        try:
            self._run_git("commit", "-m", status)
            return True, f"Committed: {status}", status
        except subprocess.CalledProcessError as e:
            return False, f"Commit failed: {e.stderr}", None

    def cleanup(self) -> GitResult:
        """
        Git cleanup: add, commit (with status as message), push.

        Returns:
            GitResult with operation outcome
        """
        if not self.repo_path.exists():
            return GitResult(
                repo_path=self.repo_path,
                operation="cleanup",
                success=False,
                message=f"Repository does not exist: {self.repo_path}",
            )

        messages = []
        changes = None

        # Add and commit
        committed, commit_msg, commit_changes = self._add_and_commit()
        messages.append(commit_msg)
        if commit_changes:
            changes = commit_changes
        commit_failed = commit_msg.startswith("Commit failed:")

        # Push (still attempt even if commit failed, to push any existing commits)
        try:
            result = self._run_git("push")
            messages.append("Pushed to remote")
            return GitResult(
                repo_path=self.repo_path,
                operation="cleanup",
                success=not commit_failed,
                message="; ".join(messages),
                changes=changes,
            )
        except subprocess.CalledProcessError as e:
            messages.append(f"Push failed: {e.stderr.strip()}")
            return GitResult(
                repo_path=self.repo_path,
                operation="cleanup",
                success=False,
                message="; ".join(messages),
                changes=changes,
            )

    def pull(self) -> GitResult:
        """
        Git pull: add, commit (with status as message), pull.

        Returns:
            GitResult with operation outcome
        """
        if not self.repo_path.exists():
            return GitResult(
                repo_path=self.repo_path,
                operation="pull",
                success=False,
                message=f"Repository does not exist: {self.repo_path}",
            )

        messages = []
        changes = None

        # Add and commit first
        committed, commit_msg, commit_changes = self._add_and_commit()
        messages.append(commit_msg)
        if commit_changes:
            changes = commit_changes
        commit_failed = commit_msg.startswith("Commit failed:")

        # Pull (still attempt even if commit failed)
        try:
            result = self._run_git("pull")
            pull_output = result.stdout.strip()
            if "Already up to date" in pull_output:
                messages.append("Already up to date")
            else:
                messages.append("Pulled from remote")
            return GitResult(
                repo_path=self.repo_path,
                operation="pull",
                success=not commit_failed,
                message="; ".join(messages),
                changes=changes,
            )
        except subprocess.CalledProcessError as e:
            messages.append(f"Pull failed: {e.stderr.strip()}")
            return GitResult(
                repo_path=self.repo_path,
                operation="pull",
                success=False,
                message="; ".join(messages),
                changes=changes,
            )

    def fetch(self) -> GitResult:
        """
        Git fetch: add, commit (with status as message), fetch, show diff.

        Returns:
            GitResult with operation outcome, changes includes diff info
        """
        if not self.repo_path.exists():
            return GitResult(
                repo_path=self.repo_path,
                operation="fetch",
                success=False,
                message=f"Repository does not exist: {self.repo_path}",
            )

        messages = []
        changes = None

        # Add and commit first
        committed, commit_msg, commit_changes = self._add_and_commit()
        messages.append(commit_msg)
        if commit_changes:
            changes = commit_changes
        commit_failed = commit_msg.startswith("Commit failed:")

        # Fetch (still attempt even if commit failed)
        try:
            self._run_git("fetch")
            messages.append("Fetched from remote")

            # Show changed files in origin/main
            try:
                diff_result = self._run_git(
                    "diff", "--name-only", "origin/main", check=False
                )
                diff_output = diff_result.stdout.strip()
                if diff_output:
                    messages.append(f"Changed in origin/main: {diff_output}")
                    if changes:
                        changes += f"\n\nRemote changes:\n{diff_output}"
                    else:
                        changes = f"Remote changes:\n{diff_output}"
                else:
                    messages.append("No differences from origin/main")
            except subprocess.CalledProcessError:
                messages.append("Could not diff with origin/main")

            return GitResult(
                repo_path=self.repo_path,
                operation="fetch",
                success=not commit_failed,
                message="; ".join(messages),
                changes=changes,
            )
        except subprocess.CalledProcessError as e:
            messages.append(f"Fetch failed: {e.stderr.strip()}")
            return GitResult(
                repo_path=self.repo_path,
                operation="fetch",
                success=False,
                message="; ".join(messages),
                changes=changes,
            )

    def get_status(self, fetch_first: bool = True) -> RepoStatus:
        """
        Get comprehensive repository status.

        Args:
            fetch_first: Whether to run git fetch before checking remote status

        Returns:
            RepoStatus with dirty, behind, ahead, untracked counts
        """
        # Check if path exists
        if not self.repo_path.exists():
            return RepoStatus(
                repo_path=self.repo_path,
                exists=False,
                is_git_repo=False,
                dirty=False,
                behind=0,
                ahead=0,
                untracked=0,
                error=f"Path does not exist: {self.repo_path}",
            )

        # Check if it's a git repo
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            return RepoStatus(
                repo_path=self.repo_path,
                exists=True,
                is_git_repo=False,
                dirty=False,
                behind=0,
                ahead=0,
                untracked=0,
                error="Not a git repository",
            )

        # Fetch from remote first if requested
        fetch_failed = False
        if fetch_first:
            try:
                result = self._run_git("fetch", check=False)
                if result.returncode != 0:
                    fetch_failed = True
            except subprocess.CalledProcessError:
                fetch_failed = True

        # Get status porcelain for dirty and untracked counts
        status_output = self._get_status_porcelain()
        status_lines = status_output.split("\n") if status_output else []

        # Count untracked files (lines starting with "??")
        untracked = sum(1 for line in status_lines if line.startswith("??"))

        # Dirty = any non-untracked changes (staged or unstaged)
        dirty = any(line and not line.startswith("??") for line in status_lines)

        # Get behind/ahead counts from upstream
        behind = 0
        ahead = 0
        try:
            # Get commits behind upstream
            result = self._run_git(
                "rev-list", "--count", "HEAD..@{upstream}", check=False
            )
            if result.returncode == 0 and result.stdout.strip():
                behind = int(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError):
            pass  # No upstream or parse error

        try:
            # Get commits ahead of upstream
            result = self._run_git(
                "rev-list", "--count", "@{upstream}..HEAD", check=False
            )
            if result.returncode == 0 and result.stdout.strip():
                ahead = int(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError):
            pass  # No upstream or parse error

        return RepoStatus(
            repo_path=self.repo_path,
            exists=True,
            is_git_repo=True,
            dirty=dirty,
            behind=behind,
            ahead=ahead,
            untracked=untracked,
            fetch_failed=fetch_failed,
        )
