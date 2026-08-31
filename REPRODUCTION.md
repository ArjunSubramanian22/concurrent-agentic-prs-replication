# Reproduction

## Expected runtime

| Target | Machine | Time | Network |
|---|---|---|---|
| `make data` | laptop | ~1 min if Hugging Face is reachable; seconds if `data/raw/` is already hashed | yes, first time |
| `make analysis` (WP1, WP2, legacy) | laptop | 1–2 min | no |
| `make figures` | laptop | <1 min | no |
| `make replay` | 3707 unique pairs | hours (fetch + merge-tree per pair) | GitHub git protocol |
| `make collect` | GitHub API | quota-bound; 5000 req/h authenticated | yes, `GITHUB_TOKEN` |
| WP5 | Docker | 15 min cap per pair, ≤400 pairs | yes (image pulls) |
| `make paper` | TeX Live | ~1 min | no |

`make all` is `data` + `analysis` + `figures`. It does **not** fetch PR refs or call the GitHub API. Reviewers can check every printed RQ1 number and every legacy RQ3 number without credentials.

## Git that merge-tree depends on

Replay wraps every invocation with

```
git -c merge.conflictStyle=merge -c diff.renameLimit=400 -c merge.renames=true
```

`data/derived/environment_record.json` records `git --version` and Python. The Dockerfile pins Python 3.12.8 and the Debian git package. Local git 2.38+ is required for `merge-tree --write-tree`.

## API quota

`analysis/collect_github.py` refuses to run unauthenticated (60 req/h is not enough). Set `GITHUB_TOKEN`. Cache lives in `data/cache/github/` as raw JSON. Do not edit cached bodies.

Human PRs are not in AIDev-pop. Without this step, WP4 is UNAVAILABLE. The paper will say so rather than borrow a literature rate.

## Expected drift

PR refs are deleted. The legacy run already had 25/747 `UNAVAIL_fetch` and 6 `UNAVAIL_nobase`. A later replay of the same 747 pairs can only stay the same or lose more rows. Confirmatory rates must be recomputed from `data/replay/pairs_replay.csv`, not assumed equal to the 2026-era CSV.

Repositories can become private. Those pairs become `UNAVAIL_fetch`. WP2 does not silently replace them; the pair-selection bootstrap is how missingness is represented.

## Bit-for-bit

Integer ratios (conflict counts over evaluable) must match. GEE coefficients may differ in the fourth decimal across BLAS builds; the paper reports them from the Docker image. Wilson intervals use `scipy.stats.norm.ppf(0.975)`, not `z=1.96`. The legacy script's `z=1.96` is recomputed as a check (`legacy_rates.csv` rows `*_z1.96`).

## Anonymity audit

Before submission:

1. `grep -R -i 'affiliation\|@\|university\|acknowled' paper/` should not yield author identity.
2. README and `ANALYSIS_PLAN.md` have no personal GitHub URLs.
3. Artifact host is an anonymous snapshot, not a personal fork. Restore Zenodo at camera-ready.
