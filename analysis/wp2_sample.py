#!/usr/bin/env python3
"""WP2: uniform-within-repo samples, designed match, legacy first-overlap.

Does not replay. Draws pair indices then materializes only the sampled pairs.
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
    DATA_SAMPLES,
    INTRA_REPO_DRAW,
    MAX_PAIRS_PER_REPO_STRATUM,
    SEED_INTRA_PAIRS,
    SEED_INTRA_REPOS,
    SEED_MATCHED,
)
from analysis.lib.intervals import (  # noqa: E402
    attach_intervals,
    first_overlap,
    median_resolution_by_agent,
    rows_from_frame,
    snapshot_cutoff,
)
from analysis.lib.io import load_pull_requests, load_repositories, write_csv, write_json  # noqa: E402
from analysis.lib.scan import collect_pairs_at_indices, frame_to_arrays  # noqa: E402


def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def _headline() -> str:
    path = DATA_DERIVED / "wp1_headline.json"
    if not path.exists():
        raise FileNotFoundError("run analysis/wp1_coactivity.py first")
    return json.loads(path.read_text())["headline_treatment"]


def _repo_map(repo: pd.DataFrame) -> dict:
    return repo.set_index("id")["full_name"].to_dict()


def arrays_by_repo(iv: pd.DataFrame) -> dict[int, dict]:
    out = {}
    for rid, g in iv.groupby("repo_id", sort=False):
        out[int(rid)] = frame_to_arrays(g)
    return out


def sample_stratum(
    repo_ids: np.ndarray,
    by_repo: dict,
    counts: pd.Series,
    want_cross: bool,
    n_take: int,
    seed: int,
    id2name: dict,
) -> pd.DataFrame:
    rng = _rng(seed)
    rows = []
    for rid in repo_ids:
        n = int(counts.loc[rid]) if rid in counts.index else 0
        if n <= 0:
            continue
        take = min(n_take, n)
        if take == n:
            idx = np.arange(n)
            rng.shuffle(idx)
        else:
            idx = rng.choice(n, size=take, replace=False)
            idx = np.sort(idx)
        arr = by_repo[int(rid)]
        found = collect_pairs_at_indices(
            arr["starts"],
            arr["ends"],
            arr["agents"],
            arr["numbers"],
            arr["states"],
            arr["users"],
            want_cross=want_cross,
            indices=set(int(x) for x in idx),
            k_seconds=0.0,
        )
        fn = id2name.get(rid)
        for pos, pair in found.items():
            rec = dict(pair)
            rec["repo_id"] = int(rid)
            rec["repo"] = fn
            rec["stratum"] = "cross" if want_cross else "same"
            rec["draw_index"] = int(pos)
            rows.append(rec)
    return pd.DataFrame(rows)


def legacy_first_overlap_sample(iv: pd.DataFrame, id2name: dict) -> pd.DataFrame:
    intra_rows = []
    cross_rows = []
    for rid, g in iv.groupby("repo_id", sort=False):
        fn = id2name.get(rid)
        if not fn:
            continue
        recs = rows_from_frame(g)
        if len(recs) < 2:
            continue
        pi = first_overlap(recs, want_cross=False)
        if pi:
            a, b = pi
            intra_rows.append(
                {
                    "stratum": "same",
                    "repo_id": rid,
                    "repo": fn,
                    "prA": a["number"],
                    "prB": b["number"],
                    "agentA": a["agent"],
                    "agentB": b["agent"],
                }
            )
        pc = first_overlap(recs, want_cross=True)
        if pc:
            a, b = pc
            cross_rows.append(
                {
                    "stratum": "cross",
                    "repo_id": rid,
                    "repo": fn,
                    "prA": a["number"],
                    "prB": b["number"],
                    "agentA": a["agent"],
                    "agentB": b["agent"],
                }
            )
    rng = _rng(SEED_INTRA_REPOS)
    if len(intra_rows) > INTRA_REPO_DRAW:
        idx = rng.choice(len(intra_rows), INTRA_REPO_DRAW, replace=False)
        intra_sel = [intra_rows[i] for i in sorted(idx)]
    else:
        intra_sel = intra_rows
    return pd.DataFrame(cross_rows + intra_sel)


def main() -> None:
    treatment = _headline()
    repo_stats = pd.read_parquet(DATA_DERIVED / f"wp1_repos_{treatment}.parquet")
    repo = load_repositories()
    id2name = _repo_map(repo)
    pr = load_pull_requests()
    cutoff = snapshot_cutoff(pr)
    med = median_resolution_by_agent(pr)
    iv = attach_intervals(pr, treatment, cutoff, med)
    print("indexing repos...", flush=True)
    by_repo = arrays_by_repo(iv)

    intra_repos = repo_stats.loc[repo_stats["has_intra"] == 1, "repo_id"].to_numpy()
    cross_repos = repo_stats.loc[repo_stats["has_cross"] == 1, "repo_id"].to_numpy()
    matched_repos = repo_stats.loc[
        (repo_stats["has_intra"] == 1) & (repo_stats["has_cross"] == 1), "repo_id"
    ].to_numpy()
    counts_intra = repo_stats.set_index("repo_id")["n_intra_pairs_k0"]
    counts_cross = repo_stats.set_index("repo_id")["n_cross_pairs_k0"]

    universe = {
        "headline_treatment": treatment,
        "k_days": 0,
        "n_intra_pairs": int(repo_stats["n_intra_pairs_k0"].sum()),
        "n_cross_pairs": int(repo_stats["n_cross_pairs_k0"].sum()),
        "n_repos_intra": int(len(intra_repos)),
        "n_repos_cross": int(len(cross_repos)),
        "n_repos_matched": int(len(matched_repos)),
        "n_repos_cross_only": int(len(set(cross_repos) - set(intra_repos))),
        "n_repos_intra_only": int(len(set(intra_repos) - set(cross_repos))),
        "seed_intra_repos": SEED_INTRA_REPOS,
        "seed_intra_pairs": SEED_INTRA_PAIRS,
        "seed_matched": SEED_MATCHED,
        "intra_repo_draw": INTRA_REPO_DRAW,
        "max_pairs_per_repo_stratum": MAX_PAIRS_PER_REPO_STRATUM,
    }
    DATA_SAMPLES.mkdir(parents=True, exist_ok=True)

    rng = _rng(SEED_INTRA_REPOS)
    if len(intra_repos) > INTRA_REPO_DRAW:
        s1_repos = rng.choice(intra_repos, INTRA_REPO_DRAW, replace=False)
    else:
        s1_repos = intra_repos

    print(f"drawing S1 n_repos={len(s1_repos)} ...", flush=True)
    s1 = sample_stratum(s1_repos, by_repo, counts_intra, False, 1, SEED_INTRA_PAIRS, id2name)
    s1m = sample_stratum(
        s1_repos, by_repo, counts_intra, False, MAX_PAIRS_PER_REPO_STRATUM, SEED_INTRA_PAIRS, id2name
    )
    print(f"drawing S2 n_repos={len(cross_repos)} ...", flush=True)
    s2 = sample_stratum(cross_repos, by_repo, counts_cross, True, 1, SEED_MATCHED, id2name)
    s2m = sample_stratum(
        cross_repos, by_repo, counts_cross, True, MAX_PAIRS_PER_REPO_STRATUM, SEED_MATCHED, id2name
    )
    print(f"drawing S3 n_matched={len(matched_repos)} ...", flush=True)
    s3i = sample_stratum(matched_repos, by_repo, counts_intra, False, 1, SEED_MATCHED, id2name)
    s3c = sample_stratum(matched_repos, by_repo, counts_cross, True, 1, SEED_MATCHED, id2name)
    s3i["match_role"] = "intra"
    s3c["match_role"] = "cross"
    s3 = pd.concat([s3i, s3c], ignore_index=True)
    s3im = sample_stratum(
        matched_repos, by_repo, counts_intra, False, MAX_PAIRS_PER_REPO_STRATUM, SEED_MATCHED, id2name
    )
    s3cm = sample_stratum(
        matched_repos, by_repo, counts_cross, True, MAX_PAIRS_PER_REPO_STRATUM, SEED_MATCHED, id2name
    )

    write_csv(s1, DATA_SAMPLES / "s1_intra_one.csv")
    write_csv(s1m, DATA_SAMPLES / "s1_intra_upto5.csv")
    write_csv(s2, DATA_SAMPLES / "s2_cross_one.csv")
    write_csv(s2m, DATA_SAMPLES / "s2_cross_upto5.csv")
    write_csv(s3, DATA_SAMPLES / "s3_matched_one.csv")
    write_csv(s3im, DATA_SAMPLES / "s3_matched_intra_upto5.csv")
    write_csv(s3cm, DATA_SAMPLES / "s3_matched_cross_upto5.csv")

    union = pd.concat(
        [
            s1m.assign(sample="s1_intra"),
            s2m.assign(sample="s2_cross"),
            s3im.assign(sample="s3_intra"),
            s3cm.assign(sample="s3_cross"),
        ],
        ignore_index=True,
    )
    union["pair_key"] = (
        union["repo"].astype(str) + "#" + union["prA"].astype(str) + "#" + union["prB"].astype(str)
    )
    unique = union.drop_duplicates("pair_key")
    write_csv(unique, DATA_SAMPLES / "replay_candidates.csv")
    universe["n_replay_candidates"] = int(len(unique))
    write_json(DATA_SAMPLES / "universe_counts.json", universe)

    print("rebuilding legacy first-overlap sample...", flush=True)
    legacy = legacy_first_overlap_sample(iv, id2name)
    write_csv(legacy, DATA_SAMPLES / "legacy_first_overlap_rebuilt.csv")
    print(json.dumps(universe, indent=2))
    print(f"S1={len(s1)} S2={len(s2)} S3={len(s3)} unique replay={len(unique)}")


if __name__ == "__main__":
    main()
