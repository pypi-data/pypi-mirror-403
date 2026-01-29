"""Configuration models for Messirve."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class GitStrategy(str, Enum):
    """Git strategy for handling commits and branches."""

    NONE = "none"
    COMMIT_PER_TASK = "commit-per-task"
    BRANCH_PER_TASK = "branch-per-task"
    SINGLE_BRANCH = "single-branch"
    WORKTREE_PARALLEL = "worktree-parallel"


class TaskFlavor(str, Enum):
    """Task flavor defining the code quality and approach."""

    PRODUCTION_READY = "production-ready"
    POC = "poc"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    BUG_FIX = "bug-fix"
    TESTING = "testing"
    EXPLORATION = "exploration"


class Verbosity(str, Enum):
    """Verbosity level for console output."""

    QUIET = "quiet"
    NORMAL = "normal"
    VERBOSE = "verbose"
    DEBUG = "debug"


class ClaudePermissions(str, Enum):
    """Claude Code permission mode."""

    SKIP = "skip"
    ASK = "ask"


@dataclass
class DefaultsConfig:
    """Default configuration values."""

    max_retries: int = 3
    retry_delay_seconds: int = 5
    verbosity: Verbosity = Verbosity.NORMAL
    git_enabled: bool = False
    git_strategy: GitStrategy = GitStrategy.NONE
    base_branch: str = "main"
    create_pr: bool = False
    draft_pr: bool = False
    claude_code_permissions: ClaudePermissions = ClaudePermissions.SKIP
    default_flavor: TaskFlavor = TaskFlavor.PRODUCTION_READY

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "DefaultsConfig":
        """Create DefaultsConfig from a dictionary.

        Args:
            data: Dictionary containing defaults configuration.

        Returns:
            DefaultsConfig instance.
        """
        if data is None:
            return cls()

        verbosity_str = data.get("verbosity", "normal")
        try:
            verbosity = Verbosity(verbosity_str)
        except ValueError:
            verbosity = Verbosity.NORMAL

        strategy_str = data.get("git_strategy", "none")
        try:
            git_strategy = GitStrategy(strategy_str)
        except ValueError:
            git_strategy = GitStrategy.NONE

        permissions_str = data.get("claude_code_permissions", "skip")
        try:
            permissions = ClaudePermissions(permissions_str)
        except ValueError:
            permissions = ClaudePermissions.SKIP

        flavor_str = data.get("default_flavor", "production-ready")
        try:
            default_flavor = TaskFlavor(flavor_str)
        except ValueError:
            default_flavor = TaskFlavor.PRODUCTION_READY

        return cls(
            max_retries=data.get("max_retries", 3),
            retry_delay_seconds=data.get("retry_delay_seconds", 5),
            verbosity=verbosity,
            git_enabled=data.get("git_enabled", False),
            git_strategy=git_strategy,
            base_branch=data.get("base_branch", "main"),
            create_pr=data.get("create_pr", False),
            draft_pr=data.get("draft_pr", False),
            claude_code_permissions=permissions,
            default_flavor=default_flavor,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary containing defaults configuration.
        """
        return {
            "max_retries": self.max_retries,
            "retry_delay_seconds": self.retry_delay_seconds,
            "verbosity": self.verbosity.value,
            "git_enabled": self.git_enabled,
            "git_strategy": self.git_strategy.value,
            "base_branch": self.base_branch,
            "create_pr": self.create_pr,
            "draft_pr": self.draft_pr,
            "claude_code_permissions": self.claude_code_permissions.value,
            "default_flavor": self.default_flavor.value,
        }


@dataclass
class HooksConfig:
    """Global hooks configuration."""

    pre_run: list[str] = field(default_factory=list)
    post_run: list[str] = field(default_factory=list)
    pre_task: list[str] = field(default_factory=list)
    post_task: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "HooksConfig":
        """Create HooksConfig from a dictionary.

        Args:
            data: Dictionary containing hooks configuration.

        Returns:
            HooksConfig instance.
        """
        if data is None:
            return cls()
        return cls(
            pre_run=data.get("pre_run", []),
            post_run=data.get("post_run", []),
            pre_task=data.get("pre_task", []),
            post_task=data.get("post_task", []),
        )

    def to_dict(self) -> dict[str, list[str]]:
        """Convert to dictionary representation.

        Returns:
            Dictionary containing hooks configuration.
        """
        return {
            "pre_run": self.pre_run,
            "post_run": self.post_run,
            "pre_task": self.pre_task,
            "post_task": self.post_task,
        }


