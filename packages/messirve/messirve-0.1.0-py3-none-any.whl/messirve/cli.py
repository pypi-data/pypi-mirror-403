"""Typer CLI commands for Messirve."""

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console as RichConsole
from rich.table import Table

from messirve import __version__
from messirve import config as config_module
from messirve.exceptions import (
    ConfigurationError,
    MessirveError,
    TaskFileError,
)
from messirve.executor import Executor
from messirve.logging.console import Console, Verbosity
from messirve.models.config import (
    ClaudePermissions,
    GitStrategy,
)
from messirve.models.task import Task, TaskFlavor, TaskHooks
from messirve.task_sources.yaml_source import YamlTaskSource
from messirve.templates import get_all_templates, get_template

# Create Typer app
app = typer.Typer(
    name="messirve",
    help="Autonomous Task Executor using Claude Code",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Config subcommand
config_app = typer.Typer(
    name="config",
    help="Configuration management commands",
    no_args_is_help=True,
)
app.add_typer(config_app, name="config")

# Rich console for output
rich_console = RichConsole()


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        rich_console.print(f"messirve version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
    ] = False,
) -> None:
    """Messirve - Autonomous Task Executor using Claude Code."""
    pass


# =============================================================================
# RUN COMMAND
# =============================================================================


@app.command()
def run(
    tasks: Annotated[
        Path,
        typer.Option(
            "--tasks",
            "-t",
            help="Path to tasks YAML file",
            exists=True,
        ),
    ] = Path("tasks.yaml"),
    task: Annotated[
        list[str] | None,
        typer.Option(
            "--task",
            help="Specific task ID(s) to run",
        ),
    ] = None,
    git_strategy: Annotated[
        str | None,
        typer.Option(
            "--git-strategy",
            "-g",
            help="Git strategy: none, commit-per-task, branch-per-task, single-branch",
        ),
    ] = None,
    base_branch: Annotated[
        str | None,
        typer.Option(
            "--base-branch",
            help="Base branch for git operations",
        ),
    ] = None,
    create_pr: Annotated[
        bool,
        typer.Option(
            "--create-pr",
            help="Create pull request after completion",
        ),
    ] = False,
    draft_pr: Annotated[
        bool,
        typer.Option(
            "--draft-pr",
            help="Create draft pull request",
        ),
    ] = False,
    max_retries: Annotated[
        int | None,
        typer.Option(
            "--max-retries",
            "-r",
            help="Maximum retries per task",
        ),
    ] = None,
    claude_permissions: Annotated[
        str | None,
        typer.Option(
            "--claude-permissions",
            help="Claude Code permission mode: skip or ask",
        ),
    ] = None,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Minimal output",
        ),
    ] = False,
    verbose: Annotated[
        int,
        typer.Option(
            "--verbose",
            "-v",
            count=True,
            help="Increase verbosity (-v, -vv, -vvv)",
        ),
    ] = 0,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-n",
            help="Show what would execute without running",
        ),
    ] = False,
    continue_run: Annotated[
        bool,
        typer.Option(
            "--continue",
            help="Continue from failed task",
        ),
    ] = False,
    analyze: Annotated[
        bool,
        typer.Option(
            "--analyze",
            "-a",
            help="Run tech debt analysis before and after execution",
        ),
    ] = False,
    fail_on_regression: Annotated[
        bool,
        typer.Option(
            "--fail-on-regression",
            help="Fail if analysis shows quality regression (requires --analyze)",
        ),
    ] = False,
    all_tasks: Annotated[
        bool,
        typer.Option(
            "--all",
            help="Run all tasks including already completed ones",
        ),
    ] = False,
) -> None:
    """Execute tasks from a YAML file."""
    try:
        # Load config
        config = config_module.load_config()

        # Apply CLI overrides
        if git_strategy:
            try:
                config.defaults.git_strategy = GitStrategy(git_strategy)
            except ValueError:
                raise typer.BadParameter(
                    f"Invalid git strategy: {git_strategy}. "
                    "Valid options: none, commit-per-task, branch-per-task, single-branch"
                )

        if base_branch:
            config.defaults.base_branch = base_branch

        if create_pr:
            config.defaults.create_pr = True

        if draft_pr:
            config.defaults.draft_pr = True

        if max_retries is not None:
            config.defaults.max_retries = max_retries

        if claude_permissions:
            try:
                config.defaults.claude_code_permissions = ClaudePermissions(claude_permissions)
            except ValueError:
                raise typer.BadParameter(
                    f"Invalid permission mode: {claude_permissions}. Valid options: skip, ask"
                )

        # Determine verbosity
        if quiet:
            verbosity = Verbosity.QUIET
        elif verbose >= 3:
            verbosity = Verbosity.DEBUG
        elif verbose >= 2:
            verbosity = Verbosity.VERBOSE
        elif verbose >= 1:
            verbosity = Verbosity.NORMAL
        else:
            verbosity = Verbosity.NORMAL

        # Create console
        console = Console(verbosity)
        console.print_header(__version__)

        # Check if production-ready flavor is used (auto-enables analysis)
        run_analysis = analyze
        if not run_analysis:
            # Check if any task uses production-ready flavor
            try:
                source = YamlTaskSource()
                loaded_tasks = source.load(tasks)
                for t in loaded_tasks:
                    if t.flavor == TaskFlavor.PRODUCTION_READY:
                        run_analysis = True
                        rich_console.print(
                            "[dim]Auto-enabling analysis for production-ready tasks[/dim]"
                        )
                        break
            except Exception:
                pass  # Ignore errors, will be caught later

        # Capture baseline if analysis is enabled
        baseline = None
        analysis_runner = None
        if run_analysis:
            from messirve.analysis import AnalysisConfig, AnalysisRunner, ReportGenerator

            rich_console.print("[bold]Pre-execution analysis...[/bold]")
            analysis_config = AnalysisConfig(
                paths=[Path(".")],
                fail_on_regression=fail_on_regression,
            )
            analysis_runner = AnalysisRunner(analysis_config, rich_console)
            baseline = analysis_runner.capture_baseline()

        # Create and run executor
        executor = Executor(config, console)
        summary = executor.run(
            tasks_file=tasks,
            task_ids=task,
            dry_run=dry_run,
            continue_from=continue_run,
            skip_completed=not all_tasks,
        )

        # Run post-execution analysis
        if run_analysis and baseline and analysis_runner:
            rich_console.print()
            rich_console.print("[bold]Post-execution analysis...[/bold]")
            comparison = analysis_runner.compare_to_baseline(baseline)

            report_gen = ReportGenerator(rich_console)
            report_gen.print_comparison(comparison)

            # Fail if regression and flag is set
            if fail_on_regression and comparison.has_regressions:
                rich_console.print(
                    "[red]Error:[/red] Quality regression detected. "
                    "Use --no-fail-on-regression to ignore."
                )
                raise typer.Exit(1)

        # Print summary
        task_metrics = [
            {
                "task_id": m.task_id,
                "status": m.status,
                "duration": m.duration_seconds,
                "input_tokens": m.input_tokens,
                "output_tokens": m.output_tokens,
                "model": m.model,
            }
            for m in summary.get_task_metrics()
        ]
        console.print_summary(
            total_tasks=summary.total_tasks,
            completed=summary.completed_tasks,
            failed=summary.failed_tasks,
            skipped=summary.skipped_tasks,
            duration=summary.total_duration_seconds,
            input_tokens=summary.total_input_tokens,
            output_tokens=summary.total_output_tokens,
            models_used=summary.get_models_used(),
            task_metrics=task_metrics,
            log_path=str(config_module.get_log_dir() / "runs" / summary.run_id),
        )

        # Exit with error if tasks failed
        if summary.failed_tasks > 0:
            raise typer.Exit(1)

    except MessirveError as e:
        rich_console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)
    except FileNotFoundError as e:
        rich_console.print(f"[red]Error:[/red] File not found: {e}")
        raise typer.Exit(1)


