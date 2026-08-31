#!/usr/bin/env python3
"""Write paper/tables/*.tex from derived CSVs. No invented numbers."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.lib.constants import DATA_DERIVED, PAPER_TAB  # noqa: E402


def pct(x) -> str:
    return f"{100.0 * float(x):.1f}"


def main() -> None:
    PAPER_TAB.mkdir(parents=True, exist_ok=True)
    prev = DATA_DERIVED / "wp1_prevalence.csv"
    if not prev.exists():
        print("no prevalence csv")
        return
    df = pd.read_csv(prev)
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Co-activity at $k{=}0$ under three end-time treatments. "
        r"Treatment A treats unresolved PRs as open until the snapshot cutoff. "
        r"Treatment B drops them. Treatment C imputes the agent-specific median lifetime. "
        r"Headline treatment is B (pre-registered 5pp/10\% rule).}",
        r"\label{tab:prevalence}",
        r"\begin{tabular}{l r r r r r}",
        r"\hline",
        r"T & PRs & PR co-active \% [95\% CI] & Repos w/ pair \% & Pairs & Cross pairs \\",
        r"\hline",
    ]
    for _, r in df.iterrows():
        lines.append(
            f"{r['treatment']} & {int(r['n_pr_included']):,} & "
            f"{pct(r['pr_share'])} [{pct(r['pr_share_ci_low'])}, {pct(r['pr_share_ci_high'])}] & "
            f"{pct(r['repo_share_all'])} & {int(r['n_pairs']):,} & {int(r['n_cross_pairs']):,} \\\\"
        )
    lines += [r"\hline", r"\end{tabular}", r"\end{table}", ""]
    (PAPER_TAB / "prevalence.tex").write_text("\n".join(lines) + "\n")

    sweep = DATA_DERIVED / "wp1_k_sweep.csv"
    if sweep.exists():
        sdf = pd.read_csv(sweep)
        hl = "B"
        import json

        hpath = DATA_DERIVED / "wp1_headline.json"
        if hpath.exists():
            hl = json.loads(hpath.read_text())["headline_treatment"]
        sub = sdf[sdf["treatment"] == hl]
        lines = [
            r"\begin{table}[t]",
            r"\centering",
            rf"\caption{{Headline treatment {hl}: co-activity versus slack $k$.}}",
            r"\label{tab:ksweep}",
            r"\begin{tabular}{r r r r}",
            r"\hline",
            r"$k$ (days) & PR co-active \% & Repo co-active \% ($\ge$2 PRs) & Pairs \\",
            r"\hline",
        ]
        for _, r in sub.iterrows():
            lines.append(
                f"{int(r['k_days'])} & {pct(r['pr_share'])} & {pct(r['repo_share_ge2'])} & {int(r['n_pairs']):,} \\\\"
            )
        lines += [r"\hline", r"\end{tabular}", r"\end{table}", ""]
        (PAPER_TAB / "ksweep.tex").write_text("\n".join(lines) + "\n")
    print("wrote paper/tables")


if __name__ == "__main__":
    main()
