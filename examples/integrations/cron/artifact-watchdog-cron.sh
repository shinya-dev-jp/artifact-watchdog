#!/usr/bin/env sh
set -eu

WORKSPACE=${ARTIFACT_WATCHDOG_WORKSPACE:-$PWD}
CONFIG=${ARTIFACT_WATCHDOG_CONFIG:-artifact-watchdog.toml}
TARGET_DATE=${ARTIFACT_WATCHDOG_DATE:-$(date -u +%F)}

cd "$WORKSPACE"

artifact-watchdog \
  --config "$CONFIG" \
  --workspace . \
  --date "$TARGET_DATE" \
  --markdown "reports/artifact-watchdog-$TARGET_DATE.md" \
  --fail-on any
