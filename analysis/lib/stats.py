"""Statistical primitives. Every comparison in the paper goes through here."""
from __future__ import annotations

import math
from typing import Iterable

import numpy as np
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import confint_proportions_2indep

Z_WILSON = float(stats.norm.ppf(0.975))
Z_LEGACY = 1.96


def wilson(k: int, n: int, z: float = Z_WILSON) -> tuple[float, float, float]:
    if n == 0 or n is None:
        return (float("nan"), float("nan"), float("nan"))
    k = int(k)
    n = int(n)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return p, max(0.0, centre - half), min(1.0, centre + half)


def wilson_legacy(k: int, n: int) -> tuple[float, float, float]:
    return wilson(k, n, z=Z_LEGACY)


def fisher_exact(k1: int, n1: int, k2: int, n2: int) -> dict:
    """Two-sided Fisher exact on [[k1, n1-k1], [k2, n2-k2]]."""
    table = np.array([[k1, n1 - k1], [k2, n2 - k2]], dtype=int)
    oddsratio, p = stats.fisher_exact(table, alternative="two-sided")
    rd, rd_lo, rd_hi = risk_difference(k1, n1, k2, n2)
    return {
        "odds_ratio": float(oddsratio),
        "p": float(p),
        "risk_difference": rd,
        "rd_low": rd_lo,
        "rd_high": rd_hi,
        "k1": int(k1),
        "n1": int(n1),
        "k2": int(k2),
        "n2": int(n2),
    }


def risk_difference(k1: int, n1: int, k2: int, n2: int) -> tuple[float, float, float]:
    """Newcombe independent risk difference p1 - p2 with 95% interval."""
    if n1 == 0 or n2 == 0:
        return (float("nan"), float("nan"), float("nan"))
    p1, p2 = k1 / n1, k2 / n2
    rd = p1 - p2
    try:
        lo, hi = confint_proportions_2indep(
            k1, n1, k2, n2, method="newcomb", compare="diff", alpha=0.05
        )
        return float(rd), float(lo), float(hi)
    except Exception:  # noqa: BLE001
        return float(rd), float("nan"), float("nan")


def mcnemar_exact(n_only_1: int, n_only_2: int) -> dict:
    """Exact McNemar (binomial) on discordant pairs.

    n_only_1: count where outcome1=1 and outcome2=0
    n_only_2: count where outcome1=0 and outcome2=1
    """
    n_only_1 = int(n_only_1)
    n_only_2 = int(n_only_2)
    n_disc = n_only_1 + n_only_2
    if n_disc == 0:
        return {
            "n_only_1": n_only_1,
            "n_only_2": n_only_2,
            "n_discordant": 0,
            "p": float("nan"),
            "p1_minus_p2": 0.0,
            "disc_ratio": float("nan"),
            "disc_ratio_low": float("nan"),
            "disc_ratio_high": float("nan"),
        }
    bt = stats.binomtest(n_only_1, n_disc, 0.5, alternative="two-sided")
    # Exact Clopper-Pearson on the share of discordant pairs that are only_1.
    ci = bt.proportion_ci(confidence_level=0.95)
    # Paired RD = (n_only_1 - n_only_2) / N is not identified without N;
    # callers add N and compute RD. Here we report the discordant split.
    return {
        "n_only_1": n_only_1,
        "n_only_2": n_only_2,
        "n_discordant": n_disc,
        "p": float(bt.pvalue),
        "disc_ratio": n_only_1 / n_disc,
        "disc_ratio_low": float(ci.low),
        "disc_ratio_high": float(ci.high),
    }


def holm(pvalues: Iterable[float], alpha: float = 0.05) -> list[dict]:
    p = list(pvalues)
    if not p:
        return []
    reject, padj, _, _ = multipletests(p, alpha=alpha, method="holm")
    return [
        {"p": float(pi), "p_holm": float(a), "reject_holm": bool(r)}
        for pi, a, r in zip(p, padj, reject)
    ]


def cramers_v(chi2: float, n: int, r: int, c: int) -> float:
    if n == 0 or min(r - 1, c - 1) == 0:
        return float("nan")
    return math.sqrt(chi2 / (n * min(r - 1, c - 1)))


def chi2_independence(table: np.ndarray) -> dict:
    chi2, p, dof, expected = stats.chi2_contingency(table)
    r, c = table.shape
    n = int(table.sum())
    return {
        "chi2": float(chi2),
        "p": float(p),
        "dof": int(dof),
        "n": n,
        "cramers_v": cramers_v(float(chi2), n, r, c),
        "min_expected": float(expected.min()),
        "expected": expected.tolist(),
    }
