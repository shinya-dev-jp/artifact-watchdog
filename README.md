# artifact-watchdog

[![CI](https://github.com/shinya-dev-jp/artifact-watchdog/actions/workflows/ci.yml/badge.svg)](https://github.com/shinya-dev-jp/artifact-watchdog/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)

`artifact-watchdog` is a small Python CLI for auditing scheduled jobs by checking the files they were supposed to produce.

It is built around a simple rule: a scheduler timestamp is not proof of success. A job is healthy only when its expected artifacts exist.

## At a Glance

- **Use it for:** cron jobs, GitHub Actions schedules, local agents, release scripts, exports, and report generators that promise to write files.
- **It checks:** TOML job rules, local artifact paths, optional runner state JSON, and optional failure logs.
- **It outputs:** terminal verdicts, JSON, Markdown reports, and CI-friendly exit codes.
- **It proves:** deterministic failure-injection fixtures for stale artifacts, failed runners, drifted schedules, invalid state, and partial success.
- **It does not need:** credentials, a hosted service, network access, or a monitoring account.

## The Problem

Many automations have two different truths:

- the runner says the job was due or attempted;
- the workspace either contains the expected output or it does not.

Those truths can disagree. A cron job, CI workflow, local agent, or release script can advance its state while failing before it writes the JSON, HTML, changelog, package, or report that people actually depend on.

`artifact-watchdog` makes that disagreement explicit.

## Use Cases

Use it when a scheduled job has a durable output contract:

| Scene | Expected artifact | Why a timestamp is not enough |
|---|---|---|
| Documentation build | `site/YYYY-MM-DD/index.html` | The workflow can start and fail before publishing docs. |
| Nightly data import | `artifacts/YYYY-MM-DD/import-summary.json` | An attempted import is not the same as a completed import. |
| Release note generation | `reports/YYYYMMDD_release-notes.md` | Maintainers need the actual note file before cutting a release. |
| Agent-maintained reports | `reports/YYYY-MM-DD.md` | An agent may resume a task but fail before writing the report. |
| Local backups or exports | `exports/YYYY-MM-DD/archive.zip` | Scheduler state does not prove the archive exists. |

It is not a replacement for Prometheus, Datadog, or hosted uptime monitoring. It is for simple maintainer workflows where success means: "this file should exist by this time."

## What It Catches

```text
runner state says: ran at 03:01
workspace says:    artifacts/2026-06-07/import-summary.json is missing
verdict:           RUN_ATTEMPTED_ARTIFACT_MISSING
```

That distinction is useful when a maintainer needs to know whether to trust an automation, rerun it, or investigate the runner itself.

## Try It in 3 Minutes

From a repository checkout:

```bash
git clone https://github.com/shinya-dev-jp/artifact-watchdog.git
cd artifact-watchdog
python3.11 -m pip install .
scripts/quickstart_smoke.sh
```

If `python3.11` is not available, install Python 3.11 or newer first. On macOS, `/usr/bin/python3` can still be Python 3.9; use `PYTHON=python3.11 scripts/quickstart_smoke.sh` when you have multiple Python versions installed.

The smoke test uses the installed CLI when available, copies the demo fixture into a temporary workspace, checks the expected verdicts, and verifies that `--fail-on any` exits non-zero for unhealthy jobs.

Expected final line:

```text
quickstart smoke ok
```

## Demo

The demo fixture contains four jobs: one healthy, one attempted-without-artifact, one with a matching runner failure log, and one with a schedule drift.

```bash
artifact-watchdog \
  --config examples/demo-workspace/watchdog.toml \
  --workspace examples/demo-workspace \
  --date 2026-06-07 \
  --now 2026-06-07T06:00:00+00:00
```

Expected output:

```text
docs-build	OK	artifact=FOUND	last=2026-06-07T02:01:00+00:00	next=2026-06-08T02:00:00+00:00	drift=none
nightly-import	RUN_ATTEMPTED_ARTIFACT_MISSING	artifact=MISSING	last=2026-06-07T03:01:00+00:00	next=2026-06-08T03:00:00+00:00	drift=none
release-notes	RUNNER_FAIL_LOG_FOUND	artifact=MISSING	last=2026-06-07T04:01:00+00:00	next=2026-06-08T04:00:00+00:00	drift=none
metrics-rollup	TIME_DRIFT_CHECK	artifact=MISSING	last=2026-06-06T05:01:00+00:00	next=2026-06-08T14:00:00+00:00	drift=expected=05:00, next_run_at=14:00
```

The demo workspace lives in [`examples/demo-workspace`](examples/demo-workspace/README.md).

## Failure Injection Lab

The reliability lab generates a temporary workspace with every major verdict class, including stale artifacts, invalid state JSON, and partial success. It then audits the workspace and fails if any observed verdict differs from the expected matrix.

```bash
PYTHONPATH=src python scripts/failure_lab.py
```

Expected final line:

```text
failure lab ok rows=10
```

Read the matrix in [`docs/FAILURE_LAB.md`](docs/FAILURE_LAB.md).

## Install

Requires Python 3.11 or newer.

From a checkout:

```bash
python3.11 -m pip install .
```

For editable local development:

```bash
python3.11 -m pip install -e .
```

## Quick Start

Start from the sample config, then edit the job ids, schedules, artifact paths, state files, and failure patterns for your own workspace.

```bash
cp examples/artifact-watchdog.toml artifact-watchdog.toml
```

Run a check from the workspace that contains the expected artifacts:

```bash
artifact-watchdog \
  --config artifact-watchdog.toml \
  --workspace . \
  --date 2026-06-07 \
  --markdown reports/2026-06-07.md
```

JSON output:

```bash
artifact-watchdog --config artifact-watchdog.toml --workspace . --json
```

Fail a CI step when any job is not `OK`:

```bash
artifact-watchdog --config artifact-watchdog.toml --workspace . --fail-on any
```

You can also fail only on specific verdicts:

```bash
artifact-watchdog \
  --config artifact-watchdog.toml \
  --workspace . \
  --fail-on RUNNER_FAIL_LOG_FOUND,RUN_ATTEMPTED_ARTIFACT_MISSING
```

## GitHub Actions And Cron

Copy [`examples/github-actions.yml`](examples/github-actions.yml) into `.github/workflows/artifact-watchdog.yml` to run artifact checks on a schedule. The sample installs the CLI from this GitHub repository, writes a Markdown report to the GitHub step summary, and fails the workflow when any configured job is not `OK`.

For a local machine or server cron, adapt [`examples/cron-daily.sh`](examples/cron-daily.sh):

```cron
30 6 * * * cd /path/to/workspace && ARTIFACT_WATCHDOG_CONFIG=artifact-watchdog.toml ./examples/cron-daily.sh
```

If your problem is a GitHub Actions schedule that runs late, does not run, or finishes without the artifact you expected, start with [`docs/GITHUB_ACTIONS_ARTIFACT_CHECKS.md`](docs/GITHUB_ACTIONS_ARTIFACT_CHECKS.md).

## Integration Templates

Copyable templates are available for common scheduled-artifact workflows:

- GitHub Actions scheduled workflow
- cron job
- systemd timer
- local agent report
- release note generation

Start with [`docs/INTEGRATION_TEMPLATES.md`](docs/INTEGRATION_TEMPLATES.md), then copy the closest template from [`examples/integrations`](examples/integrations/).

## Config

Config files use TOML and stay intentionally generic.

```toml
[watchdog]
timezone = "UTC"
grace_minutes = 15
log_lookback_hours = 24

[[jobs]]
id = "nightly-import"
status = "active"
schedule = "FREQ=DAILY;BYHOUR=3;BYMINUTE=0"
artifacts = [
  "artifacts/{date}/import-summary.json",
  "reports/{date_compact}_nightly-import.md",
]
state_file = "state/nightly-import.json"
log_paths = ["logs/*.log"]
failure_patterns = ["Scheduled run failed", "Timed out"]
```

Supported artifact placeholders:

- `{date}`: target date such as `2026-06-07`
- `{date_compact}`: target date such as `20260607`
- `{job_id}`: the configured job id

Supported schedules:

- `daily@03:00`
- `FREQ=DAILY;BYHOUR=3;BYMINUTE=0`

Optional state files are JSON:

```json
{
  "last_run_at": "2026-06-07T03:00:26+00:00",
  "next_run_at": "2026-06-08T03:00:00+00:00",
  "schedule": "FREQ=DAILY;BYHOUR=3;BYMINUTE=0"
}
```

## Verdicts

| Verdict | Meaning |
|---|---|
| `OK` | At least one expected artifact exists. |
| `STATE_FILE_INVALID` | The configured state file exists but cannot be parsed as a JSON object. |
| `TIME_DRIFT_CHECK` | Scheduler state points to a different time than the configured schedule. |
| `RUNNER_FAIL_LOG_FOUND` | No artifact exists, and a recent matching failure log was found. |
| `RUN_ATTEMPTED_ARTIFACT_MISSING` | State says the job ran on the target date, but no artifact exists. |
| `ARTIFACT_MISSING_OR_NOT_DUE` | The configured due time has not passed yet. |
| `ARTIFACT_MISSING_DUE_PASSED` | The due time has passed with no artifact and no failure evidence. |

## Exit Codes

By default, `artifact-watchdog` exits `0` after reporting verdicts. Use `--fail-on` when a shell, cron wrapper, or CI job should treat selected verdicts as failures.

| Option | Behavior |
|---|---|
| `--fail-on any` | Exit `1` if any job is not `OK`. |
| `--fail-on none` | Always exit `0` after reporting. |
| `--fail-on RUNNER_FAIL_LOG_FOUND,RUN_ATTEMPTED_ARTIFACT_MISSING` | Exit `1` only when one of the listed verdicts is present. |

## Privacy Model

The tool does not need credentials, network access, or a hosted service. It reads local config, local state JSON, local logs, and local artifact paths.

Keep private project names, customer data, internal paths, and secrets out of published config examples and reports.

## Development

```bash
PYTHONPATH=src python3.11 -m unittest discover -s tests
```

To verify the installed CLI behaves like the README demo from a clean temporary workspace:

```bash
python3.11 -m pip install .
scripts/quickstart_smoke.sh
```

To verify the integration templates still load and their shell snippets are valid:

```bash
scripts/template_pack_smoke.sh
```

To run the deterministic failure-injection lab:

```bash
PYTHONPATH=src python3.11 scripts/failure_lab.py
```

To let `artifact-watchdog` monitor this repository's own maintenance checks:

```bash
scripts/dogfood_artifacts.sh
```

The CI workflow also compiles the source files and runs the demo command on Python 3.11 and 3.12.

## Maintainer Notes

- [Dogfooding](docs/DOGFOODING.md)
- [Roadmap](docs/ROADMAP.md)
- [Release checklist](docs/RELEASING.md)
- [Changelog](CHANGELOG.md)
- [Security policy](SECURITY.md)

## Status

This is an early public release of a general artifact-based monitoring pattern. It is intentionally small: TOML config in, terminal, JSON, Markdown report, or CI exit code out.

The next useful improvements are clearer config errors, Markdown report fixtures, and GitHub step summary polish.
