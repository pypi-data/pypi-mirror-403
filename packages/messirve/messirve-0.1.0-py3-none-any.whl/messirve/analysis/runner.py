"""Analysis runner that orchestrates all analyzers."""

import subprocess
from datetime import datetime
from pathlib import Path

from rich.console import Console

from messirve.analysis.analyzers import ComplexityAnalyzer, QualityAnalyzer
from messirve.analysis.analyzers.base import BaseAnalyzer
from messirve.analysis.models import (
    AnalysisComparison,
    AnalysisConfig,
    AnalysisFinding,
    AnalysisMetrics,
    AnalysisResult,
)


class AnalysisRunner:
    """Runs analysis using configured analyzers."""

    def __init__(
        self,
        config: AnalysisConfig | None = None,
        console: Console | None = None,
    ) -> None:
        """Initialize the analysis runner.

        Args:
            config: Analysis configuration.
            console: Rich console for output.
        """
        self.config = config or AnalysisConfig()
        self.console = console or Console()
        self._analyzers: list[BaseAnalyzer] = []
        self._setup_analyzers()

    def _setup_analyzers(self) -> None:
        """Set up enabled analyzers."""
        if self.config.enable_complexity:
            complexity_analyzer = ComplexityAnalyzer(self.config)
            if complexity_analyzer.is_available():
                self._analyzers.append(complexity_analyzer)
            else:
                self.console.print(
                    "[yellow]Warning:[/yellow] radon not available, skipping complexity analysis"
                )

        if self.config.enable_quality:
            quality_analyzer = QualityAnalyzer(self.config)
            if quality_analyzer.is_available():
                self._analyzers.append(quality_analyzer)
            else:
                self.console.print(
                    "[yellow]Warning:[/yellow] ruff not available, skipping quality analysis"
                )

    def analyze(self, paths: list[Path] | None = None) -> AnalysisResult:
        """Run analysis on paths.

        Args:
            paths: Paths to analyze (defaults to config paths).

        Returns:
            Analysis result.
        """
        paths = paths or self.config.paths
        result = AnalysisResult(
            timestamp=datetime.now(),
            analyzed_paths=[str(p) for p in paths],
            git_ref=self._get_current_git_ref(),
        )

        all_findings: list[AnalysisFinding] = []
        combined_metrics = AnalysisMetrics()

        for analyzer in self._analyzers:
            self.console.print(f"[dim]Running {analyzer.name} analysis...[/dim]")
            metrics, findings = analyzer.analyze(paths)

            # Merge metrics
            self._merge_metrics(combined_metrics, metrics)
            all_findings.extend(findings)

        result.metrics = combined_metrics
        result.findings = all_findings

        return result

    def analyze_diff(
        self,
        before_ref: str | None = None,
        after_ref: str | None = None,
        paths: list[Path] | None = None,
    ) -> AnalysisComparison:
        """Analyze the difference between two git refs.

        Args:
            before_ref: Git ref for before state (default: HEAD~1 or stash).
            after_ref: Git ref for after state (default: current working tree).
            paths: Paths to analyze.

        Returns:
            Analysis comparison.
        """
        paths = paths or self.config.paths

        # If we have a before_ref, checkout and analyze
        if before_ref:
            before_result = self._analyze_at_ref(before_ref, paths)
        else:
            # Use current state as "before" (useful for pre/post task execution)
            before_result = self.analyze(paths)

        # Analyze current state (or after_ref)
        after_result = self._analyze_at_ref(after_ref, paths) if after_ref else self.analyze(paths)

        # Create comparison
        comparison = AnalysisComparison(before=before_result, after=after_result)
        comparison.calculate_deltas()

        return comparison

    def capture_baseline(self, paths: list[Path] | None = None) -> AnalysisResult:
        """Capture a baseline analysis.

        Args:
            paths: Paths to analyze.

        Returns:
            Analysis result to use as baseline.
        """
        self.console.print("[bold]Capturing baseline metrics...[/bold]")
        return self.analyze(paths)

    def compare_to_baseline(
        self, baseline: AnalysisResult, paths: list[Path] | None = None
    ) -> AnalysisComparison:
        """Compare current state to a baseline.

        Args:
            baseline: Previous analysis result to compare against.
            paths: Paths to analyze.

        Returns:
            Comparison between baseline and current state.
        """
        self.console.print("[bold]Analyzing current state...[/bold]")
        current = self.analyze(paths)

        comparison = AnalysisComparison(before=baseline, after=current)
        comparison.calculate_deltas()

        return comparison

    def _analyze_at_ref(self, git_ref: str, paths: list[Path]) -> AnalysisResult:
        """Analyze code at a specific git ref.

        This stashes current changes, checks out the ref, analyzes,
        then restores the original state.

        Args:
            git_ref: Git ref to analyze.
            paths: Paths to analyze.

        Returns:
            Analysis result.
        """
        # Store current state
        stash_result = subprocess.run(
            ["git", "stash", "push", "-m", "messirve-analysis-temp"],
            capture_output=True,
            text=True,
        )
        did_stash = "No local changes" not in stash_result.stdout

        try:
            # Checkout the ref
            subprocess.run(
                ["git", "checkout", git_ref],
                capture_output=True,
                check=True,
            )

            # Analyze
            result = self.analyze(paths)
            result.git_ref = git_ref

            return result
        finally:
            # Restore original state
            subprocess.run(
                ["git", "checkout", "-"],
                capture_output=True,
            )
            if did_stash:
                subprocess.run(
                    ["git", "stash", "pop"],
                    capture_output=True,
                )

    def _get_current_git_ref(self) -> str | None:
        """Get the current git ref.

        Returns:
            Current git commit hash or None.
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()[:8]
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return None

    def _merge_metrics(self, target: AnalysisMetrics, source: AnalysisMetrics) -> None:
        """Merge source metrics into target.

        Args:
            target: Target metrics to update.
            source: Source metrics to merge from.
        """
        # Complexity - take non-zero values
        if source.avg_cyclomatic_complexity > 0:
            target.avg_cyclomatic_complexity = source.avg_cyclomatic_complexity
        if source.max_cyclomatic_complexity > 0:
            target.max_cyclomatic_complexity = source.max_cyclomatic_complexity
        if source.avg_cognitive_complexity > 0:
            target.avg_cognitive_complexity = source.avg_cognitive_complexity
        if source.max_cognitive_complexity > 0:
            target.max_cognitive_complexity = source.max_cognitive_complexity

        # Quality - add
        target.total_warnings += source.total_warnings
        target.total_errors += source.total_errors
        for category, count in source.warnings_by_category.items():
            target.warnings_by_category[category] = (
                target.warnings_by_category.get(category, 0) + count
            )

        # Security - add
        target.security_issues += source.security_issues
        for severity, count in source.security_by_severity.items():
            target.security_by_severity[severity] = (
                target.security_by_severity.get(severity, 0) + count
            )

        # Maintainability - take non-default values
        if source.avg_maintainability_index < 100.0:
            target.avg_maintainability_index = source.avg_maintainability_index
        if source.min_maintainability_index < 100.0:
            target.min_maintainability_index = source.min_maintainability_index

        # Counts - max
        target.files_analyzed = max(target.files_analyzed, source.files_analyzed)
        target.total_lines = max(target.total_lines, source.total_lines)
