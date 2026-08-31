#!/usr/bin/env python3
"""Optional WP6. Refuses to run until WP4 and WP5 have non-UNAVAILABLE status."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.lib.constants import DATA_DERIVED, UNAVAIL  # noqa: E402
from analysis.lib.io import write_json  # noqa: E402


def _status(name: str) -> str:
    p = DATA_DERIVED / name
    if not p.exists():
        return UNAVAIL
    return json.loads(p.read_text()).get("status", UNAVAIL)


def main() -> None:
    DATA_DERIVED.mkdir(parents=True, exist_ok=True)
    wp4 = _status("wp4_status.json")
    wp5 = _status("wp5_status.json")
    if wp4 == UNAVAIL or wp5 == UNAVAIL:
        write_json(
            DATA_DERIVED / "wp6_status.json",
            {
                "status": UNAVAIL,
                "reason": "ANALYSIS_PLAN.md: drop WP6 if WP4 or WP5 is at risk",
                "wp4": wp4,
                "wp5": wp5,
            },
        )
        print("WP6 not run (WP4/WP5 not complete)")
        return
    write_json(DATA_DERIVED / "wp6_status.json", {"status": UNAVAIL, "reason": "not implemented"})


if __name__ == "__main__":
    main()
