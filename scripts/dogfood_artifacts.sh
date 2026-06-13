#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd)
REPO_ROOT=${1:-$(CDPATH= cd "$SCRIPT_DIR/.." && pwd)}
WORKSPACE=${ARTIFACT_WATCHDOG_DOGFOOD_WORKSPACE:-"$REPO_ROOT/.artifact-watchdog/dogfood"}
TARGET_DATE=${ARTIFACT_WATCHDOG_DATE:-$(date -u +%F)}
REPORT_DIR="$WORKSPACE/reports/$TARGET_DATE"
STATE_DIR="$WORKSPACE/state"
LOG_DIR="$WORKSPACE/logs"
CONFIG="$REPO_ROOT/examples/dogfood/artifact-watchdog.toml"

if [ "${PYTHON:-}" ]; then
  PYTHON_BIN=$PYTHON
elif command -v python3.12 >/dev/null 2>&1; then
  PYTHON_BIN=python3.12
elif command -v python3.11 >/dev/null 2>&1; then
  PYTHON_BIN=python3.11
else
  PYTHON_BIN=python3
fi

mkdir -p "$REPORT_DIR" "$STATE_DIR" "$LOG_DIR"

now_utc() {
  date -u +"%Y-%m-%dT%H:%M:%S+00:00"
}

RUN_TIMESTAMP=${ARTIFACT_WATCHDOG_NOW:-$(now_utc)}

write_state() {
  job_id=$1
  state_file=$2
  cat > "$state_file" <<EOF
{
  "last_run_at": "$RUN_TIMESTAMP",
  "schedule": "daily",
  "job_id": "$job_id"
}
EOF
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

failed=0

run_job() {
  job_id=$1
  artifact_file=$2
  state_file=$3
  shift 3

  tmp_file="$artifact_file.tmp"
  log_file="$LOG_DIR/$job_id.log"
  rm -f "$tmp_file" "$artifact_file"

  if "$@" > "$tmp_file" 2>&1; then
    mv "$tmp_file" "$artifact_file"
    write_state "$job_id" "$state_file"
  else
    mv "$tmp_file" "$log_file"
    printf '\nDogfood check failed: %s\n' "$job_id" >> "$log_file"
    failed=1
  fi
}

run_job \
  "unit-tests" \
  "$REPORT_DIR/unit-tests.txt" \
  "$STATE_DIR/unit-tests.json" \
  env PYTHONPATH="$REPO_ROOT/src" "$PYTHON_BIN" -m unittest tests.test_cli tests.test_core tests.test_examples

run_job \
  "readme-quickstart-smoke" \
  "$REPORT_DIR/quickstart-smoke.txt" \
  "$STATE_DIR/readme-quickstart-smoke.json" \
  "$REPO_ROOT/scripts/quickstart_smoke.sh" "$REPO_ROOT"

run_job \
  "integration-template-smoke" \
  "$REPORT_DIR/template-pack-smoke.txt" \
  "$STATE_DIR/integration-template-smoke.json" \
  "$REPO_ROOT/scripts/template_pack_smoke.sh" "$REPO_ROOT"

if ! run_watchdog \
  --config "$CONFIG" \
  --workspace "$WORKSPACE" \
  --date "$TARGET_DATE" \
  --now "$RUN_TIMESTAMP" \
  --markdown "$REPORT_DIR/dogfood-watchdog.md" \
  --fail-on any \
  > "$REPORT_DIR/dogfood-watchdog.txt" 2>&1; then
  failed=1
fi

if [ "$failed" -eq 0 ]; then
  echo "dogfood artifacts ok"
else
  echo "dogfood artifacts failed" >&2
fi

exit "$failed"
