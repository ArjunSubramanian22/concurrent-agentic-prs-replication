#!/usr/bin/env python3
"""Family 2 confirmatory tests. Refuses to invent numbers.

Runs on data/replay/pairs_replay.csv when present. The legacy 747-pair
file is never used here (see analysis/wp_legacy.py).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.lib.constants import DATA_DERIVED, DATA_REPLAY, DATA_SAMPLES, UNAVAIL  # noqa: E402
from analysis.lib.io import write_csv, write_json  # noqa: E402
from analysis.lib.stats import fisher_exact, mcnemar_exact, wilson  # noqa: E402

EVAL = {"CLEAN", "CONFLICT"}


def _load_replay() -> pd.DataFrame | None:
    path = DATA_REPLAY / "pairs_replay.csv"
    if not path.exists():
        return None
    d = pd.read_csv(path)
    if d.empty:
        return None
    return d


def _rate(g: pd.DataFrame) -> dict:
    k = int((g["label"] == "CONFLICT").sum())
    n = int(len(g))
    p, lo, hi = wilson(k, n)
    return {"conflicts": k, "evaluable": n, "rate": p, "ci_low": lo, "ci_high": hi}


def main() -> None:
    DATA_DERIVED.mkdir(parents=True, exist_ok=True)
    replay = _load_replay()
    if replay is None:
        write_json(
            DATA_DERIVED / "wp3_status.json",
            {
                "status": UNAVAIL,
                "reason": "data/replay/pairs_replay.csv missing or empty; run `make replay`",
            },
        )
        print("WP3 UNAVAILABLE: no confirmatory replay yet")
        return

    ev = replay[replay["label"].isin(EVAL)].copy()
    s1_path = DATA_SAMPLES / "s1_intra_one.csv"
    s2_path = DATA_SAMPLES / "s2_cross_one.csv"
    s3_path = DATA_SAMPLES / "s3_matched_one.csv"
    if not (s1_path.exists() and s2_path.exists() and s3_path.exists()):
        write_json(
            DATA_DERIVED / "wp3_status.json",
            {"status": UNAVAIL, "reason": "WP2 samples missing"},
        )
        print("WP3 UNAVAILABLE: samples missing")
        return

    s1 = pd.read_csv(s1_path)
    s2 = pd.read_csv(s2_path)
    s3 = pd.read_csv(s3_path)

    def key(df):
        return df["repo"].astype(str) + "#" + df["prA"].astype(str) + "#" + df["prB"].astype(str)

    replay = replay.copy()
    replay["pair_key"] = key(replay)
    done = set(replay["pair_key"])
    s1["pair_key"] = key(s1)
    s2["pair_key"] = key(s2)
    s3["pair_key"] = key(s3)
    frac1 = float(s1["pair_key"].isin(done).mean()) if len(s1) else 0.0
    frac2 = float(s2["pair_key"].isin(done).mean()) if len(s2) else 0.0
    if frac1 < 0.9 or frac2 < 0.9:
        write_json(
            DATA_DERIVED / "wp3_status.json",
            {
                "status": UNAVAIL,
                "reason": "confirmatory rates withheld until ≥90% of S1 and S2 primary draws are replayed",
                "s1_replay_frac": frac1,
                "s2_replay_frac": frac2,
                "s1_n": int(len(s1)),
                "s2_n": int(len(s2)),
            },
        )
        print(f"WP3 UNAVAILABLE: S1 replayed {frac1:.1%} S2 {frac2:.1%} (need ≥90%)")
        return

    ev = replay[replay["label"].isin(EVAL)].copy()
    ev["pair_key"] = key(ev)
    lookup = ev.drop_duplicates("pair_key").set_index("pair_key")

    def attach(sample: pd.DataFrame) -> pd.DataFrame:
        m = sample.merge(lookup[["label"]], left_on="pair_key", right_index=True, how="left")
        return m[m["label"].isin(EVAL)]

    a1 = attach(s1)
    a2 = attach(s2)
    rates = []
    r1 = {"sample": "s1_intra"} | _rate(a1) if len(a1) else {"sample": "s1_intra", "evaluable": 0}
    r2 = {"sample": "s2_cross"} | _rate(a2) if len(a2) else {"sample": "s2_cross", "evaluable": 0}
    rates.append(r1)
    rates.append(r2)
    write_csv(pd.DataFrame(rates), DATA_DERIVED / "wp3_rates.csv")

    tests = {"status": "partial" if (len(a1) == 0 or len(a2) == 0) else "ok"}
    if len(a1) and len(a2):
        tests["unmatched_fisher"] = fisher_exact(
            r2["conflicts"], r2["evaluable"], r1["conflicts"], r1["evaluable"]
        )
    else:
        tests["unmatched_fisher"] = UNAVAIL

    # S3 McNemar: one intra and one cross per repo, both evaluable
    s3["pair_key"] = key(s3)
    s3a = attach(s3)
    intra = s3a[s3a["stratum"] == "same"].drop_duplicates("repo").set_index("repo")
    cross = s3a[s3a["stratum"] == "cross"].drop_duplicates("repo").set_index("repo")
    common = intra.index.intersection(cross.index)
    if len(common) == 0:
        tests["matched_mcnemar"] = UNAVAIL
        tests["n_matched_evaluable_repos"] = 0
    else:
        ic = intra.loc[common, "label"] == "CONFLICT"
        cc = cross.loc[common, "label"] == "CONFLICT"
        only_c = int((cc & ~ic).sum())
        only_i = int((ic & ~cc).sum())
        tests["n_matched_evaluable_repos"] = int(len(common))
        tests["matched_mcnemar"] = mcnemar_exact(only_c, only_i)
        tests["matched_intra"] = _rate(intra.loc[common].reset_index())
        tests["matched_cross"] = _rate(cross.loc[common].reset_index())
        tests["paired_rd"] = (int(cc.sum()) - int(ic.sum())) / len(common)

    tests["gee_cross_or"] = UNAVAIL
    tests["gee_reason"] = "covariates not yet collected; GEE withheld rather than fit an unregistered subset"
    tests["compositional_expectation"] = UNAVAIL
    write_json(DATA_DERIVED / "wp3_tests.json", tests)
    write_json(DATA_DERIVED / "wp3_status.json", {"status": "ran_without_gee"})
    print("WP3 wrote rates/tests; GEE marked UNAVAILABLE until covariates exist")


if __name__ == "__main__":
    main()
