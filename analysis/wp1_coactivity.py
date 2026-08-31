#!/usr/bin/env python3
"""RQ1: co-activity prevalence under treatments A/B/C and k-sweep.

Confirmatory descriptive analysis. No hypothesis tests.
Does not materialize full pair tables (some repos have >10k PRs).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.lib.constants import (  # noqa: E402
    DATA_DERIVED,
    HEADLINE_ABS_PP,
    HEADLINE_REL,
    K_CURVE,
    K_TABLE,
)
from analysis.lib.intervals import (  # noqa: E402
    SECONDS_PER_DAY,
    attach_intervals,
    median_resolution_by_agent,
    snapshot_cutoff,
)
from analysis.lib.io import load_pull_requests, load_repositories, write_csv, write_json  # noqa: E402
from analysis.lib.scan import DURATION_EDGES_HOURS, frame_to_arrays, scan_repo_arrays  # noqa: E402
from analysis.lib.stats import wilson  # noqa: E402


def choose_headline(p_a: float, p_b: float) -> str:
    if not np.isfinite(p_a) or not np.isfinite(p_b):
        return "B"
    abs_diff = abs(p_a - p_b)
    rel = abs_diff / max(p_a, 1e-9)
    if abs_diff >= HEADLINE_ABS_PP or rel >= HEADLINE_REL:
        return "B"
    return "A"


def open_pr_share(pr: pd.DataFrame) -> dict:
    closed = pd.to_datetime(pr["closed_at"], utc=True, errors="coerce")
    merged = pd.to_datetime(pr["merged_at"], utc=True, errors="coerce")
    cens = closed.isna() & merged.isna()
    k, n = int(cens.sum()), int(len(pr))
    p, lo, hi = wilson(k, n)
    return {"k": k, "n": n, "rate": p, "ci_low": lo, "ci_high": hi}


def scan_treatment(iv: pd.DataFrame, k_days_list: list[float]) -> dict:
    k_seconds = [k * SECONDS_PER_DAY for k in k_days_list]
    min_gap_parts = []
    repo_rows = []
    n_pairs = {k: 0 for k in k_seconds}
    n_cross = {k: 0 for k in k_seconds}
    n_both = {k: 0 for k in k_seconds}
    dur_sum = 0.0
    dur_n = 0
    hist = np.zeros(len(DURATION_EDGES_HOURS) - 1, dtype=np.int64)
    n_lt_1h = n_lt_24h = n_ge_7d = 0
    cross_agent_pairs = {}
    n_repos_ge2 = 0
    n_pr = int(len(iv))

    for rid, g in iv.groupby("repo_id", sort=False):
        arr = frame_to_arrays(g)
        if arr["starts"].shape[0] >= 2:
            n_repos_ge2 += 1
        sc = scan_repo_arrays(
            arr["starts"], arr["ends"], arr["agents"], arr["numbers"], arr["states"], k_seconds
        )
        for k in k_seconds:
            n_pairs[k] += sc["n_pairs"][k]
            n_cross[k] += sc["n_cross"][k]
            n_both[k] += sc["n_both_merged"][k]
        dur_sum += sc["duration_sum_seconds"]
        dur_n += sc["duration_n"]
        hist += sc["hist"]
        n_lt_1h += sc["n_overlap_lt_1h"]
        n_lt_24h += sc["n_overlap_lt_24h"]
        n_ge_7d += sc["n_overlap_ge_7d"]
        mg = sc["min_gap"]
        min_gap_parts.append(
            pd.DataFrame(
                {
                    "repo_id": rid,
                    "number": arr["numbers"],
                    "agent": arr["agents"],
                    "min_gap_seconds": mg,
                    "pr_state": arr["states"],
                }
            )
        )
        k0 = 0.0
        n_all0 = sc["n_pairs"][k0]
        n_cx0 = sc["n_cross"][k0]
        repo_rows.append(
            {
                "repo_id": rid,
                "n_pr": int(len(g)),
                "n_pairs_k0": n_all0,
                "n_cross_pairs_k0": n_cx0,
                "n_intra_pairs_k0": n_all0 - n_cx0,
                "has_pair_k0": int(n_all0 > 0),
                "has_intra": int(n_all0 - n_cx0 > 0),
                "has_cross": int(n_cx0 > 0),
            }
        )

    mg_df = pd.concat(min_gap_parts, ignore_index=True) if min_gap_parts else pd.DataFrame()
    repo_df = pd.DataFrame(repo_rows)
    return {
        "min_gap": mg_df,
        "repos": repo_df,
        "n_pr": n_pr,
        "n_repos_ge2": n_repos_ge2,
        "n_pairs": n_pairs,
        "n_cross": n_cross,
        "n_both": n_both,
        "dur_sum": dur_sum,
        "dur_n": dur_n,
        "hist": hist,
        "n_lt_1h": n_lt_1h,
        "n_lt_24h": n_lt_24h,
        "n_ge_7d": n_ge_7d,
    }


def rates_at_k(sc: dict, k_days: float, n_repos_all: int, treatment: str, n_censored: int) -> dict:
    k_sec = float(k_days) * SECONDS_PER_DAY
    mg = sc["min_gap"]
    n_pr = sc["n_pr"]
    if mg.empty:
        n_pr_co = 0
        n_repo_pair = 0
    else:
        co = mg["min_gap_seconds"] < k_sec
        n_pr_co = int(co.sum())
        n_repo_pair = int(mg.loc[co, "repo_id"].nunique())
    p, lo, hi = wilson(n_pr_co, n_pr)
    rp, rlo, rhi = wilson(n_repo_pair, n_repos_all)
    n_ge2 = sc["n_repos_ge2"]
    # repo share among ge2: repos with a pair at this k among those with >=2 PRs
    if mg.empty:
        n_pair_ge2 = 0
    else:
        ge2 = set(sc["repos"].loc[sc["repos"]["n_pr"] >= 2, "repo_id"])
        n_pair_ge2 = len(set(mg.loc[mg["min_gap_seconds"] < k_sec, "repo_id"]) & ge2)
    # pair counts: only precomputed for k in K_TABLE
    n_pairs = sc["n_pairs"].get(k_sec, None)
    n_cross = sc["n_cross"].get(k_sec, None)
    n_both = sc["n_both"].get(k_sec, None)
    return {
        "treatment": treatment,
        "k_days": float(k_days),
        "n_pr_included": n_pr,
        "n_pr_coactive": n_pr_co,
        "pr_share": n_pr_co / n_pr if n_pr else float("nan"),
        "pr_share_ci_low": lo,
        "pr_share_ci_high": hi,
        "n_repos_snapshot": n_repos_all,
        "n_repos_included": int(mg["repo_id"].nunique()) if not mg.empty else 0,
        "n_repos_ge2": n_ge2,
        "n_repos_with_pair": n_repo_pair,
        "repo_share_all": n_repo_pair / n_repos_all if n_repos_all else float("nan"),
        "repo_share_all_ci_low": rlo,
        "repo_share_all_ci_high": rhi,
        "repo_share_ge2": n_pair_ge2 / n_ge2 if n_ge2 else float("nan"),
        "n_pairs": n_pairs if n_pairs is not None else np.nan,
        "n_cross_pairs": n_cross if n_cross is not None else np.nan,
        "cross_pair_share": (n_cross / n_pairs) if n_pairs else float("nan"),
        "n_both_merged_pairs": n_both if n_both is not None else np.nan,
        "n_censored_in_snapshot": n_censored,
    }


def duration_summary(sc: dict) -> dict:
    n = sc["dur_n"]
    if n == 0:
        return {"n": 0, "mean_hours": float("nan")}
    mean_h = (sc["dur_sum"] / n) / 3600.0
    return {
        "n": int(n),
        "mean_hours": float(mean_h),
        "share_lt_1h": sc["n_lt_1h"] / n,
        "share_lt_24h": sc["n_lt_24h"] / n,
        "share_ge_7d": sc["n_ge_7d"] / n,
        "hist_edges_hours": DURATION_EDGES_HOURS.tolist(),
        "hist_counts": sc["hist"].tolist(),
        "note": "percentiles are not stored as a full vector; histogram is exact. mean and share_* are exact.",
    }


def main() -> None:
    pr = load_pull_requests()
    repo = load_repositories()
    DATA_DERIVED.mkdir(parents=True, exist_ok=True)

    open_share = open_pr_share(pr)
    write_json(DATA_DERIVED / "wp1_open_share.json", open_share)

    cutoff = snapshot_cutoff(pr)
    med = median_resolution_by_agent(pr)
    n_repos_all = int(repo["id"].nunique()) if "id" in repo.columns else int(pr["repo_id"].nunique())
    closed = pd.to_datetime(pr["closed_at"], utc=True, errors="coerce")
    merged = pd.to_datetime(pr["merged_at"], utc=True, errors="coerce")
    n_censored = int((closed.isna() & merged.isna()).sum())

    k_for_scan = sorted(set(float(k) for k in K_TABLE))
    scans = {}
    rows = []
    for t in ("A", "B", "C"):
        print(f"scanning treatment {t} ...", flush=True)
        iv = attach_intervals(pr, t, cutoff, med)
        sc = scan_treatment(iv, k_for_scan)
        scans[t] = sc
        sc["min_gap"].to_parquet(DATA_DERIVED / f"wp1_mingap_{t}.parquet", index=False)
        sc["repos"].to_parquet(DATA_DERIVED / f"wp1_repos_{t}.parquet", index=False)
        st0 = rates_at_k(sc, 0.0, n_repos_all, t, n_censored)
        rows.append(st0)
        dur = duration_summary(sc)
        dur["treatment"] = t
        write_json(DATA_DERIVED / f"wp1_overlap_duration_{t}.json", dur)

    headline = choose_headline(rows[0]["pr_share"], rows[1]["pr_share"])
    write_json(
        DATA_DERIVED / "wp1_headline.json",
        {
            "headline_treatment": headline,
            "p_A": rows[0]["pr_share"],
            "p_B": rows[1]["pr_share"],
            "abs_diff": abs(rows[0]["pr_share"] - rows[1]["pr_share"]),
            "rel_diff": abs(rows[0]["pr_share"] - rows[1]["pr_share"]) / max(rows[0]["pr_share"], 1e-9),
            "rule": "B if abs>=0.05 or rel>=0.10 else A",
        },
    )
    write_csv(pd.DataFrame(rows), DATA_DERIVED / "wp1_prevalence.csv")

    sweep_rows = []
    for t in ("A", "B", "C"):
        for k in K_TABLE:
            sweep_rows.append(rates_at_k(scans[t], float(k), n_repos_all, t, n_censored))
    write_csv(pd.DataFrame(sweep_rows), DATA_DERIVED / "wp1_k_sweep.csv")

    curve = [rates_at_k(scans[headline], float(k), n_repos_all, headline, n_censored) for k in K_CURVE]
    write_csv(pd.DataFrame(curve), DATA_DERIVED / "wp1_k_curve.csv")

    # agent / language co-activity on headline k=0
    mg = scans[headline]["min_gap"].copy()
    mg["coactive"] = mg["min_gap_seconds"] < 0
    agent_rows = []
    for agent, g in mg.groupby("agent"):
        k = int(g["coactive"].sum())
        n = int(len(g))
        p, lo, hi = wilson(k, n)
        agent_rows.append({"agent": agent, "k": k, "n": n, "rate": p, "ci_low": lo, "ci_high": hi})
    write_csv(pd.DataFrame(agent_rows).sort_values("rate", ascending=False), DATA_DERIVED / "wp1_by_agent.csv")

    repo_small = repo.rename(columns={"id": "repo_id"})[["repo_id", "language", "full_name"]]
    mg = mg.merge(repo_small, on="repo_id", how="left")
    top_lang = set(mg.groupby("language").size().sort_values(ascending=False).head(10).index)
    lang_rows = []
    for lang, g in mg[mg["language"].isin(top_lang)].groupby("language"):
        k = int(g["coactive"].sum())
        n = int(len(g))
        p, lo, hi = wilson(k, n)
        lang_rows.append({"language": lang, "k": k, "n": n, "rate": p, "ci_low": lo, "ci_high": hi, "volume": n})
    write_csv(pd.DataFrame(lang_rows).sort_values("rate", ascending=False), DATA_DERIVED / "wp1_by_language.csv")

    repos = scans[headline]["repos"]
    write_json(
        DATA_DERIVED / "wp1_cross_pair_share.json",
        {
            "headline_treatment": headline,
            "n_pairs": int(scans[headline]["n_pairs"][0.0]),
            "n_cross": int(scans[headline]["n_cross"][0.0]),
            "share": (
                scans[headline]["n_cross"][0.0] / scans[headline]["n_pairs"][0.0]
                if scans[headline]["n_pairs"][0.0]
                else float("nan")
            ),
            "n_cross_repos": int(repos["has_cross"].sum()),
            "n_intra_repos": int(repos["has_intra"].sum()),
            "n_matched_repos": int(((repos["has_intra"] == 1) & (repos["has_cross"] == 1)).sum()),
        },
    )

    print(f"open share: {open_share['k']}/{open_share['n']}")
    print(f"headline treatment: {headline}")
    print(
        f"A pr-share={rows[0]['pr_share']:.4f} B={rows[1]['pr_share']:.4f} C={rows[2]['pr_share']:.4f}"
    )
    print(f"wrote {DATA_DERIVED}")


if __name__ == "__main__":
    main()