@dataclass
class BoundariesConfig:
    """File boundary configuration."""

    never_modify: list[str] = field(default_factory=list)
    read_only: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "BoundariesConfig":
        """Create BoundariesConfig from a dictionary.

        Args:
            data: Dictionary containing boundaries configuration.

        Returns:
            BoundariesConfig instance.
        """
        if data is None:
            return cls()
        return cls(
            never_modify=data.get("never_modify", []),
            read_only=data.get("read_only", []),
        )

    def to_dict(self) -> dict[str, list[str]]:
        """Convert to dictionary representation.

        Returns:
            Dictionary containing boundaries configuration.
        """
        return {
            "never_modify": self.never_modify,
            "read_only": self.read_only,
        }


class ContextIsolation(str, Enum):
    """Context isolation mode for task execution."""

    PER_TASK = "per_task"  # Fresh context for each task (recommended)
    SHARED = "shared"  # Share context across tasks in a run


@dataclass
class ContextConfig:
    """Context management configuration."""

    isolation: ContextIsolation = ContextIsolation.PER_TASK
    include_project_context: bool = True
    auto_detect_files: bool = True
    context_file: str = ".messirve/context.yaml"

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ContextConfig":
        """Create ContextConfig from a dictionary.

        Args:
            data: Dictionary containing context configuration.

        Returns:
            ContextConfig instance.
        """
        if data is None:
            return cls()

        isolation_str = data.get("isolation", "per_task")
        try:
            isolation = ContextIsolation(isolation_str)
        except ValueError:
            isolation = ContextIsolation.PER_TASK

        return cls(
            isolation=isolation,
            include_project_context=data.get("include_project_context", True),
            auto_detect_files=data.get("auto_detect_files", True),
            context_file=data.get("context_file", ".messirve/context.yaml"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary containing context configuration.
        """
        return {
            "isolation": self.isolation.value,
            "include_project_context": self.include_project_context,
            "auto_detect_files": self.auto_detect_files,
            "context_file": self.context_file,
        }


@dataclass
class MessirveConfig:
    """Main configuration for Messirve."""

    version: str = "1.0"
    defaults: DefaultsConfig = field(default_factory=DefaultsConfig)
    hooks: HooksConfig = field(default_factory=HooksConfig)
    rules: list[str] = field(default_factory=list)
    boundaries: BoundariesConfig = field(default_factory=BoundariesConfig)
    context: ContextConfig = field(default_factory=ContextConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MessirveConfig":
        """Create MessirveConfig from a dictionary.

        Args:
            data: Dictionary containing configuration.

        Returns:
            MessirveConfig instance.
        """
        return cls(
            version=data.get("version", "1.0"),
            defaults=DefaultsConfig.from_dict(data.get("defaults")),
            hooks=HooksConfig.from_dict(data.get("hooks")),
            rules=data.get("rules", []),
            boundaries=BoundariesConfig.from_dict(data.get("boundaries")),
            context=ContextConfig.from_dict(data.get("context")),
        )

    @classmethod
    def from_file(cls, path: Path) -> "MessirveConfig":
        """Load configuration from a YAML file.

        Args:
            path: Path to the configuration file.

        Returns:
            MessirveConfig instance.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            yaml.YAMLError: If the file is not valid YAML.
        """
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data or {})

    @classmethod
    def default(cls) -> "MessirveConfig":
        """Create a default configuration.

        Returns:
            MessirveConfig instance with default values.
        """
        return cls()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary containing all configuration.
        """
        return {
            "version": self.version,
            "defaults": self.defaults.to_dict(),
            "hooks": self.hooks.to_dict(),
            "rules": self.rules,
            "boundaries": self.boundaries.to_dict(),
            "context": self.context.to_dict(),
        }

    def to_yaml(self) -> str:
        """Convert to YAML string.

        Returns:
            YAML string representation of the configuration.
        """
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    def save(self, path: Path) -> None:
        """Save configuration to a YAML file.

        Args:
            path: Path to save the configuration to.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(self.to_yaml())
