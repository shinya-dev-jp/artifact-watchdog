#!/usr/bin/env sh
set -eu

WORKSPACE=${ARTIFACT_WATCHDOG_WORKSPACE:-$PWD}
TARGET_DATE=${ARTIFACT_WATCHDOG_DATE:-$(date -u +%F)}

artifact-watchdog \
  --config "$WORKSPACE/artifact-watchdog.toml" \
  --workspace "$WORKSPACE" \
  --date "$TARGET_DATE" \
  --markdown "$WORKSPACE/reports/artifact-watchdog-agent-$TARGET_DATE.md" \
  --fail-on RUNNER_FAIL_LOG_FOUND,RUN_ATTEMPTED_ARTIFACT_MISSING,ARTIFACT_MISSING_DUE_PASSED
