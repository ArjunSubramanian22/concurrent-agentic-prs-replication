# MergeGym (anonymous)

Predict (T1), resolve (T2), and schedule (T3) around conflicts between concurrent agent PRs, over `derived/pairs_labeled.csv.gz`.

Scripts resolve the zip root as two directories above `mergegym/scripts/`. Override with `MG_ROOT`.

```bash
python3 mergegym/scripts/t3_simulator.py --check
```

`--check` replays observed / FIFO / oracle on all 97 episodes and compares to `mergegym/results/t3_episode_results.csv`.

T2 replay clones repositories (network, ~4 GB):

```bash
python3 mergegym/scripts/t2_replay.py --subset core
```

The T3 predictor-gate **trainer** is not in this tree. Gate mechanics are in `t3_simulator.py`; fitted weights are in `results/t3_summary.json`. Predictor-gated rows in `t3_episode_results.csv` are the released run.

LLM scripts require Claude Code CLI and are optional. Released T1/T2 tables are already in `results/`.
