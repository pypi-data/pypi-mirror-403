"""Complexity analyzer using radon."""

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from messirve.analysis.analyzers.base import BaseAnalyzer
from messirve.analysis.models import (
    AnalysisCategory,
    AnalysisConfig,
    AnalysisFinding,
    AnalysisMetrics,
    ImpactLevel,
)


@dataclass
class MIMetrics:
    """Maintainability index metrics."""

    avg: float = 100.0
    min: float = 100.0
    by_file: dict[str, float] = field(default_factory=dict)


class ComplexityAnalyzer(BaseAnalyzer):
    """Analyzer for code complexity using radon."""

    name = "complexity"
    description = "Analyzes cyclomatic and cognitive complexity"

    def __init__(self, config: AnalysisConfig) -> None:
        """Initialize the complexity analyzer."""
        super().__init__(config)
        self._radon_path: str | None = None

    def is_available(self) -> bool:
        """Check if radon is available."""
        self._radon_path = shutil.which("radon")
        return self._radon_path is not None

    def analyze(self, paths: list[Path]) -> tuple[AnalysisMetrics, list[AnalysisFinding]]:
        """Run complexity analysis.

        Args:
            paths: Paths to analyze.

        Returns:
            Tuple of (metrics, findings).
        """
        findings: list[AnalysisFinding] = []
        metrics = AnalysisMetrics()

        python_files = self.get_python_files(paths)
        if not python_files:
            return metrics, findings

        # Run cyclomatic complexity analysis
        cc_results = self._run_cyclomatic_complexity(python_files)
        cc_metrics, cc_findings = self._parse_cc_results(cc_results)

        # Run maintainability index analysis
        mi_results = self._run_maintainability_index(python_files)
        mi_metrics = self._parse_mi_results(mi_results)

        # Combine metrics
        metrics.avg_cyclomatic_complexity = cc_metrics.get("avg", 0.0)
        metrics.max_cyclomatic_complexity = cc_metrics.get("max", 0.0)
        metrics.avg_maintainability_index = mi_metrics.avg
        metrics.min_maintainability_index = mi_metrics.min
        metrics.files_analyzed = len(python_files)

        findings.extend(cc_findings)

        # Add findings for low maintainability
        for file_path, mi_value in mi_metrics.by_file.items():
            if mi_value < self.config.min_maintainability_index:
                findings.append(
                    AnalysisFinding(
                        category=AnalysisCategory.MAINTAINABILITY,
                        message=f"Low maintainability index: {mi_value:.1f}",
                        file_path=file_path,
                        impact=ImpactLevel.MEDIUM if mi_value > 10 else ImpactLevel.HIGH,
                        rule_id="MI001",
                        suggestion="Consider refactoring to improve maintainability",
                    )
                )

        return metrics, findings

    def _run_cyclomatic_complexity(self, files: list[Path]) -> str:
        """Run radon cyclomatic complexity analysis.

        Args:
            files: Files to analyze.

        Returns:
            JSON output from radon.
        """
        if not self._radon_path:
            return "{}"

        cmd = [
            self._radon_path,
            "cc",
            "--json",
            "--show-complexity",
            *[str(f) for f in files],
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            return result.stdout
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return "{}"

    def _run_maintainability_index(self, files: list[Path]) -> str:
        """Run radon maintainability index analysis.

        Args:
            files: Files to analyze.

        Returns:
            JSON output from radon.
        """
        if not self._radon_path:
            return "{}"

        cmd = [
            self._radon_path,
            "mi",
            "--json",
            *[str(f) for f in files],
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            return result.stdout
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return "{}"

    def _parse_cc_results(self, json_output: str) -> tuple[dict[str, float], list[AnalysisFinding]]:
        """Parse cyclomatic complexity results.

        Args:
            json_output: JSON output from radon cc.

        Returns:
            Tuple of (metrics dict, findings list).
        """
        findings: list[AnalysisFinding] = []
        all_complexities: list[float] = []

        try:
            data = json.loads(json_output) if json_output.strip() else {}
        except json.JSONDecodeError:
            return {"avg": 0.0, "max": 0.0}, []

        for file_path, functions in data.items():
            for func in functions:
                complexity = func.get("complexity", 0)
                all_complexities.append(complexity)

                # Create finding for high complexity
                if complexity > self.config.max_cyclomatic_complexity:
                    func_name = func.get("name", "unknown")
                    line = func.get("lineno", 0)

                    impact = ImpactLevel.HIGH if complexity > 20 else ImpactLevel.MEDIUM

                    findings.append(
                        AnalysisFinding(
                            category=AnalysisCategory.COMPLEXITY,
                            message=f"High cyclomatic complexity ({complexity}) in {func_name}",
                            file_path=file_path,
                            line_number=line,
                            impact=impact,
                            rule_id="CC001",
                            suggestion=f"Consider breaking down {func_name} into smaller functions",
                        )
                    )

        metrics = {
            "avg": sum(all_complexities) / len(all_complexities) if all_complexities else 0.0,
            "max": max(all_complexities) if all_complexities else 0.0,
        }

        return metrics, findings

    def _parse_mi_results(self, json_output: str) -> MIMetrics:
        """Parse maintainability index results.

        Args:
            json_output: JSON output from radon mi.

        Returns:
            MIMetrics with avg, min, and by_file values.
        """
        try:
            data = json.loads(json_output) if json_output.strip() else {}
        except json.JSONDecodeError:
            return MIMetrics()

        mi_values: list[float] = []
        by_file: dict[str, float] = {}

        for file_path, info in data.items():
            # radon mi returns dict with 'mi' key or just the float
            mi = info.get("mi", 100.0) if isinstance(info, dict) else float(info) if info else 100.0

            mi_values.append(mi)
            by_file[file_path] = mi

        return MIMetrics(
            avg=sum(mi_values) / len(mi_values) if mi_values else 100.0,
            min=min(mi_values) if mi_values else 100.0,
            by_file=by_file,
        )
