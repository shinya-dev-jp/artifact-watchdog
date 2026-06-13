# Integration Templates

These templates show common ways to run `artifact-watchdog` around existing schedulers and file-producing jobs.

They are starting points, not a framework. Copy the closest template, replace the job ids and artifact paths, then run the watchdog from the workspace that should contain the files.

Most templates have a command file and a matching `artifact-watchdog.toml`. Copy both, or update the command's `--config` path to wherever you keep the config.

## Choose a Template

| Template | Use it when | Files |
|---|---|---|
| GitHub Actions | A scheduled workflow should fail when expected files are missing. | [`artifact-watchdog.yml`](../examples/integrations/github-actions/artifact-watchdog.yml) + [`artifact-watchdog.toml`](../examples/integrations/github-actions/artifact-watchdog.toml) |
| cron | A local machine or server runs a daily shell command. | [`artifact-watchdog-cron.sh`](../examples/integrations/cron/artifact-watchdog-cron.sh) + [`artifact-watchdog.toml`](../examples/integrations/cron/artifact-watchdog.toml) |
| systemd timer | A Linux host should run the check as a managed timer. | [`artifact-watchdog.service`](../examples/integrations/systemd/artifact-watchdog.service) + [`artifact-watchdog.timer`](../examples/integrations/systemd/artifact-watchdog.timer) + [`artifact-watchdog.toml`](../examples/integrations/systemd/artifact-watchdog.toml) |
| Local agent report | An automated agent or script should write a daily report. | [`run-agent-report-check.sh`](../examples/integrations/local-agent-report/run-agent-report-check.sh) + [`artifact-watchdog.toml`](../examples/integrations/local-agent-report/artifact-watchdog.toml) |
| Release notes | A release process should produce a dated note before maintainers cut a release. | [`run-release-note-check.sh`](../examples/integrations/release-notes/run-release-note-check.sh) + [`artifact-watchdog.toml`](../examples/integrations/release-notes/artifact-watchdog.toml) |

## Adaptation Checklist

1. Copy the template config into your own workspace as `artifact-watchdog.toml`.
2. Change each `id` to a stable job name used by your team.
3. Change `schedule` to the time the artifact should be ready.
4. Change `artifacts` to the files that prove the job completed.
5. Add `state_file` only if your runner already writes JSON state.
6. Add `log_paths` and `failure_patterns` when recent logs can explain why an artifact is missing.
7. Start with `--fail-on none` or no `--fail-on` while tuning.
8. Switch to `--fail-on any` when the template is ready to gate CI or a local timer.

## What to Keep Out of Public Examples

Published configs and reports should stay generic. Do not include private project names, customer names, personal paths, hostnames, credentials, tokens, or incident details.

If a real workspace path or customer term appears in a config, keep that config private and publish only a scrubbed version.
