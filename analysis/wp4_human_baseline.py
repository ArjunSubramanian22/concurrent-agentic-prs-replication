#!/usr/bin/env python3
"""WP4 human baseline. Writes UNAVAILABLE until human PR cache exists."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.lib.constants import DATA_CACHE, DATA_DERIVED, UNAVAIL  # noqa: E402
from analysis.lib.io import write_json  # noqa: E402


def main() -> None:
    DATA_DERIVED.mkdir(parents=True, exist_ok=True)
    marker = DATA_CACHE.parent / "human_prs.parquet"
    alt = DATA_DERIVED / "human_prs.parquet"
    if not marker.exists() and not alt.exists():
        write_json(
            DATA_DERIVED / "wp4_status.json",
            {
                "status": UNAVAIL,
                "reason": (
                    "Human PRs are not in AIDev-pop. Run analysis/collect_github.py "
                    "with GITHUB_TOKEN, then replay human pairs. No literature rate "
                    "is substituted."
                ),
            },
        )
        print("WP4 UNAVAILABLE: human PR collection has not been run")
        return
    write_json(
        DATA_DERIVED / "wp4_status.json",
        {"status": UNAVAIL, "reason": "collection file present but WP4 analysis not yet implemented on it"},
    )


if __name__ == "__main__":
    main()
