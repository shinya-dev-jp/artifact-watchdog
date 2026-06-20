from __future__ import annotations

import sys


def unsupported_python_message(version_info: tuple[int, ...] | None = None) -> str | None:
    version = version_info or sys.version_info
    if version >= (3, 11):
        return None

    selected = ".".join(str(part) for part in version[:3])
    return (
        "artifact-watchdog requires Python 3.11 or newer. "
        f"Selected interpreter is Python {selected}. "
        "Install Python 3.11+ or rerun with PYTHON=python3.11."
    )


def enforce_supported_python(version_info: tuple[int, ...] | None = None) -> None:
    message = unsupported_python_message(version_info)
    if message is not None:
        raise RuntimeError(message)