# =============================================================================
# TASK COMMANDS
# =============================================================================


# =============================================================================
# PLANNING COMMAND
# =============================================================================


@app.command("planning")
def planning(
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output file path for generated tasks",
        ),
    ] = None,
    goal: Annotated[
        list[str] | None,
        typer.Option(
            "--goal",
            "-g",
            help="Goals to accomplish (can be specified multiple times)",
        ),
    ] = None,
    non_interactive: Annotated[
        bool,
        typer.Option(
            "--non-interactive",
            help="Skip interactive editing (for CI/scripting)",
        ),
    ] = False,
    project_dir: Annotated[
        Path,
        typer.Option(
            "--project",
            "-p",
            help="Project directory (default: current directory)",
        ),
    ] = Path("."),
) -> None:
    """Start an interactive planning session to generate tasks from goals.

    This command helps you turn high-level goals into structured tasks.
    You provide broad goals (e.g., "improve performance of OCR pipeline"),
    and Claude generates concrete, actionable tasks with descriptions
    and acceptance criteria.

    Examples:

        # Interactive mode (recommended)
        messirve planning

        # With pre-specified goals
        messirve planning -g "Add user authentication" -g "Improve test coverage"

        # Non-interactive (for CI/scripting)
        messirve planning --goal "Add caching" --non-interactive -o tasks.yaml
    """
    from messirve.planning.session import PlanningOrchestrator

    project_path = project_dir.resolve()

    if not project_path.exists():
        rich_console.print(f"[red]Error:[/red] Directory not found: {project_path}")
        raise typer.Exit(1)

    orchestrator = PlanningOrchestrator(
        console=rich_console,
        project_dir=project_path,
    )

    result = orchestrator.run(
        output_path=output,
        goals=goal,
        non_interactive=non_interactive,
    )

    if result is None:
        raise typer.Exit(1)


# =============================================================================
# CREATE TASK COMMAND
# =============================================================================


