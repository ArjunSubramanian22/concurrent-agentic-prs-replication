#!/usr/bin/env python3
"""Update claims.csv status from the presence of output files."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.lib.constants import ROOT as REPO, UNAVAIL  # noqa: E402


def main() -> None:
    path = REPO / "claims.csv"
    rows = []
    with path.open() as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            out = Path(r["output_file"])
            if not out.is_absolute():
                out = REPO / out
            if out.exists():
                if out.suffix == ".json":
                    try:
                        blob = json.loads(out.read_text())
                        st = blob.get("status") if isinstance(blob, dict) else None
                        if st == UNAVAIL or (isinstance(blob, dict) and blob.get("reason") and "UNAVAILABLE" in str(blob.get("status", ""))):
                            r["status"] = "unavailable"
                        else:
                            r["status"] = "computed"
                    except Exception:
                        r["status"] = "computed"
                else:
                    r["status"] = "computed"
            else:
                r["status"] = "pending"
            rows.append(r)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    n = sum(1 for r in rows if r["status"] == "computed")
    print(f"claims: {n}/{len(rows)} computed")


if __name__ == "__main__":
    main()
