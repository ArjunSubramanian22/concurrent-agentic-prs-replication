#!/usr/bin/env python3
"""Write data/derived/environment_record.json (or --out)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.lib.constants import DATA_DERIVED  # noqa: E402
from analysis.lib.gitenv import record_environment  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, default=DATA_DERIVED / "environment_record.json")
    args = p.parse_args()
    rec = record_environment(args.out)
    print(f"wrote {args.out}")
    print(rec["git"])
    print(rec["python"])


if __name__ == "__main__":
    main()
