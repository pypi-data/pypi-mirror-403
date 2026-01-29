"""Base analyzer interface."""

from abc import ABC, abstractmethod
from pathlib import Path

from messirve.analysis.models import AnalysisConfig, AnalysisFinding, AnalysisMetrics


class BaseAnalyzer(ABC):
    """Base class for code analyzers."""

    name: str = "base"
    description: str = "Base analyzer"

    def __init__(self, config: AnalysisConfig) -> None:
        """Initialize the analyzer.

        Args:
            config: Analysis configuration.
        """
        self.config = config

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the analyzer's dependencies are available.

        Returns:
            True if the analyzer can run.
        """
        pass

    @abstractmethod
    def analyze(self, paths: list[Path]) -> tuple[AnalysisMetrics, list[AnalysisFinding]]:
        """Run analysis on the given paths.

        Args:
            paths: Paths to analyze.

        Returns:
            Tuple of (metrics, findings).
        """
        pass

    def get_python_files(self, paths: list[Path]) -> list[Path]:
        """Get all Python files from the given paths.

        Args:
            paths: Paths to search.

        Returns:
            List of Python file paths.
        """
        files: list[Path] = []

        for path in paths:
            if path.is_file() and path.suffix == ".py":
                files.append(path)
            elif path.is_dir():
                for py_file in path.rglob("*.py"):
                    # Check exclusion patterns
                    if not self._is_excluded(py_file):
                        files.append(py_file)

        return files

    def _is_excluded(self, path: Path) -> bool:
        """Check if a path matches any exclusion pattern.

        Args:
            path: Path to check.

        Returns:
            True if path should be excluded.
        """
        import fnmatch

        path_str = str(path)
        return any(fnmatch.fnmatch(path_str, pattern) for pattern in self.config.exclude_patterns)
