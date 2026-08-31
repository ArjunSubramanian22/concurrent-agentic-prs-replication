"""Load snapshot extracts. Never invent files; raise if missing."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from analysis.lib.constants import DATA_DERIVED, DATA_RAW, LEGACY_REPLAY


PR_LIGHT_COLS = [
    "id",
    "number",
    "agent",
    "user",
    "user_id",
    "state",
    "created_at",
    "closed_at",
    "merged_at",
    "repo_id",
    "repo_url",
    "html_url",
]


def snapshot_meta() -> dict:
    path = DATA_DERIVED / "snapshot.json"
    if not path.exists():
        raise FileNotFoundError(f"missing {path}; run `make data`")
    return json.loads(path.read_text())


def load_pull_requests() -> pd.DataFrame:
    extract = DATA_DERIVED / "pull_request_light.parquet"
    if extract.exists():
        return pd.read_parquet(extract)
    raw = DATA_RAW / "pull_request.parquet"
    if not raw.exists():
        raise FileNotFoundError(f"missing {extract} and {raw}; run `make data`")
    df = pd.read_parquet(raw, columns=[c for c in PR_LIGHT_COLS if True])
    return df


def load_repositories() -> pd.DataFrame:
    extract = DATA_DERIVED / "repository.parquet"
    if extract.exists():
        return pd.read_parquet(extract)
    raw = DATA_RAW / "repository.parquet"
    if not raw.exists():
        raise FileNotFoundError(f"missing repository parquet; run `make data`")
    return pd.read_parquet(raw)


def load_legacy_replay() -> pd.DataFrame:
    if not LEGACY_REPLAY.exists():
        raise FileNotFoundError(LEGACY_REPLAY)
    return pd.read_csv(LEGACY_REPLAY)


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n")


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
