from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import date as Date
from datetime import datetime, time, timedelta, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .config import JobConfig, WatchdogConfig


class Verdict(StrEnum):
    OK = "OK"
    STATE_FILE_INVALID = "STATE_FILE_INVALID"
    TIME_DRIFT_CHECK = "TIME_DRIFT_CHECK"
    RUNNER_FAIL_LOG_FOUND = "RUNNER_FAIL_LOG_FOUND"
    RUN_ATTEMPTED_ARTIFACT_MISSING = "RUN_ATTEMPTED_ARTIFACT_MISSING"
    ARTIFACT_MISSING_OR_NOT_DUE = "ARTIFACT_MISSING_OR_NOT_DUE"
    ARTIFACT_MISSING_DUE_PASSED = "ARTIFACT_MISSING_DUE_PASSED"


@dataclass(frozen=True)
class AuditRow:
    id: str
    status: str
    schedule: str
    state_schedule: str
    last_run_at: str
    next_run_at: str
    due_at: str
    state_error: str
    artifact_status: str
    artifacts_found: tuple[str, ...]
    latest_failure: str
    time_drift: str
    verdict: Verdict

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["verdict"] = self.verdict.value
        return data


@dataclass(frozen=True)
class JobState:
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    schedule: str = ""
    error: str = ""


def audit_workspace(
    config: WatchdogConfig,
    workspace: Path,
    target_date: Date,
    now: datetime | None = None,
) -> list[AuditRow]:
    workspace = workspace.resolve()
    rows: list[AuditRow] = []
    for job in config.jobs:
        tz = _zone(job.timezone or config.timezone)
        local_now = _coerce_now(now, tz)
        state = _load_state(workspace, job, tz)
        artifacts = _artifact_matches(workspace, job, target_date)
        failure = _latest_failure(workspace, job, local_now, config)
        due_at = _due_at(job.schedule, target_date, tz, _grace_minutes(job, config))
        drift = _time_drift(job.schedule, state.next_run_at, tz)
        verdict = _verdict(artifacts, failure, state, target_date, due_at, local_now, drift)
        rows.append(
            AuditRow(
                id=job.id,
                status=job.status,
                schedule=job.schedule,
                state_schedule=state.schedule,
                last_run_at=_format_dt(state.last_run_at),
                next_run_at=_format_dt(state.next_run_at),
                due_at=_format_dt(due_at),
                state_error=state.error,
                artifact_status="FOUND" if artifacts else "MISSING",
                artifacts_found=tuple(artifacts),
                latest_failure=failure,
                time_drift=drift,
                verdict=verdict,
            )
        )
    return rows


def _verdict(
    artifacts: list[str],
    failure: str,
    state: JobState,
    target_date: Date,
    due_at: datetime | None,
    now: datetime,
    drift: str,
) -> Verdict:
    if state.error:
        return Verdict.STATE_FILE_INVALID
    if drift != "none":
        return Verdict.TIME_DRIFT_CHECK
    if artifacts:
        return Verdict.OK
    if failure:
        return Verdict.RUNNER_FAIL_LOG_FOUND
    if state.last_run_at and state.last_run_at.date() == target_date:
        return Verdict.RUN_ATTEMPTED_ARTIFACT_MISSING
    if due_at and now < due_at:
        return Verdict.ARTIFACT_MISSING_OR_NOT_DUE
    return Verdict.ARTIFACT_MISSING_DUE_PASSED


def _artifact_matches(workspace: Path, job: JobConfig, target_date: Date) -> list[str]:
    found: list[str] = []
    context = _pattern_context(job, target_date)
    for pattern in job.artifacts:
        for match in sorted(_glob(workspace, pattern, context)):
            if match.exists():
                found.append(_display_path(workspace, match))
    return found


def _latest_failure(
    workspace: Path,
    job: JobConfig,
    now: datetime,
    config: WatchdogConfig,
) -> str:
    if not job.log_paths or not job.failure_patterns:
        return ""

    cutoff = now.timestamp() - _lookback_hours(job, config) * 3600
    context = _pattern_context(job, now.date())
    latest = ""
    for pattern in job.log_paths:
        for path in sorted(_glob(workspace, pattern, context)):
            try:
                if path.stat().st_mtime < cutoff:
                    continue
                for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                    if job.id in line and any(item in line for item in job.failure_patterns):
                        latest = f"{_display_path(workspace, path)}: {line.strip()}"
            except OSError:
                continue
    return latest


