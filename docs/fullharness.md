# Fullharness Review

Date: 2026-06-08

Target: public-safe `artifact-watchdog` OSS repo.

## Expanded Roles

| Role | Responsibility |
|---|---|
| Generator | Produce the minimal public repo. |
| Secret Leak Auditor | Reject internal paths, names, business metrics, personal data, and copied private reports. |
| OSS Value Reviewer | Confirm the repo has a general problem statement and reusable behavior. |
| Timebox Reviewer | Keep the scope finishable in one short implementation pass. |
| Test Reviewer | Require executable tests for the core verdict logic. |
| Application Reviewer | Make the application draft honest about early adoption and submission blockers. |
| Maintainer Reviewer | Keep setup, contribution, and security notes clear enough for outside users. |

## R1 Generator

Initial scope:

- Build a generic Python CLI.
- Use TOML config rather than private runner-specific settings.
- Support artifact globs, optional state JSON, optional log scanning, text/JSON/Markdown output.
- Include tests and sample config with fictional job names only.

## R1 Evaluator Criticals

| Critical | True issue | Required fix |
|---|---|---|
| C1 | Copying the private watchdog would expose private structure. | Reimplement generic logic from scratch. |
| C2 | A new repo with no adoption is weak for a program focused on active OSS maintainers. | Make the application draft honest and mark submission as blocked until the repo is public and has maintenance evidence. |
| C3 | Scheduler-specific DB parsing would make the project too narrow. | Use optional generic JSON state instead. |
| C4 | A monitoring tool without tests is not credible. | Add unit tests for each verdict class. |
| C5 | Examples can accidentally leak real paths or project names. | Use fictional examples and run leak checks. |

## R2 Generator Fixes

- No private source files were copied.
- Config is generic TOML.
- State is optional JSON with standard timestamp fields.
- Tests cover OK, not due, attempted-without-artifact, failure-log, drift, and CLI report generation using only the Python standard library.
- Docs warn against publishing private paths or secrets.
- Application draft includes a no-submit gate.

## R2 Evaluator

Remaining Criticals:

| Critical | Status |
|---|---|
| Internal information leak | Passed automated grep check. |
| Test execution | Passed local unittest run. |
| Application overclaiming | Controlled by draft wording and no-submit gate. |
| Need-scene clarity | Addressed with runnable demo workspace and use-case-first README. |

## R3 Verification

Commands run locally:

```bash
PYTHONPATH=src python -m unittest discover -s tests
python -m py_compile src/artifact_watchdog/*.py
rg -n "<private-name-or-path-patterns>" .
```

Results:

- 7 tests passed.
- Python files compiled.
- Leak grep returned no matches.
- Demo command returns OK, attempted-without-artifact, runner-failure, and time-drift examples.

## Final Gate

Critical=0 for a local public-ready repository draft.

Do not push, publish, or submit the application until the maintainer explicitly approves.
