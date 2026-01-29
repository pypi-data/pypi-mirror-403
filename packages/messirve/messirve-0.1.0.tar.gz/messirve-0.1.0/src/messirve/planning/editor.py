"""Interactive editor for reviewing and modifying generated tasks."""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from messirve.planning.models import GeneratedTask


class InteractiveEditor:
    """Interactive editor for task review and modification."""

    def __init__(self, console: Console | None = None) -> None:
        """Initialize the editor.

        Args:
            console: Rich console for output (creates new one if None).
        """
        self.console = console or Console()

    def edit_tasks(self, tasks: list[GeneratedTask]) -> list[GeneratedTask]:
        """Interactive loop for editing tasks.

        Args:
            tasks: List of generated tasks to edit.

        Returns:
            List of tasks after editing (deleted tasks excluded).
        """
        while True:
            self._display_tasks(tasks)
            self.console.print()

            action = self._prompt_action(tasks)

            if action == "done":
                break
            elif action == "accept_all":
                for task in tasks:
                    if not task.deleted:
                        task.accepted = True
                self.console.print("[green]All tasks accepted.[/green]")
            elif action.startswith("edit:"):
                idx = int(action.split(":")[1])
                self._edit_task(tasks[idx])
            elif action.startswith("delete:"):
                idx = int(action.split(":")[1])
                tasks[idx].deleted = True
                self.console.print(f"[yellow]Task {tasks[idx].id} marked for deletion.[/yellow]")
            elif action.startswith("view:"):
                idx = int(action.split(":")[1])
                self._view_task(tasks[idx])
            elif action.startswith("dep:"):
                idx = int(action.split(":")[1])
                self._edit_dependencies(tasks, idx)
            elif action == "add":
                new_task = self._add_task(len(tasks))
                if new_task:
                    tasks.append(new_task)

        return [t for t in tasks if not t.deleted]

    def _display_tasks(self, tasks: list[GeneratedTask]) -> None:
        """Display tasks in a table."""
        table = Table(
            title="Generated Tasks",
            show_header=True,
            header_style="bold",
            box=None,
            padding=(0, 1),
        )

        table.add_column("#", style="dim", width=3)
        table.add_column("ID", style="cyan", width=10)
        table.add_column("Title", width=50)
        table.add_column("Complexity", justify="center", width=10)
        table.add_column("Deps", width=15)
        table.add_column("Status", justify="center", width=10)

        for i, task in enumerate(tasks):
            if task.deleted:
                status = "[red]deleted[/red]"
            elif task.accepted:
                status = "[green]accepted[/green]"
            else:
                status = "[dim]pending[/dim]"

            complexity_style = {
                "low": "[green]low[/green]",
                "medium": "[yellow]medium[/yellow]",
                "high": "[red]high[/red]",
            }.get(task.complexity, task.complexity)

            deps = ", ".join(task.depends_on) if task.depends_on else "-"

            table.add_row(
                str(i + 1),
                task.id,
                task.title[:48] + "..." if len(task.title) > 48 else task.title,
                complexity_style,
                deps[:13] + "..." if len(deps) > 13 else deps,
                status,
            )

        self.console.print(table)

    def _prompt_action(self, tasks: list[GeneratedTask]) -> str:
        """Prompt user for action."""
        self.console.print()
        self.console.print("[bold]Actions:[/bold]")
        self.console.print("  [cyan]a[/cyan]   - Accept all tasks")
        self.console.print("  [cyan]v N[/cyan] - View task N details")
        self.console.print("  [cyan]e N[/cyan] - Edit task N")
        self.console.print("  [cyan]d N[/cyan] - Delete task N")
        self.console.print("  [cyan]p N[/cyan] - Add dependency to task N")
        self.console.print("  [cyan]n[/cyan]   - Add new task")
        self.console.print("  [cyan]done[/cyan] - Finish editing")
        self.console.print()

        while True:
            choice = Prompt.ask("Action").strip().lower()

            if choice == "done":
                return "done"
            elif choice == "a":
                return "accept_all"
            elif choice == "n":
                return "add"
            elif choice.startswith("v "):
                try:
                    idx = int(choice[2:]) - 1
                    if 0 <= idx < len(tasks):
                        return f"view:{idx}"
                except ValueError:
                    pass
            elif choice.startswith("e "):
                try:
                    idx = int(choice[2:]) - 1
                    if 0 <= idx < len(tasks):
                        return f"edit:{idx}"
                except ValueError:
                    pass
            elif choice.startswith("d "):
                try:
                    idx = int(choice[2:]) - 1
                    if 0 <= idx < len(tasks):
                        return f"delete:{idx}"
                except ValueError:
                    pass
            elif choice.startswith("p "):
                try:
                    idx = int(choice[2:]) - 1
                    if 0 <= idx < len(tasks):
                        return f"dep:{idx}"
                except ValueError:
                    pass

            self.console.print("[red]Invalid action. Try again.[/red]")

    def _view_task(self, task: GeneratedTask) -> None:
        """Display full task details."""
        content = Text()
        content.append("ID: ", style="bold")
        content.append(f"{task.id}\n")
        content.append("Title: ", style="bold")
        content.append(f"{task.title}\n")
        content.append("Complexity: ", style="bold")
        content.append(f"{task.complexity}\n")
        content.append("\nDescription:\n", style="bold")
        content.append(f"{task.description}\n")
        content.append("\nContext:\n", style="bold")
        content.append(f"{task.context}\n")
        content.append("\nAcceptance Criteria:\n", style="bold")
        for criterion in task.acceptance_criteria:
            content.append(f"  - {criterion}\n")
        if task.depends_on:
            content.append("\nDepends On: ", style="bold")
            content.append(", ".join(task.depends_on))

        panel = Panel(content, title=f"[bold]{task.id}[/bold]", border_style="blue")
        self.console.print(panel)
        self.console.print()
        Prompt.ask("[dim]Press Enter to continue[/dim]")

    def _edit_task(self, task: GeneratedTask) -> None:
        """Edit a task's fields."""
        self.console.print(f"\n[bold]Editing {task.id}[/bold]")
        self.console.print("[dim]Press Enter to keep current value[/dim]\n")

        # Title
        new_title = Prompt.ask("Title", default=task.title)
        if new_title:
            task.title = new_title

        # Description
        self.console.print(f"\n[dim]Current description:[/dim]\n{task.description}\n")
        if Confirm.ask("Edit description?", default=False):
            new_desc = Prompt.ask("New description")
            if new_desc:
                task.description = new_desc

        # Context
        self.console.print(f"\n[dim]Current context:[/dim]\n{task.context}\n")
        if Confirm.ask("Edit context?", default=False):
            new_context = Prompt.ask("New context")
            if new_context:
                task.context = new_context

        # Acceptance criteria
        self.console.print("\n[dim]Current acceptance criteria:[/dim]")
        for i, criterion in enumerate(task.acceptance_criteria, 1):
            self.console.print(f"  {i}. {criterion}")

        if Confirm.ask("\nEdit acceptance criteria?", default=False):
            self.console.print("Enter new criteria (one per line, empty line to finish):")
            new_criteria: list[str] = []
            while True:
                criterion = Prompt.ask(f"  {len(new_criteria) + 1}", default="")
                if not criterion:
                    break
                new_criteria.append(criterion)
            if new_criteria:
                task.acceptance_criteria = new_criteria

        # Complexity
        new_complexity = Prompt.ask(
            "Complexity [low/medium/high]",
            default=task.complexity,
            choices=["low", "medium", "high"],
        )
        task.complexity = new_complexity

        task.accepted = True
        self.console.print(f"\n[green]Task {task.id} updated and accepted.[/green]")

    def _edit_dependencies(self, tasks: list[GeneratedTask], idx: int) -> None:
        """Edit dependencies for a task."""
        task = tasks[idx]
        available_ids = [t.id for t in tasks if t.id != task.id and not t.deleted]

        self.console.print(f"\n[bold]Add dependency to {task.id}[/bold]")
        self.console.print(f"Current dependencies: {', '.join(task.depends_on) or 'none'}")
        self.console.print(f"Available tasks: {', '.join(available_ids)}")

        dep_id = Prompt.ask("Task ID to depend on (or 'clear' to remove all)")

        if dep_id == "clear":
            task.depends_on = []
            self.console.print("[yellow]Dependencies cleared.[/yellow]")
        elif dep_id in available_ids:
            if dep_id not in task.depends_on:
                task.depends_on.append(dep_id)
                self.console.print(f"[green]Added dependency on {dep_id}.[/green]")
            else:
                self.console.print("[yellow]Already depends on that task.[/yellow]")
        else:
            self.console.print("[red]Invalid task ID.[/red]")

    def _add_task(self, current_count: int) -> GeneratedTask | None:
        """Add a new task manually."""
        self.console.print("\n[bold]Add New Task[/bold]")

        task_id = Prompt.ask("Task ID", default=f"TASK-{current_count + 1:03d}")
        title = Prompt.ask("Title")
        if not title:
            self.console.print("[red]Title is required.[/red]")
            return None

        description = Prompt.ask("Description")
        context = Prompt.ask("Context", default="")

        self.console.print("Enter acceptance criteria (one per line, empty line to finish):")
        criteria: list[str] = []
        while True:
            criterion = Prompt.ask(f"  {len(criteria) + 1}", default="")
            if not criterion:
                break
            criteria.append(criterion)

        complexity = Prompt.ask(
            "Complexity",
            default="medium",
            choices=["low", "medium", "high"],
        )

        task = GeneratedTask(
            id=task_id,
            title=title,
            description=description,
            context=context,
            acceptance_criteria=criteria or ["Task is complete"],
            complexity=complexity,
            accepted=True,
        )

        self.console.print(f"[green]Added task {task.id}.[/green]")
        return task
