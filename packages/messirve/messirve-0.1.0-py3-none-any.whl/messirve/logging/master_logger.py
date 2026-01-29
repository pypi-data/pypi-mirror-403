"""Master logger for tracking all execution runs."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from messirve.models.execution import RunStatus, RunSummary


class MasterLogger:
    """Logger for tracking all execution runs."""

    def __init__(self, log_dir: Path) -> None:
        """Initialize the master logger.

        Args:
            log_dir: Base log directory.
        """
        self.log_dir = log_dir
        self.master_file = log_dir / "master.json"
        self._ensure_log_dir()

    def _ensure_log_dir(self) -> None:
        """Ensure the log directory exists."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        if not self.master_file.exists():
            self._write_master({"version": "1.0", "runs": []})

    def _read_master(self) -> dict[str, Any]:
        """Read the master log file.

        Returns:
            Master log data.
        """
        if not self.master_file.exists():
            return {"version": "1.0", "runs": []}
        with open(self.master_file) as f:
            return cast(dict[str, Any], json.load(f))

    def _write_master(self, data: dict[str, Any]) -> None:
        """Write the master log file.

        Args:
            data: Master log data to write.
        """
        with open(self.master_file, "w") as f:
            json.dump(data, f, indent=2)

    def start_run(self, run_id: str, tasks_file: str, git_strategy: str) -> None:
        """Record the start of a new run.

        Args:
            run_id: ID of the run.
            tasks_file: Path to the tasks file.
            git_strategy: Git strategy being used.
        """
        master = self._read_master()
        run_entry: dict[str, Any] = {
            "run_id": run_id,
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "status": RunStatus.IN_PROGRESS.value,
            "tasks_file": tasks_file,
            "git_strategy": git_strategy,
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "skipped_tasks": 0,
            "total_duration_seconds": 0,
            "total_tokens_used": 0,
            "total_cost_usd": 0,
            "task_refs": [],
        }
        master["runs"].append(run_entry)
        self._write_master(master)

    def update_run(self, summary: RunSummary) -> None:
        """Update a run in the master log.

        Args:
            summary: Run summary to update.
        """
        master = self._read_master()

        # Find and update the run
        for i, run in enumerate(master["runs"]):
            if run["run_id"] == summary.run_id:
                master["runs"][i] = {
                    "run_id": summary.run_id,
                    "started_at": summary.started_at.isoformat(),
                    "completed_at": (
                        summary.completed_at.isoformat() if summary.completed_at else None
                    ),
                    "status": summary.status.value,
                    "tasks_file": summary.tasks_file,
                    "git_strategy": summary.git_strategy,
                    "total_tasks": summary.total_tasks,
                    "completed_tasks": summary.completed_tasks,
                    "failed_tasks": summary.failed_tasks,
                    "skipped_tasks": summary.skipped_tasks,
                    "total_duration_seconds": summary.total_duration_seconds,
                    "total_tokens_used": summary.total_tokens_used,
                    "total_cost_usd": summary.total_cost_usd,
                    "task_refs": [
                        {
                            "task_id": r.task_id,
                            "status": r.status.value,
                            "log_file": f"runs/{summary.run_id}/{r.task_id}.json",
                        }
                        for r in summary.task_results
                    ],
                }
                break

        self._write_master(master)

    def get_runs(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Get run history.

        Args:
            limit: Maximum number of runs to return.

        Returns:
            List of run entries.
        """
        master = self._read_master()
        runs: list[dict[str, Any]] = master.get("runs", [])

        # Sort by started_at descending
        runs.sort(key=lambda r: r.get("started_at", ""), reverse=True)

        if limit:
            runs = runs[:limit]

        return runs

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        """Get a specific run.

        Args:
            run_id: ID of the run to get.

        Returns:
            Run entry or None if not found.
        """
        master = self._read_master()
        runs: list[dict[str, Any]] = master.get("runs", [])
        for run in runs:
            if run["run_id"] == run_id:
                return run
        return None

    def save_run_summary(self, summary: RunSummary) -> None:
        """Save a run summary to its own file.

        Args:
            summary: Run summary to save.
        """
        run_dir = self.log_dir / "runs" / summary.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        run_file = run_dir / "run.json"
        with open(run_file, "w") as f:
            json.dump(summary.to_dict(), f, indent=2)
