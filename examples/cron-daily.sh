#!/usr/bin/env sh
set -eu

cd "${ARTIFACT_WATCHDOG_WORKSPACE:-$PWD}"

artifact-watchdog \
  --config "${ARTIFACT_WATCHDOG_CONFIG:-artifact-watchdog.toml}" \
  --workspace . \
  --date "$(date -u +%F)" \
  --markdown "reports/artifact-watchdog-$(date -u +%F).md" \
  --fail-on any
