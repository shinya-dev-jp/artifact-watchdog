# Contributing

Thanks for taking a look at `artifact-watchdog`.

This project aims to stay small, local-first, and dependency-light. Contributions are most useful when they improve one of these areas:

- clearer verdicts for scheduled-job failures;
- safer config parsing;
- better report formats;
- tests for edge cases around time zones, globs, and stale logs.

Please avoid adding examples that contain real private paths, company names, customer data, account IDs, secrets, or unreleased project details.

Before opening a pull request, run:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```
