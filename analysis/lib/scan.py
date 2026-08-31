"""Per-repository scan. O(n) memory; never materializes C(n,2) pair tables."""
from __future__ import annotations

from typing import Iterable, Optional

import numpy as np
import pandas as pd

DURATION_EDGES_HOURS = np.array(
    [0.0, 1 / 60, 1.0, 6.0, 24.0, 72.0, 168.0, 336.0, 720.0, 2160.0, np.inf]
)


def to_epoch_seconds(s: pd.Series) -> np.ndarray:
    ns = pd.to_datetime(s, utc=True).astype("int64").to_numpy()
    return ns.astype(np.float64) / 1e9


def _as_epoch(a: np.ndarray) -> np.ndarray:
    return np.asarray(a, dtype=np.float64)


def _gap_row(s_i: float, e_i: float, starts: np.ndarray, ends: np.ndarray) -> np.ndarray:
    return np.maximum(s_i, starts) - np.minimum(e_i, ends)


def scan_repo_arrays(
    starts: np.ndarray,
    ends: np.ndarray,
    agents: np.ndarray,
    numbers: np.ndarray,
    states: np.ndarray,
    k_seconds: Iterable[float],
) -> dict:
    n = int(len(starts))
    ks = [float(x) for x in k_seconds]
    n_pairs = {k: 0 for k in ks}
    n_cross = {k: 0 for k in ks}
    n_both_merged = {k: 0 for k in ks}
    min_gap = np.full(n, np.inf, dtype=np.float64)
    dur_sum = 0.0
    dur_n = 0
    hist = np.zeros(len(DURATION_EDGES_HOURS) - 1, dtype=np.int64)
    share_lt_1h = share_lt_24h = share_ge_7d = 0
    empty = {
        "n": n,
        "min_gap": min_gap,
        "n_pairs": n_pairs,
        "n_cross": n_cross,
        "n_both_merged": n_both_merged,
        "duration_sum_seconds": 0.0,
        "duration_n": 0,
        "hist": hist,
        "n_overlap_lt_1h": 0,
        "n_overlap_lt_24h": 0,
        "n_overlap_ge_7d": 0,
    }
    if n < 2:
        return empty
    starts_f = _as_epoch(starts)
    ends_f = _as_epoch(ends)
    k0 = 0.0
    for i in range(n):
        sl = slice(i + 1, n)
        if sl.start >= n:
            break
        gap = _gap_row(starts_f[i], ends_f[i], starts_f[sl], ends_f[sl])
        min_gap[i] = min(min_gap[i], float(gap.min()))
        np.minimum(min_gap[sl], gap, out=min_gap[sl])
        for k in ks:
            mask = gap < k
            cnt = int(mask.sum())
            n_pairs[k] += cnt
            if cnt == 0:
                continue
            n_cross[k] += int((agents[sl][mask] != agents[i]).sum())
            if states is not None:
                n_both_merged[k] += int(((states[i] == "merged") & (states[sl][mask] == "merged")).sum())
        mask0 = gap < k0
        if mask0.any():
            ov = -gap[mask0]
            dur_sum += float(ov.sum())
            dur_n += int(mask0.sum())
            hours = ov / 3600.0
            hist += np.histogram(hours, bins=DURATION_EDGES_HOURS)[0]
            share_lt_1h += int((hours < 1).sum())
            share_lt_24h += int((hours < 24).sum())
            share_ge_7d += int((hours >= 168).sum())
    empty.update(
        {
            "min_gap": min_gap,
            "n_pairs": n_pairs,
            "n_cross": n_cross,
            "n_both_merged": n_both_merged,
            "duration_sum_seconds": dur_sum,
            "duration_n": dur_n,
            "hist": hist,
            "n_overlap_lt_1h": share_lt_1h,
            "n_overlap_lt_24h": share_lt_24h,
            "n_overlap_ge_7d": share_ge_7d,
        }
    )
    return empty


def collect_pairs_at_indices(
    starts: np.ndarray,
    ends: np.ndarray,
    agents: np.ndarray,
    numbers: np.ndarray,
    states: np.ndarray,
    users: np.ndarray,
    want_cross: Optional[bool],
    indices: set[int],
    k_seconds: float = 0.0,
) -> dict[int, dict]:
    n = int(len(starts))
    if n < 2 or not indices:
        return {}
    starts_f = _as_epoch(starts)
    ends_f = _as_epoch(ends)
    seen = 0
    found: dict[int, dict] = {}
    for i in range(n):
        sl = slice(i + 1, n)
        if sl.start >= n:
            break
        gap = _gap_row(starts_f[i], ends_f[i], starts_f[sl], ends_f[sl])
        for j in np.flatnonzero(gap < k_seconds):
            jj = i + 1 + int(j)
            cross = agents[i] != agents[jj]
            if want_cross is not None and bool(cross) != want_cross:
                continue
            if seen in indices:
                a, b = (i, jj) if int(numbers[i]) < int(numbers[jj]) else (jj, i)
                ov = min(ends_f[i], ends_f[jj]) - max(starts_f[i], starts_f[jj])
                found[seen] = {
                    "prA": int(numbers[a]),
                    "prB": int(numbers[b]),
                    "agentA": str(agents[a]),
                    "agentB": str(agents[b]),
                    "userA": str(users[a]),
                    "userB": str(users[b]),
                    "startA": float(starts_f[a]),
                    "endA": float(ends_f[a]),
                    "startB": float(starts_f[b]),
                    "endB": float(ends_f[b]),
                    "stateA": str(states[a]),
                    "stateB": str(states[b]),
                    "cross": bool(agents[a] != agents[b]),
                    "overlap_seconds": float(max(ov, 0.0)),
                }
                if len(found) == len(indices):
                    return found
            seen += 1
    return found


def frame_to_arrays(g: pd.DataFrame) -> dict[str, np.ndarray]:
    g = g.sort_values(["start", "number"])
    return {
        "starts": to_epoch_seconds(g["start"]),
        "ends": to_epoch_seconds(g["end"]),
        "agents": g["agent"].to_numpy(),
        "numbers": g["number"].to_numpy(),
        "states": g["pr_state"].to_numpy() if "pr_state" in g.columns else np.array(["unknown"] * len(g)),
        "users": g["user"].to_numpy() if "user" in g.columns else np.array([""] * len(g)),
        "index": g.index.to_numpy(),
    }
