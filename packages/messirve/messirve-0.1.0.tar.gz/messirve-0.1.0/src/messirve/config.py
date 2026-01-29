"""Configuration management for Messirve."""

from pathlib import Path
from typing import Any

from messirve.exceptions import ConfigurationError
from messirve.models.config import MessirveConfig

# Default configuration directory name
CONFIG_DIR = ".messirve"
CONFIG_FILE = "config.yaml"
DEFAULT_TASKS_FILE = "tasks.yaml"


def get_config_dir(project_dir: Path | None = None) -> Path:
    """Get the configuration directory path.

    Args:
        project_dir: Project directory. Defaults to current directory.

    Returns:
        Path to the configuration directory.
    """
    base = project_dir or Path.cwd()
    return base / CONFIG_DIR


def get_config_path(project_dir: Path | None = None) -> Path:
    """Get the configuration file path.

    Args:
        project_dir: Project directory. Defaults to current directory.

    Returns:
        Path to the configuration file.
    """
    return get_config_dir(project_dir) / CONFIG_FILE


def get_log_dir(project_dir: Path | None = None) -> Path:
    """Get the log directory path.

    Args:
        project_dir: Project directory. Defaults to current directory.

    Returns:
        Path to the log directory.
    """
    return get_config_dir(project_dir) / "logs"


def get_state_path(project_dir: Path | None = None) -> Path:
    """Get the state file path.

    Args:
        project_dir: Project directory. Defaults to current directory.

    Returns:
        Path to the state file.
    """
    return get_config_dir(project_dir) / "state.json"


def get_tech_debt_dir(project_dir: Path | None = None) -> Path:
    """Get the tech debt storage directory path.

    Args:
        project_dir: Project directory. Defaults to current directory.

    Returns:
        Path to the tech debt storage directory.
    """
    return get_config_dir(project_dir) / "tech_debt"


def load_config(project_dir: Path | None = None) -> MessirveConfig:
    """Load configuration from file or return defaults.

    Args:
        project_dir: Project directory. Defaults to current directory.

    Returns:
        MessirveConfig instance.
    """
    config_path = get_config_path(project_dir)
    if config_path.exists():
        try:
            return MessirveConfig.from_file(config_path)
        except Exception as e:
            raise ConfigurationError(f"Failed to load config: {e}") from e
    return MessirveConfig.default()


def save_config(config: MessirveConfig, project_dir: Path | None = None) -> None:
    """Save configuration to file.

    Args:
        config: Configuration to save.
        project_dir: Project directory. Defaults to current directory.
    """
    config_path = get_config_path(project_dir)
    config.save(config_path)


def init_config(project_dir: Path | None = None, force: bool = False) -> Path:
    """Initialize configuration in a project directory.

    Args:
        project_dir: Project directory. Defaults to current directory.
        force: Whether to overwrite existing configuration.

    Returns:
        Path to the created configuration file.

    Raises:
        ConfigurationError: If configuration exists and force is False.
    """
    config_path = get_config_path(project_dir)

    if config_path.exists() and not force:
        raise ConfigurationError(
            f"Configuration already exists at {config_path}. Use --force to overwrite."
        )

    # Create default configuration
    config = MessirveConfig.default()

    # Add some sensible defaults
    config.rules = [
        "Use type hints for all functions",
        "Follow PEP 8 conventions",
        "Write docstrings for public functions",
    ]

    config.save(config_path)

    # Create logs directory
    log_dir = get_log_dir(project_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    return config_path


def set_config_value(key: str, value: Any, project_dir: Path | None = None) -> None:
    """Set a configuration value.

    Args:
        key: Dot-separated key path (e.g., "defaults.max_retries").
        value: Value to set.
        project_dir: Project directory.

    Raises:
        ConfigurationError: If the key path is invalid.
    """
    config = load_config(project_dir)
    config_dict = config.to_dict()

    # Navigate to the parent and set the value
    parts = key.split(".")
    current = config_dict
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            raise ConfigurationError(f"Invalid configuration key: {key}")
        current = current[part]

    final_key = parts[-1]
    if final_key not in current:
        raise ConfigurationError(f"Invalid configuration key: {key}")

    # Convert value to appropriate type
    original_value = current[final_key]
    if isinstance(original_value, bool):
        value = str(value).lower() in ("true", "1", "yes")
    elif isinstance(original_value, int):
        value = int(value)
    elif isinstance(original_value, float):
        value = float(value)

    current[final_key] = value

    # Save updated config
    updated_config = MessirveConfig.from_dict(config_dict)
    save_config(updated_config, project_dir)


def add_rule(rule: str, project_dir: Path | None = None) -> None:
    """Add a rule to the configuration.

    Args:
        rule: Rule to add.
        project_dir: Project directory.
    """
    config = load_config(project_dir)
    if rule not in config.rules:
        config.rules.append(rule)
        save_config(config, project_dir)


def remove_rule(rule: str, project_dir: Path | None = None) -> bool:
    """Remove a rule from the configuration.

    Args:
        rule: Rule to remove.
        project_dir: Project directory.

    Returns:
        True if the rule was removed, False if not found.
    """
    config = load_config(project_dir)
    if rule in config.rules:
        config.rules.remove(rule)
        save_config(config, project_dir)
        return True
    return False


def add_boundary(pattern: str, boundary_type: str, project_dir: Path | None = None) -> None:
    """Add a file boundary pattern.

    Args:
        pattern: Glob pattern to add.
        boundary_type: Type of boundary ("never_modify" or "read_only").
        project_dir: Project directory.

    Raises:
        ConfigurationError: If boundary_type is invalid.
    """
    config = load_config(project_dir)

    if boundary_type == "never_modify":
        if pattern not in config.boundaries.never_modify:
            config.boundaries.never_modify.append(pattern)
    elif boundary_type == "read_only":
        if pattern not in config.boundaries.read_only:
            config.boundaries.read_only.append(pattern)
    else:
        raise ConfigurationError(
            f"Invalid boundary type: {boundary_type}. Must be 'never_modify' or 'read_only'."
        )

    save_config(config, project_dir)
