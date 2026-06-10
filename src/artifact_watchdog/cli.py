from __future__ import annotations

import argparse
from datetime import date as Date
from datetime import datetime
from pathlib import Path

from .config import ConfigError, load_config
from .core import Verdict, audit_workspace
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
    parser.add_argument(
        "--fail-on",
        default="",
        metavar="MODE",
        help=(
            "Exit 1 when matching verdicts are present. Use 'any' for any non-OK "
            "verdict, 'none' to never fail, or a comma-separated verdict list."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(Path(args.config))
        target_date = Date.fromisoformat(args.date)
        now = datetime.fromisoformat(args.now.replace("Z", "+00:00")) if args.now else None
        rows = audit_workspace(config, Path(args.workspace), target_date, now)
        fail_on = parse_fail_on(args.fail_on)
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

    return 1 if any(row.verdict in fail_on for row in rows) else 0


def parse_fail_on(value: str) -> set[Verdict]:
    normalized = value.strip()
    if not normalized or normalized.lower() in {"none", "never", "false"}:
        return set()
    if normalized.lower() in {"any", "non-ok", "not-ok"}:
        return {verdict for verdict in Verdict if verdict is not Verdict.OK}

    verdicts: set[Verdict] = set()
    allowed = ", ".join(verdict.value for verdict in Verdict)
    for item in normalized.split(","):
        name = item.strip().upper().replace("-", "_")
        if not name:
            continue
        try:
            verdicts.add(Verdict(name))
        except ValueError as exc:
            raise ValueError(f"unknown --fail-on verdict {item!r}; expected 'any', 'none', or one of: {allowed}") from exc
    return verdicts


if __name__ == "__main__":
    raise SystemExit(main())
