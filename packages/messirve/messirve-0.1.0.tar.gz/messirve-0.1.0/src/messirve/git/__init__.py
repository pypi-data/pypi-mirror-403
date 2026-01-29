"""Git operations for Messirve."""

from messirve.git.manager import GitManager
from messirve.git.strategies import (
    BranchPerTaskStrategy,
    CommitPerTaskStrategy,
    NoOpStrategy,
    SingleBranchStrategy,
)
from messirve.git.strategies import (
    GitStrategy as GitStrategyImpl,
)

__all__ = [
    "GitManager",
    "GitStrategyImpl",
    "NoOpStrategy",
    "CommitPerTaskStrategy",
    "BranchPerTaskStrategy",
    "SingleBranchStrategy",
]
