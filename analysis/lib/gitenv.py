"""Git flags that must be passed on every merge-tree invocation."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from analysis.lib.constants import GIT_CONFIG


def git_c_args() -> list[str]:
    args: list[str] = []
    for key, value in GIT_CONFIG.items():
        args.extend(["-c", f"{key}={value}"])
    return args


def git_cmd(*parts: str) -> list[str]:
    return ["git", *git_c_args(), *parts]


def record_environment(out: Path) -> dict:
    def _run(cmd: list[str]) -> str:
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            return (p.stdout or p.stderr).strip()
        except Exception as exc:  # noqa: BLE001 — environment probe
            return f"ERROR: {exc}"

    rec = {
        "python": sys.version.replace("\n", " "),
        "python_executable": sys.executable,
        "git": _run(["git", "--version"]),
        "git_config": {},
        "os_uname": os.uname().sysname + " " + os.uname().release,
    }
    for key in GIT_CONFIG:
        rec["git_config"][key] = _run(["git", "config", "--get", key]) or "(unset; replay overrides via -c)"
    rec["replay_overrides"] = dict(GIT_CONFIG)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n")
    return rec
