"""Task model representing a development task to execute."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskFlavor(str, Enum):
    """Task flavor defining the code quality and approach."""

    PRODUCTION_READY = "production-ready"
    POC = "poc"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    BUG_FIX = "bug-fix"
    TESTING = "testing"
    EXPLORATION = "exploration"

    def get_instructions(self) -> str:
        """Get Claude Code instructions for this flavor.

        Returns:
            Instructions string to append to task description.
        """
        instructions = {
            TaskFlavor.PRODUCTION_READY: (
                "Write production-quality code with:\n"
                "- Comprehensive error handling\n"
                "- Full type annotations\n"
                "- Docstrings for all public functions/classes\n"
                "- Unit tests with good coverage\n"
                "- Follow best practices and design patterns"
            ),
            TaskFlavor.POC: (
                "Create a proof-of-concept with:\n"
                "- Focus on demonstrating core functionality\n"
                "- Minimal but working implementation\n"
                "- Basic error handling only\n"
                "- Comments explaining key decisions\n"
                "- Skip tests unless critical"
            ),
            TaskFlavor.DOCUMENTATION: (
                "Focus on documentation:\n"
                "- Write clear README files\n"
                "- Add comprehensive docstrings\n"
                "- Include usage examples\n"
                "- Create architecture documentation\n"
                "- Add inline comments for complex logic"
            ),
            TaskFlavor.REFACTORING: (
                "Refactor existing code with:\n"
                "- Preserve existing functionality\n"
                "- Improve code structure and readability\n"
                "- Apply SOLID principles where appropriate\n"
                "- Add tests for refactored code\n"
                "- Document any breaking changes"
            ),
            TaskFlavor.BUG_FIX: (
                "Fix the bug with:\n"
                "- Minimal changes to fix the issue\n"
                "- Add test to prevent regression\n"
                "- Document root cause in comments\n"
                "- Avoid unrelated changes"
            ),
            TaskFlavor.TESTING: (
                "Focus on testing:\n"
                "- Write comprehensive unit tests\n"
                "- Include edge cases and error scenarios\n"
                "- Add integration tests where needed\n"
                "- Aim for high code coverage\n"
                "- Use appropriate mocking/fixtures"
            ),
            TaskFlavor.EXPLORATION: (
                "Explore and experiment with:\n"
                "- Try different approaches\n"
                "- Document findings and trade-offs\n"
                "- Create runnable examples\n"
                "- Focus on learning, not production code"
            ),
        }
        return instructions.get(self, "")


class TaskHooks(BaseModel):
    """Hooks that run before and after a task."""

    model_config = ConfigDict(validate_assignment=True)

    pre_task: list[str] = Field(default_factory=list)
    post_task: list[str] = Field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "TaskHooks":
        """Create TaskHooks from a dictionary.

        Args:
            data: Dictionary containing hook definitions.

        Returns:
            TaskHooks instance.
        """
        if data is None:
            return cls()
        return cls(
            pre_task=data.get("pre_task", []),
            post_task=data.get("post_task", []),
        )

    def to_dict(self) -> dict[str, list[str]]:
        """Convert to dictionary representation.

        Returns:
            Dictionary with pre_task and post_task lists.
        """
        return {
            "pre_task": self.pre_task,
            "post_task": self.post_task,
        }


class Task(BaseModel):
    """A development task to be executed by Claude Code.

    Attributes:
        id: Unique task identifier (e.g., TASK-001).
        title: Short task title.
        description: Detailed task description.
        context: Project context and existing code references.
        acceptance_criteria: List of criteria to verify completion.
        depends_on: List of task IDs that must complete first.
        hooks: Task-specific hooks to run before/after execution.
        flavor: Task flavor defining code quality approach.
        done: Whether the task has been completed.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
    )

    id: str = Field(..., min_length=1, description="Unique task identifier")
    title: str = Field(..., min_length=1, max_length=200, description="Short task title")
    description: str = Field(..., min_length=1, description="Detailed task description")
    context: str = Field(..., description="Project context and existing code references")
    acceptance_criteria: list[str] = Field(
        ..., min_length=1, description="List of criteria to verify completion"
    )
    depends_on: list[str] = Field(
        default_factory=list, description="Task IDs that must complete first"
    )
    hooks: TaskHooks = Field(default_factory=TaskHooks, description="Task-specific hooks")
    flavor: TaskFlavor = Field(default=TaskFlavor.PRODUCTION_READY, description="Task flavor")
    done: bool = Field(default=False, description="Whether the task has been completed")

    @field_validator("acceptance_criteria")
    @classmethod
    def validate_acceptance_criteria(cls, v: list[str]) -> list[str]:
        """Validate that at least one acceptance criterion is provided."""
        if not v:
            raise ValueError("At least one acceptance criterion is required")
        return v

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        """Create a Task from a dictionary.

        Args:
            data: Dictionary containing task data.

        Returns:
            Task instance.

        Raises:
            ValueError: If required fields are missing.
        """
        required_fields = ["id", "title", "description", "context", "acceptance_criteria"]
        for field_name in required_fields:
            if field_name not in data:
                raise ValueError(f"Missing required field: {field_name}")

        flavor_str = data.get("flavor", "production-ready")
        try:
            flavor = TaskFlavor(flavor_str)
        except ValueError:
            flavor = TaskFlavor.PRODUCTION_READY

        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            context=data["context"],
            acceptance_criteria=data["acceptance_criteria"],
            depends_on=data.get("depends_on", []),
            hooks=TaskHooks.from_dict(data.get("hooks")),
            flavor=flavor,
            done=data.get("done", False),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary containing all task data.
        """
        result: dict[str, Any] = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "context": self.context,
            "acceptance_criteria": self.acceptance_criteria,
            "flavor": self.flavor.value if isinstance(self.flavor, TaskFlavor) else self.flavor,
        }
        if self.depends_on:
            result["depends_on"] = self.depends_on
        if self.hooks.pre_task or self.hooks.post_task:
            result["hooks"] = self.hooks.to_dict()
        if self.done:
            result["done"] = True
        return result

    def get_full_description(self) -> str:
        """Get the full description including flavor instructions.

        Returns:
            Description with flavor-specific instructions appended.
        """
        flavor_obj = self.flavor if isinstance(self.flavor, TaskFlavor) else TaskFlavor(self.flavor)
        flavor_instructions = flavor_obj.get_instructions()
        if flavor_instructions:
            return f"{self.description}\n\n## Code Quality Guidelines ({flavor_obj.value})\n{flavor_instructions}"
        return self.description

    def slugify_title(self) -> str:
        """Create a URL-safe slug from the title.

        Returns:
            Slugified title suitable for branch names.
        """
        # Convert to lowercase and replace spaces with hyphens
        slug = self.title.lower().replace(" ", "-")
        # Remove non-alphanumeric characters except hyphens
        slug = "".join(c for c in slug if c.isalnum() or c == "-")
        # Remove consecutive hyphens
        while "--" in slug:
            slug = slug.replace("--", "-")
        # Remove leading/trailing hyphens
        slug = slug.strip("-")
        # Truncate to reasonable length
        return slug[:50]

    def get_branch_name(self) -> str:
        """Generate a git branch name for this task.

        Returns:
            Branch name in format: messirve/{task-id}-{slugified-title}
        """
        return f"messirve/{self.id}-{self.slugify_title()}"
