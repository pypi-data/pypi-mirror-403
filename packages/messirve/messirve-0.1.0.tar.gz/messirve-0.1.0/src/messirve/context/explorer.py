"""Codebase explorer using Claude Code."""

import json
import re
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from messirve.context.models import ProjectContext


class CodebaseExplorer:
    """Explores a codebase using Claude Code to generate comprehensive context."""

    CLAUDE_BINARY = "claude"

    EXPLORATION_PROMPT = """You are analyzing a codebase to generate a comprehensive project context document.

Explore this project thoroughly and provide a detailed analysis in the following JSON format:

{
    "architecture_summary": "A 2-3 paragraph description of the overall architecture and how components interact",
    "main_entry_points": ["List of main entry point files with brief descriptions"],
    "core_modules": {
        "module_path": "Description of what this module does and its responsibilities"
    },
    "key_patterns": ["List of important design patterns or architectural patterns used"],
    "data_flow": "Description of how data flows through the application",
    "external_dependencies": ["Important external services, APIs, or integrations"],
    "configuration": {
        "config_file": "Description of what this config file controls"
    },
    "testing_strategy": "Description of testing approach and test organization",
    "development_workflow": "Description of dev workflow based on scripts, configs, CI files"
}

Focus on:
1. Understanding the main purpose and architecture
2. Identifying key modules and their responsibilities
3. Understanding the data flow and component interactions
4. Noting important patterns and conventions
5. Identifying configuration and environment setup

Return ONLY the JSON object, no additional text or markdown formatting."""

    def __init__(
        self,
        project_dir: Path,
        output_callback: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize explorer.

        Args:
            project_dir: Path to the project directory.
            output_callback: Optional callback for status updates.
        """
        self.project_dir = project_dir
        self.output_callback = output_callback

    def is_available(self) -> bool:
        """Check if Claude CLI is available."""
        return shutil.which(self.CLAUDE_BINARY) is not None

    def explore(self) -> dict[str, Any]:
        """Explore the codebase using Claude Code.

        Returns:
            Dictionary with exploration results.
        """
        if not self.is_available():
            return {}

        claude_path = shutil.which(self.CLAUDE_BINARY)
        if not claude_path:
            return {}

        if self.output_callback:
            self.output_callback("Exploring codebase with Claude Code...")

        cmd = [
            claude_path,
            "-p",
            self.EXPLORATION_PROMPT,
            "--output-format",
            "text",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout for exploration
                cwd=self.project_dir,
            )

            if result.returncode != 0:
                if self.output_callback:
                    self.output_callback(f"Claude exploration failed: {result.stderr}")
                return {}

            return self._parse_exploration_result(result.stdout)

        except subprocess.TimeoutExpired:
            if self.output_callback:
                self.output_callback("Exploration timed out after 5 minutes")
            return {}
        except subprocess.SubprocessError as e:
            if self.output_callback:
                self.output_callback(f"Exploration error: {e}")
            return {}

    def _parse_exploration_result(self, output: str) -> dict[str, Any]:
        """Parse Claude's exploration output.

        Args:
            output: Raw output from Claude.

        Returns:
            Parsed exploration data.
        """
        if not output or not output.strip():
            return {}

        # Try to extract JSON from the output
        text = output.strip()

        # Try direct JSON parse first
        try:
            result: dict[str, Any] = json.loads(text)
            return result
        except json.JSONDecodeError:
            pass

        # Try to find JSON in markdown code block
        code_block_pattern = r"```(?:json)?\s*\n?([\s\S]*?)\n?```"
        matches = re.findall(code_block_pattern, text)
        for match in matches:
            try:
                result = json.loads(match.strip())
                return result
            except json.JSONDecodeError:
                continue

        # Try to find JSON object by braces
        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1 and start < end:
            try:
                result = json.loads(text[start : end + 1])
                return result
            except json.JSONDecodeError:
                pass

        return {}

    def enrich_context(
        self,
        context: ProjectContext,
        exploration_data: dict[str, Any],
    ) -> ProjectContext:
        """Enrich project context with exploration data.

        Args:
            context: Existing project context.
            exploration_data: Data from exploration.

        Returns:
            Enriched project context.
        """
        if not exploration_data:
            return context

        # Enrich description with architecture summary
        if exploration_data.get("architecture_summary"):
            if context.description:
                context.description = (
                    f"{context.description}\n\n"
                    f"## Architecture\n{exploration_data['architecture_summary']}"
                )
            else:
                context.description = exploration_data["architecture_summary"]

        # Add core modules to structure
        if exploration_data.get("core_modules"):
            for module_path, description in exploration_data["core_modules"].items():
                if module_path not in context.structure:
                    context.structure[module_path] = description

        # Add main entry points to key files
        if exploration_data.get("main_entry_points"):
            for entry in exploration_data["main_entry_points"]:
                if isinstance(entry, str) and ":" in entry:
                    parts = entry.split(":", 1)
                    context.key_files[parts[0].strip()] = parts[1].strip()
                elif isinstance(entry, str):
                    context.key_files[entry] = "Entry point"

        # Add configuration files
        if exploration_data.get("configuration"):
            for config_file, description in exploration_data["configuration"].items():
                if config_file not in context.key_files:
                    context.key_files[config_file] = description

        # Add patterns to coding standards
        if exploration_data.get("key_patterns"):
            for pattern in exploration_data["key_patterns"]:
                if pattern not in context.coding_standards:
                    context.coding_standards.append(f"Pattern: {pattern}")

        # Add business description enrichment
        if exploration_data.get("data_flow"):
            if context.business_description:
                context.business_description = (
                    f"{context.business_description}\n\nData Flow: {exploration_data['data_flow']}"
                )
            else:
                context.business_description = f"Data Flow: {exploration_data['data_flow']}"

        # Add testing info to non-functional requirements
        if exploration_data.get("testing_strategy"):
            context.non_functional_requirements["Testing Strategy"] = exploration_data[
                "testing_strategy"
            ]

        if exploration_data.get("development_workflow"):
            context.non_functional_requirements["Development Workflow"] = exploration_data[
                "development_workflow"
            ]

        return context

    def generate_context_markdown(self, exploration_data: dict[str, Any]) -> str:
        """Generate rich context markdown from exploration data.

        Args:
            exploration_data: Data from exploration.

        Returns:
            Markdown string with exploration context.
        """
        if not exploration_data:
            return ""

        lines = ["## Codebase Analysis", ""]

        if exploration_data.get("architecture_summary"):
            lines.append("### Architecture Overview")
            lines.append(exploration_data["architecture_summary"])
            lines.append("")

        if exploration_data.get("main_entry_points"):
            lines.append("### Main Entry Points")
            for entry in exploration_data["main_entry_points"]:
                lines.append(f"- {entry}")
            lines.append("")

        if exploration_data.get("core_modules"):
            lines.append("### Core Modules")
            for module_path, description in exploration_data["core_modules"].items():
                lines.append(f"- **{module_path}**: {description}")
            lines.append("")

        if exploration_data.get("key_patterns"):
            lines.append("### Key Patterns")
            for pattern in exploration_data["key_patterns"]:
                lines.append(f"- {pattern}")
            lines.append("")

        if exploration_data.get("data_flow"):
            lines.append("### Data Flow")
            lines.append(exploration_data["data_flow"])
            lines.append("")

        if exploration_data.get("external_dependencies"):
            lines.append("### External Dependencies")
            for dep in exploration_data["external_dependencies"]:
                lines.append(f"- {dep}")
            lines.append("")

        if exploration_data.get("configuration"):
            lines.append("### Configuration")
            for config_file, description in exploration_data["configuration"].items():
                lines.append(f"- **{config_file}**: {description}")
            lines.append("")

        if exploration_data.get("testing_strategy"):
            lines.append("### Testing Strategy")
            lines.append(exploration_data["testing_strategy"])
            lines.append("")

        if exploration_data.get("development_workflow"):
            lines.append("### Development Workflow")
            lines.append(exploration_data["development_workflow"])
            lines.append("")

        return "\n".join(lines)
