from __future__ import annotations

import subprocess
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

from artifact_watchdog.config import load_config
from artifact_watchdog.core import audit_workspace


REPO_ROOT = Path(__file__).resolve().parents[1]
INTEGRATIONS = REPO_ROOT / "examples" / "integrations"


class IntegrationExampleTests(unittest.TestCase):
    def test_integration_configs_load(self) -> None:
        config_paths = sorted(INTEGRATIONS.glob("*/artifact-watchdog.toml"))

        self.assertGreaterEqual(len(config_paths), 5)
        for path in config_paths:
            with self.subTest(path=path):
                config = load_config(path)
                self.assertGreater(len(config.jobs), 0)
                for job in config.jobs:
                    self.assertTrue(job.id)
                    self.assertGreater(len(job.artifacts), 0)

    def test_integration_configs_can_be_audited(self) -> None:
        config_paths = sorted(INTEGRATIONS.glob("*/artifact-watchdog.toml"))

        with tempfile.TemporaryDirectory() as tempdir:
            workspace = Path(tempdir)
            now = datetime.fromisoformat("2026-06-07T18:00:00+00:00")
            for path in config_paths:
                with self.subTest(path=path):
                    config = load_config(path)
                    rows = audit_workspace(config, workspace, date(2026, 6, 7), now)
                    self.assertEqual(len(rows), len(config.jobs))
                    self.assertTrue(all(row.id for row in rows))

    def test_shell_templates_are_syntax_valid(self) -> None:
        shell_paths = sorted(INTEGRATIONS.glob("*/*.sh")) + [REPO_ROOT / "scripts" / "template_pack_smoke.sh"]

        self.assertGreaterEqual(len(shell_paths), 3)
        for path in shell_paths:
            with self.subTest(path=path):
                subprocess.run(["sh", "-n", str(path)], check=True)

    def test_github_actions_template_has_ci_gate(self) -> None:
        workflow = (INTEGRATIONS / "github-actions" / "artifact-watchdog.yml").read_text(encoding="utf-8")

        self.assertIn("schedule:", workflow)
        self.assertIn("artifact-watchdog", workflow)
        self.assertIn("--markdown \"$GITHUB_STEP_SUMMARY\"", workflow)
        self.assertIn("--fail-on any", workflow)

    def test_systemd_template_has_timer_and_service(self) -> None:
        service = (INTEGRATIONS / "systemd" / "artifact-watchdog.service").read_text(encoding="utf-8")
        timer = (INTEGRATIONS / "systemd" / "artifact-watchdog.timer").read_text(encoding="utf-8")

        self.assertIn("[Service]", service)
        self.assertIn("Type=oneshot", service)
        self.assertIn("ExecStart=", service)
        self.assertIn("[Timer]", timer)
        self.assertIn("OnCalendar=", timer)


if __name__ == "__main__":
    unittest.main()
