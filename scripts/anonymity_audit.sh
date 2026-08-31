#!/usr/bin/env bash
# Fail if author-identifying strings appear in the submission surfaces.
# Extend the pattern list before camera-ready; do not put real names here
# as positive matches to search for — that would encode identity in the repo.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
# Personal GitHub remotes, mailto, and the old Zenodo badge must not ship
# in the anonymous artifact.
if grep -R -n -E 'zenodo\.org/badge|github\.com/[A-Z]' \
    --include='README.md' --include='*.tex' --include='ANALYSIS_PLAN.md' \
    "$root/paper" "$root/README.md" "$root/REPRODUCTION.md" 2>/dev/null; then
  echo "possible identifying URL in submission surfaces" >&2
  exit 1
fi
echo "anonymity grep: no zenodo badge / personal GitHub in submission surfaces"
exit 0
