"""Task-specific logging."""

import json
from pathlib import Path

from messirve.models.execution import ExecutionResult, TaskStatus


class TaskLogger:
    """Logger for individual task execution."""

    def __init__(self, log_dir: Path, run_id: str) -> None:
        """Initialize the task logger.

        Args:
            log_dir: Base log directory.
            run_id: ID of the current run.
        """
        self.log_dir = log_dir / "runs" / run_id
        self.run_id = run_id
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def save_result(self, result: ExecutionResult) -> None:
        """Save task execution result.

        Args:
            result: ExecutionResult to save.
        """
        # Save JSON format
        json_path = self.log_dir / f"{result.task_id}.json"
        with open(json_path, "w") as f:
            json.dump(result.to_dict(), f, indent=2)

        # Save Markdown format
        md_path = self.log_dir / f"{result.task_id}.md"
        with open(md_path, "w") as f:
            f.write(self._generate_markdown(result))

    def _generate_markdown(self, result: ExecutionResult) -> str:
        """Generate markdown log for a task.

        Args:
            result: ExecutionResult to convert.

        Returns:
            Markdown formatted string.
        """
        lines: list[str] = []

        # Header
        lines.append(f"# Task Log: {result.task_id}")
        lines.append("")
        lines.append(f"## Task: {result.title}")
        lines.append("")

        # Status
        status_icon = {
            TaskStatus.COMPLETED: "v Completed",
            TaskStatus.FAILED: "x Failed",
            TaskStatus.SKIPPED: "- Skipped",
            TaskStatus.PENDING: "o Pending",
            TaskStatus.IN_PROGRESS: "... In Progress",
        }.get(result.status, result.status.value)

        lines.append(f"**Status:** {status_icon}")
        lines.append(f"**Run ID:** {result.run_id}")

        if result.attempts:
            total_duration = sum(a.duration_seconds for a in result.attempts)
            lines.append(f"**Duration:** {self._format_duration(total_duration)}")
            lines.append(f"**Attempts:** {len(result.attempts)}")

        lines.append("")
        lines.append("---")
        lines.append("")

        # Attempts
        for attempt in result.attempts:
            lines.append(f"## Attempt {attempt.attempt_number}")
            lines.append("")
            lines.append(f"**Started:** {attempt.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
            if attempt.completed_at:
                lines.append(f"**Completed:** {attempt.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"**Duration:** {self._format_duration(attempt.duration_seconds)}")
            lines.append(f"**Outcome:** {attempt.outcome}")
            lines.append("")

            # Prompt
            if attempt.prompt:
                lines.append("### Prompt")
                lines.append("")
                lines.append("```")
                lines.append(attempt.prompt)
                lines.append("```")
                lines.append("")

            # Claude Code Output
            if attempt.claude_code_output:
                lines.append("### Claude Code Response")
                lines.append("")
                lines.append("```")
                lines.append(attempt.claude_code_output)
                lines.append("```")
                lines.append("")

            # Pre-task hooks
            if attempt.pre_task_hooks:
                lines.append("### Pre-Task Hooks")
                lines.append("")
                lines.append("| Command | Status | Duration |")
                lines.append("|---------|--------|----------|")
                for hook in attempt.pre_task_hooks:
                    status = "Pass" if hook.success else "Fail"
                    lines.append(f"| `{hook.command}` | {status} | {hook.duration_seconds:.1f}s |")
                lines.append("")

            # Post-task hooks
            if attempt.post_task_hooks:
                lines.append("### Post-Task Hooks")
                lines.append("")
                lines.append("| Command | Status | Duration |")
                lines.append("|---------|--------|----------|")
                for hook in attempt.post_task_hooks:
                    status = "Pass" if hook.success else "Fail"
                    lines.append(f"| `{hook.command}` | {status} | {hook.duration_seconds:.1f}s |")
                lines.append("")

            # Error
            if attempt.error:
                lines.append("### Error")
                lines.append("")
                lines.append(f"```\n{attempt.error}\n```")
                lines.append("")

            lines.append("---")
            lines.append("")

        # Files changed
        if result.files_changed:
            lines.append("## Files Changed")
            lines.append("")
            for file in result.files_changed:
                lines.append(f"- `{file}`")
            lines.append("")

        # Git info
        if result.git_info.branch or result.git_info.commits:
            lines.append("## Git")
            lines.append("")
            if result.git_info.branch:
                lines.append(f"- **Branch:** `{result.git_info.branch}`")
            for commit in result.git_info.commits:
                lines.append(
                    f"- **Commit:** `{commit.get('sha', '')}` - {commit.get('message', '')}"
                )
            if result.git_info.pr_url:
                lines.append(f"- **PR:** {result.git_info.pr_url}")
            lines.append("")

        # Summary
        if result.summary:
            lines.append("## Summary")
            lines.append("")
            lines.append(result.summary)
            lines.append("")

        # Code Quality Analysis
        if result.analysis_result:
            lines.append("## Code Quality Analysis")
            lines.append("")
            metrics = result.analysis_result.get("metrics", {})

            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")

            avg_cc = metrics.get("avg_cyclomatic_complexity", 0)
            lines.append(f"| Avg Cyclomatic Complexity | {avg_cc:.2f} |")

            avg_mi = metrics.get("avg_maintainability_index", 100)
            lines.append(f"| Avg Maintainability Index | {avg_mi:.1f} |")

            warnings = metrics.get("total_warnings", 0)
            lines.append(f"| Warnings | {warnings} |")

            errors = metrics.get("total_errors", 0)
            lines.append(f"| Errors | {errors} |")

            files_analyzed = metrics.get("files_analyzed", 0)
            lines.append(f"| Files Analyzed | {files_analyzed} |")

            lines.append("")

            # Critical findings
            findings = result.analysis_result.get("findings", [])
            critical = [f for f in findings if f.get("impact") in ("critical", "high")]
            if critical:
                lines.append("### Critical/High Findings")
                lines.append("")
                for finding in critical[:10]:
                    impact = finding.get("impact", "")
                    message = finding.get("message", "")
                    file_path = finding.get("file_path", "")
                    line_num = finding.get("line_number", "")
                    location = f" (`{file_path}:{line_num}`)" if file_path else ""
                    lines.append(f"- **{impact.upper()}**: {message}{location}")
                if len(critical) > 10:
                    lines.append(f"\n*...and {len(critical) - 10} more findings*")
                lines.append("")

        # Tokens & Cost
        if result.attempts:
            total_tokens = sum(a.tokens_used for a in result.attempts)
            total_cost = sum(a.cost_usd for a in result.attempts)
            if total_tokens > 0 or total_cost > 0:
                lines.append("## Tokens & Cost")
                lines.append("")
                lines.append(f"- **Tokens Used:** {total_tokens:,}")
                lines.append(f"- **Cost:** ${total_cost:.2f}")
                lines.append("")

        return "\n".join(lines)

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format.

        Args:
            seconds: Duration in seconds.

        Returns:
            Formatted duration string.
        """
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
