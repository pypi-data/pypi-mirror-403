"""Models for code analysis and tech debt tracking."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ImpactLevel(str, Enum):
    """Impact level for analysis findings."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnalysisCategory(str, Enum):
    """Categories of analysis."""

    COMPLEXITY = "complexity"
    QUALITY = "quality"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    SMELL = "smell"


@dataclass
class ReportSummary:
    """Summary of a stored analysis report."""

    report_id: str
    timestamp: datetime
    git_ref: str | None = None
    label: str | None = None
    metrics_summary: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReportSummary":
        """Create a ReportSummary from a dictionary.

        Args:
            data: Dictionary with report summary data.

        Returns:
            ReportSummary instance.
        """
        timestamp_str = data.get("timestamp", "")
        timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now()
        return cls(
            report_id=data.get("report_id", ""),
            timestamp=timestamp,
            git_ref=data.get("git_ref"),
            label=data.get("label"),
            metrics_summary=data.get("metrics_summary", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "report_id": self.report_id,
            "timestamp": self.timestamp.isoformat(),
            "git_ref": self.git_ref,
            "label": self.label,
            "metrics_summary": self.metrics_summary,
        }


@dataclass
class TrendPoint:
    """A single data point for metric trending."""

    report_id: str
    timestamp: datetime
    git_ref: str | None = None
    label: str | None = None
    value: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "report_id": self.report_id,
            "timestamp": self.timestamp.isoformat(),
            "git_ref": self.git_ref,
            "label": self.label,
            "value": self.value,
        }


@dataclass
class AnalysisFinding:
    """A single finding from an analyzer."""

    category: AnalysisCategory
    message: str
    file_path: str | None = None
    line_number: int | None = None
    impact: ImpactLevel = ImpactLevel.MEDIUM
    rule_id: str | None = None
    suggestion: str | None = None


@dataclass
class FileMetrics:
    """Metrics for a single file."""

    path: str
    lines_of_code: int = 0
    cyclomatic_complexity: float = 0.0
    cognitive_complexity: float = 0.0
    maintainability_index: float = 100.0
    warning_count: int = 0
    error_count: int = 0


@dataclass
class AnalysisMetrics:
    """Aggregated metrics from analysis."""

    # Complexity
    avg_cyclomatic_complexity: float = 0.0
    max_cyclomatic_complexity: float = 0.0
    avg_cognitive_complexity: float = 0.0
    max_cognitive_complexity: float = 0.0

    # Quality
    total_warnings: int = 0
    total_errors: int = 0
    warnings_by_category: dict[str, int] = field(default_factory=dict)

    # Security
    security_issues: int = 0
    security_by_severity: dict[str, int] = field(default_factory=dict)

    # Maintainability
    avg_maintainability_index: float = 100.0
    min_maintainability_index: float = 100.0

    # Coverage
    files_analyzed: int = 0
    total_lines: int = 0


