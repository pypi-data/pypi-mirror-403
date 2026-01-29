"""Storage for tech debt analysis reports."""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from messirve.analysis.models import AnalysisResult, ReportSummary, TrendPoint
from messirve.config import get_tech_debt_dir


class TechDebtStorage:
    """Manages persistent storage of tech debt analysis reports."""

    def __init__(self, project_dir: Path | None = None) -> None:
        """Initialize tech debt storage.

        Args:
            project_dir: Project directory. Defaults to current directory.
        """
        self.base_dir = get_tech_debt_dir(project_dir)
        self.reports_dir = self.base_dir / "reports"
        self.baselines_dir = self.base_dir / "baselines"
        self.index_file = self.base_dir / "index.json"

    def _ensure_dirs(self) -> None:
        """Create storage directories if they don't exist."""
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.baselines_dir.mkdir(parents=True, exist_ok=True)

    def _load_index(self) -> dict[str, Any]:
        """Load the index file."""
        if self.index_file.exists():
            data: dict[str, Any] = json.loads(self.index_file.read_text())
            return data
        return {"reports": [], "baselines": {}}

    def _save_index(self, index: dict[str, Any]) -> None:
        """Save the index file."""
        self._ensure_dirs()
        self.index_file.write_text(json.dumps(index, indent=2, default=str))

    def _generate_report_id(self, result: AnalysisResult) -> str:
        """Generate a unique report ID from timestamp and git ref.

        Args:
            result: Analysis result.

        Returns:
            Report ID in format: YYYY-MM-DDTHH-MM-SS_gitref
        """
        timestamp = result.timestamp.strftime("%Y-%m-%dT%H-%M-%S")
        git_ref = result.git_ref or self._get_current_git_ref() or "nogit"
        return f"{timestamp}_{git_ref}"

    def _get_current_git_ref(self) -> str | None:
        """Get the current git short ref."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return None

    def _result_to_markdown(self, result: AnalysisResult, label: str | None = None) -> str:
        """Convert analysis result to markdown format.

        Args:
            result: Analysis result.
            label: Optional label for the report.

        Returns:
            Markdown formatted report.
        """
        m = result.metrics
        lines = [
            "# Tech Debt Analysis Report",
            "",
            f"**Generated:** {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        if result.git_ref:
            lines.append(f"**Git Ref:** {result.git_ref}")
        if label:
            lines.append(f"**Label:** {label}")
        lines.extend(
            [
                "",
                "## Metrics Summary",
                "",
                "| Metric | Value |",
                "|--------|-------|",
                f"| Files Analyzed | {m.files_analyzed} |",
                f"| Total Lines | {m.total_lines} |",
                f"| Avg Cyclomatic Complexity | {m.avg_cyclomatic_complexity:.2f} |",
                f"| Max Cyclomatic Complexity | {m.max_cyclomatic_complexity:.2f} |",
                f"| Avg Maintainability Index | {m.avg_maintainability_index:.1f} |",
                f"| Min Maintainability Index | {m.min_maintainability_index:.1f} |",
                f"| Total Warnings | {m.total_warnings} |",
                f"| Total Errors | {m.total_errors} |",
                f"| Security Issues | {m.security_issues} |",
                "",
            ]
        )

        if m.warnings_by_category:
            lines.extend(
                [
                    "## Warnings by Category",
                    "",
                    "| Category | Count |",
                    "|----------|-------|",
                ]
            )
            for category, count in sorted(m.warnings_by_category.items()):
                lines.append(f"| {category} | {count} |")
            lines.append("")

        critical_findings = result.get_critical_findings()
        if critical_findings:
            lines.extend(
                [
                    "## Critical/High Impact Findings",
                    "",
                ]
            )
            for finding in critical_findings[:20]:
                location = ""
                if finding.file_path:
                    location = f" (`{finding.file_path}"
                    if finding.line_number:
                        location += f":{finding.line_number}"
                    location += "`)"
                lines.append(f"- **{finding.impact.value}**: {finding.message}{location}")
            if len(critical_findings) > 20:
                lines.append(
                    f"\n*...and {len(critical_findings) - 20} more critical/high findings*"
                )
            lines.append("")

        lines.extend(
            [
                "---",
                f"*Total findings: {len(result.findings)}*",
            ]
        )

        return "\n".join(lines)

    def save_report(self, result: AnalysisResult, label: str | None = None) -> str:
        """Save an analysis report.

        Args:
            result: Analysis result to save.
            label: Optional label for the report.

        Returns:
            Report ID.
        """
        self._ensure_dirs()
        report_id = self._generate_report_id(result)

        # Save JSON report
        json_path = self.reports_dir / f"{report_id}.json"
        report_data = result.to_dict()
        report_data["report_id"] = report_id
        report_data["label"] = label
        json_path.write_text(json.dumps(report_data, indent=2, default=str))

        # Save Markdown report
        md_path = self.reports_dir / f"{report_id}.md"
        md_path.write_text(self._result_to_markdown(result, label))

        # Update index
        index = self._load_index()
        m = result.metrics
        summary = {
            "report_id": report_id,
            "timestamp": result.timestamp.isoformat(),
            "git_ref": result.git_ref,
            "label": label,
            "metrics_summary": {
                "avg_cyclomatic_complexity": m.avg_cyclomatic_complexity,
                "avg_maintainability_index": m.avg_maintainability_index,
                "total_warnings": m.total_warnings,
                "total_errors": m.total_errors,
                "files_analyzed": m.files_analyzed,
            },
        }
        index["reports"].insert(0, summary)
        self._save_index(index)

        return report_id

    def get_reports(self, limit: int | None = None) -> list[ReportSummary]:
        """Get list of stored reports.

        Args:
            limit: Maximum number of reports to return.

        Returns:
            List of report summaries, newest first.
        """
        index = self._load_index()
        reports = index.get("reports", [])

        if limit:
            reports = reports[:limit]

        return [ReportSummary.from_dict(r) for r in reports]

    def get_report(self, report_id: str) -> AnalysisResult | None:
        """Load a full report by ID.

        Args:
            report_id: Report ID or "latest".

        Returns:
            Analysis result or None if not found.
        """
        if report_id == "latest":
            reports = self.get_reports(limit=1)
            if not reports:
                return None
            report_id = reports[0].report_id

        json_path = self.reports_dir / f"{report_id}.json"
        if not json_path.exists():
            return None

        data = json.loads(json_path.read_text())
        return AnalysisResult.from_dict(data)

    def get_report_markdown(self, report_id: str) -> str | None:
        """Get a report in markdown format.

        Args:
            report_id: Report ID or "latest".

        Returns:
            Markdown content or None if not found.
        """
        if report_id == "latest":
            reports = self.get_reports(limit=1)
            if not reports:
                return None
            report_id = reports[0].report_id

        md_path = self.reports_dir / f"{report_id}.md"
        if not md_path.exists():
            return None

        return md_path.read_text()

    def get_latest_report(self) -> AnalysisResult | None:
        """Get the most recent report.

        Returns:
            Most recent analysis result or None.
        """
        return self.get_report("latest")

    def save_baseline(self, result: AnalysisResult, name: str) -> None:
        """Save a named baseline.

        Args:
            result: Analysis result to save as baseline.
            name: Baseline name (e.g., "main", "release-1.0").
        """
        self._ensure_dirs()

        # Save baseline JSON
        baseline_path = self.baselines_dir / f"{name}.json"
        baseline_data = result.to_dict()
        baseline_data["baseline_name"] = name
        baseline_data["saved_at"] = datetime.now().isoformat()
        baseline_path.write_text(json.dumps(baseline_data, indent=2, default=str))

        # Update index
        index = self._load_index()
        index["baselines"][name] = {
            "name": name,
            "saved_at": datetime.now().isoformat(),
            "git_ref": result.git_ref,
            "metrics_summary": {
                "avg_cyclomatic_complexity": result.metrics.avg_cyclomatic_complexity,
                "avg_maintainability_index": result.metrics.avg_maintainability_index,
                "total_warnings": result.metrics.total_warnings,
            },
        }
        self._save_index(index)

    def load_baseline(self, name: str) -> AnalysisResult | None:
        """Load a named baseline.

        Args:
            name: Baseline name.

        Returns:
            Analysis result or None if not found.
        """
        baseline_path = self.baselines_dir / f"{name}.json"
        if not baseline_path.exists():
            return None

        data = json.loads(baseline_path.read_text())
        return AnalysisResult.from_dict(data)

    def list_baselines(self) -> list[dict[str, Any]]:
        """List all available baselines.

        Returns:
            List of baseline info dictionaries.
        """
        index = self._load_index()
        return list(index.get("baselines", {}).values())

    def get_trend(self, metric: str, limit: int = 10) -> list[TrendPoint]:
        """Get trend data for a specific metric.

        Args:
            metric: Metric name (e.g., "avg_cyclomatic_complexity").
            limit: Maximum number of data points.

        Returns:
            List of trend points, oldest first for charting.
        """
        index = self._load_index()
        reports = index.get("reports", [])[:limit]

        trend_points = []
        for report in reversed(reports):  # Oldest first for charting
            metrics = report.get("metrics_summary", {})
            value = metrics.get(metric, 0.0)

            timestamp_str = report.get("timestamp", "")
            timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now()

            trend_points.append(
                TrendPoint(
                    report_id=report.get("report_id", ""),
                    timestamp=timestamp,
                    git_ref=report.get("git_ref"),
                    label=report.get("label"),
                    value=float(value),
                )
            )

        return trend_points

    def delete_report(self, report_id: str) -> bool:
        """Delete a report by ID.

        Args:
            report_id: Report ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        json_path = self.reports_dir / f"{report_id}.json"
        md_path = self.reports_dir / f"{report_id}.md"

        if not json_path.exists():
            return False

        json_path.unlink(missing_ok=True)
        md_path.unlink(missing_ok=True)

        # Update index
        index = self._load_index()
        index["reports"] = [r for r in index["reports"] if r.get("report_id") != report_id]
        self._save_index(index)

        return True
