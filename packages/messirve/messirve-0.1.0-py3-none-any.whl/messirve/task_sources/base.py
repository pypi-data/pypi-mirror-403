"""Base class for task sources."""

from abc import ABC, abstractmethod
from pathlib import Path

from messirve.models.task import Task


class TaskSource(ABC):
    """Abstract base class for task sources.

    Task sources are responsible for loading tasks from various formats
    (YAML files, GitHub Issues, etc.).
    """

    @abstractmethod
    def load(self, source: Path | str) -> list[Task]:
        """Load tasks from the source.

        Args:
            source: Path or identifier for the task source.

        Returns:
            List of Task objects.

        Raises:
            TaskFileError: If the source cannot be loaded.
        """
        pass

    @abstractmethod
    def validate(self, tasks: list[Task]) -> list[str]:
        """Validate a list of tasks.

        Args:
            tasks: List of Task objects to validate.

        Returns:
            List of validation error messages (empty if valid).
        """
        pass

    @abstractmethod
    def save(self, tasks: list[Task], destination: Path | str) -> None:
        """Save tasks to the destination.

        Args:
            tasks: List of Task objects to save.
            destination: Path or identifier for the destination.

        Raises:
            TaskFileError: If the tasks cannot be saved.
        """
        pass
