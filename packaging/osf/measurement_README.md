# Measurement component (anonymous)

747-pair `git merge-tree` replay and co-activity measurement under censoring treatments A/B/C.

This folder is self-contained: `analysis/lib/constants.py` resolves `ROOT` to **this directory**, not the zip root. Run commands from here, or `make -C measurement …` from the zip root.

```bash
export PYTHONPATH=.
make all     # extracts + WP1 + WP2 + legacy re-derivation + figures (no GitHub)
make test
```

Live optional steps (`make replay`, `make collect`, WP5 Docker) are documented in `REPRODUCTION.md`. Confirmatory rates stay `UNAVAILABLE` until those steps finish; the paper macros print that string rather than inventing a value.

The committed legacy file `rq3_merge_replay_full.csv` is the execution oracle ConflictBench uses.
