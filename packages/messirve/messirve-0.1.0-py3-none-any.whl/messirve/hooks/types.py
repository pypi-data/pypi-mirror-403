"""Hook type definitions."""

from dataclasses import dataclass
from enum import Enum


class HookType(str, Enum):
    """Types of hooks that can be executed."""

    PRE_RUN = "pre_run"
    POST_RUN = "post_run"
    PRE_TASK = "pre_task"
    POST_TASK = "post_task"


@dataclass
class HookConfig:
    """Configuration for a hook.

    Attributes:
        command: Shell command to execute.
        continue_on_failure: Whether to continue if the hook fails.
        timeout: Timeout in seconds for the hook.
    """

    command: str
    continue_on_failure: bool = False
    timeout: int = 300  # 5 minutes default

    @classmethod
    def from_string(cls, command: str) -> "HookConfig":
        """Create a HookConfig from a command string.

        Args:
            command: Shell command to execute.

        Returns:
            HookConfig instance.
        """
        return cls(command=command)
