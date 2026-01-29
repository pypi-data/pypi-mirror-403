"""Coupling analyzer for detecting high module dependencies."""

import ast
from collections import defaultdict
from pathlib import Path

from messirve.analysis.analyzers.base import BaseAnalyzer
from messirve.analysis.models import (
    AnalysisCategory,
    AnalysisFinding,
    AnalysisMetrics,
    ImpactLevel,
)


class CouplingAnalyzer(BaseAnalyzer):
    """Analyzer that detects high coupling between modules.

    Analyzes Python import statements to build a dependency graph and
    identifies modules with excessive dependencies.

    Thresholds:
    - HIGH: > 15 imports
    - MEDIUM: > 10 imports
    """

    name = "coupling"
    description = "Analyzes code coupling and dependency relationships"

    # Thresholds for coupling warnings
    HIGH_COUPLING_THRESHOLD = 15
    MEDIUM_COUPLING_THRESHOLD = 10

    def is_available(self) -> bool:
        """Check if the analyzer is available.

        Returns:
            Always True as this uses built-in ast module.
        """
        return True

    def analyze(self, paths: list[Path]) -> tuple[AnalysisMetrics, list[AnalysisFinding]]:
        """Analyze coupling in Python files.

        Args:
            paths: Paths to analyze.

        Returns:
            Tuple of (metrics, findings).
        """
        findings: list[AnalysisFinding] = []
        import_graph: dict[str, set[str]] = defaultdict(set)

        python_files = self.get_python_files(paths)

        for py_file in python_files:
            self._analyze_file(py_file, import_graph, findings)

        # Detect high coupling
        for module, imports in import_graph.items():
            import_count = len(imports)
            if import_count > self.HIGH_COUPLING_THRESHOLD:
                findings.append(
                    AnalysisFinding(
                        category=AnalysisCategory.MAINTAINABILITY,
                        message=f"High coupling: imports {import_count} modules",
                        file_path=module,
                        impact=ImpactLevel.HIGH,
                        rule_id="COUP001",
                        suggestion=(
                            "Consider splitting the module or using dependency injection "
                            "to reduce coupling"
                        ),
                    )
                )
            elif import_count > self.MEDIUM_COUPLING_THRESHOLD:
                findings.append(
                    AnalysisFinding(
                        category=AnalysisCategory.MAINTAINABILITY,
                        message=f"Moderate coupling: imports {import_count} modules",
                        file_path=module,
                        impact=ImpactLevel.MEDIUM,
                        rule_id="COUP002",
                        suggestion="Consider reviewing dependencies for potential simplification",
                    )
                )

        return AnalysisMetrics(), findings

    def _analyze_file(
        self,
        path: Path,
        graph: dict[str, set[str]],
        findings: list[AnalysisFinding],
    ) -> None:
        """Analyze imports in a single file.

        Args:
            path: Path to the Python file.
            graph: Import graph to update.
            findings: List to append findings to.
        """
        try:
            content = path.read_text(encoding="utf-8")
            tree = ast.parse(content)
            imports: set[str] = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        # Get top-level module
                        module = alias.name.split(".")[0]
                        imports.add(module)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    # Get top-level module
                    module = node.module.split(".")[0]
                    imports.add(module)

            graph[str(path)] = imports

        except SyntaxError as e:
            findings.append(
                AnalysisFinding(
                    category=AnalysisCategory.QUALITY,
                    message=f"Syntax error: {e}",
                    file_path=str(path),
                    line_number=e.lineno,
                    impact=ImpactLevel.HIGH,
                    rule_id="SYN001",
                )
            )
        except (OSError, UnicodeDecodeError):
            # Skip files we can't read
            pass

    def get_dependency_graph(self, paths: list[Path]) -> dict[str, set[str]]:
        """Build and return the import dependency graph.

        This can be used for visualization or further analysis.

        Args:
            paths: Paths to analyze.

        Returns:
            Dictionary mapping module paths to their imported modules.
        """
        graph: dict[str, set[str]] = defaultdict(set)
        findings: list[AnalysisFinding] = []

        python_files = self.get_python_files(paths)
        for py_file in python_files:
            self._analyze_file(py_file, graph, findings)

        return dict(graph)

    def get_coupling_metrics(self, paths: list[Path]) -> dict[str, int]:
        """Get coupling metrics for each module.

        Args:
            paths: Paths to analyze.

        Returns:
            Dictionary mapping module paths to their import count.
        """
        graph = self.get_dependency_graph(paths)
        return {module: len(imports) for module, imports in graph.items()}

    def get_most_coupled_modules(self, paths: list[Path], limit: int = 10) -> list[tuple[str, int]]:
        """Get the modules with the highest coupling.

        Args:
            paths: Paths to analyze.
            limit: Maximum number of modules to return.

        Returns:
            List of (module_path, import_count) tuples, sorted by import count descending.
        """
        metrics = self.get_coupling_metrics(paths)
        sorted_modules = sorted(metrics.items(), key=lambda x: x[1], reverse=True)
        return sorted_modules[:limit]
