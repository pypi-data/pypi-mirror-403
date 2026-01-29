"""Git manager for handling git operations."""

from pathlib import Path
from typing import TYPE_CHECKING

from git import GitCommandError, Repo
from git.exc import InvalidGitRepositoryError

from messirve.exceptions import GitError
from messirve.models.config import GitStrategy
from messirve.models.task import Task

if TYPE_CHECKING:
    from messirve.git.strategies import GitStrategy as GitStrategyImpl


class GitManager:
    """Manages git operations for Messirve."""

    def __init__(self, repo_path: Path | None = None) -> None:
        """Initialize the git manager.

        Args:
            repo_path: Path to the git repository. Defaults to current directory.
        """
        self.repo_path = repo_path or Path.cwd()
        self._repo: Repo | None = None
        self._base_branch: str | None = None

    @property
    def repo(self) -> Repo:
        """Get the git repository.

        Returns:
            Git repository object.

        Raises:
            GitError: If the path is not a git repository.
        """
        if self._repo is None:
            try:
                self._repo = Repo(self.repo_path)
            except InvalidGitRepositoryError:
                raise GitError(
                    f"Not a git repository: {self.repo_path}",
                    operation="init",
                )
        return self._repo

    def is_git_repo(self) -> bool:
        """Check if the path is a git repository.

        Returns:
            True if the path is a git repository.
        """
        try:
            Repo(self.repo_path)
            return True
        except InvalidGitRepositoryError:
            return False

    def get_current_branch(self) -> str:
        """Get the current branch name.

        Returns:
            Name of the current branch.

        Raises:
            GitError: If the current branch cannot be determined.
        """
        try:
            return self.repo.active_branch.name
        except TypeError:
            # Detached HEAD state
            raise GitError(
                "Cannot determine current branch (detached HEAD)",
                operation="get_current_branch",
            )

    def get_changed_files(self) -> list[str]:
        """Get list of changed files (staged and unstaged).

        Returns:
            List of file paths that have changes.
        """
        changed: set[str] = set()

        # Staged changes
        for item in self.repo.index.diff("HEAD"):
            if item.a_path:
                changed.add(item.a_path)
            if item.b_path:
                changed.add(item.b_path)

        # Unstaged changes
        for item in self.repo.index.diff(None):
            if item.a_path:
                changed.add(item.a_path)
            if item.b_path:
                changed.add(item.b_path)

        # Untracked files
        changed.update(self.repo.untracked_files)

        return sorted(changed)

    def has_changes(self) -> bool:
        """Check if there are any uncommitted changes.

        Returns:
            True if there are uncommitted changes.
        """
        return bool(self.repo.is_dirty(untracked_files=True))

    def branch_exists(self, branch_name: str) -> bool:
        """Check if a branch exists.

        Args:
            branch_name: Name of the branch to check.

        Returns:
            True if the branch exists.
        """
        return branch_name in [b.name for b in self.repo.branches]

    def create_branch(self, branch_name: str, checkout: bool = True) -> None:
        """Create a new branch.

        Args:
            branch_name: Name of the branch to create.
            checkout: Whether to checkout the new branch.

        Raises:
            GitError: If the branch cannot be created.
        """
        try:
            if self.branch_exists(branch_name):
                if checkout:
                    self.checkout(branch_name)
                return

            new_branch = self.repo.create_head(branch_name)
            if checkout:
                new_branch.checkout()
        except GitCommandError as e:
            raise GitError(
                f"Failed to create branch {branch_name}: {e}",
                operation="create_branch",
                branch=branch_name,
            ) from e

    def checkout(self, branch_name: str) -> None:
        """Checkout a branch.

        Args:
            branch_name: Name of the branch to checkout.

        Raises:
            GitError: If the checkout fails.
        """
        try:
            self.repo.heads[branch_name].checkout()
        except (KeyError, GitCommandError) as e:
            raise GitError(
                f"Failed to checkout branch {branch_name}: {e}",
                operation="checkout",
                branch=branch_name,
            ) from e

    def stage_all(self) -> None:
        """Stage all changes."""
        self.repo.git.add(A=True)

    def commit(self, message: str) -> str:
        """Create a commit.

        Args:
            message: Commit message.

        Returns:
            Commit SHA.

        Raises:
            GitError: If the commit fails.
        """
        try:
            self.stage_all()
            if not self.has_changes():
                # Nothing to commit
                return self.repo.head.commit.hexsha

            commit = self.repo.index.commit(message)
            return commit.hexsha
        except GitCommandError as e:
            raise GitError(
                f"Failed to commit: {e}",
                operation="commit",
            ) from e

    def get_commit_message(self, task: Task, run_id: str) -> str:
        """Generate a commit message for a task.

        Args:
            task: The task being committed.
            run_id: ID of the current run.

        Returns:
            Formatted commit message.
        """
        return (
            f"[messirve] {task.id}: {task.title}\n\n"
            f"Executed by messirve autonomous task runner.\n"
            f"Run ID: {run_id}"
        )

    def reset_to_base(self, base_branch: str) -> None:
        """Reset to the base branch state.

        Args:
            base_branch: Name of the base branch.

        Raises:
            GitError: If the reset fails.
        """
        try:
            self.repo.git.reset("--hard", base_branch)
        except GitCommandError as e:
            raise GitError(
                f"Failed to reset to {base_branch}: {e}",
                operation="reset",
                branch=base_branch,
            ) from e

    def stash(self) -> bool:
        """Stash current changes.

        Returns:
            True if changes were stashed, False if nothing to stash.
        """
        if not self.has_changes():
            return False
        self.repo.git.stash("push", "-m", "messirve-auto-stash")
        return True

    def stash_pop(self) -> bool:
        """Pop the most recent stash.

        Returns:
            True if stash was popped, False if no stash.
        """
        try:
            self.repo.git.stash("pop")
            return True
        except GitCommandError:
            return False

    def get_strategy(self, strategy_type: GitStrategy, base_branch: str) -> "GitStrategyImpl":
        """Get the appropriate git strategy.

        Args:
            strategy_type: Type of git strategy to use.
            base_branch: Base branch for the strategy.

        Returns:
            GitStrategy implementation.
        """
        from messirve.git.strategies import (
            BranchPerTaskStrategy,
            CommitPerTaskStrategy,
            NoOpStrategy,
            SingleBranchStrategy,
        )

        strategies: dict[GitStrategy, type[GitStrategyImpl]] = {
            GitStrategy.NONE: NoOpStrategy,
            GitStrategy.COMMIT_PER_TASK: CommitPerTaskStrategy,
            GitStrategy.BRANCH_PER_TASK: BranchPerTaskStrategy,
            GitStrategy.SINGLE_BRANCH: SingleBranchStrategy,
        }

        strategy_class = strategies.get(strategy_type, NoOpStrategy)
        return strategy_class(self, base_branch)
