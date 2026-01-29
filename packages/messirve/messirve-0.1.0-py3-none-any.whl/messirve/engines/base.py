"""Base class for execution engines."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field

from messirve.models.config import MessirveConfig
from messirve.models.execution import TokenUsage
from messirve.models.task import Task


@dataclass
class EngineResult:
    """Result from running an engine."""

    success: bool
    output: str
    exit_code: int = 0
    model: str = ""
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    error: str | None = None

    # Legacy properties for backward compatibility
    @property
    def tokens_used(self) -> int:
        """Get total tokens used (legacy)."""
        return self.token_usage.total_tokens

    @property
    def cost_usd(self) -> float:
        """Cost is no longer tracked - always returns 0."""
        return 0.0


class Engine(ABC):
    """Abstract base class for execution engines.

    Engines are responsible for executing tasks using various backends
    (Claude Code, other AI assistants, etc.).
    """

    @abstractmethod
    def execute(
        self,
        task: Task,
        config: MessirveConfig,
        output_callback: Callable[[str], None] | None = None,
    ) -> EngineResult:
        """Execute a task.

        Args:
            task: The task to execute.
            config: Messirve configuration.
            output_callback: Optional callback for streaming output.

        Returns:
            EngineResult with execution details.
        """
        pass

    @abstractmethod
    def build_prompt(self, task: Task, config: MessirveConfig) -> str:
        """Build the prompt for the engine.

        Args:
            task: The task to build a prompt for.
            config: Messirve configuration.

        Returns:
            Complete prompt string.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the engine is available.

        Returns:
            True if the engine can be used, False otherwise.
        """
        pass
