# Roadmap

`artifact-watchdog` should stay small, local-first, and easy to inspect.

## Near Term

- Add stricter config validation with clearer error messages.
- Add Markdown report fixtures to make output changes easier to review.
- Add GitHub step summary polish for workflows that want both human-readable reports and machine-readable JSON.

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
