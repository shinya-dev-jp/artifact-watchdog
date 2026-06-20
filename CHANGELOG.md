# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog, and this project follows semantic versioning once public releases begin.

## [Unreleased]

### Added

- `--fail-on` CLI option for CI and cron wrappers that should fail on selected verdicts.
- GitHub Actions and cron usage examples.
- Integration template pack for GitHub Actions, cron, systemd timers, local agent reports, and release note generation.
- Template smoke tests for integration configs and shell snippets.
- Dogfooding script, config, tests, and workflow so `artifact-watchdog` can monitor its own maintenance artifacts.
- Failure injection reliability lab for `OK`, missing artifacts, stale artifacts, runner failures, schedule drift, invalid state JSON, and partial success.
- `STATE_FILE_INVALID` verdict for state files that exist but cannot be parsed as JSON objects.
- GitHub Actions artifact-check guide for scheduled workflows, missing artifacts, and output-contract checks.
- Python 3.11 preflight messages in smoke scripts so users do not hit a raw `StrEnum` import error on older system Python versions.
- Package import guard with a clear Python 3.11+ error for direct `PYTHONPATH=src` use on unsupported interpreters.
- GitHub Actions CI for Python 3.11 and 3.12.
- Demo workspace covering `OK`, attempted-without-artifact, runner-failure, and time-drift verdicts.
- Issue templates and pull request checklist.
- Roadmap and release checklist documentation.

## [0.1.0] - 2026-06-08

### Added

- Initial local-first CLI for artifact-based scheduled-job checks.
- TOML config loader.
- Optional JSON state-file support.
- Optional log scanning.
- Text, JSON, and Markdown report output.
- Unit tests for core verdict behavior.
