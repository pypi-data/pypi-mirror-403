"""Console output with Rich formatting."""

from datetime import datetime
from enum import IntEnum
from typing import Any

from rich.console import Console as RichConsole
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text

from messirve.models.execution import TaskStatus
from messirve.models.task import Task


class Verbosity(IntEnum):
    """Verbosity levels for console output."""

    QUIET = 0
    NORMAL = 1
    VERBOSE = 2
    DEBUG = 3


class Console:
    """Console output handler with Rich formatting."""

    def __init__(self, verbosity: Verbosity = Verbosity.NORMAL) -> None:
        """Initialize the console.

        Args:
            verbosity: Verbosity level for output.
        """
        self.verbosity = verbosity
        self._console = RichConsole()
        self._progress: Progress | None = None

    def print(self, message: str, level: Verbosity = Verbosity.NORMAL) -> None:
        """Print a message if verbosity allows.

        Args:
            message: Message to print.
            level: Minimum verbosity level required.
        """
        if self.verbosity >= level:
            self._console.print(message)

    def log(self, message: str, level: Verbosity = Verbosity.NORMAL) -> None:
        """Print a timestamped log message.

        Args:
            message: Message to print.
            level: Minimum verbosity level required.
        """
        if self.verbosity >= level:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self._console.print(f"[dim][{timestamp}][/dim] {message}")

    def debug(self, message: str) -> None:
        """Print a debug message.

        Args:
            message: Debug message to print.
        """
        self.log(f"[dim]{message}[/dim]", Verbosity.DEBUG)

    def verbose(self, message: str) -> None:
        """Print a verbose message.

        Args:
            message: Verbose message to print.
        """
        self.log(message, Verbosity.VERBOSE)

    def info(self, message: str) -> None:
        """Print an info message.

        Args:
            message: Info message to print.
        """
        self.log(message, Verbosity.NORMAL)

    def success(self, message: str) -> None:
        """Print a success message.

        Args:
            message: Success message to print.
        """
        self.log(f"[green]{message}[/green]", Verbosity.NORMAL)

    def warning(self, message: str) -> None:
        """Print a warning message.

        Args:
            message: Warning message to print.
        """
        self.log(f"[yellow]{message}[/yellow]", Verbosity.NORMAL)

    def error(self, message: str) -> None:
        """Print an error message.

        Args:
            message: Error message to print.
        """
        self.log(f"[red]{message}[/red]", Verbosity.QUIET)

    def print_header(self, version: str) -> None:
        """Print the application header.

        Args:
            version: Version string to display.
        """
        if self.verbosity < Verbosity.NORMAL:
            return

        header = Panel(
            Text.from_markup(
                f"[bold]MESSIRVE v{version}[/bold]\n[dim]Autonomous Task Executor[/dim]"
            ),
            border_style="blue",
        )
        self._console.print(header)
        self._console.print()

    def print_task_header(
        self,
        task: Task,
        index: int,
        total: int,
    ) -> None:
        """Print a task header.

        Args:
            task: The task being executed.
            index: Task index (1-based).
            total: Total number of tasks.
        """
        if self.verbosity < Verbosity.NORMAL:
            return

        self._console.print()
        self._console.rule(f"[bold][{index}/{total}] {task.id}: {task.title}[/bold]")

    def print_task_status(
        self,
        task: Task,
        status: TaskStatus,
        duration: float | None = None,
        tokens: int | None = None,
    ) -> None:
        """Print task completion status.

        Args:
            task: The task that completed.
            status: Final status of the task.
            duration: Duration in seconds.
            tokens: Tokens used.
        """
        status_icons = {
            TaskStatus.COMPLETED: "[green]completed[/green]",
            TaskStatus.FAILED: "[red]failed[/red]",
            TaskStatus.SKIPPED: "[yellow]skipped[/yellow]",
            TaskStatus.PENDING: "[dim]pending[/dim]",
            TaskStatus.IN_PROGRESS: "[blue]in progress[/blue]",
        }

        status_str = status_icons.get(status, str(status.value))
        parts = [f"{task.id} {status_str}"]

        if duration is not None:
            parts.append(f"({self._format_duration(duration)})")
        if tokens is not None and self.verbosity >= Verbosity.VERBOSE:
            parts.append(f"{tokens:,} tokens")

        self.log(" ".join(parts))

    def print_task_brief_summary(
        self,
        files_changed: list[str] | None = None,
        git_commits: list[str] | None = None,
        summary: str | None = None,
    ) -> None:
        """Print a brief summary after task completion.

        Args:
            files_changed: List of files that were modified.
            git_commits: List of commit hashes/messages.
            summary: Brief summary text.
        """
        if self.verbosity < Verbosity.NORMAL:
            return

        parts: list[str] = []

        if summary:
            parts.append(f"  [dim]{summary}[/dim]")

        if files_changed:
            file_count = len(files_changed)
            if file_count <= 3:
                files_str = ", ".join(files_changed)
            else:
                files_str = f"{', '.join(files_changed[:3])} (+{file_count - 3} more)"
            parts.append(f"  [dim]Files: {files_str}[/dim]")

        if git_commits:
            commit_count = len(git_commits)
            if commit_count == 1:
                parts.append(f"  [dim]Commit: {git_commits[0][:50]}[/dim]")
            else:
                parts.append(f"  [dim]Commits: {commit_count} commits[/dim]")

        for part in parts:
            self._console.print(part)

    def print_hook_result(
        self,
        command: str,
        success: bool,
        output: str | None = None,
    ) -> None:
        """Print hook execution result.

        Args:
            command: Command that was executed.
            success: Whether the hook succeeded.
            output: Hook output (for verbose mode).
        """
        if self.verbosity >= Verbosity.NORMAL:
            status = "[green]OK[/green]" if success else "[red]FAILED[/red]"
            self._console.print(f"           {command} {'.' * max(1, 50 - len(command))} {status}")

        if output and self.verbosity >= Verbosity.VERBOSE:
            self._console.print(f"[dim]{output}[/dim]")

    def print_summary(
        self,
        total_tasks: int,
        completed: int,
        failed: int,
        skipped: int,
        duration: float,
        input_tokens: int,
        output_tokens: int,
        models_used: set[str],
        task_metrics: list[dict[str, Any]],
        log_path: str,
    ) -> None:
        """Print execution summary.

        Args:
            total_tasks: Total number of tasks.
            completed: Number of completed tasks.
            failed: Number of failed tasks.
            skipped: Number of skipped tasks.
            duration: Total duration in seconds.
            input_tokens: Total input tokens used.
            output_tokens: Total output tokens used.
            models_used: Set of models used.
            task_metrics: List of per-task metrics.
            log_path: Path to log directory.
        """
        if self.verbosity < Verbosity.NORMAL:
            # Quiet mode: single line summary
            self._console.print(f"messirve: Completed {completed}/{total_tasks} tasks")
            return

        self._console.print()

        # Build summary content (mixed types for rich Group)
        content_parts: list[Any] = []

        # Basic stats
        summary = Table.grid(padding=(0, 2))
        summary.add_column(justify="right", style="bold")
        summary.add_column()

        summary.add_row("Total Tasks:", str(total_tasks))
        summary.add_row("Completed:", f"[green]{completed}[/green]")
        summary.add_row("Failed:", f"[red]{failed}[/red]" if failed else "0")
        summary.add_row("Skipped:", f"[yellow]{skipped}[/yellow]" if skipped else "0")
        summary.add_row("Duration:", self._format_duration(duration))

        content_parts.append(summary)

        # Token usage section
        total_tokens = input_tokens + output_tokens
        if total_tokens > 0:
            content_parts.append(Text())  # Spacer

            token_table = Table.grid(padding=(0, 2))
            token_table.add_column(justify="right", style="bold")
            token_table.add_column()

            # If single model, show consolidated view
            if len(models_used) == 1:
                model = list(models_used)[0]
                token_table.add_row("Model:", model or "unknown")
                token_table.add_row("Input Tokens:", f"{input_tokens:,}")
                token_table.add_row("Output Tokens:", f"{output_tokens:,}")
            else:
                # Multiple models - show total only here, per-task below
                token_table.add_row("Input Tokens:", f"{input_tokens:,}")
                token_table.add_row("Output Tokens:", f"{output_tokens:,}")

            content_parts.append(token_table)

        # Per-task breakdown
        if task_metrics:
            content_parts.append(Text())  # Spacer
            content_parts.append(Text("Task Breakdown:", style="bold"))

            task_table = Table(
                show_header=True,
                header_style="bold",
                box=None,
                padding=(0, 1),
            )
            task_table.add_column("Task", style="cyan")
            task_table.add_column("Status", justify="center")
            task_table.add_column("Duration", justify="right")
            task_table.add_column("In/Out Tokens", justify="right")
            if len(models_used) > 1:
                task_table.add_column("Model", style="dim")

            for m in task_metrics:
                status_icon = {
                    "completed": "[green]v[/green]",
                    "failed": "[red]x[/red]",
                    "skipped": "[yellow]-[/yellow]",
                }.get(m["status"], "?")

                row = [
                    m["task_id"],
                    status_icon,
                    self._format_duration(m["duration"]),
                    f"{m['input_tokens']:,}/{m['output_tokens']:,}",
                ]
                if len(models_used) > 1:
                    row.append(m.get("model", "")[:20])

                task_table.add_row(*row)

            content_parts.append(task_table)

        # Logs path
        content_parts.append(Text())  # Spacer
        logs_grid = Table.grid(padding=(0, 2))
        logs_grid.add_column(justify="right", style="bold")
        logs_grid.add_column(style="dim")
        logs_grid.add_row("Logs:", log_path)
        content_parts.append(logs_grid)

        # Create panel with all content
        from rich.console import Group

        panel = Panel(
            Group(*content_parts),
            title="[bold]EXECUTION COMPLETE[/bold]",
            border_style="green" if failed == 0 else "red",
        )
        self._console.print(panel)

    def print_quiet_task(
        self,
        task_id: str,
        index: int,
        total: int,
        status: TaskStatus,
        error: str | None = None,
    ) -> None:
        """Print task status in quiet mode.

        Args:
            task_id: Task ID.
            index: Task index (1-based).
            total: Total number of tasks.
            status: Task status.
            error: Error message if failed.
        """
        status_char = {
            TaskStatus.COMPLETED: "[green]v[/green]",
            TaskStatus.FAILED: "[red]x[/red]",
            TaskStatus.SKIPPED: "[yellow]-[/yellow]",
        }.get(status, "?")

        line = f"messirve: [{index}/{total}] {task_id} {status_char}"
        if error:
            line += f" ({error})"
        self._console.print(line)

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

    def start_progress(self, description: str) -> None:
        """Start a progress indicator.

        Args:
            description: Description for the progress.
        """
        if self.verbosity >= Verbosity.NORMAL:
            self._progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
                console=self._console,
            )
            self._progress.start()
            self._progress.add_task(description, total=None)

    def stop_progress(self) -> None:
        """Stop the progress indicator."""
        if self._progress:
            self._progress.stop()
            self._progress = None

    def stream_output(self, line: str) -> None:
        """Stream output line (for verbose mode).

        Args:
            line: Output line to stream.
        """
        if self.verbosity >= Verbosity.VERBOSE:
            self._console.print(f"[dim]{line.rstrip()}[/dim]")
