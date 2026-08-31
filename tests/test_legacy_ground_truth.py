"""Ground-truth checks against the committed legacy replay CSV."""
from analysis.lib.io import load_legacy_replay
from analysis.lib.stats import wilson, mcnemar_exact


def test_legacy_headline_counts():
    d = load_legacy_replay()
    ev = d[d["label"].isin(["CLEAN", "CONFLICT"])]
    same = ev[ev["stratum"] == "same"]
    cross = ev[ev["stratum"] == "cross"]
    assert len(d) == 747
    assert len(ev) == 716
    assert int((same["label"] == "CONFLICT").sum()) == 119
    assert len(same) == 601
    assert int((cross["label"] == "CONFLICT").sum()) == 48
    assert len(cross) == 115


def test_legacy_wilson_one_decimal():
    p, lo, hi = wilson(119, 601)
    assert round(p * 100, 1) == 19.8
    assert round(lo * 100, 1) == 16.8
    assert round(hi * 100, 1) == 23.2


def test_legacy_mcnemar_p_rounds_to_078():
    # Recompute from the CSV using the same definition as wp_legacy.py
    d = load_legacy_replay()
    ev = d[d["label"].isin(["CLEAN", "CONFLICT"])]
    same = ev[ev["stratum"] == "same"].drop_duplicates("repo").set_index("repo")
    cross = ev[ev["stratum"] == "cross"].drop_duplicates("repo").set_index("repo")
    idx = same.index.intersection(cross.index)
    s = same.loc[idx, "label"] == "CONFLICT"
    c = cross.loc[idx, "label"] == "CONFLICT"
    only_c = int((c & ~s).sum())
    only_i = int((s & ~c).sum())
    assert only_c == 15
    assert only_i == 6
    mc = mcnemar_exact(only_c, only_i)
    assert round(mc["p"], 3) == 0.078
