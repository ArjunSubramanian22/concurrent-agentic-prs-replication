#!/usr/bin/env python3
"""Assemble the anonymous NeurIPS OSF zip from the three source trees.

Run from the measurement repo (this file's parents[1]):

    python scripts/build_anonymous_osf.py

Writes:
  neurips2026-anonymous/          unpacked tree (gitignored)
  dist/neurips2026-anonymous-osf.zip
and copies the zip to ~/Downloads when that directory exists.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import stat
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "neurips2026-anonymous"
DIST = ROOT / "dist"
ZIP_NAME = "neurips2026-anonymous-osf.zip"
PACKAGING = ROOT / "packaging" / "osf"

PAPER_CODE = Path("/tmp/caprs-zips/neurips_paper_code-main")
MAIN_CODE = Path("/tmp/caprs-zips/neurips_main_code-main")

SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".mplconfig",
    "htmlcov",
    "legacy_zip",
    "neurips2026-anonymous",
    "packaging",
    "dist",
    "t2_work",
    "lineage_cache",
    "repo_cache",
    "git_repos",
    "ablation_scratch",
    "patch_cache",
}
SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".mplconfig",
    "htmlcov",
    "legacy_zip",
    "neurips2026-anonymous",
    "packaging",
    "dist",
    "t2_work",
    "lineage_cache",
    "repo_cache",
    "git_repos",
    "ablation_scratch",
    "patch_cache",
}
SKIP_FILE_NAMES = {
    ".DS_Store",
    ".coverage",
    "build_anonymous_osf.py",
    "t3_sim_check.csv",
    # Optional LLM T2 bundle (~6MB gzipped). Rebuild with t2_groundtruth.py after replay.
    "t2_hunk_bundle.jsonl.gz",
}
SKIP_SUFFIXES = {".pyc", ".egg-info"}
SKIP_MANUSCRIPT_PDF = {"vericodegen_paper_draft.pdf", "main.pdf"}

# Applied to text files only. Do not ship these patterns in the zip.
TEXT_REPLACEMENTS = [
    ("Xu, George and Subramanian, Arjun and Karthik, Nithilan", "Anonymous"),
    (r"G.~Xu, A.~Subramanian, N.~Karthik", "Anonymous"),
    ("George Xu, Arjun Subramanian, Nithilan Karthik", "Anonymous authors"),
    ("Xu, Subramanian & Karthik", "prior measurement study"),
]
BODY_REPLACEMENTS = [
    (
        r"in the corpus of Xu et al\.~\\cite\{xu2026\}",
        r"in a prior measurement corpus~\\cite{xu2026}",
    ),
    (
        r"Xu et al\.~\\cite\{xu2026\} measure pairwise conflicts between concurrent agent PRs and release",
        r"Prior measurement work~\\cite{xu2026} measures pairwise conflicts between concurrent agent PRs and releases",
    ),
    (
        r"the public replication data of Xu et al\.",
        r"a public 747-pair merge-tree replication",
    ),
]

IDENTITY_NEEDLES = (
    "Subramanian",
    "ArjunSubramanian",
    "George Xu",
    "Nithilan",
    "/Users/Arjun",
)

TEXT_SUFFIXES = {
    ".md",
    ".tex",
    ".bib",
    ".py",
    ".yml",
    ".yaml",
    ".txt",
    ".toml",
    ".sh",
    ".ini",
    ".cfg",
    ".rst",
}
JSON_SANITIZE_NAMES = {"manifest.json", "environment_record.json", "pyproject.toml"}


def is_text_path(path: Path) -> bool:
    if path.name in {".gitignore", ".dockerignore", "WAITING_FOR_HUMAN_LABELS"}:
        return True
    if path.name in JSON_SANITIZE_NAMES:
        return True
    return path.suffix.lower() in TEXT_SUFFIXES


def skip_copy(path: Path) -> bool:
    parts = set(path.parts)
    if parts & SKIP_DIR_NAMES:
        return True
    if path.name in SKIP_FILE_NAMES or path.name in SKIP_MANUSCRIPT_PDF:
        return True
    if path.suffix in SKIP_SUFFIXES:
        return True
    if path.name.endswith(".parquet") and "raw" in path.parts:
        return True
    # Historical workshop dumps superseded by semantic_conflicts/results/v1/.
    if path.name in {"judging_frame.csv.gz", "pool_flags.csv.gz"} and path.parent.name == "results":
        return True
    return False


def copy_tree(src: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if skip_copy(item):
            continue
        target = dest / item.name
        if item.is_dir():
            copy_tree(item, target)
        elif item.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def sanitize_text(text: str) -> str:
    for old, new in TEXT_REPLACEMENTS:
        text = text.replace(old, new)
    for pat, repl in BODY_REPLACEMENTS:
        text = re.sub(pat, repl, text)
    text = re.sub(r"/Users/[^\s\"']+", "REDACTED_HOME", text)
    text = re.sub(
        r'"python_executable":\s*"REDACTED_HOME[^"]*"',
        '"python_executable": ".venv/bin/python"',
        text,
    )
    text = re.sub(
        r'"config_path":\s*"REDACTED_HOME[^"]*"',
        '"config_path": "semantic_conflicts/configs/v1.yaml"',
        text,
    )
    text = re.sub(
        r'"git_commit":\s*"[0-9a-f]{7,40}"',
        '"git_commit": "omitted-for-anonymous-review"',
        text,
    )
    return text


def sanitize_tree(root: Path) -> None:
    for path in root.rglob("*"):
        if not path.is_file() or not is_text_path(path):
            continue
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        new = sanitize_text(text)
        if new != text:
            path.write_text(new, encoding="utf-8")


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def patch_t3(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')",
        "D = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))\n"
        "MG = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))",
    )
    text = text.replace(
        "ref = pd.read_csv(f'{D}/derived/paper_outputs/t3_episode_results.csv') if a.check else None",
        "ref = pd.read_csv(os.path.join(MG, 'results', 't3_episode_results.csv')) if a.check else None",
    )
    text = text.replace(
        "out.to_csv('t3_sim_results.csv', index=False)",
        "out.to_csv(os.path.join(MG, 'results', 't3_sim_check.csv'), index=False)",
    )
    text = text.replace(
        "compare with derived/paper_outputs/t3_episode_results.csv",
        "compare with mergegym/results/t3_episode_results.csv",
    )
    path.write_text(text, encoding="utf-8")


def patch_vendor(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    needle = "    DATA_DERIVED.mkdir(parents=True, exist_ok=True)\n"
    insert = '''    light = DATA_DERIVED / "pull_request_light.parquet"
    repo_extract = DATA_DERIVED / "repository.parquet"
    snap = DATA_DERIVED / "snapshot.json"
    if light.exists() and repo_extract.exists() and snap.exists():
        print("using committed extracts; skip Hugging Face download")
        return

'''
    if needle not in text:
        raise SystemExit(f"vendor_snapshot.py: expected mkdir block missing in {path}")
    path.write_text(text.replace(needle, needle + insert, 1), encoding="utf-8")


def patch_gitenv(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        '"python_executable": sys.executable,',
        '"python_executable": Path(sys.executable).name,',
    )
    path.write_text(text, encoding="utf-8")


def patch_paths_py(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    old = """        if (parent / ".git").exists() and (parent / "semantic_conflicts").is_dir() and (
            parent / "data"
        ).is_dir():
            return parent"""
    new = """        if (parent / ".artifact_root").exists() and (parent / "semantic_conflicts").is_dir():
            return parent
        if (parent / ".git").exists() and (parent / "semantic_conflicts").is_dir() and (
            parent / "data"
        ).is_dir():
            return parent"""
    if old not in text:
        raise SystemExit("paths.py marker block not found")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_conflictbench_makefile(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace("PYTHON ?= python3.13", "PYTHON ?= python3")
    path.write_text(text, encoding="utf-8")


def copy_packaging_overlay() -> None:
    mapping = {
        "README.md": DEST / "README.md",
        "OSF.md": DEST / "OSF.md",
        "REPRODUCE.md": DEST / "REPRODUCE.md",
        "ANONYMITY.md": DEST / "ANONYMITY.md",
        "LICENSE": DEST / "LICENSE",
        "Makefile": DEST / "Makefile",
        "pyproject.toml": DEST / "pyproject.toml",
        "requirements.txt": DEST / "requirements.txt",
        "environment.yml": DEST / "environment.yml",
        "Dockerfile": DEST / "Dockerfile",
        ".gitignore": DEST / ".gitignore",
        "pytest.ini": DEST / "pytest.ini",
        "measurement_README.md": DEST / "measurement" / "README.md",
        "conflictbench_README.md": DEST / "conflictbench" / "README.md",
        "mergegym_README.md": DEST / "mergegym" / "README.md",
    }
    for src_name, dest in mapping.items():
        src = PACKAGING / src_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    (DEST / "scripts").mkdir(parents=True, exist_ok=True)
    shutil.copy2(PACKAGING / "scripts" / "anonymity_audit.sh", DEST / "scripts" / "anonymity_audit.sh")
    dest_mode = os.stat(DEST / "scripts" / "anonymity_audit.sh").st_mode
    os.chmod(DEST / "scripts" / "anonymity_audit.sh", dest_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    tests_dest = DEST / "tests"
    tests_dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PACKAGING / "tests" / "test_layout.py", tests_dest / "test_layout.py")
    shutil.copy2(PACKAGING / "tests" / "test_anonymity.py", tests_dest / "test_anonymity.py")


def identity_scan(root: Path) -> list[str]:
    hits: list[str] = []
    skip_parts = {"data", "derived", "results", "samples"}
    for path in root.rglob("*"):
        if not path.is_file() or not is_text_path(path):
            continue
        if any(p in skip_parts for p in path.parts) and path.suffix.lower() in {".csv", ".json", ".gz"}:
            # Still scan manifests and markdown under results.
            if path.suffix.lower() == ".json" and path.name in {"manifest.json", "environment_record.json"}:
                pass
            elif path.suffix.lower() != ".md":
                continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for needle in IDENTITY_NEEDLES:
            if needle in text:
                hits.append(f"{path.relative_to(root)}: {needle}")
        if re.search(r"\bArjun\b", text) and path.suffix not in {".csv"}:
            hits.append(f"{path.relative_to(root)}: word Arjun")
    return hits


def zip_tree(src: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()
    skip_parts = {".git", ".venv", ".pytest_cache", "__pycache__"}
    skip_names = {
        ".DS_Store",
        "t3_sim_check.csv",
        "t2_hunk_bundle.jsonl.gz",
        "vericodegen_paper_draft.pdf",
        "main.pdf",
    }
    with zipfile.ZipFile(
        zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as zf:
        for path in sorted(src.rglob("*")):
            if path.is_dir():
                continue
            if skip_parts & set(path.parts):
                continue
            if path.name in skip_names:
                continue
            if path.name in {"judging_frame.csv.gz", "pool_flags.csv.gz"} and path.parent.name == "results":
                continue
            arc = Path(src.name) / path.relative_to(src)
            zf.write(path, arc.as_posix())


def main() -> None:
    for required in (PAPER_CODE, MAIN_CODE, PACKAGING, ROOT / "analysis"):
        if not required.exists():
            raise SystemExit(f"missing source: {required}")

    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)

    # Shared 577k corpus + MergeGym + Semantic Conflicts.
    for name in ("data", "derived", "common", "mergegym", "semantic_conflicts"):
        copy_tree(PAPER_CODE / name, DEST / name)
    if (PAPER_CODE / ".github").exists():
        copy_tree(PAPER_CODE / ".github", DEST / ".github")

    # ConflictBench.
    copy_tree(MAIN_CODE, DEST / "conflictbench")

    # Measurement study (this repo), nested so ROOT in constants.py is measurement/.
    meas = DEST / "measurement"
    meas.mkdir()
    for name in (
        "ANALYSIS_PLAN.md",
        "claims.csv",
        "REPRODUCTION.md",
        "Makefile",
        "Dockerfile",
        "environment.yml",
        "requirements.txt",
        "pytest.ini",
        "rq3_merge_replay_full.csv",
        "rq3_taxonomy_full.csv",
        "rq3_rates_full.csv",
        "build_sample.py",
        "analyze.py",
        "finish_missing.py",
        "make_figures2.py",
        "run_replay.py",
    ):
        src = ROOT / name
        if src.exists():
            shutil.copy2(src, meas / name)
    for dirname in ("analysis", "tests", "scripts", "paper", "config"):
        copy_tree(ROOT / dirname, meas / dirname)
    copy_tree(ROOT / "data", meas / "data")

    # Marker so path walkers find the zip root without a .git directory.
    (DEST / ".artifact_root").write_text("neurips2026-anonymous\n", encoding="utf-8")

    copy_packaging_overlay()
    (DEST / "scripts").mkdir(exist_ok=True)
    # Overlay already copied anonymity_audit.sh.

    patch_t3(DEST / "mergegym" / "scripts" / "t3_simulator.py")
    patch_vendor(DEST / "measurement" / "scripts" / "vendor_snapshot.py")
    patch_gitenv(DEST / "measurement" / "analysis" / "lib" / "gitenv.py")
    patch_paths_py(DEST / "semantic_conflicts" / "src" / "semantic_conflicts" / "paths.py")
    patch_conflictbench_makefile(DEST / "conflictbench" / "Makefile")

    # Measurement Makefile already sets PYTHONPATH=$(CURDIR); keep it.
    sanitize_tree(DEST)

    env_rec = DEST / "measurement" / "data" / "derived" / "environment_record.json"
    if env_rec.exists():
        obj = json.loads(env_rec.read_text(encoding="utf-8"))
        obj["python_executable"] = "python"
        env_rec.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    hits = identity_scan(DEST)
    if hits:
        print("IDENTITY LEAKS:", file=sys.stderr)
        print("\n".join(hits[:80]), file=sys.stderr)
        raise SystemExit(1)

    zip_path = DIST / ZIP_NAME
    zip_tree(DEST, zip_path)
    downloads = Path.home() / "Downloads" / ZIP_NAME
    try:
        shutil.copy2(zip_path, downloads)
        copied = downloads
    except OSError:
        copied = None

    nbytes = zip_path.stat().st_size
    print(f"unpacked: {DEST}")
    print(f"zip:      {zip_path} ({nbytes / 1e6:.1f} MB)")
    if copied:
        print(f"copy:     {copied}")
    print("identity scan: clean")


if __name__ == "__main__":
    main()
