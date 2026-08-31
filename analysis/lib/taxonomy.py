"""File-category and conflict-type taxonomy. Frozen with ANALYSIS_PLAN.md."""
from __future__ import annotations

import re
from collections import Counter

MANIFEST_BASE = {
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "npm-shrinkwrap.json",
    "cargo.toml",
    "cargo.lock",
    "go.mod",
    "go.sum",
    "poetry.lock",
    "pipfile",
    "pipfile.lock",
    "uv.lock",
    "gemfile",
    "gemfile.lock",
    "pom.xml",
    "composer.json",
    "composer.lock",
    "pubspec.yaml",
    "pubspec.lock",
    "mix.exs",
    "mix.lock",
    "podfile",
    "podfile.lock",
    "bun.lock",
    "bun.lockb",
    "packages.lock.json",
    "gradle.lockfile",
}

CONFIG_BASE = {
    "dockerfile",
    "makefile",
    "tsconfig.json",
    ".gitignore",
    ".dockerignore",
    ".npmrc",
    ".eslintrc",
    ".eslintrc.js",
    ".eslintrc.json",
    ".prettierrc",
    ".editorconfig",
    "vite.config.js",
    "vite.config.ts",
    "webpack.config.js",
    "rollup.config.js",
    "next.config.js",
    "next.config.mjs",
    "jest.config.js",
    "babel.config.js",
    ".env",
    ".env.example",
}

SRC_EXT = {
    ".py",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".kts",
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hpp",
    ".rb",
    ".php",
    ".cs",
    ".swift",
    ".scala",
    ".m",
    ".mm",
    ".dart",
    ".ex",
    ".exs",
    ".lua",
    ".r",
    ".jl",
    ".vue",
    ".svelte",
    ".sh",
    ".bash",
    ".ps1",
    ".sql",
    ".pl",
    ".clj",
    ".hs",
    ".elm",
}

DOC_EXT = {".md", ".mdx", ".rst", ".txt", ".adoc"}
CFG_EXT = {".yml", ".yaml", ".json", ".toml", ".ini", ".cfg", ".conf", ".properties", ".xml", ".env"}

STRUCTURAL_TYPES = frozenset({"modify/delete", "add/add", "rename/delete", "file location"})
CONTENT_TYPE = "content"


def is_manifest(basename: str) -> bool:
    b = basename.lower()
    if b in MANIFEST_BASE:
        return True
    if b.startswith("requirements") and b.endswith(".txt"):
        return True
    if b.endswith(".csproj") or b.endswith(".gemspec"):
        return True
    if re.search(r"build\.gradle(\.kts)?$", b):
        return True
    return False


def categorize(path: str) -> str:
    b = path.rsplit("/", 1)[-1].lower()
    ext = "." + b.rsplit(".", 1)[-1] if "." in b else ""
    if is_manifest(b):
        return "Manifest & Lockfile"
    lower = path.lower()
    if b in CONFIG_BASE or "/.github/" in "/" + lower or lower.startswith(".github/"):
        return "Config & CI"
    if ext in SRC_EXT:
        return "Source Code"
    if ext in DOC_EXT or b in ("license", "changelog", "readme"):
        return "Docs & Text"
    if ext in CFG_EXT:
        return "Config & CI"
    return "Other / Assets"


def touches_config_or_lockfile(paths: list[str]) -> bool:
    for p in paths:
        cat = categorize(p)
        if cat in {"Config & CI", "Manifest & Lockfile"}:
            return True
    return False


def type_group(conflict_type: str) -> str:
    t = conflict_type.strip()
    if t == CONTENT_TYPE:
        return "content"
    if t in STRUCTURAL_TYPES:
        return "structural"
    return "other"


def count_types(type_strings: list[str]) -> Counter:
    ctr: Counter = Counter()
    for s in type_strings:
        if not s or str(s) == "nan":
            continue
        for t in str(s).split("|"):
            if t:
                ctr[t] += 1
    return ctr
