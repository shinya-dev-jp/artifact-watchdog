from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when a watchdog config is invalid."""


@dataclass(frozen=True)
class WatchdogConfig:
    timezone: str
    grace_minutes: int
    log_lookback_hours: int
    jobs: tuple["JobConfig", ...]


@dataclass(frozen=True)
class JobConfig:
    id: str
    schedule: str
    artifacts: tuple[str, ...]
    status: str = "active"
    state_file: str | None = None
    log_paths: tuple[str, ...] = ()
    failure_patterns: tuple[str, ...] = ()
    timezone: str | None = None
    grace_minutes: int | None = None
    log_lookback_hours: int | None = None


def load_config(path: Path) -> WatchdogConfig:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    watchdog = raw.get("watchdog", {})
    if not isinstance(watchdog, dict):
        raise ConfigError("[watchdog] must be a table")

    jobs = raw.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        raise ConfigError("config must define at least one [[jobs]] table")

    defaults = {
        "timezone": _string(watchdog, "timezone", default="UTC"),
        "grace_minutes": _int(watchdog, "grace_minutes", default=0),
        "log_lookback_hours": _int(watchdog, "log_lookback_hours", default=24),
    }

    return WatchdogConfig(
        timezone=defaults["timezone"],
        grace_minutes=defaults["grace_minutes"],
        log_lookback_hours=defaults["log_lookback_hours"],
        jobs=tuple(_load_job(job, defaults) for job in jobs),
    )


def _load_job(raw: Any, defaults: dict[str, Any]) -> JobConfig:
    if not isinstance(raw, dict):
        raise ConfigError("each [[jobs]] entry must be a table")

    job_id = _required_string(raw, "id")
    schedule = _required_string(raw, "schedule")
    artifacts = _required_string_list(raw, "artifacts")
    status = _string(raw, "status", default="active")

    return JobConfig(
        id=job_id,
        schedule=schedule,
        artifacts=artifacts,
        status=status,
        state_file=_optional_string(raw, "state_file"),
        log_paths=_string_list(raw, "log_paths"),
        failure_patterns=_string_list(raw, "failure_patterns"),
        timezone=_optional_string(raw, "timezone") or defaults["timezone"],
        grace_minutes=_optional_int(raw, "grace_minutes"),
        log_lookback_hours=_optional_int(raw, "log_lookback_hours"),
    )


def _required_string(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{key!r} must be a non-empty string")
    return value


def _required_string_list(raw: dict[str, Any], key: str) -> tuple[str, ...]:
    values = _string_list(raw, key)
    if not values:
        raise ConfigError(f"{key!r} must contain at least one string")
    return values


def _string(raw: dict[str, Any], key: str, *, default: str) -> str:
    value = raw.get(key, default)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{key!r} must be a string")
    return value


def _optional_string(raw: dict[str, Any], key: str) -> str | None:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{key!r} must be a string")
    return value


def _string_list(raw: dict[str, Any], key: str) -> tuple[str, ...]:
    value = raw.get(key, [])
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ConfigError(f"{key!r} must be a list of strings")
    return tuple(value)


def _int(raw: dict[str, Any], key: str, *, default: int) -> int:
    value = raw.get(key, default)
    if not isinstance(value, int) or value < 0:
        raise ConfigError(f"{key!r} must be a non-negative integer")
    return value


def _optional_int(raw: dict[str, Any], key: str) -> int | None:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, int) or value < 0:
        raise ConfigError(f"{key!r} must be a non-negative integer")
    return value

