#!/usr/bin/env python3
"""Figures from derived CSVs only. Missing inputs skip the figure."""
from __future__ import annotations

import json
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".mplconfig"))
sys.path.insert(0, str(ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis.lib.constants import DATA_DERIVED, PAPER_FIG  # noqa: E402

INDIGO = "#4B48F8"
MAGENTA = "#DC267F"
NAVY = "#06122A"
GREY = "#8A93A6"


def _setup():
    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 160,
            "savefig.bbox": "tight",
            "pdf.fonttype": 42,
        }
    )
    PAPER_FIG.mkdir(parents=True, exist_ok=True)


def fig_prevalence():
    path = DATA_DERIVED / "wp1_k_sweep.csv"
    if not path.exists():
        print("skip fig_prevalence: no wp1_k_sweep.csv")
        return
    df = pd.read_csv(path)
    hl = json.loads((DATA_DERIVED / "wp1_headline.json").read_text())["headline_treatment"]
    sub = df[df["treatment"] == hl]
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    ax.plot(sub["k_days"], 100 * sub["pr_share"], "o-", color=INDIGO, label="PR-level")
    ax.plot(sub["k_days"], 100 * sub["repo_share_ge2"], "s-", color=NAVY, label="Repo-level (≥2 PRs)")
    ax.set_xlabel("co-activity slack $k$ (days)")
    ax.set_ylabel("co-active share (%)")
    ax.set_title(f"Co-activity under headline treatment {hl}")
    ax.legend()
    fig.savefig(PAPER_FIG / "fig_coactivity_k.pdf")
    fig.savefig(PAPER_FIG / "fig_coactivity_k.png")
    plt.close()
    print("wrote fig_coactivity_k")


def fig_kcurve():
    path = DATA_DERIVED / "wp1_k_curve.csv"
    if not path.exists():
        print("skip fig_kcurve")
        return
    df = pd.read_csv(path)
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    ax.plot(df["k_days"], 100 * df["pr_share"], color=INDIGO)
    ax.set_xlabel("co-activity slack $k$ (days)")
    ax.set_ylabel("PR-level co-active share (%)")
    fig.savefig(PAPER_FIG / "fig_kcurve.pdf")
    fig.savefig(PAPER_FIG / "fig_kcurve.png")
    plt.close()
    print("wrote fig_kcurve")


def fig_legacy_rates():
    path = DATA_DERIVED / "legacy_rates.csv"
    if not path.exists():
        print("skip fig_legacy_rates")
        return
    df = pd.read_csv(path)
    sub = df[df["label"].isin(["same", "cross"])]
    if len(sub) < 2:
        return
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    labels = ["Intra-agent\n(legacy sample)", "Cross-agent\n(legacy sample)"]
    p = sub["rate"].to_numpy()
    lo = sub["ci_low"].to_numpy()
    hi = sub["ci_high"].to_numpy()
    yerr = np.vstack([p - lo, hi - p])
    bars = ax.bar(labels, p * 100, yerr=yerr * 100, capsize=6, color=[INDIGO, MAGENTA], width=0.62)
    for i, b in enumerate(bars):
        ax.text(b.get_x() + b.get_width() / 2, hi[i] * 100 + 1.5, f"{p[i]*100:.1f}%", ha="center", fontweight="bold")
    ax.set_ylabel("Textual merge-conflict rate (%)")
    ax.set_ylim(0, 62)
    ax.set_title("Legacy earliest-pair sample (not confirmatory)")
    fig.savefig(PAPER_FIG / "fig_legacy_rates.pdf")
    fig.savefig(PAPER_FIG / "fig_legacy_rates.png")
    plt.close()
    print("wrote fig_legacy_rates")


def fig_censoring():
    path = DATA_DERIVED / "wp1_prevalence.csv"
    if not path.exists():
        return
    df = pd.read_csv(path)
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    xs = np.arange(len(df))
    ax.bar(xs - 0.2, 100 * df["pr_share"], 0.4, color=INDIGO, label="PR-level")
    ax.bar(xs + 0.2, 100 * df["repo_share_ge2"], 0.4, color=NAVY, label="Repo-level (≥2)")
    ax.set_xticks(xs)
    ax.set_xticklabels([f"T={t}" for t in df["treatment"]])
    ax.set_ylabel("co-active share at $k=0$ (%)")
    ax.legend()
    ax.set_title("Censoring treatments A / B / C")
    fig.savefig(PAPER_FIG / "fig_censoring.pdf")
    fig.savefig(PAPER_FIG / "fig_censoring.png")
    plt.close()
    print("wrote fig_censoring")


def main() -> None:
    _setup()
    fig_prevalence()
    fig_kcurve()
    fig_censoring()
    fig_legacy_rates()


if __name__ == "__main__":
    main()