@dataclass
class AnalysisResult:
    """Result of running analysis."""

    timestamp: datetime = field(default_factory=datetime.now)
    metrics: AnalysisMetrics = field(default_factory=AnalysisMetrics)
    findings: list[AnalysisFinding] = field(default_factory=list)
    file_metrics: list[FileMetrics] = field(default_factory=list)
    analyzed_paths: list[str] = field(default_factory=list)
    git_ref: str | None = None

    def get_findings_by_category(self, category: AnalysisCategory) -> list[AnalysisFinding]:
        """Get findings filtered by category."""
        return [f for f in self.findings if f.category == category]

    def get_critical_findings(self) -> list[AnalysisFinding]:
        """Get all critical and high impact findings."""
        return [f for f in self.findings if f.impact in (ImpactLevel.CRITICAL, ImpactLevel.HIGH)]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the analysis result.
        """
        return {
            "timestamp": self.timestamp.isoformat(),
            "git_ref": self.git_ref,
            "analyzed_paths": self.analyzed_paths,
            "metrics": {
                "avg_cyclomatic_complexity": self.metrics.avg_cyclomatic_complexity,
                "max_cyclomatic_complexity": self.metrics.max_cyclomatic_complexity,
                "avg_cognitive_complexity": self.metrics.avg_cognitive_complexity,
                "max_cognitive_complexity": self.metrics.max_cognitive_complexity,
                "total_warnings": self.metrics.total_warnings,
                "total_errors": self.metrics.total_errors,
                "warnings_by_category": self.metrics.warnings_by_category,
                "security_issues": self.metrics.security_issues,
                "security_by_severity": self.metrics.security_by_severity,
                "avg_maintainability_index": self.metrics.avg_maintainability_index,
                "min_maintainability_index": self.metrics.min_maintainability_index,
                "files_analyzed": self.metrics.files_analyzed,
                "total_lines": self.metrics.total_lines,
            },
            "findings": [
                {
                    "category": f.category.value,
                    "message": f.message,
                    "file_path": f.file_path,
                    "line_number": f.line_number,
                    "impact": f.impact.value,
                    "rule_id": f.rule_id,
                    "suggestion": f.suggestion,
                }
                for f in self.findings
            ],
            "file_metrics": [
                {
                    "path": fm.path,
                    "lines_of_code": fm.lines_of_code,
                    "cyclomatic_complexity": fm.cyclomatic_complexity,
                    "cognitive_complexity": fm.cognitive_complexity,
                    "maintainability_index": fm.maintainability_index,
                    "warning_count": fm.warning_count,
                    "error_count": fm.error_count,
                }
                for fm in self.file_metrics
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AnalysisResult":
        """Create an AnalysisResult from a dictionary.

        Args:
            data: Dictionary with analysis result data.

        Returns:
            AnalysisResult instance.
        """
        timestamp_str = data.get("timestamp", "")
        timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now()

        metrics_data = data.get("metrics", {})
        metrics = AnalysisMetrics(
            avg_cyclomatic_complexity=metrics_data.get("avg_cyclomatic_complexity", 0.0),
            max_cyclomatic_complexity=metrics_data.get("max_cyclomatic_complexity", 0.0),
            avg_cognitive_complexity=metrics_data.get("avg_cognitive_complexity", 0.0),
            max_cognitive_complexity=metrics_data.get("max_cognitive_complexity", 0.0),
            total_warnings=metrics_data.get("total_warnings", 0),
            total_errors=metrics_data.get("total_errors", 0),
            warnings_by_category=metrics_data.get("warnings_by_category", {}),
            security_issues=metrics_data.get("security_issues", 0),
            security_by_severity=metrics_data.get("security_by_severity", {}),
            avg_maintainability_index=metrics_data.get("avg_maintainability_index", 100.0),
            min_maintainability_index=metrics_data.get("min_maintainability_index", 100.0),
            files_analyzed=metrics_data.get("files_analyzed", 0),
            total_lines=metrics_data.get("total_lines", 0),
        )

        findings = [
            AnalysisFinding(
                category=AnalysisCategory(f.get("category", "quality")),
                message=f.get("message", ""),
                file_path=f.get("file_path"),
                line_number=f.get("line_number"),
                impact=ImpactLevel(f.get("impact", "medium")),
                rule_id=f.get("rule_id"),
                suggestion=f.get("suggestion"),
            )
            for f in data.get("findings", [])
        ]

        file_metrics = [
            FileMetrics(
                path=fm.get("path", ""),
                lines_of_code=fm.get("lines_of_code", 0),
                cyclomatic_complexity=fm.get("cyclomatic_complexity", 0.0),
                cognitive_complexity=fm.get("cognitive_complexity", 0.0),
                maintainability_index=fm.get("maintainability_index", 100.0),
                warning_count=fm.get("warning_count", 0),
                error_count=fm.get("error_count", 0),
            )
            for fm in data.get("file_metrics", [])
        ]

        return cls(
            timestamp=timestamp,
            git_ref=data.get("git_ref"),
            analyzed_paths=data.get("analyzed_paths", []),
            metrics=metrics,
            findings=findings,
            file_metrics=file_metrics,
        )


@dataclass
class MetricsDelta:
    """Change in a metric between before and after."""

    metric_name: str
    before: float
    after: float
    absolute_change: float
    percent_change: float
    is_regression: bool

    @classmethod
    def calculate(
        cls,
        name: str,
        before: float,
        after: float,
        higher_is_worse: bool = True,
    ) -> "MetricsDelta":
        """Calculate delta between two values."""
        absolute = after - before
        percent = ((after - before) / before * 100) if before != 0 else 0.0
        is_regression = (absolute > 0) if higher_is_worse else (absolute < 0)

        return cls(
            metric_name=name,
            before=before,
            after=after,
            absolute_change=absolute,
            percent_change=percent,
            is_regression=is_regression,
        )


@dataclass
class AnalysisComparison:
    """Comparison between two analysis results."""

    before: AnalysisResult
    after: AnalysisResult
    deltas: list[MetricsDelta] = field(default_factory=list)
    new_findings: list[AnalysisFinding] = field(default_factory=list)
    resolved_findings: list[AnalysisFinding] = field(default_factory=list)

    @property
    def has_regressions(self) -> bool:
        """Check if any metrics regressed."""
        return any(d.is_regression for d in self.deltas)

    @property
    def overall_impact(self) -> str:
        """Determine overall impact level."""
        critical_regressions = sum(
            1 for d in self.deltas if d.is_regression and abs(d.percent_change) > 20
        )
        moderate_regressions = sum(
            1 for d in self.deltas if d.is_regression and 5 < abs(d.percent_change) <= 20
        )

        if critical_regressions > 0 or len(self.new_findings) > 10:
            return "high_concern"
        elif moderate_regressions > 0 or len(self.new_findings) > 5:
            return "moderate_concern"
        elif self.has_regressions:
            return "minor_concern"
        else:
            return "acceptable"

    def calculate_deltas(self) -> None:
        """Calculate all metric deltas."""
        b = self.before.metrics
        a = self.after.metrics

        self.deltas = [
            MetricsDelta.calculate(
                "avg_cyclomatic_complexity",
                b.avg_cyclomatic_complexity,
                a.avg_cyclomatic_complexity,
                higher_is_worse=True,
            ),
            MetricsDelta.calculate(
                "avg_cognitive_complexity",
                b.avg_cognitive_complexity,
                a.avg_cognitive_complexity,
                higher_is_worse=True,
            ),
            MetricsDelta.calculate(
                "total_warnings",
                float(b.total_warnings),
                float(a.total_warnings),
                higher_is_worse=True,
            ),
            MetricsDelta.calculate(
                "security_issues",
                float(b.security_issues),
                float(a.security_issues),
                higher_is_worse=True,
            ),
            MetricsDelta.calculate(
                "avg_maintainability_index",
                b.avg_maintainability_index,
                a.avg_maintainability_index,
                higher_is_worse=False,  # Higher MI is better
            ),
        ]

        # Calculate new and resolved findings
        before_keys = {(f.file_path, f.line_number, f.rule_id) for f in self.before.findings}
        after_keys = {(f.file_path, f.line_number, f.rule_id) for f in self.after.findings}

        new_keys = after_keys - before_keys
        resolved_keys = before_keys - after_keys

        self.new_findings = [
            f for f in self.after.findings if (f.file_path, f.line_number, f.rule_id) in new_keys
        ]
        self.resolved_findings = [
            f
            for f in self.before.findings
            if (f.file_path, f.line_number, f.rule_id) in resolved_keys
        ]


@dataclass
class AnalysisConfig:
    """Configuration for analysis."""

    # Paths
    paths: list[Path] = field(default_factory=lambda: [Path(".")])
    exclude_patterns: list[str] = field(
        default_factory=lambda: [
            "**/node_modules/**",
            "**/.venv/**",
            "**/venv/**",
            "**/__pycache__/**",
        ]
    )

    # Analyzer toggles
    enable_complexity: bool = True
    enable_quality: bool = True
    enable_security: bool = False  # Requires bandit
    enable_maintainability: bool = True

    # Thresholds
    max_cyclomatic_complexity: float = 10.0
    max_cognitive_complexity: float = 15.0
    min_maintainability_index: float = 20.0
    max_warnings_increase_percent: float = 10.0

    # Output
    fail_on_regression: bool = False
    report_format: str = "console"  # console, yaml, json, markdown
