# Failure Injection Reliability Lab

The failure lab is a deterministic workspace generator for proving what `artifact-watchdog` catches.

It creates a local fixture with healthy artifacts, missing artifacts, stale artifacts, runner failures, schedule drift, invalid state JSON, and partial success. Then it runs the same audit a maintainer would run in CI and verifies the observed verdicts against the expected matrix.

No credentials, network access, hosted service, or private paths are required.

## Run It

From a repository checkout:

```bash
PYTHONPATH=src python scripts/failure_lab.py
```

The script writes a generated workspace under `.artifact-watchdog/failure-lab` and exits non-zero if any verdict differs from the expected matrix.

Expected final line:

```text
failure lab ok rows=10
```

Use a custom temporary workspace:

```bash
PYTHONPATH=src python scripts/failure_lab.py --workspace /tmp/artifact-watchdog-failure-lab
```

The script refuses to reset a non-empty directory unless that directory already contains the lab marker file. This keeps the lab safe to run locally and in CI.

## What It Generates

| Output | Purpose |
|---|---|
| `reports/failure-lab.md` | Markdown audit report from the normal reporter. |
| `reports/failure-lab.json` | Machine-readable audit rows for snapshot checks or CI parsing. |
| `reports/failure-lab-matrix.md` | Expected vs observed verdict matrix with operator actions. |
| `artifacts/` | Target-date, stale-date, and partial-success artifacts. |
| `state/` | Valid, missing, drifted, and invalid runner state examples. |
| `logs/` | Runner failure evidence. |

## Cases

| Case | Expected verdict | Why it matters |
|---|---|---|
| `healthy-report` | `OK` | A target-date artifact exists. |
| `attempted-no-artifact` | `RUN_ATTEMPTED_ARTIFACT_MISSING` | Scheduler state says the job ran, but output is missing. |
| `runner-failure-log` | `RUNNER_FAIL_LOG_FOUND` | A recent failure log explains the missing artifact. |
| `time-drift` | `TIME_DRIFT_CHECK` | Scheduler state drifted away from the configured time. |
| `not-due-yet` | `ARTIFACT_MISSING_OR_NOT_DUE` | The due time has not passed yet. |
| `due-passed-missing` | `ARTIFACT_MISSING_DUE_PASSED` | The due time passed with no artifact or failure evidence. |
| `stale-artifact-only` | `ARTIFACT_MISSING_DUE_PASSED` | Yesterday's artifact does not satisfy today's contract. |
| `invalid-state-json` | `STATE_FILE_INVALID` | A state file exists but cannot be parsed as a JSON object. |
| `partial-suite-report` | `OK` | One job in a suite can pass. |
| `partial-suite-index` | `RUN_ATTEMPTED_ARTIFACT_MISSING` | A sibling job can fail without hiding behind the passing job. |

## CI Use

The repository CI runs the lab directly:

```bash
PYTHONPATH=src python scripts/failure_lab.py --workspace "$RUNNER_TEMP/failure-lab"
```

This is intentionally stronger than checking that a fixture exists. It regenerates the workspace, audits it, compares every observed verdict against the expected matrix, and fails if the tool stops detecting a class of failure.

## Config

The lab uses [`examples/failure-lab/artifact-watchdog.toml`](../examples/failure-lab/artifact-watchdog.toml). The config is intentionally generic so it can be copied into other repositories without leaking private project names or paths.
