"""Context generator for enriching project context."""

import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from messirve.context.detector import ProjectDetector
from messirve.context.explorer import CodebaseExplorer
from messirve.context.models import ProjectContext


class ContextGenerator:
    """Generates and manages project context."""

    def __init__(self, project_dir: Path) -> None:
        """Initialize generator.

        Args:
            project_dir: Path to the project directory.
        """
        self.project_dir = project_dir
        self.context_dir = project_dir / ".messirve"
        self.context_file = self.context_dir / "context.yaml"
        self.context_md_file = self.context_dir / "context.md"

    def generate(self, force: bool = False) -> ProjectContext:
        """Generate project context.

        Args:
            force: If True, regenerate even if context exists.

        Returns:
            Generated ProjectContext.
        """
        if self.context_file.exists() and not force:
            return ProjectContext.from_file(self.context_file)

        # Detect project info
        detector = ProjectDetector(self.project_dir)
        context = detector.detect()

        # Save both YAML and markdown versions
        self.save(context)

        return context

    def save(self, context: ProjectContext) -> None:
        """Save context to files.

        Args:
            context: ProjectContext to save.
        """
        self.context_dir.mkdir(parents=True, exist_ok=True)
        context.save(self.context_file)
        context.save_markdown(self.context_md_file)

    def load(self) -> ProjectContext:
        """Load existing context.

        Returns:
            Loaded ProjectContext or empty context if not found.
        """
        if self.context_file.exists():
            return ProjectContext.from_file(self.context_file)
        return ProjectContext()

    def exists(self) -> bool:
        """Check if context file exists.

        Returns:
            True if context file exists.
        """
        return self.context_file.exists()

    def get_markdown(self) -> str:
        """Get context as markdown string.

        Returns:
            Markdown representation of context.
        """
        context = self.load()
        return context.to_markdown()


class OnboardingRunner:
    """Runs project onboarding process."""

    def __init__(
        self,
        project_dir: Path,
        output_callback: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize runner.

        Args:
            project_dir: Path to the project directory.
            output_callback: Optional callback for command output.
        """
        self.project_dir = project_dir
        self.output_callback = output_callback
        self.generator = ContextGenerator(project_dir)
        self.explorer = CodebaseExplorer(project_dir, output_callback)

    def run(
        self,
        skip_setup: bool = False,
        skip_verify: bool = False,
        force_context: bool = False,
        skip_exploration: bool = False,
    ) -> tuple[ProjectContext, list[dict[str, str | bool]], dict[str, Any]]:
        """Run full onboarding process.

        Args:
            skip_setup: Skip running setup commands.
            skip_verify: Skip running verification commands.
            force_context: Force regenerate context even if exists.
            skip_exploration: Skip Claude Code exploration.

        Returns:
            Tuple of (ProjectContext, list of command results, exploration data).
        """
        results: list[dict[str, str | bool]] = []
        exploration_data: dict[str, Any] = {}

        # Generate basic context from detection
        context = self.generator.generate(force=force_context)

        # Run Claude Code exploration to enrich context
        if not skip_exploration and self.explorer.is_available():
            if self.output_callback:
                self.output_callback("Running codebase exploration with Claude Code...")
            exploration_data = self.explorer.explore()
            if exploration_data:
                context = self.explorer.enrich_context(context, exploration_data)
                # Save the enriched context
                self.generator.save(context)
                if self.output_callback:
                    self.output_callback("Context enriched with exploration data")

        # Run setup commands
        if not skip_setup and context.setup_commands:
            for cmd in context.setup_commands:
                result = self._run_command(cmd, "setup")
                results.append(result)
                if not result["success"]:
                    break

        # Run verify commands
        if not skip_verify and context.verify_commands:
            for cmd in context.verify_commands:
                result = self._run_command(cmd, "verify")
                results.append(result)

        return context, results, exploration_data

    def _run_command(self, command: str, stage: str) -> dict[str, str | bool]:
        """Run a shell command.

        Args:
            command: Command to run.
            stage: Stage name (setup/verify).

        Returns:
            Dict with command, stage, success, and output.
        """
        if self.output_callback:
            self.output_callback(f"Running: {command}\n")

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            output = result.stdout + result.stderr
            success = result.returncode == 0

            if self.output_callback and output.strip():
                self.output_callback(output)

            return {
                "command": command,
                "stage": stage,
                "success": success,
                "output": output[:1000],  # Limit output size
            }

        except subprocess.TimeoutExpired:
            return {
                "command": command,
                "stage": stage,
                "success": False,
                "output": "Command timed out after 5 minutes",
            }
        except Exception as e:
            return {
                "command": command,
                "stage": stage,
                "success": False,
                "output": str(e),
            }

    def run_setup(self, context: ProjectContext) -> list[dict[str, str | bool]]:
        """Run only setup commands.

        Args:
            context: ProjectContext with setup commands.

        Returns:
            List of command results.
        """
        results = []
        for cmd in context.setup_commands:
            result = self._run_command(cmd, "setup")
            results.append(result)
            if not result["success"]:
                break
        return results

    def run_verify(self, context: ProjectContext) -> list[dict[str, str | bool]]:
        """Run only verification commands.

        Args:
            context: ProjectContext with verify commands.

        Returns:
            List of command results.
        """
        results = []
        for cmd in context.verify_commands:
            result = self._run_command(cmd, "verify")
            results.append(result)
        return results
