from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from artifact_watchdog.config import load_config
from artifact_watchdog.core import Verdict, audit_workspace


def write_config(workspace: Path, body: str) -> Path:
    path = workspace / "watchdog.toml"
    path.write_text(body, encoding="utf-8")
    return path


def config_body(schedule: str = "FREQ=DAILY;BYHOUR=3;BYMINUTE=0") -> str:
    return f"""
[watchdog]
timezone = "UTC"
grace_minutes = 15
log_lookback_hours = 24

[[jobs]]
id = "nightly-import"
schedule = "{schedule}"
artifacts = ["artifacts/{{date}}/summary.json"]
state_file = "state/nightly-import.json"
log_paths = ["logs/*.log"]
failure_patterns = ["Scheduled run failed", "Timed out"]
"""


class CoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def audit(self, now: str = "2026-06-07T04:00:00+00:00"):
        config = load_config(write_config(self.workspace, config_body()))
        return audit_workspace(
            config,
            self.workspace,
            date(2026, 6, 7),
            datetime.fromisoformat(now),
        )[0]

    def test_ok_when_expected_artifact_exists(self) -> None:
        artifact = self.workspace / "artifacts" / "2026-06-07" / "summary.json"
        artifact.parent.mkdir(parents=True)
        artifact.write_text("{}", encoding="utf-8")

        row = self.audit()

        self.assertEqual(row.verdict, Verdict.OK)
        self.assertEqual(row.artifacts_found, ("artifacts/2026-06-07/summary.json",))

    def test_attempted_run_without_artifact_is_reported(self) -> None:
        state = self.workspace / "state" / "nightly-import.json"
        state.parent.mkdir(parents=True)
        state.write_text(
            json.dumps({"last_run_at": "2026-06-07T03:01:00+00:00"}),
            encoding="utf-8",
        )

        row = self.audit()

        self.assertEqual(row.verdict, Verdict.RUN_ATTEMPTED_ARTIFACT_MISSING)

    def test_failure_log_takes_precedence_over_attempted_without_artifact(self) -> None:
        state = self.workspace / "state" / "nightly-import.json"
        state.parent.mkdir(parents=True)
        state.write_text(
            json.dumps({"last_run_at": "2026-06-07T03:01:00+00:00"}),
            encoding="utf-8",
        )
        log = self.workspace / "logs" / "runner.log"
        log.parent.mkdir(parents=True)
        log.write_text(
            "2026-06-07 nightly-import Scheduled run failed: Timed out\n",
            encoding="utf-8",
        )

        row = self.audit()

        self.assertEqual(row.verdict, Verdict.RUNNER_FAIL_LOG_FOUND)
        self.assertIn("Scheduled run failed", row.latest_failure)

    def test_missing_artifact_before_due_time_is_not_due(self) -> None:
        row = self.audit(now="2026-06-07T02:00:00+00:00")

        self.assertEqual(row.verdict, Verdict.ARTIFACT_MISSING_OR_NOT_DUE)

    def test_next_run_time_drift_is_flagged(self) -> None:
        state = self.workspace / "state" / "nightly-import.json"
        state.parent.mkdir(parents=True)
        state.write_text(
            json.dumps({"next_run_at": "2026-06-08T12:00:00+00:00"}),
            encoding="utf-8",
        )

        row = self.audit()

        self.assertEqual(row.verdict, Verdict.TIME_DRIFT_CHECK)
        self.assertEqual(row.time_drift, "expected=03:00, next_run_at=12:00")

    def test_invalid_state_file_is_reported_as_verdict(self) -> None:
        state = self.workspace / "state" / "nightly-import.json"
        state.parent.mkdir(parents=True)
        state.write_text("{not-json", encoding="utf-8")

        row = self.audit()

        self.assertEqual(row.verdict, Verdict.STATE_FILE_INVALID)
        self.assertIn("nightly-import.json", row.state_error)
        self.assertIn("JSONDecodeError", row.state_error)

    def test_daily_at_schedule_format(self) -> None:
        config = load_config(write_config(self.workspace, config_body("daily@04:30")))
        rows = audit_workspace(
            config,
            self.workspace,
            date(2026, 6, 7),
            datetime(2026, 6, 7, 4, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(rows[0].verdict, Verdict.ARTIFACT_MISSING_OR_NOT_DUE)


if __name__ == "__main__":
    unittest.main()
