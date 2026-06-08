# Roadmap

`artifact-watchdog` should stay small, local-first, and easy to inspect.

## Near Term

- Add a compact example for GitHub Actions artifact checks.
- Add stricter config validation with clearer error messages.
- Add a `--fail-on` option for CI use, such as failing when any job is not `OK`.
- Add Markdown report fixtures to make output changes easier to review.

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

