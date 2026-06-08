from __future__ import annotations

import argparse
from datetime import date as Date
from datetime import datetime
from pathlib import Path

from .config import ConfigError, load_config
from .core import audit_workspace
from .report import rows_to_json, rows_to_text, write_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="artifact-watchdog",
        description="Audit scheduled jobs by checking expected output artifacts.",
    )
    parser.add_argument("--config", required=True, help="Path to artifact-watchdog TOML config.")
    parser.add_argument("--workspace", default=".", help="Workspace root for artifact and log paths.")
    parser.add_argument("--date", default=Date.today().isoformat(), help="Target date in YYYY-MM-DD.")
    parser.add_argument("--now", help="Override current time as an ISO-8601 timestamp.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    parser.add_argument("--markdown", help="Write a Markdown report to this path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(Path(args.config))
        target_date = Date.fromisoformat(args.date)
        now = datetime.fromisoformat(args.now.replace("Z", "+00:00")) if args.now else None
        rows = audit_workspace(config, Path(args.workspace), target_date, now)
    except (ConfigError, ValueError, OSError) as exc:
        parser.error(str(exc))

    if args.json:
        print(rows_to_json(rows))
    else:
        print(rows_to_text(rows))

    if args.markdown:
        generated_at = now or datetime.now().astimezone()
        out = write_markdown(Path(args.markdown), rows, target_date, generated_at)
        print(f"report={out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