@app.command("create-task")
def create_task(
    task_id: Annotated[
        str | None,
        typer.Option(
            "--id",
            help="Task ID",
        ),
    ] = None,
    title: Annotated[
        str | None,
        typer.Option(
            "--title",
            help="Task title",
        ),
    ] = None,
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Output file for the task",
        ),
    ] = Path("tasks.yaml"),
) -> None:
    """Create a new task interactively or with inline values."""
    # Get task details
    if not task_id:
        task_id = typer.prompt("Task ID (e.g., TASK-001)")

    if not title:
        title = typer.prompt("Task title")

    description = typer.prompt("Task description", default="")
    context = typer.prompt("Task context", default="")

    # Get acceptance criteria
    criteria: list[str] = []
    rich_console.print("Enter acceptance criteria (empty line to finish):")
    while True:
        criterion = typer.prompt("  -", default="")
        if not criterion:
            break
        criteria.append(criterion)

    if not criteria:
        criteria = [typer.prompt("At least one criterion required")]

    # Get dependencies
    depends_str = typer.prompt("Dependencies (comma-separated task IDs)", default="")
    depends_on = [d.strip() for d in depends_str.split(",") if d.strip()]

    # Create task
    new_task = Task(
        id=task_id,
        title=title,
        description=description,
        context=context,
        acceptance_criteria=criteria,
        depends_on=depends_on,
        hooks=TaskHooks(),
    )

    # Load existing tasks or create new file
    source = YamlTaskSource()
    tasks: list[Task] = []

    if output.exists():
        try:
            tasks = source.load(output)
        except TaskFileError:
            tasks = []

    # Check for duplicate ID
    existing_ids = {t.id for t in tasks}
    if new_task.id in existing_ids:
        rich_console.print(f"[yellow]Warning:[/yellow] Task {new_task.id} already exists")
        if not typer.confirm("Replace existing task?"):
            raise typer.Exit(0)
        tasks = [t for t in tasks if t.id != new_task.id]

    tasks.append(new_task)

    # Save
    source.save(tasks, output)
    rich_console.print(f"[green]Task {new_task.id} saved to {output}[/green]")


@app.command("list-tasks")
def list_tasks(
    tasks: Annotated[
        Path,
        typer.Option(
            "--tasks",
            "-t",
            help="Path to tasks YAML file",
        ),
    ] = Path("tasks.yaml"),
    all_tasks: Annotated[
        bool,
        typer.Option(
            "--all",
            help="Show all tasks including completed ones",
        ),
    ] = False,
) -> None:
    """List tasks from a file."""
    if not tasks.exists():
        rich_console.print(f"[red]Error:[/red] Tasks file not found: {tasks}")
        raise typer.Exit(1)

    try:
        source = YamlTaskSource()
        task_list = source.load(tasks)

        # Count completed and pending
        completed_count = sum(1 for t in task_list if t.done)
        pending_count = len(task_list) - completed_count

        # Filter if not showing all
        if not all_tasks:
            task_list = [t for t in task_list if not t.done]

        table = Table(title=f"Tasks in {tasks}")
        table.add_column("Status", style="dim")
        table.add_column("ID", style="cyan")
        table.add_column("Title")
        table.add_column("Dependencies")
        table.add_column("Criteria")

        for task in task_list:
            deps = ", ".join(task.depends_on) if task.depends_on else "-"
            status = "[green][x][/green]" if task.done else "[ ]"
            table.add_row(
                status,
                task.id,
                task.title,
                deps,
                str(len(task.acceptance_criteria)),
            )

        rich_console.print(table)

        if all_tasks:
            rich_console.print(
                f"\nTotal: {completed_count + pending_count} tasks "
                f"({completed_count} completed, {pending_count} pending)"
            )
        else:
            if completed_count > 0:
                rich_console.print(
                    f"\nShowing {pending_count} pending task(s). "
                    f"Use --all to show {completed_count} completed task(s)."
                )
            else:
                rich_console.print(f"\nTotal: {pending_count} tasks (none completed)")

    except TaskFileError as e:
        rich_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("show-task")
def show_task(
    task_id: Annotated[str, typer.Argument(help="Task ID to show")],
    tasks: Annotated[
        Path,
        typer.Option(
            "--tasks",
            "-t",
            help="Path to tasks YAML file",
        ),
    ] = Path("tasks.yaml"),
) -> None:
    """Show details of a specific task."""
    if not tasks.exists():
        rich_console.print(f"[red]Error:[/red] Tasks file not found: {tasks}")
        raise typer.Exit(1)

    try:
        source = YamlTaskSource()
        task_list = source.load(tasks)

        task = next((t for t in task_list if t.id == task_id), None)
        if not task:
            rich_console.print(f"[red]Error:[/red] Task not found: {task_id}")
            raise typer.Exit(1)

        rich_console.print(f"\n[bold cyan]{task.id}[/bold cyan]: {task.title}")
        rich_console.print(f"\n[bold]Description:[/bold]\n{task.description}")
        rich_console.print(f"\n[bold]Context:[/bold]\n{task.context}")
        rich_console.print("\n[bold]Acceptance Criteria:[/bold]")
        for criterion in task.acceptance_criteria:
            rich_console.print(f"  - {criterion}")

        if task.depends_on:
            rich_console.print(f"\n[bold]Dependencies:[/bold] {', '.join(task.depends_on)}")

        if task.hooks.pre_task or task.hooks.post_task:
            rich_console.print("\n[bold]Hooks:[/bold]")
            if task.hooks.pre_task:
                rich_console.print(f"  Pre-task: {task.hooks.pre_task}")
            if task.hooks.post_task:
                rich_console.print(f"  Post-task: {task.hooks.post_task}")

        rich_console.print()

    except TaskFileError as e:
        rich_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("reset-tasks")
