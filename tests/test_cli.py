from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from artifact_watchdog.cli import main


class CliTests(unittest.TestCase):
    def test_cli_outputs_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace = Path(tempdir)
            config = workspace / "watchdog.toml"
            config.write_text(
                """
[watchdog]
timezone = "UTC"

[[jobs]]
id = "nightly-import"
schedule = "daily@03:00"
artifacts = ["artifacts/{date}/summary.json"]
""",
                encoding="utf-8",
            )
            report = workspace / "report.md"

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "--config",
                        str(config),
                        "--workspace",
                        str(workspace),
                        "--date",
                        "2026-06-07",
                        "--now",
                        "2026-06-07T04:00:00+00:00",
                        "--json",
                        "--markdown",
                        str(report),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn('"id": "nightly-import"', stdout.getvalue())
            self.assertIn("ARTIFACT_MISSING_DUE_PASSED", stdout.getvalue())
            self.assertTrue(report.exists())
            self.assertIn("Artifact Watchdog Report", report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

