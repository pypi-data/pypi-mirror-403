"""Models for the planning module."""

from dataclasses import dataclass, field
from datetime import date


@dataclass
class PlanningGoal:
    """A high-level goal provided by the user."""

    description: str
    priority: int = 1  # 1=high, 2=medium, 3=low


@dataclass
class GeneratedTask:
    """A task generated from planning goals."""

    id: str
    title: str
    description: str
    context: str
    acceptance_criteria: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    complexity: str = "medium"  # low/medium/high
    flavor: str = "production-ready"  # Task flavor

    # User editing state (not persisted)
    accepted: bool = False
    deleted: bool = False

    def to_yaml_dict(self) -> dict[str, object]:
        """Convert to dictionary for YAML output."""
        result: dict[str, object] = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "context": self.context,
            "acceptance_criteria": self.acceptance_criteria,
            "flavor": self.flavor,
        }
        if self.depends_on:
            result["depends_on"] = self.depends_on
        return result


@dataclass
class PlanningSession:
    """State for a planning session."""

    goals: list[PlanningGoal] = field(default_factory=list)
    generated_tasks: list[GeneratedTask] = field(default_factory=list)
    output_file: str = ""
    created_date: date = field(default_factory=date.today)

    def get_active_tasks(self) -> list[GeneratedTask]:
        """Get tasks that haven't been deleted."""
        return [t for t in self.generated_tasks if not t.deleted]

    def to_yaml_content(self) -> str:
        """Convert session tasks to YAML content."""
        import yaml

        tasks = [t.to_yaml_dict() for t in self.get_active_tasks()]
        content = {
            "version": "1.0",
            "tasks": tasks,
        }
        return yaml.dump(content, default_flow_style=False, sort_keys=False, allow_unicode=True)
