#!/usr/bin/env python3
"""Re-derive quantities from the committed legacy 747-pair replay CSV.

Every output is labeled legacy_earliest_pair. These tests motivated WP2/WP3;
they are not the confirmatory S3/GEE results.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.lib.constants import DATA_DERIVED  # noqa: E402
from analysis.lib.io import load_legacy_replay, write_csv, write_json  # noqa: E402
from analysis.lib.stats import fisher_exact, mcnemar_exact, wilson, wilson_legacy  # noqa: E402
from analysis.lib.taxonomy import categorize, count_types, type_group  # noqa: E402


EVAL = {"CLEAN", "CONFLICT"}


def _rate_row(label: str, k: int, n: int, z_legacy: bool = False) -> dict:
    fn = wilson_legacy if z_legacy else wilson
    p, lo, hi = fn(k, n)
    return {
        "label": label,
        "conflicts": int(k),
        "evaluable": int(n),
        "rate": p,
        "ci_low": lo,
        "ci_high": hi,
    }


def main() -> None:
    d = load_legacy_replay()
    DATA_DERIVED.mkdir(parents=True, exist_ok=True)
    ev = d[d["label"].isin(EVAL)].copy()
    rows = []
    for s in ("same", "cross"):
        g = ev[ev["stratum"] == s]
        k = int((g["label"] == "CONFLICT").sum())
        n = int(len(g))
        att = int((d["stratum"] == s).sum())
        row = _rate_row(s, k, n)
        row_leg = _rate_row(s + "_z1.96", k, n, z_legacy=True)
        row["attempted"] = att
        row["unavailable"] = att - n
        rows.append(row)
        rows.append(row_leg)
    k = int((ev["label"] == "CONFLICT").sum())
    n = int(len(ev))
    pool = _rate_row("__pool__", k, n)
    pool["attempted"] = int(len(d))
    pool["unavailable"] = int(len(d) - n)
    rows.append(pool)
    write_csv(pd.DataFrame(rows), DATA_DERIVED / "legacy_rates.csv")
    write_json(
        DATA_DERIVED / "legacy_availability.json",
        {
            "attempted": int(len(d)),
            "evaluable": int(len(ev)),
            "label_counts": {str(a): int(b) for a, b in d["label"].value_counts().items()},
        },
    )

    # taxonomy
    conf = d[d["label"] == "CONFLICT"].copy()
    file_cat = {}
    type_ctr = {}
    total_files = 0
    for _, r in conf.iterrows():
        files = str(r["files"]).split("|") if pd.notna(r["files"]) and r["files"] else []
        for fp in files:
            if not fp:
                continue
            c = categorize(fp)
            file_cat[c] = file_cat.get(c, 0) + 1
            total_files += 1
        for t in str(r["types"]).split("|") if pd.notna(r["types"]) and r["types"] else []:
            if t:
                type_ctr[t] = type_ctr.get(t, 0) + 1
    tax_rows = []
    for c, nfiles in sorted(file_cat.items(), key=lambda x: -x[1]):
        tax_rows.append(
            {
                "kind": "file_category",
                "name": c,
                "count": nfiles,
                "pct": nfiles / total_files if total_files else float("nan"),
            }
        )
    tt = sum(type_ctr.values())
    grouped = {"content": 0, "structural": 0, "other": 0}
    for t, ntypes in type_ctr.items():
        g = type_group(t)
        grouped[g] = grouped.get(g, 0) + ntypes
        tax_rows.append(
            {
                "kind": "conflict_type",
                "name": t,
                "count": ntypes,
                "pct": ntypes / tt if tt else float("nan"),
            }
        )
    for g, ntypes in grouped.items():
        tax_rows.append(
            {
                "kind": "type_group",
                "name": g,
                "count": ntypes,
                "pct": ntypes / tt if tt else float("nan"),
            }
        )
    write_csv(pd.DataFrame(tax_rows), DATA_DERIVED / "legacy_taxonomy.csv")
    write_json(
        DATA_DERIVED / "legacy_taxonomy_totals.json",
        {
            "n_conflicting_pairs": int(len(conf)),
            "n_conflicted_files": int(total_files),
            "n_type_signals": int(tt),
        },
    )

    # shared repos / McNemar
    same = ev[ev["stratum"] == "same"].set_index("repo")
    cross = ev[ev["stratum"] == "cross"].set_index("repo")
    shared = same.index.intersection(cross.index)
    s_conf = (same.loc[shared, "label"] == "CONFLICT")
    c_conf = (cross.loc[shared, "label"] == "CONFLICT")
    # align
    s_conf = s_conf.groupby(level=0).first()
    c_conf = c_conf.groupby(level=0).first()
    idx = s_conf.index.intersection(c_conf.index)
    s_conf, c_conf = s_conf.loc[idx], c_conf.loc[idx]
    only_cross = int((c_conf & ~s_conf).sum())
    only_intra = int((s_conf & ~c_conf).sum())
    both = int((s_conf & c_conf).sum())
    neither = int((~s_conf & ~c_conf).sum())
    mc = mcnemar_exact(only_cross, only_intra)  # n_only_1 = cross-only
    n = int(len(idx))
    intra_k, intra_n = int(s_conf.sum()), int(n)
    cross_k, cross_n = int(c_conf.sum()), int(n)
    matched = {
        "n_shared_repos_in_csv": int(len(set(d[d["stratum"] == "same"]["repo"]) & set(d[d["stratum"] == "cross"]["repo"]))),
        "n_shared_evaluable": n,
        "intra_conflicts": intra_k,
        "intra_n": intra_n,
        "cross_conflicts": cross_k,
        "cross_n": cross_n,
        "both_conflict": both,
        "neither": neither,
        "cross_only_conflict": only_cross,
        "intra_only_conflict": only_intra,
        "mcnemar": mc,
        "paired_rd": (cross_k - intra_k) / n if n else float("nan"),
    }
    ir = _rate_row("matched_intra", intra_k, intra_n)
    cr = _rate_row("matched_cross", cross_k, cross_n)
    matched["intra_rate"] = ir
    matched["cross_rate"] = cr
    write_json(DATA_DERIVED / "legacy_matched.json", matched)

    # multi-vendor vs single-vendor intra (multi-vendor := repo also has a cross pair in the sample)
    all_cross_repos = set(d[d["stratum"] == "cross"]["repo"])
    intra_ev = ev[ev["stratum"] == "same"].copy()
    intra_ev["multi"] = intra_ev["repo"].isin(all_cross_repos)
    k_m = int((intra_ev.loc[intra_ev["multi"], "label"] == "CONFLICT").sum())
    n_m = int(intra_ev["multi"].sum())
    k_s = int((intra_ev.loc[~intra_ev["multi"], "label"] == "CONFLICT").sum())
    n_s = int((~intra_ev["multi"]).sum())
    fish = fisher_exact(k_m, n_m, k_s, n_s)
    write_json(
        DATA_DERIVED / "legacy_multivendor_intra.json",
        {
            "multi_k": k_m,
            "multi_n": n_m,
            "single_k": k_s,
            "single_n": n_s,
            "fisher": fish,
            "multi_rate": _rate_row("multi", k_m, n_m),
            "single_rate": _rate_row("single", k_s, n_s),
        },
    )

    # intra by agent
    def pair_agent(row):
        return row["agentA"] if row["agentA"] == row["agentB"] else "CROSS"

    intra_ev["agent"] = [pair_agent(r) for _, r in intra_ev.iterrows()]
    agent_rows = []
    for agent, g in intra_ev.groupby("agent"):
        k = int((g["label"] == "CONFLICT").sum())
        n = int(len(g))
        agent_rows.append(_rate_row(agent, k, n) | {"agent": agent})
    write_csv(pd.DataFrame(agent_rows), DATA_DERIVED / "legacy_agent_intra.csv")

    # compositional expectation on cross evaluable
    intra_rate = {
        r["agent"]: r["rate"] for r in agent_rows if r["agent"] != "CROSS"
    }
    cross_ev = ev[ev["stratum"] == "cross"].copy()

    def expect_row(r):
        pa = intra_rate.get(r["agentA"])
        pb = intra_rate.get(r["agentB"])
        if pa is None or pb is None or not pd.notna(pa) or not pd.notna(pb):
            return float("nan")
        return pa + pb - pa * pb

    ex = cross_ev.apply(expect_row, axis=1)
    obs_k = int((cross_ev["label"] == "CONFLICT").sum())
    obs_n = int(len(cross_ev))
    write_json(
        DATA_DERIVED / "legacy_composition.json",
        {
            "n_cross_evaluable": obs_n,
            "observed_conflicts": obs_k,
            "observed_rate": obs_k / obs_n if obs_n else float("nan"),
            "expected_rate_mean": float(ex.mean()) if len(ex) else float("nan"),
            "n_cross_with_known_intra": int(ex.notna().sum()),
            "intra_rates_used": intra_rate,
        },
    )
    print("legacy rates:")
    print(pd.DataFrame(rows).to_string(index=False))
    print("matched McNemar p=", mc["p"], "cross_only", only_cross, "intra_only", only_intra)


if __name__ == "__main__":
    main()
