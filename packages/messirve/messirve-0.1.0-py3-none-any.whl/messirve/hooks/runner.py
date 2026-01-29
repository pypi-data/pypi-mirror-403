"""Hook runner for executing shell commands."""

import subprocess
import time
from collections.abc import Callable, Sequence

from messirve.exceptions import HookError
from messirve.hooks.types import HookConfig, HookType
from messirve.models.execution import HookResult


class HookRunner:
    """Runs hooks (shell commands) for various stages of execution."""

    def __init__(
        self,
        working_dir: str | None = None,
        output_callback: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize the hook runner.

        Args:
            working_dir: Working directory for hook execution.
            output_callback: Callback for streaming output.
        """
        self.working_dir = working_dir
        self.output_callback = output_callback

    def run_hook(
        self,
        hook: HookConfig | str,
        hook_type: HookType,
        fail_on_error: bool = True,
    ) -> HookResult:
        """Run a single hook.

        Args:
            hook: Hook configuration or command string.
            hook_type: Type of hook being run.
            fail_on_error: Whether to raise an exception on failure.

        Returns:
            HookResult with execution details.

        Raises:
            HookError: If the hook fails and fail_on_error is True.
        """
        if isinstance(hook, str):
            hook = HookConfig.from_string(hook)

        start_time = time.time()

        try:
            process = subprocess.Popen(
                hook.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=self.working_dir,
            )

            output_lines: list[str] = []
            if process.stdout:
                for line in process.stdout:
                    output_lines.append(line)
                    if self.output_callback:
                        self.output_callback(line.rstrip())

            process.wait(timeout=hook.timeout)
            output = "".join(output_lines)
            exit_code = process.returncode
            duration = time.time() - start_time

            result = HookResult(
                command=hook.command,
                exit_code=exit_code,
                output=output,
                duration_seconds=duration,
            )

            if exit_code != 0 and fail_on_error and not hook.continue_on_failure:
                raise HookError(
                    f"Hook failed: {hook.command}",
                    hook_type=hook_type.value,
                    command=hook.command,
                    exit_code=exit_code,
                    output=output,
                )

            return result

        except subprocess.TimeoutExpired:
            process.kill()
            duration = time.time() - start_time
            result = HookResult(
                command=hook.command,
                exit_code=-1,
                output="Hook timed out",
                duration_seconds=duration,
            )
            if fail_on_error:
                raise HookError(
                    f"Hook timed out after {hook.timeout}s: {hook.command}",
                    hook_type=hook_type.value,
                    command=hook.command,
                    exit_code=-1,
                    output="Timeout",
                )
            return result

        except subprocess.SubprocessError as e:
            duration = time.time() - start_time
            result = HookResult(
                command=hook.command,
                exit_code=-1,
                output=str(e),
                duration_seconds=duration,
            )
            if fail_on_error:
                raise HookError(
                    f"Hook execution failed: {e}",
                    hook_type=hook_type.value,
                    command=hook.command,
                    exit_code=-1,
                    output=str(e),
                )
            return result

    def run_hooks(
        self,
        hooks: Sequence[HookConfig | str],
        hook_type: HookType,
        fail_on_error: bool = True,
    ) -> list[HookResult]:
        """Run multiple hooks in sequence.

        Args:
            hooks: List of hook configurations or command strings.
            hook_type: Type of hooks being run.
            fail_on_error: Whether to raise an exception on failure.

        Returns:
            List of HookResult objects.

        Raises:
            HookError: If any hook fails and fail_on_error is True.
        """
        results: list[HookResult] = []
        for hook in hooks:
            result = self.run_hook(hook, hook_type, fail_on_error)
            results.append(result)
        return results