def reset_tasks(
    tasks: Annotated[
        Path,
        typer.Option(
            "--tasks",
            "-t",
            help="Path to tasks YAML file",
        ),
    ] = Path("tasks.yaml"),
    task_id: Annotated[
        str | None,
        typer.Option(
            "--task",
            help="Reset a specific task by ID (default: reset all)",
        ),
    ] = None,
) -> None:
    """Reset completion status of tasks.

    By default, resets all tasks to not completed. Use --task to reset a specific task.

    Examples:

        # Reset all tasks
        messirve reset-tasks

        # Reset a specific task
        messirve reset-tasks --task TASK-001
    """
    if not tasks.exists():
        rich_console.print(f"[red]Error:[/red] Tasks file not found: {tasks}")
        raise typer.Exit(1)

    try:
        source = YamlTaskSource()

        if task_id:
            # Reset a specific task
            if source.reset_task(tasks, task_id):
                rich_console.print(f"[green]Reset task:[/green] {task_id}")
            else:
                rich_console.print(f"[red]Error:[/red] Task not found: {task_id}")
                raise typer.Exit(1)
        else:
            # Reset all tasks
            count = source.reset_all_tasks(tasks)
            if count > 0:
                rich_console.print(f"[green]Reset {count} task(s)[/green]")
            else:
                rich_console.print("[dim]No completed tasks to reset[/dim]")

    except TaskFileError as e:
        rich_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("validate")
def validate(
    tasks: Annotated[
        Path,
        typer.Option(
            "--tasks",
            "-t",
            help="Path to tasks YAML file",
        ),
    ] = Path("tasks.yaml"),
) -> None:
    """Validate a tasks file."""
    if not tasks.exists():
        rich_console.print(f"[red]Error:[/red] Tasks file not found: {tasks}")
        raise typer.Exit(1)

    try:
        source = YamlTaskSource()
        task_list = source.load(tasks)
        errors = source.validate(task_list)

        if errors:
            rich_console.print("[red]Validation failed:[/red]")
            for error in errors:
                rich_console.print(f"  - {error}")
            raise typer.Exit(1)
        else:
            rich_console.print(
                f"[green]Validation passed:[/green] {len(task_list)} tasks are valid"
            )

    except TaskFileError as e:
        rich_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


# =============================================================================
# CONFIG COMMANDS
# =============================================================================


@app.command("init")
def init(
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Overwrite existing configuration",
        ),
    ] = False,
) -> None:
    """Initialize messirve in the current project."""
    try:
        config_path = config_module.init_config(force=force)
        rich_console.print(f"[green]Configuration created:[/green] {config_path}")
        rich_console.print("\nNext steps:")
        rich_console.print("  1. Edit .messirve/config.yaml to customize settings")
        rich_console.print("  2. Create tasks.yaml with your tasks")
        rich_console.print("  3. Run: messirve run")

    except ConfigurationError as e:
        rich_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@config_app.command("show")
def config_show() -> None:
    """Show current configuration."""
    try:
        config = config_module.load_config()

        rich_console.print("\n[bold]Current Configuration:[/bold]")
        rich_console.print(f"\n{config.to_yaml()}")

    except ConfigurationError as e:
        rich_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@config_app.command("set")
def config_set(
    key: Annotated[str, typer.Argument(help="Configuration key (e.g., defaults.max_retries)")],
    value: Annotated[str, typer.Argument(help="Value to set")],
) -> None:
    """Set a configuration value."""
    try:
        config_module.set_config_value(key, value)
        rich_console.print(f"[green]Set {key} = {value}[/green]")

    except ConfigurationError as e:
        rich_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@config_app.command("add-rule")
def config_add_rule(
    rule: Annotated[str, typer.Argument(help="Rule to add")],
) -> None:
    """Add a project rule."""
    try:
        config_module.add_rule(rule)
        rich_console.print(f"[green]Added rule:[/green] {rule}")

    except ConfigurationError as e:
        rich_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@config_app.command("add-boundary")
def config_add_boundary(
    pattern: Annotated[str, typer.Argument(help="Glob pattern to add")],
    boundary_type: Annotated[
        str,
        typer.Option(
            "--type",
            "-t",
            help="Boundary type: never_modify or read_only",
        ),
    ] = "never_modify",
) -> None:
    """Add a file boundary pattern."""
    try:
        config_module.add_boundary(pattern, boundary_type)
        rich_console.print(f"[green]Added {boundary_type} boundary:[/green] {pattern}")

    except ConfigurationError as e:
        rich_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


# =============================================================================
# LOG COMMANDS
# =============================================================================


