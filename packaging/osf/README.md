# Concurrent agentic pull requests — anonymous NeurIPS 2026 artifact

**Anonymous supplementary.** No author names, institutions, personal GitHub remotes, or camera-ready DOIs appear in this tree. Upload the zip as-is to OSF (or OpenReview) for dual-anonymous review. See `OSF.md`.

This package is one codebase and one frozen corpus supporting four manuscripts that share the same measurement stack:

| Folder | Manuscript | What it is |
|---|---|---|
| `measurement/` | *Merge Conflicts Among Concurrent Agentic Pull Requests* | Co-activity under censoring; 747-pair `git merge-tree` replay (labels ConflictBench uses) |
| `conflictbench/` | *The Conflict Isn't in the Diff* | Lineage-aware prediction on the 715-pair labeled replay |
| `semantic_conflicts/` | *Beyond File Overlap* | Semantic-conflict candidate pools on 577,045 co-active pairs |
| `mergegym/` | *MergeGym* | Predict / resolve / schedule tracks on the same 577k pairs |

Shared tables live at the repository root (`data/`, `derived/`). Paper-specific code never reaches into another paper's `results/` except through those shared tables.

**Do not invent numbers.** Frozen CSVs and JSON are the source of truth. If a live step has not been run, scripts print `UNAVAILABLE` (measurement) or leave `WAITING_FOR_HUMAN_LABELS` (semantic conflicts). Null results are results.

## Reviewer path (offline, no tokens)

Python 3.10–3.12. No GitHub token, no Claude CLI, no TeX, no Docker.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e ".[dev]"   # Semantic Conflicts package
export PYTHONPATH=measurement:semantic_conflicts/src:.
make check
```

`make check` regenerates ConflictBench `numbers.json` from committed predictions, re-runs MergeGym T3 observed/FIFO/oracle against the released episode table, and runs unit tests. It does **not** clone repositories, call the GitHub API, or invoke an LLM.

Expected wall time on a laptop: a few minutes (T3 loads the 577k-pair table once; ConflictBench bootstrap is 2,000 resamples with a fixed seed).

## What is frozen vs live

| Already in the zip | Live / optional |
|---|---|
| 577,045 labeled pairs (`derived/pairs_labeled.csv.gz`) | MergeGym T2 blob-less clones (`mergegym/scripts/t2_replay.py`) |
| 747-row merge-tree replay (`measurement/rq3_merge_replay_full.csv`) | Measurement confirmatory replay (`make -C measurement replay`) |
| ConflictBench pairs, lineage features, verified LLM preds | `GITHUB_TOKEN` collection; Claude Code LLM re-runs |
| MergeGym T1/T2/T3 result tables | T3 *predictor-gate trainer* (weights are in `mergegym/results/t3_summary.json`; the trainer script was not in the source trees) |
| Semantic Conflicts v1 pools, frame, calibration sheet | Human gold labels (`WAITING_FOR_HUMAN_LABELS`); LLM judge |

## Layout

```
data/                      AIDev-pop extracts for the 577k-pair papers
derived/                   pairs_labeled.csv.gz and related joins
common/                    pair enumeration + 55-claim verification log
measurement/               747-pair study (analysis, extracts, IEEEtran source)
conflictbench/             lineage benchmark (metrics.py → numbers.json)
semantic_conflicts/        installable package + v1 results
mergegym/                  T1/T2/T3 scripts and released result tables
papers/                    convenience copies of TeX (same files as in each folder)
```

## Anonymity

- Author blocks are `Anonymous`.
- Self-citations of the prior measurement study are third-person with the author list omitted from this zip (`Anonymous` in `.bib` / `\bibitem`).
- Absolute machine paths and personal remotes are stripped.
- This zip contains no `.git` directory (commit metadata would identify the submitter).

Run `make audit` before you upload. Camera-ready restores names and a DOI; do not restore them in the review zip.
