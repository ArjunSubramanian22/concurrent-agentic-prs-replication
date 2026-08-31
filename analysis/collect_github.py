#!/usr/bin/env python3
"""Collect GitHub PR/repo JSON into data/cache/github/. Requires GITHUB_TOKEN.

Writes data/derived/human_prs.parquet when listing succeeds. Does not
compute conflict labels. Cache files are raw API bodies.
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.lib.agent_logins import EXTRA_AGENT_LOGINS, NON_AGENT_BOT_LOGINS  # noqa: E402
from analysis.lib.constants import DATA_CACHE, DATA_DERIVED, DATA_SAMPLES, UNAVAIL  # noqa: E402
from analysis.lib.io import load_pull_requests, write_json  # noqa: E402


def token() -> str | None:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def get(url: str, tok: str) -> tuple[int, object | None, dict]:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "anonymous-saner2027-replication",
            "Authorization": f"Bearer {tok}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            body = json.loads(resp.read().decode())
            headers = {k.lower(): v for k, v in resp.headers.items()}
            return resp.status, body, headers
    except urllib.error.HTTPError as e:
        return e.code, None, {"error": e.read().decode()[:400]}
    except Exception as exc:  # noqa: BLE001
        return 0, None, {"error": str(exc)}


def agent_login_set() -> set[str]:
    pr = load_pull_requests()
    users = set(str(u).lower() for u in pr["user"].dropna().unique())
    users |= {x.lower() for x in EXTRA_AGENT_LOGINS}
    return users


def classify_login(login: str, agents: set[str]) -> str:
    if not login:
        return "author_unknown"
    low = login.lower()
    if low in agents:
        return "agent"
    if low in {x.lower() for x in NON_AGENT_BOT_LOGINS}:
        return "author_unknown"
    if low.endswith("[bot]"):
        return "author_unknown"
    return "human"


def repos_from_samples() -> list[str]:
    path = DATA_SAMPLES / "s3_matched_one.csv"
    if not path.exists():
        return []
    names = []
    with path.open() as f:
        for r in csv.DictReader(f):
            if r.get("repo"):
                names.append(r["repo"])
    return sorted(set(names))


def list_pulls(repo: str, tok: str, cache_dir: Path, max_pages: int = 15) -> tuple[list[dict], bool]:
    dest = cache_dir / repo.replace("/", "_") / "pulls.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        payload = json.loads(dest.read_text())
        if isinstance(payload, dict) and "pulls" in payload:
            return payload["pulls"], bool(payload.get("truncated"))
        if isinstance(payload, list):
            return payload, False
    out = []
    truncated = False
    page = 1
    while page <= max_pages:
        q = urllib.parse.urlencode({"state": "all", "per_page": 100, "page": page, "sort": "created", "direction": "desc"})
        url = f"https://api.github.com/repos/{repo}/pulls?{q}"
        status, body, meta = get(url, tok)
        if status == 403:
            print(f"rate limited on {repo}; stopping collection")
            truncated = True
            break
        if status != 200 or not isinstance(body, list):
            print(f"UNAVAILABLE {repo} pulls page {page}: {status} {meta.get('error', '')[:80]}")
            truncated = True
            break
        out.extend(body)
        if len(body) < 100:
            break
        if page == max_pages and len(body) == 100:
            truncated = True
        page += 1
        time.sleep(0.2)
    dest.write_text(json.dumps({"pulls": out, "truncated": truncated}))
    return out, truncated


def main() -> None:
    DATA_CACHE.mkdir(parents=True, exist_ok=True)
    tok = token()
    if not tok:
        write_json(
            DATA_CACHE.parent / "collect_status.json",
            {
                "status": UNAVAIL,
                "reason": "GITHUB_TOKEN / GH_TOKEN not set; unauthenticated collection is not attempted",
            },
        )
        print("collect UNAVAILABLE: no token")
        return
    repos = repos_from_samples()
    if not repos:
        print("UNAVAILABLE: s3_matched_one.csv missing; run wp2 first")
        return
    agents = agent_login_set()
    rows = []
    truncated_repos = []
    for i, repo in enumerate(repos, 1):
        print(f"[{i}/{len(repos)}] {repo}", flush=True)
        pulls, trunc = list_pulls(repo, tok, DATA_CACHE)
        if trunc:
            truncated_repos.append(repo)
        for p in pulls:
            login = ((p.get("user") or {}) or {}).get("login") or ""
            cls = classify_login(login, agents)
            rows.append(
                {
                    "repo": repo,
                    "number": p.get("number"),
                    "login": login,
                    "class": cls,
                    "state": p.get("state"),
                    "created_at": p.get("created_at"),
                    "closed_at": p.get("closed_at"),
                    "merged_at": p.get("merged_at"),
                    "html_url": p.get("html_url"),
                }
            )
    import pandas as pd

    df = pd.DataFrame(rows)
    outp = DATA_DERIVED / "human_prs.parquet"
    if not df.empty:
        humans = df[df["class"] == "human"]
        humans.to_parquet(outp, index=False)
        write_json(
            DATA_CACHE.parent / "collect_status.json",
            {
                "status": "ok",
                "n_repos": len(repos),
                "n_prs_listed": int(len(df)),
                "n_human": int((df["class"] == "human").sum()),
                "n_agent": int((df["class"] == "agent").sum()),
                "n_unknown": int((df["class"] == "author_unknown").sum()),
                "truncated_repos": truncated_repos,
            },
        )
        print(f"wrote {outp} humans={len(humans)}")
    else:
        write_json(DATA_CACHE.parent / "collect_status.json", {"status": UNAVAIL, "reason": "no PRs listed"})


if __name__ == "__main__":
    main()
