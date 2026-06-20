# GitHub Actions Artifact Checks

GitHub Actions can report that a workflow ran while the artifact a maintainer expected is still missing. `artifact-watchdog` is meant for that gap: it checks the durable file contract after the scheduler or workflow has had a chance to run.

## When To Use It

Use `artifact-watchdog` when a workflow or scheduled job is supposed to leave behind a file that another human or job relies on:

- generated documentation
- nightly import summaries
- release notes
- test reports
- local agent reports
- build outputs or archives

The useful question is not only "did the workflow run?" It is "does the expected output exist for the target date?"

## GitHub Actions Patterns It Fits

### Scheduled workflows can be late

GitHub's schedule event is not a precise timer. A workflow can be delayed during busy periods, and scheduled workflows only run from the default branch. That makes a target-date artifact check useful when a report has to exist by the next morning.

### Artifact upload can succeed as a warning path

The `actions/upload-artifact` action can warn when no files match the configured path, depending on its `if-no-files-found` behavior. `artifact-watchdog` gives you an independent check after the producing step, so your CI can fail on the missing output contract instead of relying only on upload behavior.

### Workflow success is not always output success

For simple maintainer workflows, the output file is often the real deliverable. If the file is missing, stale, or only partially produced, the next action should be investigation or rerun, not a green dashboard assumption.

## Minimal Workflow Shape

```yaml
name: Artifact watchdog

on:
  schedule:
    - cron: "30 6 * * *"
  workflow_dispatch:

jobs:
  watchdog:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python -m pip install git+https://github.com/shinya-dev-jp/artifact-watchdog.git
      - run: |
          artifact-watchdog \
            --config artifact-watchdog.toml \
            --workspace . \
            --date "$(date -u +%F)" \
            --markdown "$GITHUB_STEP_SUMMARY" \
            --fail-on any
```

For a copyable template, see [`examples/integrations/github-actions`](../examples/integrations/github-actions/).

## What To Record In Config

Each job should describe:

- when the artifact should exist
- where the artifact should be
- optional state JSON from the scheduler or runner
- optional logs that prove the runner failed before writing the file

```toml
[[jobs]]
id = "nightly-report"
schedule = "daily@06:00"
artifacts = ["reports/{date}.md"]
state_file = "state/nightly-report.json"
log_paths = ["logs/*.log"]
failure_patterns = ["Scheduled run failed", "Timed out"]
```

## Interpreting Results

- `OK`: at least one expected artifact exists.
- `RUN_ATTEMPTED_ARTIFACT_MISSING`: state says the job ran, but the artifact is missing.
- `RUNNER_FAIL_LOG_FOUND`: no artifact exists, and a matching failure log was found.
- `TIME_DRIFT_CHECK`: scheduler state does not match the configured schedule.
- `ARTIFACT_MISSING_DUE_PASSED`: the due time passed with no artifact and no failure evidence.

## Privacy

Do not publish private paths, customer names, internal job names, secrets, or raw logs. Keep examples generic, and replace private job labels before opening a public issue.

## Further Reading

- [GitHub Docs: store and share data with workflow artifacts](https://docs.github.com/en/actions/tutorials/store-and-share-data)
- [GitHub Docs: disabling and enabling workflows](https://docs.github.com/actions/managing-workflow-runs/disabling-and-enabling-a-workflow)
- [actions/upload-artifact documentation](https://github.com/actions/upload-artifact)
- [actions/upload-artifact issue: upload should fail if no files are found](https://github.com/actions/upload-artifact/issues/91)
