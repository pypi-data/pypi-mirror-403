"""Quality analyzer using ruff."""

import json
import shutil
import subprocess
from pathlib import Path

from messirve.analysis.analyzers.base import BaseAnalyzer
from messirve.analysis.models import (
    AnalysisCategory,
    AnalysisConfig,
    AnalysisFinding,
    AnalysisMetrics,
    ImpactLevel,
)


class QualityAnalyzer(BaseAnalyzer):
    """Analyzer for code quality using ruff."""

    name = "quality"
    description = "Analyzes code quality using ruff linter"

    # Map ruff rule prefixes to categories for grouping
    RULE_CATEGORIES = {
        "E": "error",
        "W": "warning",
        "F": "pyflakes",
        "C": "convention",
        "I": "isort",
        "N": "naming",
        "D": "docstring",
        "UP": "upgrade",
        "B": "bugbear",
        "A": "builtins",
        "S": "security",
        "T": "type",
        "PL": "pylint",
        "RUF": "ruff",
    }

    # Rules that indicate potential security issues
    SECURITY_RULES = {"S", "B"}

    def __init__(self, config: AnalysisConfig) -> None:
        """Initialize the quality analyzer."""
        super().__init__(config)
        self._ruff_path: str | None = None

    def is_available(self) -> bool:
        """Check if ruff is available."""
        self._ruff_path = shutil.which("ruff")
        return self._ruff_path is not None

    def analyze(self, paths: list[Path]) -> tuple[AnalysisMetrics, list[AnalysisFinding]]:
        """Run quality analysis.

        Args:
            paths: Paths to analyze.

        Returns:
            Tuple of (metrics, findings).
        """
        findings: list[AnalysisFinding] = []
        metrics = AnalysisMetrics()

        if not self._ruff_path:
            return metrics, findings

        # Run ruff check
        json_output = self._run_ruff(paths)
        ruff_findings = self._parse_ruff_output(json_output)

        # Calculate metrics
        warnings_by_category: dict[str, int] = {}
        error_count = 0
        warning_count = 0

        for finding in ruff_findings:
            # Categorize the rule
            rule_id = finding.rule_id or ""
            category = self._get_rule_category(rule_id)
            warnings_by_category[category] = warnings_by_category.get(category, 0) + 1

            # Count errors vs warnings
            if rule_id.startswith("E") or finding.impact == ImpactLevel.HIGH:
                error_count += 1
            else:
                warning_count += 1

        metrics.total_warnings = warning_count
        metrics.total_errors = error_count
        metrics.warnings_by_category = warnings_by_category
        metrics.files_analyzed = len(self.get_python_files(paths))

        findings.extend(ruff_findings)

        return metrics, findings

    def _run_ruff(self, paths: list[Path]) -> str:
        """Run ruff check on paths.

        Args:
            paths: Paths to check.

        Returns:
            JSON output from ruff.
        """
        if not self._ruff_path:
            return "[]"

        path_strs = [str(p) for p in paths]

        cmd = [
            self._ruff_path,
            "check",
            "--output-format",
            "json",
            "--exit-zero",  # Don't fail on findings
            *path_strs,
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
            return "[]"

    def _parse_ruff_output(self, json_output: str) -> list[AnalysisFinding]:
        """Parse ruff JSON output into findings.

        Args:
            json_output: JSON output from ruff.

        Returns:
            List of analysis findings.
        """
        findings: list[AnalysisFinding] = []

        try:
            data = json.loads(json_output) if json_output.strip() else []
        except json.JSONDecodeError:
            return findings

        for item in data:
            rule_id = item.get("code", "")
            message = item.get("message", "")
            file_path = item.get("filename", "")
            line = item.get("location", {}).get("row", 0)

            # Determine impact level
            impact = self._get_impact_level(rule_id)

            # Determine category
            if any(rule_id.startswith(prefix) for prefix in self.SECURITY_RULES):
                category = AnalysisCategory.SECURITY
            else:
                category = AnalysisCategory.QUALITY

            # Get suggestion from fix if available
            fix = item.get("fix")
            suggestion = None
            if fix and fix.get("message"):
                suggestion = fix["message"]

            findings.append(
                AnalysisFinding(
                    category=category,
                    message=message,
                    file_path=file_path,
                    line_number=line,
                    impact=impact,
                    rule_id=rule_id,
                    suggestion=suggestion,
                )
            )

        return findings

    def _get_rule_category(self, rule_id: str) -> str:
        """Get category for a rule ID.

        Args:
            rule_id: The rule ID (e.g., "E501", "F401").

        Returns:
            Category name.
        """
        for prefix, category in self.RULE_CATEGORIES.items():
            if rule_id.startswith(prefix):
                return category
        return "other"

    def _get_impact_level(self, rule_id: str) -> ImpactLevel:
        """Determine impact level from rule ID.

        Args:
            rule_id: The rule ID.

        Returns:
            Impact level.
        """
        # Security issues are high impact
        if any(rule_id.startswith(prefix) for prefix in self.SECURITY_RULES):
            return ImpactLevel.HIGH

        # Errors are high impact
        if rule_id.startswith("E"):
            return ImpactLevel.MEDIUM

        # F (pyflakes) can be bugs
        if rule_id.startswith("F"):
            return ImpactLevel.MEDIUM

        # B (bugbear) are potential bugs
        if rule_id.startswith("B"):
            return ImpactLevel.MEDIUM

        return ImpactLevel.LOW
