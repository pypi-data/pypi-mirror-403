"""Task generator using Claude to convert goals into tasks."""

import json
import shutil
import subprocess
from pathlib import Path

from messirve.context.models import ProjectContext
from messirve.planning.models import GeneratedTask, PlanningGoal


class TaskGenerator:
    """Generates tasks from goals using Claude."""

    CLAUDE_BINARY = "claude"

    def __init__(self, project_context: ProjectContext | None = None) -> None:
        """Initialize the task generator.

        Args:
            project_context: Optional project context to include in prompts.
        """
        self.project_context = project_context

    def is_available(self) -> bool:
        """Check if Claude CLI is available."""
        return shutil.which(self.CLAUDE_BINARY) is not None

    def generate_tasks(
        self,
        goals: list[PlanningGoal],
        num_tasks: int = 5,
    ) -> list[GeneratedTask]:
        """Generate tasks from goals using Claude.

        Args:
            goals: List of high-level goals.
            num_tasks: Approximate number of tasks to generate.

        Returns:
            List of generated tasks.
        """
        prompt = self._build_prompt(goals, num_tasks)
        output = self._call_claude(prompt)
        return self._parse_response(output)

    def _build_prompt(self, goals: list[PlanningGoal], num_tasks: int) -> str:
        """Build the prompt for task generation."""
        lines = [
            "You are a software project planner. Your task is to break down high-level goals",
            "into concrete, actionable development tasks.",
            "",
        ]

        # Include project context if available
        if self.project_context:
            lines.append("=== PROJECT CONTEXT ===")
            if self.project_context.name:
                lines.append(f"Project: {self.project_context.name}")
            if self.project_context.description:
                lines.append(f"Description: {self.project_context.description}")

            if self.project_context.tech_stack:
                ts = self.project_context.tech_stack
                lines.append("Tech Stack:")
                if ts.language:
                    lines.append(f"  - Language: {ts.language}")
                if ts.framework:
                    lines.append(f"  - Framework: {ts.framework}")
                if ts.testing:
                    lines.append(f"  - Testing: {ts.testing}")

            if self.project_context.coding_standards:
                lines.append("Coding Standards:")
                for standard in self.project_context.coding_standards:
                    lines.append(f"  - {standard}")

            lines.append("")

        # Goals
        lines.append("=== GOALS TO ACCOMPLISH ===")
        for i, goal in enumerate(goals, 1):
            priority_label = {1: "HIGH", 2: "MEDIUM", 3: "LOW"}.get(goal.priority, "MEDIUM")
            lines.append(f"{i}. [{priority_label}] {goal.description}")
        lines.append("")

        # Instructions
        lines.append("=== INSTRUCTIONS ===")
        lines.append(
            f"Generate approximately {num_tasks} development tasks to accomplish these goals."
        )
        lines.append("")
        lines.append("IMPORTANT: Your response must be ONLY a valid JSON array. No explanations,")
        lines.append(
            "no markdown formatting, no code blocks - just raw JSON starting with [ and ending with ]."
        )
        lines.append("")
        lines.append("JSON Schema:")
        lines.append("""[
  {
    "id": "TASK-001",
    "title": "Short descriptive title (max 80 chars)",
    "description": "Detailed description of what needs to be done",
    "context": "Why this task matters and relevant background",
    "acceptance_criteria": ["Criterion 1", "Criterion 2"],
    "complexity": "low|medium|high"
  }
]""")
        lines.append("")
        lines.append("Requirements:")
        lines.append("- IDs must be sequential: TASK-001, TASK-002, etc.")
        lines.append("- Tasks should be specific and actionable")
        lines.append("- Each task should be completable in a reasonable time")
        lines.append("- Include 2-4 acceptance criteria per task")
        lines.append("- Order tasks logically (foundational tasks first)")
        lines.append("- DO NOT include depends_on field")
        lines.append("")
        lines.append("Remember: Output ONLY the JSON array, nothing else.")

        return "\n".join(lines)

    def _call_claude(self, prompt: str) -> str:
        """Call Claude CLI with the prompt."""
        claude_path = shutil.which(self.CLAUDE_BINARY)
        if not claude_path:
            raise RuntimeError("Claude CLI not found. Please install it first.")

        cmd = [
            claude_path,
            "-p",
            prompt,
            "--output-format",
            "text",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,  # Increased timeout for complex prompts
            )

            # Check for errors
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                raise RuntimeError(f"Claude CLI returned error: {error_msg}")

            if not result.stdout.strip():
                error_msg = result.stderr.strip() if result.stderr else "No output"
                raise RuntimeError(f"Claude CLI returned empty output. Stderr: {error_msg}")

            return result.stdout

        except subprocess.TimeoutExpired:
            raise RuntimeError("Claude CLI timed out after 180 seconds")
        except subprocess.SubprocessError as e:
            raise RuntimeError(f"Claude CLI failed: {e}")

    def _parse_response(self, output: str) -> list[GeneratedTask]:
        """Parse Claude's response into GeneratedTask objects."""
        if not output or not output.strip():
            raise ValueError("Claude returned empty output")

        # Try to find JSON array in the output
        json_str = self._extract_json(output)

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse Claude's response as JSON: {e}\n"
                f"Extracted JSON: {json_str[:500]}\n"
                f"Full output: {output[:1000]}"
            )

        if not isinstance(data, list):
            raise ValueError(f"Expected JSON array, got {type(data).__name__}")

        if not data:
            raise ValueError("Claude returned an empty task list")

        tasks: list[GeneratedTask] = []
        for item in data:
            task = GeneratedTask(
                id=item.get("id", f"TASK-{len(tasks) + 1:03d}"),
                title=item.get("title", "Untitled Task"),
                description=item.get("description", ""),
                context=item.get("context", ""),
                acceptance_criteria=item.get("acceptance_criteria", []),
                depends_on=[],  # Users add dependencies manually
                complexity=item.get("complexity", "medium"),
            )
            tasks.append(task)

        return tasks

    def _extract_json(self, text: str) -> str:
        """Extract JSON array from text that may contain other content."""
        import re

        # First, try to parse the whole text as JSON directly
        text = text.strip()
        if text.startswith("["):
            try:
                json.loads(text)
                return text
            except json.JSONDecodeError:
                pass

        # Try to extract from markdown code block (```json ... ``` or ``` ... ```)
        code_block_pattern = r"```(?:json)?\s*\n?([\s\S]*?)\n?```"
        matches: list[str] = re.findall(code_block_pattern, text)
        for match in matches:
            match_str = match.strip()
            if match_str.startswith("["):
                try:
                    json.loads(match_str)
                    return match_str
                except json.JSONDecodeError:
                    continue

        # Fall back to finding [ and ] brackets
        start = text.find("[")
        end = text.rfind("]")

        if start == -1 or end == -1 or start >= end:
            # Provide helpful error with actual output
            preview = text[:500] if len(text) > 500 else text
            raise ValueError(f"No JSON array found in output. Claude returned:\n{preview}")

        return text[start : end + 1]


def load_project_context(project_dir: Path) -> ProjectContext | None:
    """Load project context if available.

    Args:
        project_dir: Project directory.

    Returns:
        ProjectContext or None if not found.
    """
    from messirve.context.generator import ContextGenerator

    generator = ContextGenerator(project_dir)
    if generator.exists():
        try:
            return generator.load()
        except Exception:
            return None
    return None
