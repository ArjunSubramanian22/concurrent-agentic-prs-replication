# ConflictBench (anonymous)

Lineage-aware detection of merge conflicts between concurrent agent PRs. Labels come from the 747-pair merge-tree replay in `../measurement/rq3_merge_replay_full.csv` (715 pairs after one deleted PR).

Python 3.10+ (`python3`). `pip install -r ../requirements.txt`.

## Frozen inputs (in this folder)

- `benchmark_pairs.jsonl` — 715 labeled pairs (167 CONFLICT / 548 CLEAN)
- `predictions_claude.jsonl` / `predictions_haiku.jsonl` — verified `claude-haiku-4-5-20251001`
- `lineage_features.jsonl` — GitHub compare-API features (714/715; one HTTP 422)
- `ablation_results.csv` — patch-replay ablation (resumable)

## Offline

```bash
python3 metrics.py                 # numbers.json + paper/numbers.tex (seed 0, 2000 bootstrap)
python3 figures.py                 # optional; needs matplotlib
```

`make metrics` from this folder, or `make conflictbench-metrics` from the zip root. Running `metrics.py` twice is bit-identical.

## Live / optional

```bash
python3 lineage_touch.py           # resumable lineage_cache/ (GitHub API)
python3 ablation_patch_replay.py   # clones; PATCH_FAILED is never folded in
python3 run_llm_baseline.py …      # requires Claude Code CLI; --model is required
```

A prior narrative draft with incorrect model names is **not** in this zip.
