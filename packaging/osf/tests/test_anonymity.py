"""Path-leak scan. Surnames are not listed here on purpose."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {
    ".venv",
    "__pycache__",
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    "data",
    "derived",
    "results",
    "samples",
}
SKIP_SUFFIX = {".png", ".pdf", ".parquet", ".gz", ".zip", ".pyc", ".csv", ".jsonl"}
NEEDLES = ("/Users/", "C:\\Users\\", "mailto:", "zenodo.org/badge")
SKIP_FILES = {"anonymity_audit.sh", "ANONYMITY.md", "OSF.md", "test_anonymity.py"}


def test_no_home_paths_or_mailto_in_text():
    hits = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(p in SKIP_DIRS for p in path.parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIX:
            continue
        if path.name in SKIP_FILES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for needle in NEEDLES:
            if needle in text:
                hits.append(f"{path.relative_to(ROOT)}: {needle}")
    assert hits == [], "\n".join(hits[:40])
