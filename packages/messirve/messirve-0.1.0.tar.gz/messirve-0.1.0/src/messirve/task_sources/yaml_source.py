"""YAML task source for loading tasks from YAML files."""

from pathlib import Path
from typing import Any

import yaml

from messirve.exceptions import DependencyError, TaskFileError, TaskValidationError
from messirve.models.task import Task
from messirve.task_sources.base import TaskSource


class YamlTaskSource(TaskSource):
    """Task source that loads tasks from YAML files."""

    SUPPORTED_VERSIONS = ["1.0"]

    def load(self, source: Path | str) -> list[Task]:
        """Load tasks from a YAML file.

        Args:
            source: Path to the YAML file.

        Returns:
            List of Task objects.

        Raises:
            TaskFileError: If the file cannot be loaded or parsed.
        """
        path = Path(source) if isinstance(source, str) else source

        if not path.exists():
            raise TaskFileError(f"Task file not found: {path}")

        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise TaskFileError(f"Invalid YAML in task file: {e}") from e

        if data is None:
            raise TaskFileError("Task file is empty")

        return self._parse_tasks(data, path)

    def _parse_tasks(self, data: dict[str, Any], path: Path) -> list[Task]:
        """Parse tasks from YAML data.

        Args:
            data: Parsed YAML data.
            path: Path to the source file (for error messages).

        Returns:
            List of Task objects.

        Raises:
            TaskFileError: If the data structure is invalid.
            TaskValidationError: If a task fails validation.
        """
        # Validate version
        version = data.get("version", "1.0")
        if version not in self.SUPPORTED_VERSIONS:
            raise TaskFileError(
                f"Unsupported task file version: {version}. "
                f"Supported versions: {', '.join(self.SUPPORTED_VERSIONS)}"
            )

        # Get tasks list
        tasks_data = data.get("tasks", [])
        if not isinstance(tasks_data, list):
            raise TaskFileError("'tasks' must be a list")

        if not tasks_data:
            raise TaskFileError("No tasks found in file")

        tasks: list[Task] = []
        seen_ids: set[str] = set()

        for i, task_data in enumerate(tasks_data):
            if not isinstance(task_data, dict):
                raise TaskFileError(f"Task {i + 1} must be a dictionary")

            try:
                task = Task.from_dict(task_data)
            except ValueError as e:
                task_id = task_data.get("id", f"task_{i + 1}")
                raise TaskValidationError(
                    str(e),
                    task_id=task_id,
                    details={"file": str(path), "index": i},
                ) from e

            # Check for duplicate IDs
            if task.id in seen_ids:
                raise TaskValidationError(
                    f"Duplicate task ID: {task.id}",
                    task_id=task.id,
                    details={"file": str(path)},
                )
            seen_ids.add(task.id)
            tasks.append(task)

        return tasks

    def validate(self, tasks: list[Task]) -> list[str]:
        """Validate a list of tasks.

        Checks for:
        - Required fields are present
        - Task IDs are unique
        - Dependencies reference existing tasks
        - No circular dependencies

        Args:
            tasks: List of Task objects to validate.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors: list[str] = []
        task_ids = {t.id for t in tasks}

        for task in tasks:
            # Check required fields
            if not task.id:
                errors.append("Task missing required field: id")
            if not task.title:
                errors.append(f"Task {task.id}: missing required field: title")
            if not task.description:
                errors.append(f"Task {task.id}: missing required field: description")
            if not task.context:
                errors.append(f"Task {task.id}: missing required field: context")
            if not task.acceptance_criteria:
                errors.append(f"Task {task.id}: missing required field: acceptance_criteria")

            # Check dependencies exist
            for dep_id in task.depends_on:
                if dep_id not in task_ids:
                    errors.append(f"Task {task.id}: depends on unknown task: {dep_id}")

        # Check for circular dependencies
        circular = self._find_circular_dependencies(tasks)
        if circular:
            errors.append(f"Circular dependency detected: {' -> '.join(circular)}")

        return errors

    def _find_circular_dependencies(self, tasks: list[Task]) -> list[str]:
        """Find circular dependencies in tasks.

        Args:
            tasks: List of Task objects.

        Returns:
            List of task IDs forming a cycle, or empty list if no cycle.
        """
        task_map = {t.id: t for t in tasks}
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def dfs(task_id: str) -> list[str]:
            visited.add(task_id)
            rec_stack.add(task_id)
            path.append(task_id)

            task = task_map.get(task_id)
            if task:
                for dep_id in task.depends_on:
                    if dep_id not in visited:
                        result = dfs(dep_id)
                        if result:
                            return result
                    elif dep_id in rec_stack:
                        # Found cycle
                        cycle_start = path.index(dep_id)
                        return path[cycle_start:] + [dep_id]

            path.pop()
            rec_stack.remove(task_id)
            return []

        for task in tasks:
            if task.id not in visited:
                result = dfs(task.id)
                if result:
                    return result

        return []

    def validate_dependencies(self, tasks: list[Task], completed_ids: set[str]) -> list[Task]:
        """Get tasks that have all dependencies satisfied.

        Args:
            tasks: List of all Task objects.
            completed_ids: Set of completed task IDs.

        Returns:
            List of tasks ready to execute.
        """
        ready: list[Task] = []
        for task in tasks:
            if task.id in completed_ids:
                continue
            if all(dep_id in completed_ids for dep_id in task.depends_on):
                ready.append(task)
        return ready

    def get_execution_order(self, tasks: list[Task]) -> list[Task]:
        """Get tasks in dependency-respecting execution order.

        Uses topological sort to order tasks such that dependencies
        are executed before dependents.

        Args:
            tasks: List of Task objects.

        Returns:
            List of tasks in execution order.

        Raises:
            DependencyError: If dependencies cannot be resolved.
        """
        # Check for circular dependencies first
        circular = self._find_circular_dependencies(tasks)
        if circular:
            raise DependencyError(
                f"Circular dependency detected: {' -> '.join(circular)}",
                missing_deps=circular,
            )

        task_map = {t.id: t for t in tasks}
        in_degree: dict[str, int] = {t.id: 0 for t in tasks}
        graph: dict[str, list[str]] = {t.id: [] for t in tasks}

        # Build graph
        for task in tasks:
            for dep_id in task.depends_on:
                if dep_id in graph:
                    graph[dep_id].append(task.id)
                    in_degree[task.id] += 1

        # Kahn's algorithm for topological sort
        queue: list[str] = [tid for tid, deg in in_degree.items() if deg == 0]
        result: list[Task] = []

        while queue:
            # Sort queue to get deterministic ordering
            queue.sort()
            current = queue.pop(0)
            result.append(task_map[current])

            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(tasks):
            # This shouldn't happen if circular check passed
            raise DependencyError("Could not resolve all dependencies")

        return result

    def save(self, tasks: list[Task], destination: Path | str) -> None:
        """Save tasks to a YAML file.

        Args:
            tasks: List of Task objects to save.
            destination: Path to save the file to.

        Raises:
            TaskFileError: If the file cannot be saved.
        """
        path = Path(destination) if isinstance(destination, str) else destination

        data = {
            "version": "1.0",
            "tasks": [task.to_dict() for task in tasks],
        }

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        except OSError as e:
            raise TaskFileError(f"Failed to save task file: {e}") from e

    def mark_task_done(self, source: Path | str, task_id: str) -> bool:
        """Mark a specific task as done in the YAML file.

        Re-reads the file before updating to avoid overwriting concurrent changes.

        Args:
            source: Path to the YAML file.
            task_id: ID of the task to mark as done.

        Returns:
            True if the task was found and marked, False if not found.

        Raises:
            TaskFileError: If the file cannot be read or written.
        """
        path = Path(source) if isinstance(source, str) else source

        # Re-read the file to get the latest state
        tasks = self.load(path)

        # Find and update the task
        found = False
        for task in tasks:
            if task.id == task_id:
                task.done = True
                found = True
                break

        if found:
            self.save(tasks, path)

        return found

    def reset_task(self, source: Path | str, task_id: str) -> bool:
        """Reset a specific task to not done.

        Args:
            source: Path to the YAML file.
            task_id: ID of the task to reset.

        Returns:
            True if the task was found and reset, False if not found.

        Raises:
            TaskFileError: If the file cannot be read or written.
        """
        path = Path(source) if isinstance(source, str) else source

        tasks = self.load(path)

        found = False
        for task in tasks:
            if task.id == task_id:
                task.done = False
                found = True
                break

        if found:
            self.save(tasks, path)

        return found

    def reset_all_tasks(self, source: Path | str) -> int:
        """Reset all tasks to not done.

        Args:
            source: Path to the YAML file.

        Returns:
            Count of tasks that were reset.

        Raises:
            TaskFileError: If the file cannot be read or written.
        """
        path = Path(source) if isinstance(source, str) else source

        tasks = self.load(path)

        reset_count = 0
        for task in tasks:
            if task.done:
                task.done = False
                reset_count += 1

        if reset_count > 0:
            self.save(tasks, path)

        return reset_count

    def get_pending_tasks(self, tasks: list[Task]) -> list[Task]:
        """Get tasks that are not yet done.

        Args:
            tasks: List of Task objects.

        Returns:
            List of tasks that have done=False.
        """
        return [t for t in tasks if not t.done]
