# Reproduction

## Software

- Python **3.10, 3.11, or 3.12** (3.13 may work; it is not the advertised range).
- `git` 2.38+ only if you run merge-tree replay.
- Optional: TeX Live / tectonic for PDFs; Docker for measurement WP5; `GITHUB_TOKEN` for live GitHub; Claude Code CLI for LLM rows.

Install:

```bash
python3 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e ".[dev]"
```

`environment.yml` pins a conda stack at Python 3.12. The Dockerfile is the bit-for-bit image for `make check`.

## Targets

| Command | Network | What it does |
|---|---|---|
| `make check` | no | tests + ConflictBench metrics + T3 `--check` + anonymity audit |
| `make -C measurement all` | no, if extracts present | WP1, WP2, legacy re-derivation, figures |
| `python -m semantic_conflicts.pipeline deterministic` | no | rebuild Semantic Conflicts v1 from `data/` + `derived/` (minutes) |
| `python mergegym/scripts/t3_simulator.py --check` | no | 97 episodes vs `mergegym/results/t3_episode_results.csv` |
| `make -C conflictbench metrics` | no | `numbers.json` + `paper/numbers.tex` |
| `make -C measurement replay` | GitHub git | confirmatory merge-tree (~3707 candidate pairs) |
| `make -C measurement collect` | GitHub API | covariates + human PRs; refuses unauthenticated |
| `mergegym/scripts/t2_replay.py` | GitHub git | partial clones into `mergegym/t2_work/` (~4 GB) |
| LLM scripts | Claude Code | MergeGym T1/T2, Semantic Conflicts judge, ConflictBench sweep |

## Bit-for-bit notes

- ConflictBench `metrics.py` uses seed `0` and 2,000 bootstrap replicates. Running twice is identical.
- MergeGym T3 `--check` compares observed/FIFO/oracle to the released CSV. Conflict counts match exactly (0/291 mismatches). `delay_days_per_pr` can differ at `1e-3` on 2/291 rows across pandas versions; that is printed, not treated as a hard failure. Predictor-gated rows are the released run; the IRLS trainer is not in this tree. Weights are recorded in `mergegym/results/t3_summary.json`.
- Measurement Wilson intervals use `scipy.stats.norm.ppf(0.975)`, not `z=1.96`. A `z=1.96` recompute is stored as `*_z1.96` rows for the legacy CSV.
- Semantic Conflicts `manifest.json` records input SHA-256. `pipeline check` regenerates and confirms `pool_counts` consistency. Gold labels are absent (`WAITING_FOR_HUMAN_LABELS`).
- Replay wraps git with `merge.conflictStyle=merge`, `diff.renameLimit=400`, `merge.renames=true`.

## Expected drift on live GitHub

PR refs disappear. The 747-pair file already has fetch/base unavailability. A later replay of the same pairs can only stay the same or lose rows. Do not paste 2026-era rates over a new `pairs_replay.csv`.

## What was not in the source trees

- MergeGym T3 predictor-gate **training** script (mechanics are in `t3_simulator.py`; weights are in JSON).
- AIDev per-commit patch table (not redistributable here).
- Human gold labels for Semantic Conflicts.
- Raw Hugging Face `pull_request.parquet` (~1.5 GB). Measurement ships a column-pruned extract. `scripts/vendor_snapshot.py` downloads the raw files only if that extract is missing.
