from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

from artifact_watchdog._compat import unsupported_python_message


ROOT = Path(__file__).resolve().parents[1]


class PythonRequirementDocsTests(unittest.TestCase):
    def test_project_declares_python_311_or_newer(self) -> None:
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

        self.assertEqual(pyproject["project"]["requires-python"], ">=3.11")

    def test_public_quickstart_mentions_python_311(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("Python 3.11", readme)
        self.assertIn("python3.11", readme)
        self.assertIn("PYTHON=python3.11 scripts/quickstart_smoke.sh", readme)

    def test_smoke_scripts_fail_fast_before_python_311(self) -> None:
        for path in (
            ROOT / "scripts" / "quickstart_smoke.sh",
            ROOT / "scripts" / "template_pack_smoke.sh",
        ):
            with self.subTest(path=path.name):
                script = path.read_text(encoding="utf-8")
                self.assertIn("sys.version_info < (3, 11)", script)
                self.assertIn("requires Python 3.11 or newer", script)

    def test_runtime_guard_message_matches_docs(self) -> None:
        message = unsupported_python_message((3, 9, 6))

        self.assertIsNotNone(message)
        self.assertIn("Python 3.9.6", message)
        self.assertIn("PYTHON=python3.11", message)

    def test_runtime_guard_allows_supported_python(self) -> None:
        self.assertIsNone(unsupported_python_message((3, 11, 0)))


if __name__ == "__main__":
    raise SystemExit(unittest.main())
