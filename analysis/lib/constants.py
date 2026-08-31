"""Frozen constants. Edits here after the analysis-plan commit are deviations."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MASTER_SEED = 42
SEED_INTRA_REPOS = 42
SEED_INTRA_PAIRS = 42
SEED_MATCHED = 43
SEED_BOOTSTRAP_BASE = 1042
BOOTSTRAP_B = 200
SEED_WP5 = 2026
SEED_WP6 = 7
MAX_PAIRS_PER_REPO_STRATUM = 5
INTRA_REPO_DRAW = 625

K_TABLE = (0, 1, 3, 7)
K_CURVE = tuple([0.0] + [x / 2 for x in range(1, 29)])  # 0, 0.5, ..., 14

HEADLINE_ABS_PP = 0.05
HEADLINE_REL = 0.10

FETCH_DEPTH = 80
FETCH_DEPTH_RETRY = 600
TIMEOUT_FETCH = 90
TIMEOUT_FETCH_RETRY = 150
TIMEOUT_MERGE_BASE = 15
TIMEOUT_MERGE_TREE = 60

GIT_CONFIG = {
    "merge.conflictStyle": "merge",
    "diff.renameLimit": "400",
    "merge.renames": "true",
    "diff.renames": "true",
}

DATA_RAW = ROOT / "data" / "raw"
DATA_DERIVED = ROOT / "data" / "derived"
DATA_REPLAY = ROOT / "data" / "replay"
DATA_SAMPLES = ROOT / "data" / "samples"
DATA_CACHE = ROOT / "data" / "cache" / "github"
PAPER_GEN = ROOT / "paper" / "generated"
PAPER_FIG = ROOT / "paper" / "figures"
PAPER_TAB = ROOT / "paper" / "tables"
LEGACY_REPLAY = ROOT / "rq3_merge_replay_full.csv"

UNAVAIL = "UNAVAILABLE"
