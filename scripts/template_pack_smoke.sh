#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd)
REPO_ROOT=${1:-$(CDPATH= cd "$SCRIPT_DIR/.." && pwd)}

if [ "${PYTHON:-}" ]; then
  PYTHON_BIN=$PYTHON
elif command -v python3.12 >/dev/null 2>&1; then
  PYTHON_BIN=python3.12
elif command -v python3.11 >/dev/null 2>&1; then
  PYTHON_BIN=python3.11
else
  PYTHON_BIN=python3
fi

"$PYTHON_BIN" - <<'PY'
import sys

if sys.version_info < (3, 11):
    version = ".".join(str(part) for part in sys.version_info[:3])
    print(
        "artifact-watchdog requires Python 3.11 or newer. "
        f"Selected interpreter is Python {version}. "
        "Install Python 3.11+ or rerun with PYTHON=python3.11.",
        file=sys.stderr,
    )
    raise SystemExit(2)
PY

find "$REPO_ROOT/examples/integrations" -name "*.sh" -type f | while IFS= read -r script; do
  sh -n "$script"
done

PYTHONPATH="$REPO_ROOT/src" "$PYTHON_BIN" -m unittest tests.test_examples

echo "template pack smoke ok"
