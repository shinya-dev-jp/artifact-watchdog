from __future__ import annotations

import json
from datetime import date as Date
from datetime import datetime
from pathlib import Path

from .core import AuditRow


def rows_to_json(rows: list[AuditRow]) -> str:
    return json.dumps([row.to_dict() for row in rows], indent=2, ensure_ascii=False)


def rows_to_text(rows: list[AuditRow]) -> str:
    lines = []
    for row in rows:
        line = (
            f"{row.id}\t{row.verdict.value}\tartifact={row.artifact_status}"
            f"\tlast={row.last_run_at}\tnext={row.next_run_at}\tdrift={row.time_drift}"
        )
        if row.state_error:
            line += f"\tstate_error={row.state_error}"
        lines.append(line)
    return "\n".join(lines)


def rows_to_markdown(rows: list[AuditRow], target_date: Date, generated_at: datetime) -> str:
    lines = [
        f"# Artifact Watchdog Report: {target_date.isoformat()}",
        "",
        f"Generated: {generated_at.isoformat(timespec='seconds')}",
        "",
        "## Summary",
        "",
        "| job | status | schedule | last run | next run | artifact | drift | state error | verdict |",
        "|---|---|---|---:|---:|---|---|---|---|",
    ]
    for row in rows:
        artifacts = ", ".join(row.artifacts_found) if row.artifacts_found else row.artifact_status
        lines.append(
            f"| `{_table_cell(row.id)}` | {_table_cell(row.status)} | `{_table_cell(row.schedule)}` | "
            f"{_table_cell(row.last_run_at)} | {_table_cell(row.next_run_at)} | {_table_cell(artifacts)} | "
            f"{_table_cell(row.time_drift)} | {_table_cell(row.state_error)} | {row.verdict.value} |"
        )

    failures = [row for row in rows if row.latest_failure]
    state_errors = [row for row in rows if row.state_error]
    lines.extend(["", "## Failure Evidence", ""])
    if failures:
        for row in failures:
            lines.extend([f"### {row.id}", "", "```text", row.latest_failure, "```", ""])
    else:
        lines.append("No matching runner failure logs were found.")

    lines.extend(["", "## State File Errors", ""])
    if state_errors:
        for row in state_errors:
            lines.extend([f"### {row.id}", "", "```text", row.state_error, "```", ""])
    else:
        lines.append("No state-file parsing errors were found.")

    lines.extend(
        [
            "",
            "## Reading The Verdicts",
            "",
            "- `OK`: at least one expected artifact exists.",
            "- `STATE_FILE_INVALID`: the configured state file exists but cannot be parsed as a JSON object.",
            "- `TIME_DRIFT_CHECK`: scheduler state points to a different time than the configured schedule.",
            "- `RUNNER_FAIL_LOG_FOUND`: no artifact was found, and a recent matching failure log exists.",
            "- `RUN_ATTEMPTED_ARTIFACT_MISSING`: state says the job ran on the target date, but no artifact exists.",
            "- `ARTIFACT_MISSING_OR_NOT_DUE`: the target due time has not passed yet.",
            "- `ARTIFACT_MISSING_DUE_PASSED`: the target due time has passed with no artifact and no failure evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(path: Path, rows: list[AuditRow], target_date: Date, generated_at: datetime) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rows_to_markdown(rows, target_date, generated_at) + "\n", encoding="utf-8")
    return path


def _table_cell(value: str) -> str:
    return value.replace("\n", " ").replace("|", "\\|")
