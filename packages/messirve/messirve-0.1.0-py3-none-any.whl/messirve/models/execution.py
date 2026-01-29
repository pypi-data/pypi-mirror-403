"""Execution result models for tracking task execution."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    """Status of a task execution."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class RunStatus(str, Enum):
    """Status of an entire run."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TokenUsage:
    """Token usage breakdown for an execution."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        """Calculate total tokens."""
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> dict[str, int]:
        """Convert to dictionary."""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_creation_tokens": self.cache_creation_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass
class HookResult:
    """Result of executing a hook command."""

    command: str
    exit_code: int
    output: str
    duration_seconds: float
    success: bool = field(init=False)

    def __post_init__(self) -> None:
        """Set success based on exit code."""
        self.success = self.exit_code == 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary containing hook result data.
        """
        return {
            "command": self.command,
            "exit_code": self.exit_code,
            "output": self.output,
            "duration_seconds": self.duration_seconds,
        }


@dataclass
class TaskAttempt:
    """Record of a single task execution attempt."""

    attempt_number: int
    started_at: datetime
    completed_at: datetime | None = None
    duration_seconds: float = 0.0
    prompt: str = ""
    claude_code_output: str = ""
    model: str = ""
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    pre_task_hooks: list[HookResult] = field(default_factory=list)
    post_task_hooks: list[HookResult] = field(default_factory=list)
    outcome: str = ""  # "success", "failure", "error"
    error: str | None = None

    # Legacy property for backward compatibility
    @property
    def tokens_used(self) -> int:
        """Get total tokens used (legacy)."""
        return self.token_usage.total_tokens

    @property
    def cost_usd(self) -> float:
        """Cost is no longer tracked."""
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary containing attempt data.
        """
        return {
            "attempt_number": self.attempt_number,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "prompt": self.prompt,
            "claude_code_output": self.claude_code_output,
            "model": self.model,
            "token_usage": self.token_usage.to_dict(),
            "pre_task_hooks": [h.to_dict() for h in self.pre_task_hooks],
            "post_task_hooks": [h.to_dict() for h in self.post_task_hooks],
            "outcome": self.outcome,
            "error": self.error,
        }


@dataclass
class GitInfo:
    """Git information for a task execution."""

    branch: str | None = None
    commits: list[dict[str, str]] = field(default_factory=list)
    pr_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary containing git info.
        """
        return {
            "branch": self.branch,
            "commits": self.commits,
            "pr_url": self.pr_url,
        }


@dataclass
class ExecutionResult:
    """Complete result of executing a task."""

    task_id: str
    title: str
    run_id: str
    status: TaskStatus
    attempts: list[TaskAttempt] = field(default_factory=list)
    files_changed: list[str] = field(default_factory=list)
    git_info: GitInfo = field(default_factory=GitInfo)
    summary: str = ""
    analysis_result: dict[str, Any] | None = (
        None  # Code quality analysis for production-ready tasks
    )

    @property
    def total_tokens(self) -> int:
        """Calculate total tokens used across all attempts."""
        return sum(a.tokens_used for a in self.attempts)

    @property
    def total_input_tokens(self) -> int:
        """Calculate total input tokens across all attempts."""
        return sum(a.token_usage.input_tokens for a in self.attempts)

    @property
    def total_output_tokens(self) -> int:
        """Calculate total output tokens across all attempts."""
        return sum(a.token_usage.output_tokens for a in self.attempts)

    @property
    def total_cost(self) -> float:
        """Cost is no longer tracked."""
        return 0.0

    @property
    def total_duration(self) -> float:
        """Calculate total duration across all attempts."""
        return sum(a.duration_seconds for a in self.attempts)

    @property
    def model(self) -> str:
        """Get the model used (from last successful attempt)."""
        for attempt in reversed(self.attempts):
            if attempt.model:
                return attempt.model
        return ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "version": "1.0",
            "task_id": self.task_id,
            "title": self.title,
            "run_id": self.run_id,
            "status": self.status.value,
            "model": self.model,
            "token_usage": {
                "input_tokens": self.total_input_tokens,
                "output_tokens": self.total_output_tokens,
                "total_tokens": self.total_tokens,
            },
            "duration_seconds": self.total_duration,
            "attempts": [a.to_dict() for a in self.attempts],
            "final_status": self.status.value,
            "files_changed": self.files_changed,
            "git": self.git_info.to_dict(),
            "summary": self.summary,
        }
        if self.analysis_result:
            result["analysis_result"] = self.analysis_result
        return result


@dataclass
class TaskMetrics:
    """Metrics for a single task in the summary."""

    task_id: str
    title: str
    status: str
    model: str
    duration_seconds: float
    input_tokens: int
    output_tokens: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "status": self.status,
            "model": self.model,
            "duration_seconds": self.duration_seconds,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }


@dataclass
class RunSummary:
    """Summary of an entire execution run."""

    run_id: str
    started_at: datetime
    completed_at: datetime | None = None
    status: RunStatus = RunStatus.PENDING
    tasks_file: str = ""
    git_strategy: str = "none"
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    skipped_tasks: int = 0
    total_duration_seconds: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    task_results: list[ExecutionResult] = field(default_factory=list)

    # Legacy property
    @property
    def total_tokens_used(self) -> int:
        """Get total tokens (legacy)."""
        return self.total_input_tokens + self.total_output_tokens

    @property
    def total_cost_usd(self) -> float:
        """Cost is no longer tracked."""
        return 0.0

    def get_models_used(self) -> set[str]:
        """Get set of all models used in this run."""
        models = set()
        for result in self.task_results:
            if result.model:
                models.add(result.model)
        return models

    def get_task_metrics(self) -> list[TaskMetrics]:
        """Get metrics for each task."""
        metrics = []
        for result in self.task_results:
            metrics.append(
                TaskMetrics(
                    task_id=result.task_id,
                    title=result.title,
                    status=result.status.value,
                    model=result.model,
                    duration_seconds=result.total_duration,
                    input_tokens=result.total_input_tokens,
                    output_tokens=result.total_output_tokens,
                )
            )
        return metrics

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "run_id": self.run_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status.value,
            "tasks_file": self.tasks_file,
            "git_strategy": self.git_strategy,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "skipped_tasks": self.skipped_tasks,
            "total_duration_seconds": self.total_duration_seconds,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "models_used": list(self.get_models_used()),
            "task_metrics": [m.to_dict() for m in self.get_task_metrics()],
            "task_refs": [
                {
                    "task_id": r.task_id,
                    "status": r.status.value,
                    "log_file": f"runs/{self.run_id}/{r.task_id}.json",
                }
                for r in self.task_results
            ],
        }
