# Demo Workspace

This fixture shows four common scheduled-job states:

| Job | Expected result |
|---|---|
| `docs-build` | `OK`, because the expected HTML artifact exists. |
| `nightly-import` | `RUN_ATTEMPTED_ARTIFACT_MISSING`, because state says it ran today but no artifact exists. |
| `release-notes` | `RUNNER_FAIL_LOG_FOUND`, because a matching failure log exists. |
| `metrics-rollup` | `TIME_DRIFT_CHECK`, because `next_run_at` points to a different time than the schedule. |

Run from the repository root:

```bash
PYTHONPATH=src python -m artifact_watchdog.cli \
  --config examples/demo-workspace/watchdog.toml \
  --workspace examples/demo-workspace \
  --date 2026-06-07 \
  --now 2026-06-07T06:00:00+00:00
```

To test CI-style failure behavior, add `--fail-on any`. This fixture should exit non-zero because three of the four jobs are intentionally unhealthy.
