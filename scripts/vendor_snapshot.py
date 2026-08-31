#!/usr/bin/env python3
"""Pin the AIDev-pop snapshot: hashes, row counts, column-pruned extract."""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.lib.constants import DATA_DERIVED, DATA_RAW  # noqa: E402
from analysis.lib.io import PR_LIGHT_COLS  # noqa: E402

HF_SOURCE = "https://huggingface.co/datasets/hao-li/AIDev/resolve/main/{name}"
FILES = {
    "pull_request.parquet": "c0b8e81e1d099905ef9ea420bf907d45179771ff5972afce6c219d8cafcef3e8",
    "repository.parquet": "a08e34be4921c708be88a4ebd9e275b32f37fd442bb2770c0b69c94834dc6aa7",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(name: str) -> Path:
    dest = DATA_RAW / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = HF_SOURCE.format(name=name)
    if dest.exists() and sha256(dest) == FILES[name]:
        return dest
    try:
        import urllib.request

        print(f"downloading {url}")
        urllib.request.urlretrieve(url, dest)
    except Exception as exc:  # noqa: BLE001
        print(f"UNAVAILABLE: could not download {name}: {exc}")
        sys.exit(1)
    return dest


def main() -> None:
    import pandas as pd

    DATA_DERIVED.mkdir(parents=True, exist_ok=True)
    meta = {
        "source": "hao-li/AIDev AIDev-pop (pull_request.parquet, repository.parquet)",
        "huggingface_url": "https://huggingface.co/datasets/hao-li/AIDev",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "expected_sha256": FILES,
        "actual_sha256": {},
        "hash_ok": {},
    }
    for name, expected in FILES.items():
        path = DATA_RAW / name
        if not path.exists():
            download(name)
        digest = sha256(path)
        meta["actual_sha256"][name] = digest
        meta["hash_ok"][name] = digest == expected
        if digest != expected:
            print(f"WARNING: {name} hash {digest} != expected {expected}")

    pr = pd.read_parquet(DATA_RAW / "pull_request.parquet")
    repo = pd.read_parquet(DATA_RAW / "repository.parquet")
    light_cols = [c for c in PR_LIGHT_COLS if c in pr.columns]
    light = pr[light_cols]
    light_path = DATA_DERIVED / "pull_request_light.parquet"
    repo_path = DATA_DERIVED / "repository.parquet"
    light.to_parquet(light_path, index=False)
    repo.to_parquet(repo_path, index=False)
    meta["n_pull_requests"] = int(len(pr))
    meta["n_repositories"] = int(len(repo))
    meta["n_repo_ids_in_prs"] = int(pr["repo_id"].nunique())
    meta["agents"] = {str(k): int(v) for k, v in pr["agent"].value_counts().items()}
    meta["created_at_min"] = str(pr["created_at"].min())
    meta["created_at_max"] = str(pr["created_at"].max())
    meta["light_columns"] = light_cols
    meta["light_sha256"] = sha256(light_path)
    meta["repository_extract_sha256"] = sha256(repo_path)
    (DATA_DERIVED / "snapshot.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: meta[k] for k in ("n_pull_requests", "n_repositories", "hash_ok", "agents")}, indent=2))
    if not all(meta["hash_ok"].values()):
        sys.exit(2)


if __name__ == "__main__":
    main()
