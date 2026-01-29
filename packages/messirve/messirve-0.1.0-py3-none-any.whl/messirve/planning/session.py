"""Planning session orchestrator."""

from datetime import date
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.text import Text

from messirve.context.models import ProjectContext
from messirve.planning.editor import InteractiveEditor
from messirve.planning.generator import TaskGenerator, load_project_context
from messirve.planning.models import GeneratedTask, PlanningGoal, PlanningSession


class PlanningOrchestrator:
    """Orchestrates the planning session workflow."""

    def __init__(
        self,
        console: Console | None = None,
        project_dir: Path | None = None,
    ) -> None:
        """Initialize the orchestrator.

        Args:
            console: Rich console for output.
            project_dir: Project directory (defaults to cwd).
        """
        self.console = console or Console()
        self.project_dir = project_dir or Path.cwd()
        self.project_context: ProjectContext | None = None

    def run(
        self,
        output_path: Path | None = None,
        goals: list[str] | None = None,
        non_interactive: bool = False,
    ) -> Path | None:
        """Run the planning session.

        Args:
            output_path: Optional output file path.
            goals: Optional pre-specified goals (for non-interactive mode).
            non_interactive: If True, skip interactive editing.

        Returns:
            Path to the generated tasks file, or None if cancelled.
        """
        # Print welcome
        self._print_welcome()

        # Load project context
        self.project_context = load_project_context(self.project_dir)
        if self.project_context:
            self.console.print(f"[dim]Using project context: {self.project_context.name}[/dim]\n")

        # Collect goals
        if goals:
            planning_goals = [PlanningGoal(description=g) for g in goals]
        else:
            planning_goals = self._collect_goals()
            if not planning_goals:
                self.console.print("[yellow]No goals provided. Exiting.[/yellow]")
                return None

        # Create session
        session = PlanningSession(goals=planning_goals)

        # Generate tasks
        self.console.print("\n[bold]Generating tasks...[/bold]")
        self.console.print("[dim]This may take a moment...[/dim]\n")

        generator = TaskGenerator(project_context=self.project_context)

        if not generator.is_available():
            self.console.print(
                "[red]Error:[/red] Claude CLI not found. Please install it first.\n"
                "  Install: npm install -g @anthropic-ai/claude-code"
            )
            return None

        try:
            tasks = generator.generate_tasks(
                planning_goals,
                num_tasks=self._estimate_task_count(planning_goals),
            )
            session.generated_tasks = tasks
        except Exception as e:
            self.console.print(f"[red]Error generating tasks:[/red] {e}")
            return None

        self.console.print(f"[green]Generated {len(tasks)} tasks.[/green]\n")

        # Select flavor for all tasks
        if not non_interactive:
            selected_flavor = self._select_flavor()
            self._apply_flavor_to_tasks(tasks, selected_flavor)
            self.console.print(f"[dim]Applied flavor: {selected_flavor}[/dim]\n")
        else:
            # Use default flavor (production-ready)
            self._apply_flavor_to_tasks(tasks, "production-ready")

        # Interactive editing (unless non-interactive)
        if not non_interactive:
            editor = InteractiveEditor(self.console)
            final_tasks = editor.edit_tasks(tasks)

            if not final_tasks:
                self.console.print("[yellow]No tasks to save. Exiting.[/yellow]")
                return None

            session.generated_tasks = final_tasks + [t for t in tasks if t.deleted]
        else:
            final_tasks = tasks

        # Determine output path
        if output_path is None:
            output_path = self._get_default_output_path()

        # Confirm save
        if not non_interactive:
            self.console.print()
            if not Confirm.ask(f"Save {len(final_tasks)} tasks to {output_path}?", default=True):
                self.console.print("[yellow]Cancelled.[/yellow]")
                return None

        # Save to file
        self._save_tasks(session, output_path)

        # Print success
        self.console.print()
        self.console.print(
            Panel(
                f"[green]Created {output_path}[/green]\n\n"
                f"Tasks: {len(final_tasks)}\n\n"
                f"[dim]Run with:[/dim] messirve run {output_path}",
                title="[bold]Planning Complete[/bold]",
                border_style="green",
            )
        )

        return output_path

    def _print_welcome(self) -> None:
        """Print welcome message."""
        welcome = Text()
        welcome.append("MESSIRVE PLANNING\n", style="bold blue")
        welcome.append(
            "Turn high-level goals into structured tasks.\n",
            style="dim",
        )
        self.console.print(Panel(welcome, border_style="blue"))
        self.console.print()

    def _collect_goals(self) -> list[PlanningGoal]:
        """Collect goals from user."""
        self.console.print("[bold]What do you want to accomplish?[/bold]")
        self.console.print("[dim]Enter your goals (one per line, empty line to finish):[/dim]\n")

        goals: list[PlanningGoal] = []
        priority = 1

        while True:
            goal_text = Prompt.ask(f"  Goal {len(goals) + 1}", default="")
            if not goal_text:
                break

            goals.append(PlanningGoal(description=goal_text, priority=priority))
            priority = min(priority + 1, 3)  # Lower priority for later goals

        return goals

    def _estimate_task_count(self, goals: list[PlanningGoal]) -> int:
        """Estimate number of tasks based on goals.

        Simple heuristic: ~3-5 tasks per goal.
        """
        base = len(goals) * 4
        return max(3, min(base, 15))  # Between 3 and 15 tasks

    def _get_default_output_path(self) -> Path:
        """Get default output file path."""
        date_str = date.today().isoformat()
        return Path(f"tasks-{date_str}.yaml")

    def _save_tasks(self, session: PlanningSession, output_path: Path) -> None:
        """Save session tasks to YAML file."""
        content = session.to_yaml_content()
        output_path.write_text(content)

    def _select_flavor(self) -> str:
        """Prompt user to select a task flavor.

        Returns:
            Selected flavor string.
        """
        self.console.print("[bold]Select task flavor:[/bold]")
        self.console.print("[dim]This determines the code quality approach for all tasks.[/dim]\n")

        flavors = [
            ("1", "production-ready", "Full quality with tests, docs, error handling"),
            ("2", "poc", "Quick proof-of-concept, minimal implementation"),
            ("3", "bug-fix", "Minimal changes with regression tests"),
            ("4", "refactoring", "Improve structure, preserve functionality"),
            ("5", "testing", "Comprehensive test coverage"),
            ("6", "documentation", "Focus on README, docstrings, examples"),
            ("7", "exploration", "Experimental, document findings"),
        ]

        for num, name, desc in flavors:
            self.console.print(f"  [cyan]{num}[/cyan]. [bold]{name}[/bold] - {desc}")

        self.console.print()
        choice = Prompt.ask(
            "  Choose flavor",
            choices=["1", "2", "3", "4", "5", "6", "7"],
            default="1",
        )

        flavor_map = {f[0]: f[1] for f in flavors}
        return flavor_map.get(choice, "production-ready")

    def _apply_flavor_to_tasks(self, tasks: list[GeneratedTask], flavor: str) -> None:
        """Apply flavor to all generated tasks.

        Args:
            tasks: List of generated tasks.
            flavor: Flavor string to apply.
        """
        for task in tasks:
            task.flavor = flavor


def run_planning(
    output: Path | None = None,
    goals: list[str] | None = None,
    project_dir: Path | None = None,
    non_interactive: bool = False,
) -> Path | None:
    """Convenience function to run a planning session.

    Args:
        output: Optional output file path.
        goals: Optional pre-specified goals.
        project_dir: Project directory.
        non_interactive: Skip interactive editing.

    Returns:
        Path to generated file or None.
    """
    orchestrator = PlanningOrchestrator(project_dir=project_dir)
    return orchestrator.run(
        output_path=output,
        goals=goals,
        non_interactive=non_interactive,
    )