@app.command("logs")
def logs(
    run_id: Annotated[
        str | None,
        typer.Option(
            "--run",
            help="Show specific run",
        ),
    ] = None,
    task_id: Annotated[
        str | None,
        typer.Option(
            "--task",
            help="Show specific task log",
        ),
    ] = None,
    limit: Annotated[
        int,
        typer.Option(
            "--limit",
            "-n",
            help="Maximum runs to show",
        ),
    ] = 10,
) -> None:
    """Show execution history."""
    from messirve.logging.master_logger import MasterLogger

    log_dir = config_module.get_log_dir()
    logger = MasterLogger(log_dir)

    if task_id and run_id:
        # Show specific task log
        task_log_path = log_dir / "runs" / run_id / f"{task_id}.md"
        if task_log_path.exists():
            rich_console.print(task_log_path.read_text())
        else:
            rich_console.print(f"[red]Error:[/red] Task log not found: {task_log_path}")
            raise typer.Exit(1)
        return

    if run_id:
        # Show specific run
        run = logger.get_run(run_id)
        if not run:
            rich_console.print(f"[red]Error:[/red] Run not found: {run_id}")
            raise typer.Exit(1)

        rich_console.print(f"\n[bold]Run: {run_id}[/bold]")
        rich_console.print(f"Status: {run.get('status', 'unknown')}")
        rich_console.print(f"Started: {run.get('started_at', 'unknown')}")
        rich_console.print(
            f"Tasks: {run.get('completed_tasks', 0)}/{run.get('total_tasks', 0)} completed"
        )

        if run.get("task_refs"):
            rich_console.print("\nTasks:")
            for ref in run["task_refs"]:
                status_icon = "[green]v[/green]" if ref["status"] == "completed" else "[red]x[/red]"
                rich_console.print(f"  {status_icon} {ref['task_id']}")
        return

    # Show run history
    runs = logger.get_runs(limit=limit)

    if not runs:
        rich_console.print("No execution history found.")
        return

    table = Table(title="Execution History")
    table.add_column("Run ID", style="cyan")
    table.add_column("Status")
    table.add_column("Tasks")
    table.add_column("Duration")
    table.add_column("Started")

    for run in runs:
        status = run.get("status", "unknown")
        status_style = (
            "green" if status == "completed" else "red" if status == "failed" else "yellow"
        )

        completed = run.get("completed_tasks", 0)
        total = run.get("total_tasks", 0)
        failed = run.get("failed_tasks", 0)

        duration = run.get("total_duration_seconds", 0)
        if duration < 60:
            duration_str = f"{duration:.0f}s"
        elif duration < 3600:
            duration_str = f"{duration // 60:.0f}m"
        else:
            duration_str = f"{duration // 3600:.0f}h {(duration % 3600) // 60:.0f}m"

        started = run.get("started_at", "")[:19].replace("T", " ")

        table.add_row(
            run.get("run_id", "unknown"),
            f"[{status_style}]{status}[/{status_style}]",
            f"{completed}/{total}" + (f" ({failed} failed)" if failed else ""),
            duration_str,
            started,
        )

    rich_console.print(table)


@app.command("report")
def report(
    format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format: json or markdown",
        ),
    ] = "markdown",
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output file",
        ),
    ] = None,
    run_id: Annotated[
        str | None,
        typer.Option(
            "--run",
            help="Run ID to report on (default: latest)",
        ),
    ] = None,
) -> None:
    """Export execution report."""
    from messirve.logging.master_logger import MasterLogger

    log_dir = config_module.get_log_dir()
    logger = MasterLogger(log_dir)

    # Get run
    if run_id:
        run = logger.get_run(run_id)
    else:
        runs = logger.get_runs(limit=1)
        run = runs[0] if runs else None

    if not run:
        rich_console.print("[red]Error:[/red] No runs found")
        raise typer.Exit(1)

    # Generate report
    if format == "json":
        content = json.dumps(run, indent=2)
        if output:
            output.write_text(content)
            rich_console.print(f"[green]Report saved to {output}[/green]")
        else:
            rich_console.print(content)

    elif format == "markdown":
        lines = [
            "# Messirve Execution Report",
            "",
            f"## Run: {run.get('run_id', 'unknown')}",
            "",
            f"- **Status:** {run.get('status', 'unknown')}",
            f"- **Started:** {run.get('started_at', 'unknown')}",
            f"- **Completed:** {run.get('completed_at', 'unknown')}",
            f"- **Tasks File:** {run.get('tasks_file', 'unknown')}",
            f"- **Git Strategy:** {run.get('git_strategy', 'unknown')}",
            "",
            "## Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Total Tasks | {run.get('total_tasks', 0)} |",
            f"| Completed | {run.get('completed_tasks', 0)} |",
            f"| Failed | {run.get('failed_tasks', 0)} |",
            f"| Skipped | {run.get('skipped_tasks', 0)} |",
            f"| Duration | {run.get('total_duration_seconds', 0):.0f}s |",
            f"| Tokens Used | {run.get('total_tokens_used', 0):,} |",
            f"| Cost | ${run.get('total_cost_usd', 0):.2f} |",
            "",
            "## Tasks",
            "",
        ]

        for ref in run.get("task_refs", []):
            status_icon = "v" if ref["status"] == "completed" else "x"
            lines.append(f"- [{status_icon}] **{ref['task_id']}** - {ref['status']}")

        content = "\n".join(lines)

        if output:
            output.write_text(content)
            rich_console.print(f"[green]Report saved to {output}[/green]")
        else:
            rich_console.print(content)

    else:
        rich_console.print(f"[red]Error:[/red] Unknown format: {format}")
        raise typer.Exit(1)


# =============================================================================
# TEMPLATE COMMANDS
# =============================================================================


@app.command("list-templates")
def list_templates() -> None:
    """List all available task templates."""
    templates = get_all_templates()

    table = Table(title="Available Templates")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Tasks", justify="right", style="green")

    for name, template in sorted(templates.items()):
        table.add_row(
            name,
            template.get("description", ""),
            str(len(template.get("tasks", []))),
        )

    rich_console.print(table)
    rich_console.print(
        "\n[dim]Use 'messirve generate --template <name>' to create a tasks file[/dim]"
    )


