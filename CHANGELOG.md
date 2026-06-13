# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog, and this project follows semantic versioning once public releases begin.

## [Unreleased]

### Added

- `--fail-on` CLI option for CI and cron wrappers that should fail on selected verdicts.
- GitHub Actions and cron usage examples.
- Integration template pack for GitHub Actions, cron, systemd timers, local agent reports, and release note generation.
- Template smoke tests for integration configs and shell snippets.
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
