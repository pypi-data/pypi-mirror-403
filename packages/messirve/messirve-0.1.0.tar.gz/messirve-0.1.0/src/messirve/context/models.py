"""Models for project context."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class ProjectType(str, Enum):
    """Detected project type."""

    PYTHON = "python"
    NODE = "node"
    GO = "go"
    RUST = "rust"
    JAVA = "java"
    UNKNOWN = "unknown"


@dataclass
class TechStack:
    """Technology stack information."""

    language: str = ""
    language_version: str = ""
    framework: str = ""
    framework_version: str = ""
    package_manager: str = ""
    database: str = ""
    testing: list[str] = field(default_factory=list)
    linting: list[str] = field(default_factory=list)
    other: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "TechStack":
        """Create TechStack from dictionary."""
        if data is None:
            return cls()
        return cls(
            language=data.get("language", ""),
            language_version=data.get("language_version", ""),
            framework=data.get("framework", ""),
            framework_version=data.get("framework_version", ""),
            package_manager=data.get("package_manager", ""),
            database=data.get("database", ""),
            testing=data.get("testing", []),
            linting=data.get("linting", []),
            other=data.get("other", []),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "language": self.language,
            "language_version": self.language_version,
            "framework": self.framework,
            "framework_version": self.framework_version,
            "package_manager": self.package_manager,
            "database": self.database,
            "testing": self.testing,
            "linting": self.linting,
            "other": self.other,
        }


@dataclass
class ProjectContext:
    """Complete project context for task execution."""

    # Basic info
    name: str = ""
    description: str = ""
    project_type: ProjectType = ProjectType.UNKNOWN

    # Tech stack
    tech_stack: TechStack = field(default_factory=TechStack)

    # Project structure
    structure: dict[str, str] = field(default_factory=dict)
    key_files: dict[str, str] = field(default_factory=dict)

    # Business context
    business_description: str = ""
    users: list[str] = field(default_factory=list)

    # Requirements
    functional_requirements: list[str] = field(default_factory=list)
    non_functional_requirements: dict[str, str] = field(default_factory=dict)

    # Coding standards
    coding_standards: list[str] = field(default_factory=list)

    # Setup commands
    setup_commands: list[str] = field(default_factory=list)
    verify_commands: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectContext":
        """Create ProjectContext from dictionary."""
        project_type_str = data.get("project_type", "unknown")
        try:
            project_type = ProjectType(project_type_str)
        except ValueError:
            project_type = ProjectType.UNKNOWN

        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            project_type=project_type,
            tech_stack=TechStack.from_dict(data.get("tech_stack")),
            structure=data.get("structure", {}),
            key_files=data.get("key_files", {}),
            business_description=data.get("business_description", ""),
            users=data.get("users", []),
            functional_requirements=data.get("functional_requirements", []),
            non_functional_requirements=data.get("non_functional_requirements", {}),
            coding_standards=data.get("coding_standards", []),
            setup_commands=data.get("setup_commands", []),
            verify_commands=data.get("verify_commands", []),
        )

    @classmethod
    def from_file(cls, path: Path) -> "ProjectContext":
        """Load context from YAML file."""
        if not path.exists():
            return cls()
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return cls.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "project_type": self.project_type.value,
            "tech_stack": self.tech_stack.to_dict(),
            "structure": self.structure,
            "key_files": self.key_files,
            "business_description": self.business_description,
            "users": self.users,
            "functional_requirements": self.functional_requirements,
            "non_functional_requirements": self.non_functional_requirements,
            "coding_standards": self.coding_standards,
            "setup_commands": self.setup_commands,
            "verify_commands": self.verify_commands,
        }

    def to_yaml(self) -> str:
        """Convert to YAML string."""
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    def save(self, path: Path) -> None:
        """Save context to YAML file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(self.to_yaml())

    def to_markdown(self) -> str:
        """Generate markdown representation for Claude context."""
        lines = [
            f"# Project Context: {self.name}",
            "",
        ]

        if self.description:
            lines.extend(["## Overview", self.description, ""])

        # Tech Stack
        if self.tech_stack.language:
            lines.append("## Tech Stack")
            if self.tech_stack.language:
                lines.append(
                    f"- **Language**: {self.tech_stack.language}"
                    + (
                        f" {self.tech_stack.language_version}"
                        if self.tech_stack.language_version
                        else ""
                    )
                )
            if self.tech_stack.framework:
                lines.append(
                    f"- **Framework**: {self.tech_stack.framework}"
                    + (
                        f" {self.tech_stack.framework_version}"
                        if self.tech_stack.framework_version
                        else ""
                    )
                )
            if self.tech_stack.package_manager:
                lines.append(f"- **Package Manager**: {self.tech_stack.package_manager}")
            if self.tech_stack.database:
                lines.append(f"- **Database**: {self.tech_stack.database}")
            if self.tech_stack.testing:
                lines.append(f"- **Testing**: {', '.join(self.tech_stack.testing)}")
            if self.tech_stack.linting:
                lines.append(f"- **Linting**: {', '.join(self.tech_stack.linting)}")
            lines.append("")

        # Structure
        if self.structure:
            lines.append("## Project Structure")
            lines.append("```")
            for path, desc in self.structure.items():
                lines.append(f"{path}  # {desc}")
            lines.append("```")
            lines.append("")

        # Business Context
        if self.business_description:
            lines.extend(["## Business Context", self.business_description, ""])

        if self.users:
            lines.append("### Users")
            for user in self.users:
                lines.append(f"- {user}")
            lines.append("")

        # Requirements
        if self.functional_requirements:
            lines.append("## Functional Requirements")
            for req in self.functional_requirements:
                lines.append(f"- {req}")
            lines.append("")

        if self.non_functional_requirements:
            lines.append("## Non-Functional Requirements")
            for key, value in self.non_functional_requirements.items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")

        # Coding Standards
        if self.coding_standards:
            lines.append("## Coding Standards")
            for standard in self.coding_standards:
                lines.append(f"- {standard}")
            lines.append("")

        # Key Files
        if self.key_files:
            lines.append("## Key Files")
            for file_path, desc in self.key_files.items():
                lines.append(f"- `{file_path}` - {desc}")
            lines.append("")

        return "\n".join(lines)

    def save_markdown(self, path: Path) -> None:
        """Save context as markdown file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(self.to_markdown())