@app.command("show-template")
def show_template(
    name: Annotated[str, typer.Argument(help="Template name")],
) -> None:
    """Show details of a specific template."""
    template = get_template(name)

    if not template:
        rich_console.print(f"[red]Error:[/red] Template '{name}' not found")
        rich_console.print("\nAvailable templates:")
        for tpl_name in sorted(get_all_templates().keys()):
            rich_console.print(f"  - {tpl_name}")
        raise typer.Exit(1)

    rich_console.print(f"\n[bold cyan]{template.get('name', name)}[/bold cyan]")
    rich_console.print(f"[dim]{template.get('description', '')}[/dim]\n")

    tasks = template.get("tasks", [])
    rich_console.print(f"[bold]Tasks ({len(tasks)}):[/bold]\n")

    for task in tasks:
        deps = task.get("depends_on", [])
        deps_str = f" [dim](depends on: {', '.join(deps)})[/dim]" if deps else ""
        flavor = task.get("flavor", "production-ready")

        rich_console.print(f"  [cyan]{task['id']}[/cyan]: {task['title']}{deps_str}")
        rich_console.print(f"    [dim]Flavor: {flavor}[/dim]")
        rich_console.print()


@app.command("generate")
def generate(
    template_name: Annotated[
        str,
        typer.Option(
            "--template",
            "-t",
            help="Template name to use",
        ),
    ] = "example",
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Output file path",
        ),
    ] = Path("tasks.yaml"),
    flavor: Annotated[
        str | None,
        typer.Option(
            "--flavor",
            "-f",
            help="Override flavor for all tasks (production-ready, poc, documentation, etc.)",
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Overwrite existing file",
        ),
    ] = False,
) -> None:
    """Generate a tasks file from a template."""
    template = get_template(template_name)

    if not template:
        rich_console.print(f"[red]Error:[/red] Template '{template_name}' not found")
        rich_console.print("\nAvailable templates:")
        for tpl_name in sorted(get_all_templates().keys()):
            rich_console.print(f"  - {tpl_name}")
        raise typer.Exit(1)

    if output.exists() and not force:
        rich_console.print(
            f"[red]Error:[/red] File '{output}' already exists. Use --force to overwrite."
        )
        raise typer.Exit(1)

    # Get tasks from template
    tasks = template.get("tasks", [])

    # Override flavor if specified
    if flavor:
        try:
            TaskFlavor(flavor)  # Validate flavor
            for task in tasks:
                task["flavor"] = flavor
        except ValueError:
            rich_console.print(f"[red]Error:[/red] Invalid flavor '{flavor}'")
            rich_console.print("\nAvailable flavors:")
            for f in TaskFlavor:
                rich_console.print(f"  - {f.value}")
            raise typer.Exit(1)

    # Create Task objects and write to file
    task_objs = [Task.from_dict(t) for t in tasks]
    source = YamlTaskSource()
    source.save(task_objs, output)

    rich_console.print(f"[green]Generated tasks file:[/green] {output}")
    rich_console.print(f"[dim]Template: {template.get('name', template_name)}[/dim]")
    rich_console.print(f"[dim]Tasks: {len(tasks)}[/dim]")


