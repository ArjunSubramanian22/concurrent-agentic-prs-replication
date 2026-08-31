"""Co-activity intervals. Definitions are ANALYSIS_PLAN.md §3."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal, Optional

import numpy as np
import pandas as pd

Treatment = Literal["A", "B", "C"]
SECONDS_PER_DAY = 86400.0


@dataclass(frozen=True)
class PRRec:
    repo_id: int
    number: int
    agent: str
    user: str
    start: pd.Timestamp
    end: pd.Timestamp
    is_censored: bool
    pr_state: str
    merged_at: Optional[pd.Timestamp]


def utc_series(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce", utc=True)


def pr_state(closed_at: pd.Timestamp, merged_at: pd.Timestamp) -> str:
    if pd.notna(merged_at):
        return "merged"
    if pd.notna(closed_at):
        return "closed_unmerged"
    return "open"


def snapshot_cutoff(pr: pd.DataFrame) -> pd.Timestamp:
    parts = [utc_series(pr[c]) for c in ("created_at", "closed_at", "merged_at") if c in pr.columns]
    return pd.concat(parts).max()


def median_resolution_by_agent(pr: pd.DataFrame) -> dict[str, pd.Timedelta]:
    start = utc_series(pr["created_at"])
    closed = utc_series(pr["closed_at"])
    merged = utc_series(pr["merged_at"])
    resolved = closed.where(closed.notna(), merged)
    dur = resolved - start
    ok = resolved.notna() & start.notna() & (resolved >= start)
    med: dict[str, pd.Timedelta] = {}
    for agent, idx in pr.loc[ok].groupby("agent").groups.items():
        med[agent] = dur.loc[idx].median()
    global_med = dur[ok].median()
    if pd.isna(global_med):
        global_med = pd.Timedelta(days=1)
    med["__global__"] = global_med
    return med


def attach_intervals(
    pr: pd.DataFrame, treatment: Treatment, cutoff: pd.Timestamp, med_by_agent: dict[str, pd.Timedelta]
) -> pd.DataFrame:
    out = pr.copy()
    out["start"] = utc_series(out["created_at"])
    closed = utc_series(out["closed_at"])
    merged = utc_series(out["merged_at"])
    resolved = closed.where(closed.notna(), merged)
    out["is_censored"] = resolved.isna()
    out["pr_state"] = [
        pr_state(c, m) for c, m in zip(closed.tolist(), merged.tolist())
    ]
    invalid = out["start"].isna() | ((resolved.notna()) & (resolved < out["start"]))
    if treatment == "A":
        end = resolved.where(resolved.notna(), cutoff)
        keep = ~invalid
    elif treatment == "B":
        end = resolved
        keep = (~invalid) & (~out["is_censored"])
    elif treatment == "C":
        imputed = []
        for start, agent, res, cens in zip(out["start"], out["agent"], resolved, out["is_censored"]):
            if pd.notna(res):
                imputed.append(res)
            else:
                m = med_by_agent.get(agent, med_by_agent["__global__"])
                imputed.append(min(start + m, cutoff) if pd.notna(start) else pd.NaT)
        end = pd.to_datetime(pd.Series(imputed, index=out.index), utc=True)
        keep = ~invalid
    else:
        raise ValueError(treatment)
    out["end"] = end
    out = out.loc[keep & out["start"].notna() & out["end"].notna() & (out["end"] >= out["start"])].copy()
    return out


def overlaps(s1: pd.Timestamp, e1: pd.Timestamp, s2: pd.Timestamp, e2: pd.Timestamp, k_days: float) -> bool:
    slack = pd.Timedelta(seconds=k_days * SECONDS_PER_DAY)
    return max(s1, s2) < min(e1, e2) + slack


def sweep_pairs(rows: list[dict], k_days: float) -> list[tuple[dict, dict]]:
    """Return undirected overlapping pairs among rows of one repository."""
    if len(rows) < 2:
        return []
    slack = pd.Timedelta(days=k_days)
    ordered = sorted(rows, key=lambda r: (r["start"], r["number"]))
    active: list[dict] = []
    pairs: list[tuple[dict, dict]] = []
    for r in ordered:
        active = [a for a in active if r["start"] < a["end"] + slack]
        for a in active:
            if a["number"] == r["number"]:
                continue
            lo, hi = (a, r) if a["number"] < r["number"] else (r, a)
            pairs.append((lo, hi))
        active.append(r)
    return pairs


def first_overlap(rows: list[dict], want_cross: bool, k_days: float = 0.0) -> Optional[tuple[dict, dict]]:
    """Legacy sampler: earliest overlapping pair matching intra/cross."""
    for a, b in sweep_pairs(rows, k_days):
        cross = a["agent"] != b["agent"]
        if want_cross and cross:
            return (a, b)
        if (not want_cross) and (not cross):
            return (a, b)
    return None


def rows_from_frame(g: pd.DataFrame) -> list[dict]:
    recs = []
    for rec in g.itertuples(index=False):
        recs.append(
            {
                "repo_id": rec.repo_id,
                "number": int(rec.number),
                "agent": rec.agent,
                "user": getattr(rec, "user", ""),
                "start": rec.start,
                "end": rec.end,
                "is_censored": bool(rec.is_censored),
                "pr_state": rec.pr_state,
            }
        )
    return recs


def pair_table(pr_iv: pd.DataFrame, k_days: float) -> pd.DataFrame:
    """Enumerate all undirected overlapping pairs at slack k."""
    recs = []
    for rid, g in pr_iv.groupby("repo_id", sort=False):
        rows = rows_from_frame(g)
        for a, b in sweep_pairs(rows, k_days):
            recs.append(
                {
                    "repo_id": rid,
                    "prA": a["number"],
                    "prB": b["number"],
                    "agentA": a["agent"],
                    "agentB": b["agent"],
                    "userA": a["user"],
                    "userB": b["user"],
                    "startA": a["start"],
                    "endA": a["end"],
                    "startB": b["start"],
                    "endB": b["end"],
                    "stateA": a["pr_state"],
                    "stateB": b["pr_state"],
                    "censoredA": a["is_censored"],
                    "censoredB": b["is_censored"],
                    "cross": a["agent"] != b["agent"],
                    "overlap_seconds": (
                        min(a["end"], b["end"]) - max(a["start"], b["start"])
                    ).total_seconds(),
                }
            )
    if not recs:
        return pd.DataFrame(
            columns=[
                "repo_id",
                "prA",
                "prB",
                "agentA",
                "agentB",
                "cross",
                "overlap_seconds",
            ]
        )
    df = pd.DataFrame(recs)
    df["overlap_seconds"] = df["overlap_seconds"].clip(lower=0)
    return df


def pr_coactive_flags(pr_iv: pd.DataFrame, pairs: pd.DataFrame) -> pd.Series:
    """Boolean Series indexed like pr_iv: PR overlaps at least one other."""
    if pairs.empty:
        return pd.Series(False, index=pr_iv.index)
    touched = set()
    for rid, a, b in zip(pairs["repo_id"], pairs["prA"], pairs["prB"]):
        touched.add((rid, int(a)))
        touched.add((rid, int(b)))
    return pd.Series(
        [(rid, int(n)) in touched for rid, n in zip(pr_iv["repo_id"], pr_iv["number"])],
        index=pr_iv.index,
    )