def _load_state(workspace: Path, job: JobConfig, tz: ZoneInfo | timezone) -> JobState:
    if not job.state_file:
        return JobState()

    path = _resolve_workspace_path(workspace, job.state_file)
    if not path.exists():
        return JobState()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return JobState(error=f"{_display_path(workspace, path)}: {exc.__class__.__name__}: {exc}")
    if not isinstance(data, dict):
        return JobState(error=f"{_display_path(workspace, path)}: expected JSON object")

    return JobState(
        last_run_at=_parse_datetime(data.get("last_run_at"), tz),
        next_run_at=_parse_datetime(data.get("next_run_at"), tz),
        schedule=str(data.get("schedule") or data.get("rrule") or ""),
    )


def _due_at(
    schedule: str,
    target_date: Date,
    tz: ZoneInfo | timezone,
    grace_minutes: int,
) -> datetime | None:
    scheduled = _schedule_time(schedule)
    if scheduled is None:
        return None
    return datetime.combine(target_date, scheduled, tzinfo=tz) + timedelta(minutes=grace_minutes)


def _time_drift(schedule: str, next_run_at: datetime | None, tz: ZoneInfo | timezone) -> str:
    scheduled = _schedule_time(schedule)
    if scheduled is None or next_run_at is None:
        return "none"

    observed = next_run_at.astimezone(tz).time().replace(second=0, microsecond=0)
    if observed == scheduled:
        return "none"
    return f"expected={scheduled.strftime('%H:%M')}, next_run_at={observed.strftime('%H:%M')}"


def _schedule_time(schedule: str) -> time | None:
    daily = re.fullmatch(r"daily@(\d{1,2}):(\d{2})", schedule.strip())
    if daily:
        return _valid_time(int(daily.group(1)), int(daily.group(2)))

    hour = _rrule_int(schedule, "BYHOUR")
    minute = _rrule_int(schedule, "BYMINUTE")
    if hour is not None:
        return _valid_time(hour, minute or 0)
    return None


def _rrule_int(schedule: str, key: str) -> int | None:
    match = re.search(rf"(?:^|;){key}=(\d+)(?:;|$)", schedule)
    if not match:
        return None
    return int(match.group(1))


def _valid_time(hour: int, minute: int) -> time:
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError(f"invalid schedule time {hour:02d}:{minute:02d}")
    return time(hour=hour, minute=minute)


def _parse_datetime(value: Any, tz: ZoneInfo | timezone) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, int | float):
        dt = datetime.fromtimestamp(value / 1000 if value > 10_000_000_000 else value, timezone.utc)
        return dt.astimezone(tz)
    if not isinstance(value, str):
        return None

    normalized = value.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz)
    return dt.astimezone(tz)


def _coerce_now(now: datetime | None, tz: ZoneInfo | timezone) -> datetime:
    if now is None:
        return datetime.now(tz)
    if now.tzinfo is None:
        return now.replace(tzinfo=tz)
    return now.astimezone(tz)


def _zone(name: str) -> ZoneInfo | timezone:
    if name.upper() == "UTC":
        return timezone.utc
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"unknown timezone: {name}") from exc


def _pattern_context(job: JobConfig, target_date: Date) -> dict[str, str]:
    return {
        "date": target_date.isoformat(),
        "date_compact": target_date.strftime("%Y%m%d"),
        "job_id": job.id,
    }


def _glob(workspace: Path, pattern: str, context: dict[str, str]) -> list[Path]:
    rendered = pattern.format(**context)
    path = _resolve_workspace_path(workspace, rendered)
    if path.is_absolute():
        return list(path.parent.glob(path.name))
    return list(workspace.glob(rendered))


def _resolve_workspace_path(workspace: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return workspace / path


def _display_path(workspace: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(workspace))
    except ValueError:
        return str(path)


def _grace_minutes(job: JobConfig, config: WatchdogConfig) -> int:
    return config.grace_minutes if job.grace_minutes is None else job.grace_minutes


def _lookback_hours(job: JobConfig, config: WatchdogConfig) -> int:
    return config.log_lookback_hours if job.log_lookback_hours is None else job.log_lookback_hours


def _format_dt(value: datetime | None) -> str:
    if not value:
        return ""
    return value.isoformat(timespec="seconds")
