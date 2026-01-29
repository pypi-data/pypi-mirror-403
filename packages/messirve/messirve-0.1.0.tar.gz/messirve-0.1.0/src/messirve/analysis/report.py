"""Report generation for analysis results."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from messirve.analysis.models import (
    AnalysisComparison,
    AnalysisResult,
    ImpactLevel,
    MetricsDelta,
)


class ReportGenerator:
    """Generates reports from analysis results."""

    def __init__(self, console: Console | None = None) -> None:
        """Initialize the report generator.

        Args:
            console: Rich console for output.
        """
        self.console = console or Console()

    def print_result(self, result: AnalysisResult) -> None:
        """Print analysis result to console.

        Args:
            result: Analysis result to print.
        """
        # Header
        self.console.print()
        self.console.print(
            Panel(
                "[bold blue]Code Analysis Report[/bold blue]",
                subtitle=f"Analyzed at {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            )
        )

        # Metrics table
        metrics_table = Table(title="Metrics Summary", box=None, padding=(0, 2))
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", justify="right")

        m = result.metrics
        metrics_table.add_row("Files Analyzed", str(m.files_analyzed))
        metrics_table.add_row("Avg Cyclomatic Complexity", f"{m.avg_cyclomatic_complexity:.2f}")
        metrics_table.add_row("Max Cyclomatic Complexity", f"{m.max_cyclomatic_complexity:.2f}")
        metrics_table.add_row("Avg Maintainability Index", f"{m.avg_maintainability_index:.1f}")
        metrics_table.add_row("Total Warnings", str(m.total_warnings))
        metrics_table.add_row("Total Errors", str(m.total_errors))

        self.console.print(metrics_table)

        # Findings summary
        if result.findings:
            self.console.print()
            findings_table = Table(title="Findings", box=None, padding=(0, 1))
            findings_table.add_column("Impact", width=10)
            findings_table.add_column("Rule", width=10)
            findings_table.add_column("Message")
            findings_table.add_column("Location", style="dim")

            # Sort by impact
            sorted_findings = sorted(
                result.findings,
                key=lambda f: list(ImpactLevel).index(f.impact),
            )

            for finding in sorted_findings[:20]:  # Limit to 20
                impact_style = self._get_impact_style(finding.impact)
                location = ""
                if finding.file_path:
                    location = finding.file_path
                    if finding.line_number:
                        location += f":{finding.line_number}"

                findings_table.add_row(
                    f"[{impact_style}]{finding.impact.value}[/{impact_style}]",
                    finding.rule_id or "-",
                    finding.message[:60] + "..." if len(finding.message) > 60 else finding.message,
                    location[:40] + "..." if len(location) > 40 else location,
                )

            self.console.print(findings_table)

            if len(result.findings) > 20:
                self.console.print(f"[dim]... and {len(result.findings) - 20} more findings[/dim]")

    def print_comparison(self, comparison: AnalysisComparison) -> None:
        """Print analysis comparison to console.

        Args:
            comparison: Comparison to print.
        """
        self.console.print()

        # Overall status
        impact = comparison.overall_impact
        impact_color = {
            "acceptable": "green",
            "minor_concern": "yellow",
            "moderate_concern": "orange1",
            "high_concern": "red",
        }.get(impact, "white")

        status_text = Text()
        status_text.append("Overall Impact: ", style="bold")
        status_text.append(impact.replace("_", " ").title(), style=f"bold {impact_color}")

        self.console.print(
            Panel(
                status_text,
                title="[bold blue]Tech Debt Analysis[/bold blue]",
                border_style=impact_color,
            )
        )

        # Delta table
        if comparison.deltas:
            self.console.print()
            delta_table = Table(title="Metric Changes", box=None, padding=(0, 2))
            delta_table.add_column("Metric", style="cyan")
            delta_table.add_column("Before", justify="right")
            delta_table.add_column("After", justify="right")
            delta_table.add_column("Change", justify="right")
            delta_table.add_column("Status", justify="center")

            for delta in comparison.deltas:
                change_str = self._format_change(delta)
                status = "[red]regression[/red]" if delta.is_regression else "[green]ok[/green]"

                delta_table.add_row(
                    self._format_metric_name(delta.metric_name),
                    f"{delta.before:.2f}",
                    f"{delta.after:.2f}",
                    change_str,
                    status,
                )

            self.console.print(delta_table)

        # New findings
        if comparison.new_findings:
            self.console.print()
            self.console.print(f"[bold red]New Issues ({len(comparison.new_findings)}):[/bold red]")
            for finding in comparison.new_findings[:10]:
                impact_style = self._get_impact_style(finding.impact)
                self.console.print(
                    f"  [{impact_style}]{finding.impact.value}[/{impact_style}] {finding.message}"
                )
            if len(comparison.new_findings) > 10:
                self.console.print(f"  [dim]... and {len(comparison.new_findings) - 10} more[/dim]")

        # Resolved findings
        if comparison.resolved_findings:
            self.console.print()
            self.console.print(
                f"[bold green]Resolved Issues ({len(comparison.resolved_findings)}):[/bold green]"
            )
            for finding in comparison.resolved_findings[:5]:
                self.console.print(f"  [dim]{finding.message}[/dim]")

    def to_yaml(self, result: AnalysisResult) -> str:
        """Convert analysis result to YAML.

        Args:
            result: Analysis result.

        Returns:
            YAML string.
        """
        data = self._result_to_dict(result)
        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    def to_json(self, result: AnalysisResult) -> str:
        """Convert analysis result to JSON.

        Args:
            result: Analysis result.

        Returns:
            JSON string.
        """
        data = self._result_to_dict(result)
        return json.dumps(data, indent=2, default=str)

    def to_markdown(self, comparison: AnalysisComparison) -> str:
        """Convert comparison to markdown report.

        Args:
            comparison: Analysis comparison.

        Returns:
            Markdown string.
        """
        lines = [
            "# Tech Debt Analysis Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Overall Impact:** {comparison.overall_impact.replace('_', ' ').title()}",
            "",
            "## Metric Changes",
            "",
            "| Metric | Before | After | Change | Status |",
            "|--------|--------|-------|--------|--------|",
        ]

        for delta in comparison.deltas:
            change_pct = f"{delta.percent_change:+.1f}%"
            status = "regression" if delta.is_regression else "ok"
            lines.append(
                f"| {self._format_metric_name(delta.metric_name)} | "
                f"{delta.before:.2f} | {delta.after:.2f} | {change_pct} | {status} |"
            )

        if comparison.new_findings:
            lines.extend(
                [
                    "",
                    f"## New Issues ({len(comparison.new_findings)})",
                    "",
                ]
            )
            for finding in comparison.new_findings:
                location = ""
                if finding.file_path:
                    location = f" (`{finding.file_path}"
                    if finding.line_number:
                        location += f":{finding.line_number}"
                    location += "`)"
                lines.append(f"- **{finding.impact.value}**: {finding.message}{location}")

        if comparison.resolved_findings:
            lines.extend(
                [
                    "",
                    f"## Resolved Issues ({len(comparison.resolved_findings)})",
                    "",
                ]
            )
            for finding in comparison.resolved_findings:
                lines.append(f"- ~~{finding.message}~~")

        return "\n".join(lines)

    def save_report(
        self,
        result: AnalysisResult | AnalysisComparison,
        output_path: Path,
        format: str = "yaml",
    ) -> None:
        """Save report to file.

        Args:
            result: Analysis result or comparison.
            output_path: Output file path.
            format: Output format (yaml, json, markdown).
        """
        if isinstance(result, AnalysisComparison):
            if format == "markdown":
                content = self.to_markdown(result)
            else:
                # Convert comparison to dict
                data = {
                    "overall_impact": result.overall_impact,
                    "before": self._result_to_dict(result.before),
                    "after": self._result_to_dict(result.after),
                    "deltas": [
                        {
                            "metric": d.metric_name,
                            "before": d.before,
                            "after": d.after,
                            "change_percent": d.percent_change,
                            "is_regression": d.is_regression,
                        }
                        for d in result.deltas
                    ],
                    "new_findings_count": len(result.new_findings),
                    "resolved_findings_count": len(result.resolved_findings),
                }
                if format == "json":
                    content = json.dumps(data, indent=2, default=str)
                else:
                    content = yaml.dump(data, default_flow_style=False, sort_keys=False)
        else:
            content = self.to_json(result) if format == "json" else self.to_yaml(result)

        output_path.write_text(content)
        self.console.print(f"[green]Report saved to {output_path}[/green]")

    def _result_to_dict(self, result: AnalysisResult) -> dict[str, Any]:
        """Convert analysis result to dictionary.

        Args:
            result: Analysis result.

        Returns:
            Dictionary representation.
        """
        m = result.metrics
        return {
            "timestamp": result.timestamp.isoformat(),
            "git_ref": result.git_ref,
            "metrics": {
                "files_analyzed": m.files_analyzed,
                "avg_cyclomatic_complexity": m.avg_cyclomatic_complexity,
                "max_cyclomatic_complexity": m.max_cyclomatic_complexity,
                "avg_maintainability_index": m.avg_maintainability_index,
                "min_maintainability_index": m.min_maintainability_index,
                "total_warnings": m.total_warnings,
                "total_errors": m.total_errors,
                "warnings_by_category": m.warnings_by_category,
                "security_issues": m.security_issues,
            },
            "findings_count": len(result.findings),
            "critical_findings": len(result.get_critical_findings()),
        }

    def _format_change(self, delta: MetricsDelta) -> str:
        """Format a metric change for display.

        Args:
            delta: Metric delta.

        Returns:
            Formatted change string.
        """
        if delta.percent_change == 0:
            return "[dim]0%[/dim]"

        sign = "+" if delta.percent_change > 0 else ""
        color = "red" if delta.is_regression else "green"
        return f"[{color}]{sign}{delta.percent_change:.1f}%[/{color}]"

    def _format_metric_name(self, name: str) -> str:
        """Format metric name for display.

        Args:
            name: Metric name.

        Returns:
            Formatted name.
        """
        return name.replace("_", " ").title()

    def _get_impact_style(self, impact: ImpactLevel) -> str:
        """Get Rich style for impact level.

        Args:
            impact: Impact level.

        Returns:
            Style string.
        """
        return {
            ImpactLevel.LOW: "dim",
            ImpactLevel.MEDIUM: "yellow",
            ImpactLevel.HIGH: "red",
            ImpactLevel.CRITICAL: "bold red",
        }.get(impact, "white")
