from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from artifact_watchdog.config import load_config
from artifact_watchdog.core import Verdict


REPO_ROOT = Path(__file__).resolve().parents[1]
FAILURE_LAB_CONFIG = REPO_ROOT / "examples" / "failure-lab" / "artifact-watchdog.toml"
FAILURE_LAB_SCRIPT = REPO_ROOT / "scripts" / "failure_lab.py"


EXPECTED_VERDICTS = {
    "healthy-report": Verdict.OK.value,
    "attempted-no-artifact": Verdict.RUN_ATTEMPTED_ARTIFACT_MISSING.value,
    "runner-failure-log": Verdict.RUNNER_FAIL_LOG_FOUND.value,
    "time-drift": Verdict.TIME_DRIFT_CHECK.value,
    "not-due-yet": Verdict.ARTIFACT_MISSING_OR_NOT_DUE.value,
    "due-passed-missing": Verdict.ARTIFACT_MISSING_DUE_PASSED.value,
    "stale-artifact-only": Verdict.ARTIFACT_MISSING_DUE_PASSED.value,
    "invalid-state-json": Verdict.STATE_FILE_INVALID.value,
    "partial-suite-report": Verdict.OK.value,
    "partial-suite-index": Verdict.RUN_ATTEMPTED_ARTIFACT_MISSING.value,
}


class FailureLabTests(unittest.TestCase):
    def test_failure_lab_config_loads(self) -> None:
        config = load_config(FAILURE_LAB_CONFIG)

        self.assertEqual([job.id for job in config.jobs], list(EXPECTED_VERDICTS))

    def test_failure_lab_script_produces_expected_verdict_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace = Path(tempdir) / "lab"

            result = subprocess.run(
                [sys.executable, str(FAILURE_LAB_SCRIPT), "--workspace", str(workspace)],
                env=script_env(),
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("failure lab ok", result.stdout)

            rows = json.loads((workspace / "reports" / "failure-lab.json").read_text(encoding="utf-8"))
            verdicts = {row["id"]: row["verdict"] for row in rows}
            self.assertEqual(verdicts, EXPECTED_VERDICTS)

            invalid_state = next(row for row in rows if row["id"] == "invalid-state-json")
            self.assertIn("JSONDecodeError", invalid_state["state_error"])

            matrix = (workspace / "reports" / "failure-lab-matrix.md").read_text(encoding="utf-8")
            self.assertIn("stale output", matrix)
            self.assertIn("partial success", matrix)
            self.assertIn("STATE_FILE_INVALID", matrix)

            markdown = (workspace / "reports" / "failure-lab.md").read_text(encoding="utf-8")
            self.assertIn("State File Errors", markdown)
            self.assertIn("invalid-state-json", markdown)

    def test_failure_lab_refuses_to_reset_unknown_non_empty_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace = Path(tempdir) / "not-a-lab"
            workspace.mkdir()
            (workspace / "keep.txt").write_text("do not remove\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(FAILURE_LAB_SCRIPT), "--workspace", str(workspace)],
                env=script_env(),
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("refusing to reset non-lab workspace", result.stderr)
            self.assertTrue((workspace / "keep.txt").exists())


def script_env() -> dict[str, str]:
    env = os.environ.copy()
    src = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = src if not env.get("PYTHONPATH") else src + os.pathsep + env["PYTHONPATH"]
    return env


if __name__ == "__main__":
    unittest.main()
