#!/usr/bin/env python3
"""WP5 build/test layer. Docker required. Never codes timeout as PASS."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.lib.constants import DATA_DERIVED, UNAVAIL  # noqa: E402
from analysis.lib.io import write_json  # noqa: E402


def main() -> None:
    DATA_DERIVED.mkdir(parents=True, exist_ok=True)
    if shutil.which("docker") is None:
        write_json(
            DATA_DERIVED / "wp5_status.json",
            {
                "status": UNAVAIL,
                "reason": "docker not on PATH; WP5 not run; no build-conflict rate invented",
            },
        )
        print("WP5 UNAVAILABLE: docker missing")
        return
    write_json(
        DATA_DERIVED / "wp5_status.json",
        {"status": UNAVAIL, "reason": "docker present but WP5 runner not yet executed on a CLEAN subset"},
    )


if __name__ == "__main__":
    main()
