"""Main task execution loop."""

import time
from datetime import datetime
from pathlib import Path
from typing import Any

from messirve import config as config_module
from messirve.analysis.models import AnalysisConfig
from messirve.analysis.runner import AnalysisRunner
from messirve.analysis.storage import TechDebtStorage
from messirve.context.generator import ContextGenerator
from messirve.context.models import ProjectContext
from messirve.engines.base import Engine
from messirve.engines.claude_code import ClaudeCodeEngine
from messirve.exceptions import (
    ExecutionError,
    HookError,
)
from messirve.git.manager import GitManager
from messirve.git.strategies import GitStrategy
from messirve.hooks.runner import HookRunner
from messirve.hooks.types import HookType
from messirve.logging.console import Console, Verbosity
from messirve.logging.master_logger import MasterLogger
from messirve.logging.task_logger import TaskLogger
from messirve.models.config import ContextIsolation, MessirveConfig
from messirve.models.config import GitStrategy as GitStrategyEnum
from messirve.models.execution import (
    ExecutionResult,
    HookResult,
    RunStatus,
    RunSummary,
    TaskAttempt,
    TaskStatus,
)
from messirve.models.task import Task, TaskFlavor
from messirve.task_sources.yaml_source import YamlTaskSource


class Executor:
    """Main task executor that orchestrates the execution loop."""

    def __init__(
        self,
        config: MessirveConfig,
        console: Console,
        engine: Engine | None = None,
        working_dir: Path | None = None,
    ) -> None:
        """Initialize the executor.

        Args:
            config: Messirve configuration.
            console: Console output handler.
            engine: Execution engine (defaults to ClaudeCodeEngine).
            working_dir: Working directory (defaults to current directory).
        """
        self.config = config
        self.console = console
        self.working_dir = working_dir or Path.cwd()

        # Load project context if available
        self._project_context: ProjectContext | None = None
        if config.context.include_project_context:
            self._project_context = self._load_project_context()

        # Initialize engine with project context
        self.engine = engine or ClaudeCodeEngine(project_context=self._project_context)

        # Initialize components
        self.log_dir = config_module.get_log_dir(self.working_dir)
        self.master_logger = MasterLogger(self.log_dir)
        self.hook_runner = HookRunner(
            working_dir=str(self.working_dir),
            output_callback=self.console.stream_output
            if console.verbosity >= Verbosity.VERBOSE
            else None,
        )

        # Git manager (initialized lazily)
        self._git_manager: GitManager | None = None
        self._git_strategy: GitStrategy | None = None

    def _load_project_context(self) -> ProjectContext | None:
        """Load project context if available.

        Returns:
            ProjectContext or None if not found.
        """
        context_file = self.working_dir / self.config.context.context_file
        if context_file.exists():
            try:
                generator = ContextGenerator(self.working_dir)
                context = generator.load()
                self.console.info(f"Loaded project context: {context.name}")
                return context
            except Exception as e:
                self.console.warning(f"Failed to load project context: {e}")
                return None
        return None

    @property
    def git_manager(self) -> GitManager:
        """Get the git manager, initializing if needed."""
        if self._git_manager is None:
            self._git_manager = GitManager(self.working_dir)
        return self._git_manager

    def run(
        self,
        tasks_file: Path,
        task_ids: list[str] | None = None,
        dry_run: bool = False,
        continue_from: bool = False,
        skip_completed: bool = True,
    ) -> RunSummary:
        """Execute tasks from a file.

        Args:
            tasks_file: Path to the tasks file.
            task_ids: Specific task IDs to run (None = all tasks).
            dry_run: If True, show what would execute without running.
            continue_from: If True, continue from the last failed task.
            skip_completed: If True, skip tasks marked as done in the YAML file.

        Returns:
            RunSummary with execution results.
        """
        # Generate run ID
        run_id = datetime.now().strftime("%Y-%m-%d-%H%M%S")

        # Log context isolation mode
        if self.config.context.isolation == ContextIsolation.PER_TASK:
            self.console.info("Context isolation: per-task (fresh context for each task)")
        else:
            self.console.info("Context isolation: shared (context shared across tasks)")

        if self._project_context:
            self.console.info(f"Using project context: {self._project_context.name}")

        # Load tasks
        source = YamlTaskSource()
        all_tasks = source.load(tasks_file)

        # Filter tasks if specific IDs provided
        if task_ids:
            tasks = [t for t in all_tasks if t.id in task_ids]
            if not tasks:
                raise ExecutionError("No matching tasks found")
        else:
            tasks = all_tasks

        # Track completed task IDs from the file for dependency checking
        # (completed tasks in file still satisfy dependencies)
        file_completed_ids = {t.id for t in all_tasks if t.done}

        # Filter out completed tasks if skip_completed is True
        if skip_completed and not task_ids:
            pending_tasks = source.get_pending_tasks(tasks)
            skipped_completed_count = len(tasks) - len(pending_tasks)
            if skipped_completed_count > 0:
                self.console.info(f"Skipping {skipped_completed_count} already completed task(s)")
            tasks = pending_tasks
            if not tasks:
                self.console.success("All tasks are already completed!")
                return RunSummary(
                    run_id=run_id,
                    started_at=datetime.now(),
                    completed_at=datetime.now(),
                    tasks_file=str(tasks_file),
                    git_strategy=self.config.defaults.git_strategy.value,
                    total_tasks=0,
                    status=RunStatus.COMPLETED,
                )

        # Validate tasks
        errors = source.validate(tasks)
        if errors:
            raise ExecutionError(
                "Task validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            )

        # Get execution order
        tasks = source.get_execution_order(tasks)

        # Initialize summary
        summary = RunSummary(
            run_id=run_id,
            started_at=datetime.now(),
            tasks_file=str(tasks_file),
            git_strategy=self.config.defaults.git_strategy.value,
            total_tasks=len(tasks),
        )

        if dry_run:
            return self._dry_run(tasks, summary)

        # Initialize logging
        task_logger = TaskLogger(self.log_dir, run_id)
        self.master_logger.start_run(
            run_id,
            str(tasks_file),
            self.config.defaults.git_strategy.value,
        )

        # Initialize git strategy (only if git is enabled)
        if (
            self.config.defaults.git_enabled
            and self.config.defaults.git_strategy != GitStrategyEnum.NONE
            and self.git_manager.is_git_repo()
        ):
            self._git_strategy = self.git_manager.get_strategy(
                self.config.defaults.git_strategy,
                self.config.defaults.base_branch,
            )
            self._git_strategy.setup(run_id)

        try:
            # Run pre_run hooks
            self._run_hooks(
                self.config.hooks.pre_run,
                HookType.PRE_RUN,
                "Running pre_run hooks...",
            )

            # Execute tasks
            # Include already-completed tasks from the file for dependency checking
            completed_ids: set[str] = file_completed_ids.copy()
            for i, task in enumerate(tasks, 1):
                result = self._execute_task(
                    task,
                    run_id,
                    i,
                    len(tasks),
                    completed_ids,
                )

                # Save task result
                task_logger.save_result(result)
                summary.task_results.append(result)

                # Update counters
                if result.status == TaskStatus.COMPLETED:
                    summary.completed_tasks += 1
                    completed_ids.add(task.id)
                    # Mark task as done in the YAML file
                    try:
                        source.mark_task_done(tasks_file, task.id)
                    except Exception as e:
                        self.console.warning(f"Failed to mark task as done: {e}")
                elif result.status == TaskStatus.FAILED:
                    summary.failed_tasks += 1
                    # Stop on failure unless continue mode
                    if not continue_from:
                        break
                elif result.status == TaskStatus.SKIPPED:
                    summary.skipped_tasks += 1

                # Update summary stats
                summary.total_input_tokens += result.total_input_tokens
                summary.total_output_tokens += result.total_output_tokens
                summary.total_duration_seconds += result.total_duration

                # Update master log
                self.master_logger.update_run(summary)

            # Run post_run hooks
            self._run_hooks(
                self.config.hooks.post_run,
                HookType.POST_RUN,
                "Running post_run hooks...",
            )

            # Finalize
            summary.completed_at = datetime.now()
            summary.status = RunStatus.COMPLETED if summary.failed_tasks == 0 else RunStatus.FAILED

        except Exception as e:
            summary.completed_at = datetime.now()
            summary.status = RunStatus.FAILED
            self.console.error(f"Execution failed: {e}")
            raise

        finally:
            # Cleanup git strategy
            if self._git_strategy:
                self._git_strategy.cleanup(run_id)

            # Save final summary
            self.master_logger.update_run(summary)
            self.master_logger.save_run_summary(summary)

        return summary

    def _execute_task(
        self,
        task: Task,
        run_id: str,
        index: int,
        total: int,
        completed_ids: set[str],
    ) -> ExecutionResult:
        """Execute a single task with retries.

        Args:
            task: Task to execute.
            run_id: ID of the current run.
            index: Task index (1-based).
            total: Total number of tasks.
            completed_ids: Set of completed task IDs.

        Returns:
            ExecutionResult with task execution details.
        """
        # Print task header
        self.console.print_task_header(task, index, total)

        # Check dependencies
        missing_deps = [d for d in task.depends_on if d not in completed_ids]
        if missing_deps:
            self.console.warning(f"Skipping {task.id}: missing dependencies {missing_deps}")
            return ExecutionResult(
                task_id=task.id,
                title=task.title,
                run_id=run_id,
                status=TaskStatus.SKIPPED,
                summary=f"Skipped due to missing dependencies: {missing_deps}",
            )

        # Initialize result
        result = ExecutionResult(
            task_id=task.id,
            title=task.title,
            run_id=run_id,
            status=TaskStatus.IN_PROGRESS,
        )

        # Git pre-task
        if self._git_strategy:
            self._git_strategy.pre_task(task, run_id)
            result.git_info.branch = task.get_branch_name()

        # Execute with retries
        max_retries = self.config.defaults.max_retries
        for attempt_num in range(1, max_retries + 1):
            attempt = self._execute_attempt(
                task,
                attempt_num,
                max_retries,
            )
            result.attempts.append(attempt)

            if attempt.outcome == "success":
                result.status = TaskStatus.COMPLETED

                # Git post-task
                if self._git_strategy:
                    commit_info = self._git_strategy.post_task(task, run_id, True)
                    if commit_info:
                        result.git_info.commits.append(commit_info)

                # Get changed files
                if self._git_manager:
                    result.files_changed = self._git_manager.get_changed_files()

                # Generate meaningful summary
                result.summary = self._generate_task_summary(result)

                # Run post-task analysis for production-ready tasks
                result.analysis_result = self._run_post_task_analysis(task, run_id, result)

                break
            else:
                if attempt_num < max_retries:
                    self.console.warning(
                        f"Attempt {attempt_num} failed, retrying in "
                        f"{self.config.defaults.retry_delay_seconds}s..."
                    )
                    time.sleep(self.config.defaults.retry_delay_seconds)

        else:
            # All retries exhausted
            result.status = TaskStatus.FAILED
            result.summary = f"Failed after {max_retries} attempts"

            # Git post-task (failure)
            if self._git_strategy:
                self._git_strategy.post_task(task, run_id, False)

        # Print status
        self.console.print_task_status(
            task,
            result.status,
            result.total_duration,
            result.total_tokens,
        )

        # Print brief summary
        git_commits = (
            [c.get("message", "") for c in result.git_info.commits]
            if result.git_info.commits
            else None
        )
        self.console.print_task_brief_summary(
            files_changed=result.files_changed,
            git_commits=git_commits,
            summary=result.summary if result.status == TaskStatus.COMPLETED else None,
        )

        return result

    def _execute_attempt(
        self,
        task: Task,
        attempt_num: int,
        max_attempts: int,
    ) -> TaskAttempt:
        """Execute a single attempt of a task.

        Args:
            task: Task to execute.
            attempt_num: Current attempt number.
            max_attempts: Maximum number of attempts.

        Returns:
            TaskAttempt with execution details.
        """
        attempt = TaskAttempt(
            attempt_number=attempt_num,
            started_at=datetime.now(),
        )

        self.console.info(f"[Step 1/4] Starting attempt {attempt_num}/{max_attempts}...")

        try:
            # Run pre_task hooks
            pre_hooks = self.config.hooks.pre_task + task.hooks.pre_task
            if pre_hooks:
                self.console.info(f"[Step 2/4] Running {len(pre_hooks)} pre-task hook(s)...")
                attempt.pre_task_hooks = self._run_hooks(
                    pre_hooks,
                    HookType.PRE_TASK,
                    report_results=True,
                )
                if not all(h.success for h in attempt.pre_task_hooks):
                    attempt.outcome = "failure"
                    attempt.error = "Pre-task hooks failed"
                    attempt.completed_at = datetime.now()
                    attempt.duration_seconds = (
                        attempt.completed_at - attempt.started_at
                    ).total_seconds()
                    return attempt
            else:
                self.console.debug("[Step 2/4] No pre-task hooks to run")

            # Build prompt and execute
            self.console.info("[Step 3/4] Building prompt and executing Claude Code...")
            prompt = self.engine.build_prompt(task, self.config)
            attempt.prompt = prompt

            self.console.start_progress("Waiting for Claude Code response...")
            engine_result = self.engine.execute(
                task,
                self.config,
                output_callback=self.console.stream_output,
            )
            self.console.stop_progress()

            attempt.claude_code_output = engine_result.output
            attempt.model = engine_result.model
            attempt.token_usage = engine_result.token_usage

            if not engine_result.success:
                attempt.outcome = "failure"
                attempt.error = engine_result.error
                attempt.completed_at = datetime.now()
                attempt.duration_seconds = (
                    attempt.completed_at - attempt.started_at
                ).total_seconds()
                return attempt

            # Run post_task hooks
            post_hooks = self.config.hooks.post_task + task.hooks.post_task
            if post_hooks:
                self.console.info(f"[Step 4/4] Running {len(post_hooks)} post-task hook(s)...")
                attempt.post_task_hooks = self._run_hooks(
                    post_hooks,
                    HookType.POST_TASK,
                    report_results=True,
                )
                if not all(h.success for h in attempt.post_task_hooks):
                    attempt.outcome = "failure"
                    attempt.error = "Post-task hooks failed"
                    attempt.completed_at = datetime.now()
                    attempt.duration_seconds = (
                        attempt.completed_at - attempt.started_at
                    ).total_seconds()
                    return attempt
            else:
                self.console.debug("[Step 4/4] No post-task hooks to run")

            # Success
            attempt.outcome = "success"
            attempt.completed_at = datetime.now()
            attempt.duration_seconds = (attempt.completed_at - attempt.started_at).total_seconds()

            self.console.success(
                f"Claude Code completed ({attempt.duration_seconds:.1f}s, "
                f"{attempt.tokens_used:,} tokens)"
            )

            return attempt

        except HookError as e:
            attempt.outcome = "failure"
            attempt.error = str(e)
            attempt.completed_at = datetime.now()
            attempt.duration_seconds = (attempt.completed_at - attempt.started_at).total_seconds()
            self.console.error(f"Hook failed: {e}")
            return attempt

        except Exception as e:
            attempt.outcome = "error"
            attempt.error = str(e)
            attempt.completed_at = datetime.now()
            attempt.duration_seconds = (attempt.completed_at - attempt.started_at).total_seconds()
            self.console.error(f"Execution error: {e}")
            return attempt

        finally:
            self.console.stop_progress()

    def _run_hooks(
        self,
        hooks: list[str],
        hook_type: HookType,
        message: str | None = None,
        report_results: bool = False,
    ) -> list[HookResult]:
        """Run a list of hooks.

        Args:
            hooks: List of hook commands.
            hook_type: Type of hooks being run.
            message: Optional message to log before running.
            report_results: Whether to report individual results.

        Returns:
            List of HookResult objects.
        """
        if not hooks:
            return []

        if message:
            self.console.info(message)

        results = self.hook_runner.run_hooks(
            hooks,
            hook_type,
            fail_on_error=False,  # We'll check results ourselves
        )

        if report_results:
            for result in results:
                self.console.print_hook_result(
                    result.command,
                    result.success,
                    result.output if not result.success else None,
                )

        return results

    def _dry_run(self, tasks: list[Task], summary: RunSummary) -> RunSummary:
        """Perform a dry run, showing what would execute.

        Args:
            tasks: Tasks to execute.
            summary: Run summary to update.

        Returns:
            Updated summary.
        """
        self.console.info("DRY RUN - No changes will be made")
        self.console.print("")

        for i, task in enumerate(tasks, 1):
            self.console.print(f"[{i}/{len(tasks)}] {task.id}: {task.title}")
            self.console.print(f"    Description: {task.description[:100]}...")
            if task.depends_on:
                self.console.print(f"    Dependencies: {', '.join(task.depends_on)}")
            if task.hooks.pre_task:
                self.console.print(f"    Pre-task hooks: {task.hooks.pre_task}")
            if task.hooks.post_task:
                self.console.print(f"    Post-task hooks: {task.hooks.post_task}")
            self.console.print("")

        summary.status = RunStatus.COMPLETED
        summary.completed_at = datetime.now()
        return summary

    def _generate_task_summary(self, result: ExecutionResult) -> str:
        """Generate a meaningful summary for a completed task.

        Args:
            result: Execution result with task details.

        Returns:
            Descriptive summary string.
        """
        parts: list[str] = []

        # Categorize changed files
        if result.files_changed:
            categories: dict[str, list[str]] = {
                "src": [],
                "test": [],
                "config": [],
                "docs": [],
                "other": [],
            }

            for file_path in result.files_changed:
                lower_path = file_path.lower()
                if "/test" in lower_path or lower_path.startswith("test"):
                    categories["test"].append(file_path)
                elif any(
                    lower_path.endswith(ext) for ext in (".yaml", ".yml", ".json", ".toml", ".ini")
                ):
                    categories["config"].append(file_path)
                elif any(lower_path.endswith(ext) for ext in (".md", ".rst", ".txt")):
                    categories["docs"].append(file_path)
                elif "/src/" in lower_path or lower_path.endswith(".py"):
                    categories["src"].append(file_path)
                else:
                    categories["other"].append(file_path)

            # Build summary parts
            file_parts: list[str] = []
            if categories["src"]:
                file_parts.append(f"{len(categories['src'])} source")
            if categories["test"]:
                file_parts.append(f"{len(categories['test'])} test")
            if categories["config"]:
                file_parts.append(f"{len(categories['config'])} config")
            if categories["docs"]:
                file_parts.append(f"{len(categories['docs'])} docs")
            if categories["other"]:
                file_parts.append(f"{len(categories['other'])} other")

            if file_parts:
                parts.append(f"Modified {', '.join(file_parts)} file(s)")
        else:
            parts.append("No files changed")

        # Add git commit info
        if result.git_info.commits:
            commit_count = len(result.git_info.commits)
            if commit_count == 1:
                commit_msg = result.git_info.commits[0].get("message", "")
                if commit_msg:
                    # Truncate long commit messages
                    if len(commit_msg) > 50:
                        commit_msg = commit_msg[:47] + "..."
                    parts.append(f"Committed: {commit_msg}")
            else:
                parts.append(f"Created {commit_count} commits")

        # Add duration and token info if available
        if result.total_duration > 0:
            duration_str = f"{result.total_duration:.1f}s"
            if result.total_tokens > 0:
                parts.append(f"Completed in {duration_str} using {result.total_tokens:,} tokens")
            else:
                parts.append(f"Completed in {duration_str}")

        return ". ".join(parts) if parts else "Task completed successfully"

    def _run_post_task_analysis(
        self,
        task: Task,
        run_id: str,
        result: ExecutionResult,
    ) -> dict[str, Any] | None:
        """Run code quality analysis for production-ready tasks.

        Args:
            task: The executed task.
            run_id: ID of the current run.
            result: Execution result with changed files.

        Returns:
            Analysis result dictionary or None if not applicable.
        """
        # Only run analysis for production-ready tasks
        if task.flavor != TaskFlavor.PRODUCTION_READY:
            return None

        # Only analyze if there are changed files
        if not result.files_changed:
            return None

        # Filter to Python files only (analysis currently supports Python)
        python_files = [
            f for f in result.files_changed if f.endswith(".py") and not f.startswith("test")
        ]
        if not python_files:
            return None

        try:
            self.console.debug("Running code quality analysis on changed files...")

            # Run analysis
            analysis_config = AnalysisConfig(
                paths=[Path(f) for f in python_files],
                enable_complexity=True,
                enable_quality=True,
                enable_maintainability=True,
                enable_security=False,  # Skip security for now
            )
            runner = AnalysisRunner(analysis_config)
            analysis_result = runner.analyze()

            # Store the analysis
            storage = TechDebtStorage(self.working_dir)
            label = f"{run_id}/{task.id}"
            report_id = storage.save_report(analysis_result, label=label)

            self.console.debug(f"Analysis saved: {report_id}")

            result_dict: dict[str, Any] = analysis_result.to_dict()
            return result_dict

        except Exception as e:
            self.console.warning(f"Code analysis failed: {e}")
            return None
