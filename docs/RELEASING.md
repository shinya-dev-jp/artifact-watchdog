# Releasing

This project has not cut its first public package release yet.

## Pre-Release Checklist

1. Run tests:

   ```bash
   PYTHONPATH=src python -m unittest discover -s tests
   ```

2. Run the demo command:

   ```bash
   PYTHONPATH=src python -m artifact_watchdog.cli \
     --config examples/demo-workspace/watchdog.toml \
     --workspace examples/demo-workspace \
     --date 2026-06-07 \
     --now 2026-06-07T06:00:00+00:00
   ```

3. Scan public files for private paths, secrets, customer data, and internal project names.
4. Update `CHANGELOG.md`.
5. Tag the release:

   ```bash
   git tag v0.1.0
   git push origin main v0.1.0
   ```

## Current Recommendation

Use GitHub releases before PyPI. Publish to PyPI only after at least one external user can run the demo and understands the config model.

