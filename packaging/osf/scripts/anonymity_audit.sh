#!/usr/bin/env bash
# Fail if the anonymous zip still contains path leaks or identifying URLs.
# Do not add author surnames as patterns; that would encode identity here.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
fail=0

if [[ -d "$root/.git" ]]; then
  echo "FAIL: .git must not ship in the anonymous zip" >&2
  fail=1
fi

# Home directories, Windows user profiles, mailto, Zenodo badge, personal GitHub.
# /home/repro is the anonymous Docker HOME and is allowed.
if grep -R -n -E '/Users/|C:\\Users\\|mailto:|zenodo\.org/badge|github\.com/[A-Z]' \
    --exclude-dir='.venv' --exclude-dir='.git' --exclude-dir='__pycache__' \
    --exclude-dir='data' --exclude-dir='derived' --exclude-dir='results' \
    --exclude-dir='samples' --exclude='*.png' --exclude='*.pdf' --exclude='*.parquet' \
    --exclude='*.gz' --exclude='*.zip' --exclude='*.csv' --exclude='*.jsonl' \
    --include='*.md' --include='*.tex' --include='*.bib' --include='*.py' \
    --include='*.yml' --include='*.yaml' --include='*.txt' --include='*.toml' \
    --include='*.sh' --include='*.json' --include='Makefile' --include='Dockerfile' \
    --include='*.ini' \
    "$root" 2>/dev/null \
    | grep -v 'scripts/anonymity_audit.sh' \
    | grep -v 'ANONYMITY.md' \
    | grep -v 'OSF.md' \
    | grep -v 'tests/test_anonymity.py' ; then
  echo "FAIL: identifying path or URL in artifact" >&2
  fail=1
fi

if [[ "$fail" -ne 0 ]]; then
  exit 1
fi
echo "anonymity audit: no home paths, mailto, Zenodo badge, or personal GitHub URLs"
exit 0
