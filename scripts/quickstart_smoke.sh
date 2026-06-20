#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd)
REPO_ROOT=${1:-$(CDPATH= cd "$SCRIPT_DIR/.." && pwd)}
FIXTURE="$REPO_ROOT/examples/demo-workspace"

if [ "${PYTHON:-}" ]; then
  PYTHON_BIN=$PYTHON
elif command -v python3.12 >/dev/null 2>&1; then
  PYTHON_BIN=python3.12
elif command -v python3.11 >/dev/null 2>&1; then
  PYTHON_BIN=python3.11
else
  PYTHON_BIN=python3
fi

check_python_version() {
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
}

run_watchdog() {
  if [ "${ARTIFACT_WATCHDOG_BIN:-}" ]; then
    "$ARTIFACT_WATCHDOG_BIN" "$@"
  elif command -v artifact-watchdog >/dev/null 2>&1; then
    artifact-watchdog "$@"
  else
    PYTHONPATH="$REPO_ROOT/src" "$PYTHON_BIN" -m artifact_watchdog.cli "$@"
  fi
}

if [ ! -d "$FIXTURE" ]; then
  echo "missing demo fixture: $FIXTURE" >&2
  exit 1
fi

check_python_version

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT INT TERM

cp -R "$FIXTURE" "$tmpdir/demo-workspace"
cd "$tmpdir"

run_watchdog \
  --config demo-workspace/watchdog.toml \
  --workspace demo-workspace \
  --date 2026-06-07 \
  --now 2026-06-07T06:00:00+00:00 \
  > output.txt

grep 'docs-build[[:space:]]OK[[:space:]]artifact=FOUND' output.txt
grep 'nightly-import[[:space:]]RUN_ATTEMPTED_ARTIFACT_MISSING[[:space:]]artifact=MISSING' output.txt
grep 'release-notes[[:space:]]RUNNER_FAIL_LOG_FOUND[[:space:]]artifact=MISSING' output.txt
grep 'metrics-rollup[[:space:]]TIME_DRIFT_CHECK[[:space:]]artifact=MISSING' output.txt

if run_watchdog \
  --config demo-workspace/watchdog.toml \
  --workspace demo-workspace \
  --date 2026-06-07 \
  --now 2026-06-07T06:00:00+00:00 \
  --fail-on any > fail-on-output.txt 2>&1; then
  echo "expected --fail-on any to exit non-zero for the unhealthy demo fixture" >&2
  exit 1
fi

echo "quickstart smoke ok"
