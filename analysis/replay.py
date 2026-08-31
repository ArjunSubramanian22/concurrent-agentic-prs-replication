#!/usr/bin/env python3
"""Resumable git merge-tree replay. Deterministic git -c flags. No invented labels."""
from __future__ import annotations

import argparse
import csv
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.lib.constants import (  # noqa: E402
    DATA_REPLAY,
    DATA_SAMPLES,
    FETCH_DEPTH,
    FETCH_DEPTH_RETRY,
    TIMEOUT_FETCH,
    TIMEOUT_FETCH_RETRY,
    TIMEOUT_MERGE_BASE,
    TIMEOUT_MERGE_TREE,
)
from analysis.lib.gitenv import git_cmd  # noqa: E402

HEADER = [
    "stratum",
    "repo",
    "prA",
    "prB",
    "agentA",
    "agentB",
    "label",
    "n_files",
    "files",
    "types",
    "sample",
]


def _run(cmd, cwd, timeout):
    try:
        return subprocess.run(
            cmd, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return None


def parse_conflict(stdout: str):
    lines = stdout.split("\n")
    files = set()
    types = []
    for ln in lines[1:]:
        if ln == "":
            break
        if "\t" in ln:
            files.add(ln.split("\t", 1)[1])
    for ln in lines:
        if ln.startswith("CONFLICT ("):
            types.append(ln[10:].split(")", 1)[0])
    return files, types


def replay_one(repo: str, a: int | str, b: int | str) -> tuple[str, int, str, str]:
    d = tempfile.mkdtemp(prefix="caprs-replay-")
    try:
        _run(git_cmd("init", "-q"), d, 20)
        _run(git_cmd("remote", "add", "origin", f"https://github.com/{repo}.git"), d, 20)
        f = _run(
            git_cmd(
                "-c",
                "protocol.version=2",
                "fetch",
                "-q",
                "--no-tags",
                "--depth",
                str(FETCH_DEPTH),
                "origin",
                f"refs/pull/{a}/head:pra",
                f"refs/pull/{b}/head:prb",
            ),
            d,
            TIMEOUT_FETCH,
        )
        if f is None or f.returncode != 0:
            return ("UNAVAIL_fetch", 0, "", "")
        mb = _run(git_cmd("merge-base", "pra", "prb"), d, TIMEOUT_MERGE_BASE)
        if mb is None or not (mb.stdout or "").strip():
            _run(
                git_cmd(
                    "-c",
                    "protocol.version=2",
                    "fetch",
                    "-q",
                    "--no-tags",
                    "--depth",
                    str(FETCH_DEPTH_RETRY),
                    "origin",
                    f"refs/pull/{a}/head:pra",
                    f"refs/pull/{b}/head:prb",
                ),
                d,
                TIMEOUT_FETCH_RETRY,
            )
            mb = _run(git_cmd("merge-base", "pra", "prb"), d, TIMEOUT_MERGE_BASE)
            if mb is None or not (mb.stdout or "").strip():
                return ("UNAVAIL_nobase", 0, "", "")
        mt = _run(git_cmd("merge-tree", "--write-tree", "pra", "prb"), d, TIMEOUT_MERGE_TREE)
        if mt is None:
            return ("UNAVAIL_timeout", 0, "", "")
        if mt.returncode == 0:
            return ("CLEAN", 0, "", "")
        if mt.returncode == 1:
            files, types = parse_conflict(mt.stdout or "")
            return ("CONFLICT", len(files), "|".join(sorted(files)), "|".join(types))
        return (f"ERR{mt.returncode}", 0, "", "")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def load_candidates(path: Path) -> list[dict]:
    rows = []
    with path.open() as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def already_done(result_path: Path) -> set[tuple[str, str, str]]:
    done = set()
    if not result_path.exists():
        return done
    with result_path.open() as f:
        for r in csv.DictReader(f):
            done.add((r["repo"], str(r["prA"]), str(r["prB"])))
    return done


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--candidates", type=Path, default=DATA_SAMPLES / "replay_candidates.csv")
    p.add_argument("--out", type=Path, default=DATA_REPLAY / "pairs_replay.csv")
    p.add_argument("--limit", type=int, default=0, help="max new pairs this invocation (0 = all)")
    p.add_argument("--sleep", type=float, default=0.0)
    args = p.parse_args()
    if not args.candidates.exists():
        print(f"UNAVAILABLE: {args.candidates} missing; run wp2 first")
        sys.exit(1)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if not args.out.exists():
        with args.out.open("w", newline="") as f:
            csv.writer(f).writerow(HEADER)
    done = already_done(args.out)
    todo = []
    for r in load_candidates(args.candidates):
        key = (r["repo"], str(r["prA"]), str(r["prB"]))
        if key in done:
            continue
        todo.append(r)
    if args.limit:
        todo = todo[: args.limit]
    print(f"to process {len(todo)} (already {len(done)})")
    n = 0
    t0 = time.time()
    for r in todo:
        lab, nf, files, types = replay_one(r["repo"], r["prA"], r["prB"])
        with args.out.open("a", newline="") as f:
            csv.writer(f).writerow(
                [
                    r.get("stratum", ""),
                    r["repo"],
                    r["prA"],
                    r["prB"],
                    r.get("agentA", ""),
                    r.get("agentB", ""),
                    lab,
                    nf,
                    files,
                    types,
                    r.get("sample", ""),
                ]
            )
        n += 1
        if n % 10 == 0:
            print(f"  ...{n} done ({time.time() - t0:.0f}s) last={r['repo']} {lab}")
        if args.sleep:
            time.sleep(args.sleep)
    print(f"BATCH done={n} elapsed={time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
