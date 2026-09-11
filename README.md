# Concurrent Agentic Pull Requests

**NeurIPS 2026 dual-anonymous OSF package:** upload `dist/neurips2026-anonymous-osf.zip` (also copied to `~/Downloads/`). Rebuild from the three source trees with `.venv/bin/python scripts/build_anonymous_osf.py`. Reviewer instructions are in the zip: `README.md` and `OSF.md`.

This git working copy is the measurement study (SANER 2027 Agentic AI4SE). The zip combines it with ConflictBench, Semantic Conflicts, and MergeGym over the shared 577k-pair corpus. Do not upload this git remote; the zip has no `.git` and no author names.

---

Anonymous replication package for a SANER 2027 Agentic AI4SE submission.

Anonymous replication package for a SANER 2027 Agentic AI4SE submission.

**Title:** *Merge Conflicts Among Concurrent Agentic Pull Requests: Prevalence, Composition, and a Human Baseline*

Every number in the manuscript is emitted by a committed script from committed data. If a computation has not been run, the paper prints **UNAVAILABLE**. It does not invent a value.

The analysis plan (`ANALYSIS_PLAN.md`) was committed **before** any WP3–WP6 model. That commit is the pre-registration.

## What this package already reproduces

From `make data analysis figures` (no GitHub token, no Docker, no TeX):

- RQ1 co-activity under censoring treatments A/B/C and a $k$-sweep
- WP2 samples (uniform pair within repo; designed match)
- Re-derivation of the legacy 747-pair replay (rates, taxonomy, McNemar, composition)
- Figures in `paper/figures/` and macros in `paper/generated/macros.tex`

## What is still live (not in `make all`)

| Step | Command | Status in this snapshot |
|---|---|---|
| Confirmatory merge-tree replay | `make replay` | needs GitHub fetch of PR refs (~3707 unique pairs) |
| GitHub covariates + human PRs | `make collect` | needs `GITHUB_TOKEN` |
| Build/test layer | `python analysis/wp5_build_test.py` | needs Docker |
| PDF | `make paper` | needs TeX Live + IEEEtran |

## Commands

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
export PYTHONPATH=.
make all          # data, analysis, figures
make test
make replay       # live git fetch; optional --limit via analysis/replay.py
make collect      # live GitHub API
make paper        # pdflatex, if installed
```

Docker (pinned Python 3.12.8 and Debian git):

```bash
docker build -t caprs .
docker run --rm -v "$PWD":/work caprs make all
```

## Data

- `data/derived/pull_request_light.parquet` — column-pruned AIDev-pop PRs (no title/body)
- `data/derived/repository.parquet` — AIDev-pop repositories
- `data/derived/snapshot.json` — SHA-256 of the Hugging Face files, row counts, agent histogram
- `rq3_merge_replay_full.csv` — legacy earliest-pair replay (747 rows)

Raw Hugging Face parquet is downloaded by `make data` if missing. Expected SHA-256 values are in `scripts/vendor_snapshot.py`.

## Anonymity

This README, the manuscript, and artifact URLs contain no author names. The camera-ready version restores a Zenodo DOI. Do not point reviewers at a deanonymizing GitHub remote.

## Layout

```
ANALYSIS_PLAN.md     pre-registered plan
claims.csv           claim → script → output → paper location
analysis/            WP1–WP6, replay, emitters
data/derived/        committed extracts and tables
data/samples/        WP2 pair draws
paper/               IEEEtran source (10pt, conference, no compsoc)
legacy scripts at repo root (build_sample.py, …) are the original artifact
```
