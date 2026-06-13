#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass
from datetime import date as Date
from datetime import datetime
from datetime import timedelta
from pathlib import Path

from artifact_watchdog.config import load_config
from artifact_watchdog.core import AuditRow, Verdict, audit_workspace
from artifact_watchdog.report import rows_to_json, write_markdown


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "examples" / "failure-lab" / "artifact-watchdog.toml"
DEFAULT_WORKSPACE = REPO_ROOT / ".artifact-watchdog" / "failure-lab"
DEFAULT_DATE = "2026-06-07"
DEFAULT_NOW = "2026-06-07T08:30:00+00:00"
MARKER = ".artifact-watchdog-failure-lab"


@dataclass(frozen=True)
class Case:
    expected: Verdict
    signal: str
    operator_action: str


CASES: dict[str, Case] = {
    "healthy-report": Case(
        Verdict.OK,
        "Expected artifact exists for the target date.",
        "No action; keep the artifact contract unchanged.",
    ),
    "attempted-no-artifact": Case(
        Verdict.RUN_ATTEMPTED_ARTIFACT_MISSING,
        "State says the job ran today, but the promised artifact is missing.",
        "Rerun or inspect the job after the point where it writes the artifact.",
    ),
    "runner-failure-log": Case(
        Verdict.RUNNER_FAIL_LOG_FOUND,
        "A recent runner log contains a configured failure phrase.",
        "Start from the failure log before rerunning.",
    ),
    "time-drift": Case(
        Verdict.TIME_DRIFT_CHECK,
        "The scheduler state points to a different next run time than the config.",
        "Fix scheduler drift or update the config if the schedule intentionally changed.",
    ),
    "not-due-yet": Case(
        Verdict.ARTIFACT_MISSING_OR_NOT_DUE,
        "The artifact is missing, but the configured due time has not passed.",
        "Wait until due time plus grace before treating it as a failure.",
    ),
    "due-passed-missing": Case(
        Verdict.ARTIFACT_MISSING_DUE_PASSED,
        "The due time passed with no artifact, state, or matching failure log.",
        "Check whether the scheduler skipped the job entirely.",
    ),
    "stale-artifact-only": Case(
        Verdict.ARTIFACT_MISSING_DUE_PASSED,
        "A previous day's artifact exists, but today's artifact is missing.",
        "Do not accept stale output; produce the target-date artifact.",
    ),
    "invalid-state-json": Case(
        Verdict.STATE_FILE_INVALID,
        "The configured state file exists but is not valid JSON.",
        "Repair or regenerate the state file before trusting scheduler metadata.",
    ),
    "partial-suite-report": Case(
        Verdict.OK,
        "One artifact in a multi-job suite exists.",
        "Keep the successful artifact and inspect the sibling failure separately.",
    ),
    "partial-suite-index": Case(
        Verdict.RUN_ATTEMPTED_ARTIFACT_MISSING,
        "A sibling job in the same suite ran but did not write its artifact.",
        "Treat the suite as partial success, not a blanket pass.",
    ),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a deterministic failure-injection workspace and verify watchdog verdicts."
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Failure lab TOML config.")
    parser.add_argument("--workspace", default=str(DEFAULT_WORKSPACE), help="Workspace to generate.")
    parser.add_argument("--date", default=DEFAULT_DATE, help="Target date in YYYY-MM-DD.")
    parser.add_argument("--now", default=DEFAULT_NOW, help="Current time as an ISO-8601 timestamp.")
    parser.add_argument("--markdown", help="Markdown report path. Defaults inside the generated workspace.")
    parser.add_argument("--json", help="JSON report path. Defaults inside the generated workspace.")
    parser.add_argument("--matrix", help="Human-readable verdict matrix path. Defaults inside the workspace.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config_path = Path(args.config)
    workspace = Path(args.workspace)
    target_date = Date.fromisoformat(args.date)
    now = datetime.fromisoformat(args.now.replace("Z", "+00:00"))

    reset_workspace(workspace)
    populate_workspace(workspace, target_date)

    config = load_config(config_path)
    rows = audit_workspace(config, workspace, target_date, now)
    mismatches = expected_mismatches(rows)

    markdown_path = Path(args.markdown) if args.markdown else workspace / "reports" / "failure-lab.md"
    json_path = Path(args.json) if args.json else workspace / "reports" / "failure-lab.json"
    matrix_path = Path(args.matrix) if args.matrix else workspace / "reports" / "failure-lab-matrix.md"

    write_markdown(markdown_path, rows, target_date, now)
    write_json(json_path, rows)
    write_matrix(matrix_path, rows, target_date, now)

    if mismatches:
        for mismatch in mismatches:
            print(mismatch, file=sys.stderr)
        return 1

    print(f"failure lab ok rows={len(rows)}")
    print(f"workspace={workspace}")
    print(f"matrix={matrix_path}")
    print(f"markdown={markdown_path}")
    print(f"json={json_path}")
    return 0


def reset_workspace(workspace: Path) -> None:
    if workspace.exists():
        marker = workspace / MARKER
        if not marker.exists() and any(workspace.iterdir()):
            raise SystemExit(
                f"refusing to reset non-lab workspace: {workspace}. "
                f"Choose an empty directory or one containing {MARKER}."
            )
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    (workspace / MARKER).write_text("artifact-watchdog failure lab workspace\n", encoding="utf-8")


def populate_workspace(workspace: Path, target_date: Date) -> None:
    day = target_date.isoformat()
    previous_day = (target_date - timedelta(days=1)).isoformat()

    write_text(workspace / "artifacts" / day / "healthy-report.txt", "healthy report\n")
    write_json_file(
        workspace / "state" / "healthy-report.json",
        {
            "last_run_at": f"{day}T02:01:00+00:00",
            "next_run_at": "2026-06-08T02:00:00+00:00",
            "schedule": "daily@02:00",
        },
    )

    write_json_file(
        workspace / "state" / "attempted-no-artifact.json",
        {
            "last_run_at": f"{day}T03:01:00+00:00",
            "next_run_at": "2026-06-08T03:00:00+00:00",
            "schedule": "daily@03:00",
        },
    )

    write_json_file(
        workspace / "state" / "runner-failure-log.json",
        {
            "last_run_at": f"{day}T04:01:00+00:00",
            "next_run_at": "2026-06-08T04:00:00+00:00",
            "schedule": "daily@04:00",
        },
    )
    write_text(
        workspace / "logs" / "runner.log",
        f"{day} runner-failure-log Scheduled run failed: Timed out before writing artifact\n",
    )

    write_json_file(
        workspace / "state" / "time-drift.json",
        {
            "last_run_at": "2026-06-06T05:01:00+00:00",
            "next_run_at": "2026-06-08T14:00:00+00:00",
            "schedule": "daily@05:00",
        },
    )

    write_text(workspace / "artifacts" / previous_day / "stale-artifact-only.txt", "old output\n")
    write_text(workspace / "state" / "invalid-state-json.json", "{not-json\n")

    write_text(workspace / "artifacts" / day / "partial-suite-report.txt", "partial report\n")
    write_json_file(
        workspace / "state" / "partial-suite-report.json",
        {
            "last_run_at": f"{day}T08:01:00+00:00",
            "next_run_at": "2026-06-08T08:00:00+00:00",
            "schedule": "daily@08:00",
        },
    )
    write_json_file(
        workspace / "state" / "partial-suite-index.json",
        {
            "last_run_at": f"{day}T08:01:00+00:00",
            "next_run_at": "2026-06-08T08:00:00+00:00",
            "schedule": "daily@08:00",
        },
    )


def expected_mismatches(rows: list[AuditRow]) -> list[str]:
    mismatches: list[str] = []
    seen = {row.id for row in rows}
    for job_id, case in CASES.items():
        if job_id not in seen:
            mismatches.append(f"missing row for {job_id}")

    for row in rows:
        case = CASES.get(row.id)
        if case is None:
            mismatches.append(f"unexpected row {row.id}: {row.verdict.value}")
        elif row.verdict != case.expected:
            mismatches.append(f"{row.id}: expected {case.expected.value}, got {row.verdict.value}")
    return mismatches


def write_json(path: Path, rows: list[AuditRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rows_to_json(rows) + "\n", encoding="utf-8")


def write_matrix(path: Path, rows: list[AuditRow], target_date: Date, now: datetime) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row_by_id = {row.id: row for row in rows}
    lines = [
        f"# Failure Injection Reliability Lab: {target_date.isoformat()}",
        "",
        f"Generated: {now.isoformat(timespec='seconds')}",
        "",
        "## Verdict Matrix",
        "",
        "| case | expected | observed | artifact | signal | operator action |",
        "|---|---|---|---|---|---|",
    ]
    for job_id, case in CASES.items():
        row = row_by_id.get(job_id)
        observed = row.verdict.value if row else "MISSING_ROW"
        artifact = row.artifact_status if row else "unknown"
        lines.append(
            f"| `{job_id}` | `{case.expected.value}` | `{observed}` | {artifact} | "
            f"{case.signal} | {case.operator_action} |"
        )

    lines.extend(
        [
            "",
            "## What This Lab Proves",
            "",
            "- Target-date artifacts beat scheduler timestamps.",
            "- Stale artifacts from another date do not satisfy today's contract.",
            "- Runner failures, state drift, invalid state, and partial success produce distinct operator actions.",
            "- `--fail-on any` can turn the same matrix into a CI gate.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_text(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def write_json_file(path: Path, body: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
