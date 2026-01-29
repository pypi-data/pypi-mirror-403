"""Messirve - Autonomous Task Executor using Claude Code.

Messirve is a CLI tool that orchestrates Claude Code to execute development
tasks autonomously in a loop. It takes a list of Jira-like tasks from a YAML
file and executes them one-by-one using Claude Code, with comprehensive logging,
git integration, and quality gates.
"""

__version__ = "0.0.8"
__author__ = "Messirve Team"

from messirve.models.config import MessirveConfig
from messirve.models.execution import ExecutionResult, TaskAttempt
from messirve.models.task import Task

__all__ = [
    "__version__",
    "__author__",
    "Task",
    "ExecutionResult",
    "TaskAttempt",
    "MessirveConfig",
]
