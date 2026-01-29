"""Custom exceptions for Messirve."""

from typing import Any


class MessirveError(Exception):
    """Base exception for all Messirve errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            details: Additional context about the error.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(MessirveError):
    """Raised when there's an error in configuration."""

    pass


class TaskFileError(MessirveError):
    """Raised when there's an error parsing or validating the task file."""

    pass


class TaskValidationError(TaskFileError):
    """Raised when a task fails validation."""

    def __init__(
        self,
        message: str,
        task_id: str | None = None,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            task_id: ID of the task that failed validation.
            field: Field that caused the validation error.
            details: Additional context about the error.
        """
        super().__init__(message, details)
        self.task_id = task_id
        self.field = field


class DependencyError(MessirveError):
    """Raised when task dependencies cannot be resolved."""

    def __init__(
        self,
        message: str,
        task_id: str | None = None,
        missing_deps: list[str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            task_id: ID of the task with dependency issues.
            missing_deps: List of missing dependency IDs.
            details: Additional context about the error.
        """
        super().__init__(message, details)
        self.task_id = task_id
        self.missing_deps = missing_deps or []


class ExecutionError(MessirveError):
    """Raised when task execution fails."""

    def __init__(
        self,
        message: str,
        task_id: str | None = None,
        attempt: int | None = None,
        exit_code: int | None = None,
        output: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            task_id: ID of the task that failed.
            attempt: Attempt number when the failure occurred.
            exit_code: Exit code from the failed command.
            output: Output from the failed command.
            details: Additional context about the error.
        """
        super().__init__(message, details)
        self.task_id = task_id
        self.attempt = attempt
        self.exit_code = exit_code
        self.output = output


class HookError(MessirveError):
    """Raised when a hook fails to execute."""

    def __init__(
        self,
        message: str,
        hook_type: str | None = None,
        command: str | None = None,
        exit_code: int | None = None,
        output: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            hook_type: Type of hook that failed (pre_task, post_task, etc.).
            command: Command that failed.
            exit_code: Exit code from the failed command.
            output: Output from the failed command.
            details: Additional context about the error.
        """
        super().__init__(message, details)
        self.hook_type = hook_type
        self.command = command
        self.exit_code = exit_code
        self.output = output


class GitError(MessirveError):
    """Raised when a git operation fails."""

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        branch: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            operation: Git operation that failed.
            branch: Branch involved in the failure.
            details: Additional context about the error.
        """
        super().__init__(message, details)
        self.operation = operation
        self.branch = branch


class ClaudeCodeError(ExecutionError):
    """Raised when Claude Code execution fails."""

    pass


class StateError(MessirveError):
    """Raised when there's an error with execution state."""

    pass