@app.command("list-flavors")
def list_flavors() -> None:
    """List all available task flavors."""
    table = Table(title="Task Flavors")
    table.add_column("Flavor", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")

    flavor_descriptions = {
        "production-ready": "Full production quality with tests, docs, error handling",
        "poc": "Quick proof-of-concept, minimal implementation",
        "documentation": "Focus on README, docstrings, and examples",
        "refactoring": "Improve code structure while preserving functionality",
        "bug-fix": "Minimal changes to fix issues with regression tests",
        "testing": "Focus on comprehensive test coverage",
        "exploration": "Experimental code for learning and discovery",
    }

    for flavor in TaskFlavor:
        table.add_row(
            flavor.value,
            flavor_descriptions.get(flavor.value, ""),
        )

    rich_console.print(table)


# =============================================================================
# CONTEXT COMMANDS
# =============================================================================

# Context subcommand
context_app = typer.Typer(
    name="context",
    help="Project context management commands",
    no_args_is_help=True,
)
app.add_typer(context_app, name="context")


@app.command("onboard")
def onboard(
    skip_setup: Annotated[
        bool,
        typer.Option(
            "--skip-setup",
            help="Skip running setup commands",
        ),
    ] = False,
    skip_verify: Annotated[
        bool,
        typer.Option(
            "--skip-verify",
            help="Skip running verification commands",
        ),
    ] = False,
    skip_exploration: Annotated[
        bool,
        typer.Option(
            "--skip-exploration",
            help="Skip Claude Code exploration (faster but less detailed)",
        ),
    ] = False,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Force regenerate context even if exists",
        ),
    ] = False,
    project_dir: Annotated[
        Path,
        typer.Option(
            "--project",
            "-p",
            help="Project directory (default: current directory)",
        ),
    ] = Path("."),
) -> None:
    """Onboard to a project: detect stack, explore codebase, generate context.

    This command performs a comprehensive project analysis similar to 'claude init':
    - Detects project type and tech stack
    - Uses Claude Code to explore the codebase architecture
    - Generates context.yaml and context.md with detailed project information
    - Runs setup and verification commands
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn

    from messirve.context.generator import OnboardingRunner

    project_path = project_dir.resolve()

    if not project_path.exists():
        rich_console.print(f"[red]Error:[/red] Directory not found: {project_path}")
        raise typer.Exit(1)

    rich_console.print(f"\n[bold]Onboarding project:[/bold] {project_path.name}\n")

    def output_callback(text: str) -> None:
        rich_console.print(f"[dim]{text.strip()}[/dim]")

    runner = OnboardingRunner(project_path, output_callback=output_callback)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=rich_console,
    ) as progress:
        # Detect and generate context
        if skip_exploration:
            task = progress.add_task("Detecting project type...", total=None)
        else:
            task = progress.add_task(
                "Exploring codebase with Claude Code (this may take a moment)...",
                total=None,
            )

        context, results, exploration_data = runner.run(
            skip_setup=skip_setup,
            skip_verify=skip_verify,
            force_context=force,
            skip_exploration=skip_exploration,
        )
        progress.remove_task(task)

    # Show detected info
    rich_console.print("\n[bold green]Project detected:[/bold green]")
    rich_console.print(f"  Name: {context.name}")
    if context.tech_stack:
        rich_console.print(f"  Language: {context.tech_stack.language}")
        if context.tech_stack.framework:
            rich_console.print(f"  Framework: {context.tech_stack.framework}")
        if context.tech_stack.package_manager:
            rich_console.print(f"  Package Manager: {context.tech_stack.package_manager}")

    # Show exploration results
    if exploration_data:
        rich_console.print("\n[bold cyan]Codebase exploration complete:[/bold cyan]")
        if exploration_data.get("core_modules"):
            rich_console.print(f"  Found {len(exploration_data['core_modules'])} core modules")
        if exploration_data.get("key_patterns"):
            rich_console.print(f"  Identified {len(exploration_data['key_patterns'])} key patterns")
        if exploration_data.get("architecture_summary"):
            rich_console.print("  Architecture summary generated")
    elif not skip_exploration:
        rich_console.print(
            "\n[yellow]Note:[/yellow] Claude Code exploration was skipped "
            "(Claude CLI not available or exploration failed)"
        )

    # Show command results
    if results:
        rich_console.print("\n[bold]Command results:[/bold]")
        for result in results:
            status = "[green]v[/green]" if result["success"] else "[red]x[/red]"
            rich_console.print(f"  {status} [{result['stage']}] {result['command']}")

    # Show context file location
    rich_console.print("\n[bold]Context saved to:[/bold]")
    rich_console.print(f"  - {runner.generator.context_file}")
    rich_console.print(f"  - {runner.generator.context_md_file}")

    rich_console.print("\n[dim]Run 'messirve context show' to view the full context[/dim]")


@context_app.command("generate")
def context_generate(
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Force regenerate even if context exists",
        ),
    ] = False,
    project_dir: Annotated[
        Path,
        typer.Option(
            "--project",
            "-p",
            help="Project directory (default: current directory)",
        ),
    ] = Path("."),
) -> None:
    """Generate project context from auto-detection."""
    from messirve.context.generator import ContextGenerator

    project_path = project_dir.resolve()

    if not project_path.exists():
        rich_console.print(f"[red]Error:[/red] Directory not found: {project_path}")
        raise typer.Exit(1)

    generator = ContextGenerator(project_path)

    if generator.exists() and not force:
        rich_console.print("[yellow]Context already exists.[/yellow] Use --force to regenerate.")
        raise typer.Exit(0)

    context = generator.generate(force=force)

    rich_console.print("[green]Context generated successfully![/green]")
    rich_console.print(f"\n  YAML: {generator.context_file}")
    rich_console.print(f"  Markdown: {generator.context_md_file}")

    # Show summary
    rich_console.print(f"\n[bold]Project:[/bold] {context.name}")
    if context.tech_stack:
        rich_console.print(f"[bold]Tech Stack:[/bold] {context.tech_stack.language}")
        if context.tech_stack.framework:
            rich_console.print(f"  Framework: {context.tech_stack.framework}")


@context_app.command("show")
def context_show(
    format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format: yaml or markdown",
        ),
    ] = "markdown",
    project_dir: Annotated[
        Path,
        typer.Option(
            "--project",
            "-p",
            help="Project directory (default: current directory)",
        ),
    ] = Path("."),
) -> None:
    """Show current project context."""
    from messirve.context.generator import ContextGenerator

    project_path = project_dir.resolve()
    generator = ContextGenerator(project_path)

    if not generator.exists():
        rich_console.print(
            "[yellow]No context found.[/yellow] Run 'messirve onboard' or 'messirve context generate' first."
        )
        raise typer.Exit(1)

    context = generator.load()

    if format == "yaml":
        rich_console.print(context.to_yaml())
    elif format == "markdown":
        rich_console.print(context.to_markdown())
    else:
        rich_console.print(f"[red]Error:[/red] Unknown format: {format}")
        raise typer.Exit(1)


@context_app.command("edit")
def context_edit(
    project_dir: Annotated[
        Path,
        typer.Option(
            "--project",
            "-p",
            help="Project directory (default: current directory)",
        ),
    ] = Path("."),
) -> None:
    """Open project context file in editor."""
    import os
    import subprocess

    from messirve.context.generator import ContextGenerator

    project_path = project_dir.resolve()
    generator = ContextGenerator(project_path)

    if not generator.exists():
        rich_console.print(
            "[yellow]No context found.[/yellow] Run 'messirve onboard' or 'messirve context generate' first."
        )
        raise typer.Exit(1)

    # Get editor from environment
    editor = os.environ.get("EDITOR", os.environ.get("VISUAL", "vim"))

    try:
        subprocess.run([editor, str(generator.context_file)], check=True)
        rich_console.print("[green]Context file saved.[/green]")

        # Regenerate markdown from updated YAML
        context = generator.load()
        context.save_markdown(generator.context_md_file)
        rich_console.print("[dim]Markdown file updated.[/dim]")

    except subprocess.CalledProcessError:
        rich_console.print("[red]Error:[/red] Editor exited with error")
        raise typer.Exit(1)
    except FileNotFoundError:
        rich_console.print(f"[red]Error:[/red] Editor not found: {editor}")
        rich_console.print("Set EDITOR environment variable to your preferred editor")
        raise typer.Exit(1)


@context_app.command("set")
def context_set(
    key: Annotated[
        str, typer.Argument(help="Context key to set (e.g., description, business_description)")
    ],
    value: Annotated[str, typer.Argument(help="Value to set")],
    project_dir: Annotated[
        Path,
        typer.Option(
            "--project",
            "-p",
            help="Project directory (default: current directory)",
        ),
    ] = Path("."),
) -> None:
    """Set a specific context value."""
    from messirve.context.generator import ContextGenerator

    project_path = project_dir.resolve()
    generator = ContextGenerator(project_path)

    if not generator.exists():
        rich_console.print("[yellow]No context found.[/yellow] Run 'messirve onboard' first.")
        raise typer.Exit(1)

    context = generator.load()

    # Handle different keys
    valid_keys = [
        "name",
        "description",
        "business_description",
        "users",
        "coding_standards",
    ]
    list_keys = [
        "functional_requirements",
        "non_functional_requirements",
        "setup_commands",
        "verify_commands",
    ]

    if key in valid_keys:
        setattr(context, key, value)
        generator.save(context)
        rich_console.print(f"[green]Set {key}[/green]")
    elif key in list_keys:
        # For list fields, append the value
        current = getattr(context, key)
        current.append(value)
        generator.save(context)
        rich_console.print(f"[green]Added to {key}[/green]")
    else:
        rich_console.print(f"[red]Error:[/red] Unknown key: {key}")
        rich_console.print(f"\nValid keys: {', '.join(valid_keys)}")
        rich_console.print(f"List keys (append): {', '.join(list_keys)}")
        raise typer.Exit(1)


# =============================================================================
# ANALYZE COMMAND
# =============================================================================


@app.command("analyze")
def analyze_cmd(
    path: Annotated[
        list[Path],
        typer.Argument(
            help="Paths to analyze (default: current directory)",
        ),
    ] = None,  # type: ignore[assignment]
    before_ref: Annotated[
        str | None,
        typer.Option(
            "--before",
            "-b",
            help="Git ref to compare against (e.g., main, HEAD~1)",
        ),
    ] = None,
    after_ref: Annotated[
        str | None,
        typer.Option(
            "--after",
            "-a",
            help="Git ref for 'after' state (default: current working tree)",
        ),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output file for report",
        ),
    ] = None,
    format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format: console, yaml, json, markdown",
        ),
    ] = "console",
    fail_on_regression: Annotated[
        bool,
        typer.Option(
            "--fail-on-regression",
            help="Exit with error if quality regression detected",
        ),
    ] = False,
    no_complexity: Annotated[
        bool,
        typer.Option(
            "--no-complexity",
            help="Disable complexity analysis",
        ),
    ] = False,
    no_quality: Annotated[
        bool,
        typer.Option(
            "--no-quality",
            help="Disable quality (ruff) analysis",
        ),
    ] = False,
) -> None:
    """Analyze code for tech debt and quality metrics.

    Run standalone analysis or compare between git refs.

    Examples:

        # Analyze current directory
        messirve analyze

        # Analyze specific paths
        messirve analyze src/ tests/

        # Compare against main branch
        messirve analyze --before main

        # Save report to file
        messirve analyze --output report.yaml --format yaml

        # Compare two git refs
        messirve analyze --before main --after feature-branch
    """
    from messirve.analysis import AnalysisConfig, AnalysisRunner, ReportGenerator

    # Default to current directory if no paths specified
    paths = list(path) if path else [Path(".")]

    # Create config
    config = AnalysisConfig(
        paths=paths,
        enable_complexity=not no_complexity,
        enable_quality=not no_quality,
        fail_on_regression=fail_on_regression,
    )

    runner = AnalysisRunner(config, rich_console)
    report_gen = ReportGenerator(rich_console)

    # Determine mode: comparison or single analysis
    if before_ref:
        # Comparison mode
        rich_console.print(f"[bold]Comparing {before_ref} → {after_ref or 'working tree'}[/bold]")
        comparison = runner.analyze_diff(
            before_ref=before_ref,
            after_ref=after_ref,
            paths=paths,
        )

        if format == "console":
            report_gen.print_comparison(comparison)
        elif output:
            report_gen.save_report(comparison, output, format)
        else:
            # Print to stdout in requested format
            if format == "markdown":
                rich_console.print(report_gen.to_markdown(comparison))
            elif format == "json":
                import json as json_mod

                rich_console.print(
                    json_mod.dumps(
                        {
                            "overall_impact": comparison.overall_impact,
                            "has_regressions": comparison.has_regressions,
                            "new_findings": len(comparison.new_findings),
                        },
                        indent=2,
                    )
                )

        # Fail on regression if requested
        if fail_on_regression and comparison.has_regressions:
            rich_console.print("[red]Quality regression detected.[/red]")
            raise typer.Exit(1)

    else:
        # Single analysis mode
        rich_console.print("[bold]Running code analysis...[/bold]")
        result = runner.analyze(paths)

        if format == "console":
            report_gen.print_result(result)
        elif output:
            report_gen.save_report(result, output, format)
        else:
            if format == "yaml":
                rich_console.print(report_gen.to_yaml(result))
            elif format == "json":
                rich_console.print(report_gen.to_json(result))


if __name__ == "__main__":
    app()
