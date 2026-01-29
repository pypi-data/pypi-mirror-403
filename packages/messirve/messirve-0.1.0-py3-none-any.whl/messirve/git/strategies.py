"""Git strategies for different commit/branch workflows."""

import contextlib
from abc import ABC, abstractmethod

from messirve.git.manager import GitManager
from messirve.models.task import Task


class GitStrategy(ABC):
    """Abstract base class for git strategies."""

    def __init__(self, manager: GitManager, base_branch: str) -> None:
        """Initialize the strategy.

        Args:
            manager: GitManager instance.
            base_branch: Base branch name.
        """
        self.manager = manager
        self.base_branch = base_branch

    @abstractmethod
    def setup(self, run_id: str) -> None:
        """Setup the strategy for a new run.

        Args:
            run_id: ID of the current run.
        """
        pass

    @abstractmethod
    def pre_task(self, task: Task, run_id: str) -> None:
        """Prepare for task execution.

        Args:
            task: The task about to be executed.
            run_id: ID of the current run.
        """
        pass

    @abstractmethod
    def post_task(self, task: Task, run_id: str, success: bool) -> dict[str, str] | None:
        """Handle post-task git operations.

        Args:
            task: The task that was executed.
            run_id: ID of the current run.
            success: Whether the task succeeded.

        Returns:
            Commit info dict with 'sha' and 'message', or None if no commit.
        """
        pass

    @abstractmethod
    def cleanup(self, run_id: str) -> None:
        """Cleanup after the run.

        Args:
            run_id: ID of the current run.
        """
        pass


class NoOpStrategy(GitStrategy):
    """Strategy that performs no git operations."""

    def setup(self, _run_id: str) -> None:
        """No-op setup."""
        pass

    def pre_task(self, _task: Task, _run_id: str) -> None:
        """No-op pre-task."""
        pass

    def post_task(self, _task: Task, _run_id: str, _success: bool) -> dict[str, str] | None:
        """No-op post-task."""
        return None

    def cleanup(self, _run_id: str) -> None:
        """No-op cleanup."""
        pass


class CommitPerTaskStrategy(GitStrategy):
    """Strategy that commits after each task on the current branch."""

    def setup(self, _run_id: str) -> None:
        """Store the current branch for reference."""
        pass

    def pre_task(self, _task: Task, _run_id: str) -> None:
        """No preparation needed."""
        pass

    def post_task(self, task: Task, run_id: str, success: bool) -> dict[str, str] | None:
        """Commit changes after successful task.

        Args:
            task: The task that was executed.
            run_id: ID of the current run.
            success: Whether the task succeeded.

        Returns:
            Commit info dict, or None if no changes or task failed.
        """
        if not success:
            return None

        if not self.manager.has_changes():
            return None

        message = self.manager.get_commit_message(task, run_id)
        sha = self.manager.commit(message)
        return {"sha": sha, "message": message}

    def cleanup(self, _run_id: str) -> None:
        """No cleanup needed."""
        pass


class BranchPerTaskStrategy(GitStrategy):
    """Strategy that creates a new branch for each task."""

    def __init__(self, manager: GitManager, base_branch: str) -> None:
        """Initialize the strategy."""
        super().__init__(manager, base_branch)
        self._original_branch: str | None = None

    def setup(self, _run_id: str) -> None:
        """Store the original branch."""
        self._original_branch = self.manager.get_current_branch()

    def pre_task(self, task: Task, _run_id: str) -> None:
        """Create and checkout task branch.

        Args:
            task: The task about to be executed.
            _run_id: ID of the current run (unused).
        """
        # Start from base branch
        self.manager.checkout(self.base_branch)
        # Create task branch
        branch_name = task.get_branch_name()
        self.manager.create_branch(branch_name, checkout=True)

    def post_task(self, task: Task, run_id: str, success: bool) -> dict[str, str] | None:
        """Commit changes on task branch.

        Args:
            task: The task that was executed.
            run_id: ID of the current run.
            success: Whether the task succeeded.

        Returns:
            Commit info dict, or None if no changes or task failed.
        """
        if not success:
            return None

        if not self.manager.has_changes():
            return None

        message = self.manager.get_commit_message(task, run_id)
        sha = self.manager.commit(message)
        return {"sha": sha, "message": message}

    def cleanup(self, _run_id: str) -> None:
        """Return to original branch."""
        if self._original_branch:
            with contextlib.suppress(Exception):
                self.manager.checkout(self._original_branch)


class SingleBranchStrategy(GitStrategy):
    """Strategy that puts all work on a single feature branch."""

    def __init__(self, manager: GitManager, base_branch: str) -> None:
        """Initialize the strategy."""
        super().__init__(manager, base_branch)
        self._run_branch: str | None = None
        self._original_branch: str | None = None

    def setup(self, run_id: str) -> None:
        """Create the run branch.

        Args:
            run_id: ID of the current run.
        """
        self._original_branch = self.manager.get_current_branch()
        self._run_branch = f"messirve/run-{run_id}"

        # Start from base branch
        self.manager.checkout(self.base_branch)
        # Create run branch
        self.manager.create_branch(self._run_branch, checkout=True)

    def pre_task(self, _task: Task, _run_id: str) -> None:
        """Ensure we're on the run branch.

        Args:
            _task: The task about to be executed (unused).
            _run_id: ID of the current run (unused).
        """
        if self._run_branch:
            current = self.manager.get_current_branch()
            if current != self._run_branch:
                self.manager.checkout(self._run_branch)

    def post_task(self, task: Task, run_id: str, success: bool) -> dict[str, str] | None:
        """Commit changes on the run branch.

        Args:
            task: The task that was executed.
            run_id: ID of the current run.
            success: Whether the task succeeded.

        Returns:
            Commit info dict, or None if no changes or task failed.
        """
        if not success:
            return None

        if not self.manager.has_changes():
            return None

        message = self.manager.get_commit_message(task, run_id)
        sha = self.manager.commit(message)
        return {"sha": sha, "message": message}

    def cleanup(self, _run_id: str) -> None:
        """Return to original branch."""
        if self._original_branch:
            with contextlib.suppress(Exception):
                self.manager.checkout(self._original_branch)
