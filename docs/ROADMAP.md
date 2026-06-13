# Roadmap

`artifact-watchdog` should stay small, local-first, and easy to inspect.

## Near Term

- Add stricter config validation with clearer error messages.
- Add Markdown report fixtures to make output changes easier to review.
- Add GitHub step summary polish for workflows that want both human-readable reports and machine-readable JSON.
- Keep integration templates covered by smoke tests as the CLI surface changes.
- Keep dogfood artifacts aligned with README quickstart, template smoke, and unit test coverage.
- Keep the failure injection lab aligned with every public verdict so detection regressions are caught in CI.

## Possible Later Work

- Support weekly schedules.
- Add a small plugin point for custom state readers.
- Add SARIF or GitHub step summary output.
- Publish to PyPI after the CLI surface settles.

## Non-Goals

- Hosted monitoring.
- Alert delivery.
- Metrics dashboards.
- Reading secrets or remote service credentials.
- Replacing CI, cron, Prometheus, Datadog, or similar systems.
