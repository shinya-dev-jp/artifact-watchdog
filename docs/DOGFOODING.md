# Dogfooding

`artifact-watchdog` can monitor its own maintenance checks. This is intentionally small and local-first: the repo runs checks, writes durable artifacts, then uses `artifact-watchdog` to verify those artifacts exist.

The dogfood pack checks three jobs:

| Job | Artifact |
|---|---|
| `unit-tests` | `reports/{date}/unit-tests.txt` |
| `readme-quickstart-smoke` | `reports/{date}/quickstart-smoke.txt` |
| `integration-template-smoke` | `reports/{date}/template-pack-smoke.txt` |

Run it from a checkout:

```bash
scripts/dogfood_artifacts.sh
```

By default, artifacts are written under `.artifact-watchdog/dogfood`, which is ignored by git. Override the workspace when needed:

```bash
ARTIFACT_WATCHDOG_DOGFOOD_WORKSPACE=/tmp/artifact-watchdog-dogfood \
  scripts/dogfood_artifacts.sh
```

For deterministic local checks, set `ARTIFACT_WATCHDOG_DATE` and `ARTIFACT_WATCHDOG_NOW`.

The script writes:

- check output artifacts under `reports/YYYY-MM-DD/`
- runner-style state JSON under `state/`
- failure logs under `logs/`
- an `artifact-watchdog` Markdown report at `reports/YYYY-MM-DD/dogfood-watchdog.md`

The config lives at [`examples/dogfood/artifact-watchdog.toml`](../examples/dogfood/artifact-watchdog.toml).

## CI Workflow

The [`Dogfood`](../.github/workflows/dogfood.yml) workflow runs the same script on push, pull request, manual dispatch, and a daily schedule.

This does not call external services, create credentials, or require a hosted monitoring account. It only checks files produced inside the workflow workspace.
