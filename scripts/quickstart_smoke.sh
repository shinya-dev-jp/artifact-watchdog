#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd)
REPO_ROOT=${1:-$(CDPATH= cd "$SCRIPT_DIR/.." && pwd)}
WATCHDOG_BIN=${ARTIFACT_WATCHDOG_BIN:-artifact-watchdog}
FIXTURE="$REPO_ROOT/examples/demo-workspace"

if [ ! -d "$FIXTURE" ]; then
  echo "missing demo fixture: $FIXTURE" >&2
  exit 1
fi

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT INT TERM

cp -R "$FIXTURE" "$tmpdir/demo-workspace"
cd "$tmpdir"

"$WATCHDOG_BIN" \
  --config demo-workspace/watchdog.toml \
  --workspace demo-workspace \
  --date 2026-06-07 \
  --now 2026-06-07T06:00:00+00:00 \
  > output.txt

grep 'docs-build[[:space:]]OK[[:space:]]artifact=FOUND' output.txt
grep 'nightly-import[[:space:]]RUN_ATTEMPTED_ARTIFACT_MISSING[[:space:]]artifact=MISSING' output.txt
grep 'release-notes[[:space:]]RUNNER_FAIL_LOG_FOUND[[:space:]]artifact=MISSING' output.txt
grep 'metrics-rollup[[:space:]]TIME_DRIFT_CHECK[[:space:]]artifact=MISSING' output.txt

if "$WATCHDOG_BIN" \
  --config demo-workspace/watchdog.toml \
  --workspace demo-workspace \
  --date 2026-06-07 \
  --now 2026-06-07T06:00:00+00:00 \
  --fail-on any > fail-on-output.txt 2>&1; then
  echo "expected --fail-on any to exit non-zero for the unhealthy demo fixture" >&2
  exit 1
fi

echo "quickstart smoke ok"
