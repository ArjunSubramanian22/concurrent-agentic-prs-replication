"""Smoke tests for the unified anonymous artifact layout."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_shared_corpus_present():
    assert (ROOT / "derived" / "pairs_labeled.csv.gz").is_file()
    assert (ROOT / "data" / "pr_files.csv.gz").is_file()
    assert (ROOT / "data" / "pr_texts.csv.gz").is_file()


def test_four_components_present():
    assert (ROOT / "measurement" / "rq3_merge_replay_full.csv").is_file()
    assert (ROOT / "conflictbench" / "benchmark_pairs.jsonl").is_file()
    assert (ROOT / "semantic_conflicts" / "results" / "v1" / "manifest.json").is_file()
    assert (ROOT / "mergegym" / "results" / "t3_episode_results.csv").is_file()


def test_no_git_directory():
    assert not (ROOT / ".git").exists()


def test_conflictbench_has_no_legacy_zip():
    assert not (ROOT / "conflictbench" / "paper" / "legacy_zip").exists()
