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

find "$REPO_ROOT/examples/integrations" -name "*.sh" -type f | while IFS= read -r script; do
  sh -n "$script"
done

PYTHONPATH="$REPO_ROOT/src" "$PYTHON_BIN" -m unittest tests.test_examples

echo "template pack smoke ok"
