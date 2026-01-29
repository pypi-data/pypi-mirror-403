"""Claude Code execution engine."""

import json
import shutil
import subprocess
from collections.abc import Callable

from messirve.context.models import ProjectContext
from messirve.engines.base import Engine, EngineResult
from messirve.exceptions import ClaudeCodeError
from messirve.models.config import ClaudePermissions, MessirveConfig
from messirve.models.execution import TokenUsage
from messirve.models.task import Task


class ClaudeCodeEngine(Engine):
    """Engine that executes tasks using Claude Code CLI."""

    CLAUDE_BINARY = "claude"

    def __init__(self, project_context: ProjectContext | None = None) -> None:
        """Initialize the Claude Code engine.

        Args:
            project_context: Optional project context to include in prompts.
        """
        self._claude_path: str | None = None
        self.project_context = project_context

    def is_available(self) -> bool:
        """Check if Claude Code CLI is available.

        Returns:
            True if Claude Code is installed and accessible.
        """
        return shutil.which(self.CLAUDE_BINARY) is not None

    def _get_claude_path(self) -> str:
        """Get the path to the Claude Code binary.

        Returns:
            Path to the Claude Code binary.

        Raises:
            ClaudeCodeError: If Claude Code is not installed.
        """
        if self._claude_path is None:
            self._claude_path = shutil.which(self.CLAUDE_BINARY)
            if self._claude_path is None:
                raise ClaudeCodeError(
                    "Claude Code CLI not found. Please install it first.",
                    exit_code=1,
                )
        return self._claude_path

    def build_prompt(self, task: Task, config: MessirveConfig) -> str:
        """Build the prompt for Claude Code.

        Args:
            task: The task to build a prompt for.
            config: Messirve configuration.

        Returns:
            Complete prompt string.
        """
        lines: list[str] = []

        # Include project context if available
        if self.project_context and config.context.include_project_context:
            lines.append("=" * 60)
            lines.append("PROJECT CONTEXT")
            lines.append("=" * 60)
            lines.append("")

            if self.project_context.name:
                lines.append(f"Project: {self.project_context.name}")

            if self.project_context.description:
                lines.append(f"Description: {self.project_context.description}")
                lines.append("")

            # Tech stack
            if self.project_context.tech_stack:
                ts = self.project_context.tech_stack
                lines.append("Tech Stack:")
                if ts.language:
                    lines.append(f"  - Language: {ts.language}")
                if ts.framework:
                    lines.append(f"  - Framework: {ts.framework}")
                if ts.package_manager:
                    lines.append(f"  - Package Manager: {ts.package_manager}")
                if ts.database:
                    lines.append(f"  - Database: {ts.database}")
                if ts.testing:
                    lines.append(f"  - Testing: {ts.testing}")
                if ts.linting:
                    lines.append(f"  - Linting: {ts.linting}")
                lines.append("")

            # Business context
            if self.project_context.business_description:
                lines.append("Business Context:")
                lines.append(self.project_context.business_description)
                lines.append("")

            if self.project_context.users:
                lines.append(f"Target Users: {self.project_context.users}")
                lines.append("")

            # Requirements
            if self.project_context.functional_requirements:
                lines.append("Functional Requirements:")
                for req in self.project_context.functional_requirements:
                    lines.append(f"  - {req}")
                lines.append("")

            if self.project_context.non_functional_requirements:
                lines.append("Non-Functional Requirements:")
                for req in self.project_context.non_functional_requirements:
                    lines.append(f"  - {req}")
                lines.append("")

            # Coding standards
            if self.project_context.coding_standards:
                lines.append("Coding Standards:")
                for standard in self.project_context.coding_standards:
                    lines.append(f"  - {standard}")
                lines.append("")

            lines.append("=" * 60)
            lines.append("")

        # Task header
        lines.append(f"Task: {task.title}")
        lines.append(f"Task ID: {task.id}")
        lines.append("")

        # Flavor guidance
        if task.flavor:
            lines.append(f"Task Flavor: {task.flavor.value}")
            lines.append(self._get_flavor_guidance(task.flavor.value))
            lines.append("")

        # Description
        lines.append("Description:")
        lines.append(task.description.strip())
        lines.append("")

        # Context
        lines.append("Context:")
        lines.append(task.context.strip())
        lines.append("")

        # Acceptance Criteria
        lines.append("Acceptance Criteria:")
        for criterion in task.acceptance_criteria:
            lines.append(f"- {criterion}")
        lines.append("")

        # Project Rules
        if config.rules:
            lines.append("Project Rules:")
            for rule in config.rules:
                lines.append(f"- {rule}")
            lines.append("")

        # File Boundaries
        if config.boundaries.never_modify or config.boundaries.read_only:
            lines.append("File Boundaries:")
            if config.boundaries.never_modify:
                lines.append("Never modify these files:")
                for pattern in config.boundaries.never_modify:
                    lines.append(f"  - {pattern}")
            if config.boundaries.read_only:
                lines.append("Read-only files (do not modify):")
                for pattern in config.boundaries.read_only:
                    lines.append(f"  - {pattern}")
            lines.append("")

        # Instructions
        lines.append("Instructions:")
        lines.append("- Implement the task as described above")
        lines.append("- Ensure all acceptance criteria are met")
        lines.append("- Follow all project rules")
        lines.append("- Respect file boundaries")
        lines.append("- Write tests if applicable")

        return "\n".join(lines)

    def _get_flavor_guidance(self, flavor: str) -> str:
        """Get guidance text for a task flavor.

        Args:
            flavor: The task flavor.

        Returns:
            Guidance text for the flavor.
        """
        guidance = {
            "production-ready": (
                "This task requires production-quality code with comprehensive tests, "
                "proper error handling, documentation, and following best practices."
            ),
            "poc": (
                "This is a proof-of-concept task. Focus on demonstrating the core idea "
                "with minimal but working implementation. Polish is not required."
            ),
            "documentation": (
                "Focus on documentation: README, docstrings, examples, and inline comments. "
                "Code changes should be minimal and primarily to support documentation."
            ),
            "refactoring": (
                "Improve code structure and quality without changing functionality. "
                "Add tests to verify behavior preservation."
            ),
            "bug-fix": (
                "Focus on fixing the specific issue with minimal changes. "
                "Add regression tests to prevent the bug from recurring."
            ),
            "testing": (
                "Focus on comprehensive test coverage: unit tests, integration tests, "
                "edge cases, and error scenarios. Improve test quality and organization."
            ),
            "exploration": (
                "This is exploratory work. Try different approaches, experiment, "
                "and document findings. Code doesn't need to be production-ready."
            ),
        }
        return guidance.get(flavor, "")

    def execute(
        self,
        task: Task,
        config: MessirveConfig,
        output_callback: Callable[[str], None] | None = None,
    ) -> EngineResult:
        """Execute a task using Claude Code CLI.

        Args:
            task: The task to execute.
            config: Messirve configuration.
            output_callback: Optional callback for streaming output.

        Returns:
            EngineResult with execution details.
        """
        claude_path = self._get_claude_path()
        prompt = self.build_prompt(task, config)

        # Build command - use JSON output for structured data
        cmd = [claude_path, "-p", prompt, "--output-format", "json"]

        # Add permission flag
        if config.defaults.claude_code_permissions == ClaudePermissions.SKIP:
            cmd.append("--dangerously-skip-permissions")

        try:
            # Run Claude Code
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            output_lines: list[str] = []
            if process.stdout:
                for line in process.stdout:
                    output_lines.append(line)
                    if output_callback:
                        output_callback(line)

            process.wait()
            output = "".join(output_lines)
            exit_code = process.returncode

            # Parse JSON output
            model, token_usage, result_text = self._parse_json_output(output)

            if exit_code == 0:
                return EngineResult(
                    success=True,
                    output=result_text or output,
                    exit_code=exit_code,
                    model=model,
                    token_usage=token_usage,
                )
            else:
                return EngineResult(
                    success=False,
                    output=result_text or output,
                    exit_code=exit_code,
                    model=model,
                    token_usage=token_usage,
                    error=f"Claude Code exited with code {exit_code}",
                )

        except FileNotFoundError:
            raise ClaudeCodeError(
                "Claude Code CLI not found. Please install it first.",
                exit_code=1,
            )
        except subprocess.SubprocessError as e:
            return EngineResult(
                success=False,
                output="",
                exit_code=1,
                error=str(e),
            )

    def _parse_json_output(self, output: str) -> tuple[str, TokenUsage, str]:
        """Parse JSON output from Claude Code CLI.

        Args:
            output: Raw output from Claude Code.

        Returns:
            Tuple of (model, token_usage, result_text).
        """
        model = ""
        token_usage = TokenUsage()
        result_text = output

        try:
            # Try to parse as JSON
            data = json.loads(output)

            # Extract model
            model = data.get("model", "")

            # Extract token usage from various possible locations
            usage = data.get("usage", {})
            if usage:
                token_usage = TokenUsage(
                    input_tokens=usage.get("input_tokens", 0),
                    output_tokens=usage.get("output_tokens", 0),
                    cache_read_tokens=usage.get("cache_read_input_tokens", 0),
                    cache_creation_tokens=usage.get("cache_creation_input_tokens", 0),
                )

            # Extract result text
            result_text = data.get("result", data.get("response", output))

        except json.JSONDecodeError:
            # Output is not JSON, try to extract info from text
            # Look for streaming JSON lines (one per line)
            for line in output.strip().split("\n"):
                try:
                    data = json.loads(line)
                    if "model" in data and not model:
                        model = data["model"]
                    if "usage" in data:
                        usage = data["usage"]
                        token_usage = TokenUsage(
                            input_tokens=usage.get("input_tokens", 0),
                            output_tokens=usage.get("output_tokens", 0),
                            cache_read_tokens=usage.get("cache_read_input_tokens", 0),
                            cache_creation_tokens=usage.get("cache_creation_input_tokens", 0),
                        )
                except json.JSONDecodeError:
                    continue

        return model, token_usage, result_text
