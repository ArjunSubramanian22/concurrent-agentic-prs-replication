"""Unit tests for interval overlap and headline rule. No data required."""
from __future__ import annotations

import pandas as pd

from analysis.lib.intervals import overlaps, sweep_pairs
from analysis.wp1_coactivity import choose_headline


def _pr(num, start, end, agent="A"):
    return {
        "repo_id": 1,
        "number": num,
        "agent": agent,
        "user": "u",
        "start": pd.Timestamp(start, tz="UTC"),
        "end": pd.Timestamp(end, tz="UTC"),
        "is_censored": False,
        "pr_state": "merged",
    }


def test_strict_overlap_k0():
    a = _pr(1, "2025-01-01", "2025-01-10")
    b = _pr(2, "2025-01-05", "2025-01-12")
    assert overlaps(a["start"], a["end"], b["start"], b["end"], 0)
    pairs = sweep_pairs([a, b], 0)
    assert len(pairs) == 1


def test_adjacent_no_overlap_k0():
    a = _pr(1, "2025-01-01", "2025-01-10")
    b = _pr(2, "2025-01-10", "2025-01-12")
    assert not overlaps(a["start"], a["end"], b["start"], b["end"], 0)
    # k=1 day must catch a 0-gap (touching) pair
    assert overlaps(a["start"], a["end"], b["start"], b["end"], 1)
    assert sweep_pairs([a, b], 0) == []
    assert len(sweep_pairs([a, b], 1)) == 1


def test_disjoint_needs_slack():
    a = _pr(1, "2025-01-01", "2025-01-02")
    b = _pr(2, "2025-01-05", "2025-01-06")
    # gap is exactly 3 days; plan uses strict < so k=3 does not overlap
    assert not overlaps(a["start"], a["end"], b["start"], b["end"], 2)
    assert not overlaps(a["start"], a["end"], b["start"], b["end"], 3)
    assert overlaps(a["start"], a["end"], b["start"], b["end"], 3.01)


def test_cross_and_intra_enumerated():
    rows = [
        _pr(1, "2025-01-01", "2025-01-10", "Codex"),
        _pr(2, "2025-01-02", "2025-01-11", "Codex"),
        _pr(3, "2025-01-03", "2025-01-12", "Devin"),
    ]
    pairs = sweep_pairs(rows, 0)
    assert len(pairs) == 3


def test_headline_switches_on_five_points():
    assert choose_headline(0.80, 0.74) == "B"
    assert choose_headline(0.80, 0.78) == "A"
    assert choose_headline(0.10, 0.08) == "B"  # 20% relative
