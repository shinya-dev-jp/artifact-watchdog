from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

from artifact_watchdog.config import load_config
from artifact_watchdog.core import Verdict, audit_workspace


REPO_ROOT = Path(__file__).resolve().parents[1]
DOGFOOD_CONFIG = REPO_ROOT / "examples" / "dogfood" / "artifact-watchdog.toml"
DOGFOOD_SCRIPT = REPO_ROOT / "scripts" / "dogfood_artifacts.sh"
DOGFOOD_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "dogfood.yml"


class DogfoodTests(unittest.TestCase):
    def test_dogfood_config_loads(self) -> None:
        config = load_config(DOGFOOD_CONFIG)

        self.assertEqual(
            [job.id for job in config.jobs],
            ["unit-tests", "readme-quickstart-smoke", "integration-template-smoke"],
        )
        self.assertTrue(all(job.state_file for job in config.jobs))
        self.assertTrue(all(job.log_paths for job in config.jobs))

    def test_dogfood_script_is_syntax_valid(self) -> None:
        subprocess.run(["sh", "-n", str(DOGFOOD_SCRIPT)], check=True)

    def test_dogfood_script_produces_auditable_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            env = os.environ.copy()
            env["ARTIFACT_WATCHDOG_DOGFOOD_WORKSPACE"] = tempdir
            env["ARTIFACT_WATCHDOG_DATE"] = "2026-06-07"
            env["ARTIFACT_WATCHDOG_NOW"] = "2026-06-07T08:00:00+00:00"
            env["PYTHON"] = sys.executable

            subprocess.run([str(DOGFOOD_SCRIPT), str(REPO_ROOT)], env=env, check=True)

            workspace = Path(tempdir)
            report_dir = workspace / "reports" / "2026-06-07"
            self.assertTrue((report_dir / "unit-tests.txt").exists())
            self.assertTrue((report_dir / "quickstart-smoke.txt").exists())
            self.assertTrue((report_dir / "template-pack-smoke.txt").exists())
            self.assertTrue((report_dir / "dogfood-watchdog.md").exists())

            config = load_config(DOGFOOD_CONFIG)
            rows = audit_workspace(
                config,
                workspace,
                date(2026, 6, 7),
                datetime.fromisoformat("2026-06-07T08:00:00+00:00"),
            )
            self.assertTrue(all(row.verdict is Verdict.OK for row in rows))

    def test_dogfood_workflow_runs_the_script(self) -> None:
        workflow = DOGFOOD_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("schedule:", workflow)
        self.assertIn("python -m pip install .", workflow)
        self.assertIn("scripts/dogfood_artifacts.sh", workflow)


if __name__ == "__main__":
    unittest.main()
