# Upload this zip to OSF (dual-anonymous)

This file is the only checklist you need after `make check` passes.

## 1. Use the zip, not a git remote

Upload **`neurips2026-anonymous-osf.zip`**. Do not point reviewers at GitHub, a personal OSF profile, or a Zenodo badge. The zip has no `.git` directory.

## 2. OSF project settings

1. Create a new OSF project (or component) whose title is the **paper title**, not a name.
2. Upload the zip as a file (one file; do not unpack on OSF).
3. Under *Contributors*, keep the project private to you until you create a view-only link.
4. Create an **anonymous view-only link** (OSF: *Share* → view-only link → anonymize, so your name is not shown on the project page).
5. Put that link in the paper / OpenReview supplementary field. Do not paste a profile URL.

If the venue wants the zip on OpenReview instead of OSF, upload the same file there. Do not upload both a named GitHub repo and this zip.

## 3. Pre-upload grep (must be empty)

From the unpacked tree:

```bash
make audit
```

`make audit` fails if it finds home-directory paths, `mailto:`, a Zenodo badge, or a personal `github.com/CapitalName` URL. It does **not** search for author surnames (that would encode identity in the artifact). The packer already stripped those strings; if you edit files after packing, re-run the packer.

## 4. What reviewers can do without you

- Recompute ConflictBench tables from committed JSONL (`make -C conflictbench metrics`).
- Re-run MergeGym T3 observed/FIFO/oracle (`python mergegym/scripts/t3_simulator.py --check`).
- Re-run measurement WP1/WP2/legacy from committed parquet (`make -C measurement all` — no Hugging Face if extracts are present).
- Run Semantic Conflicts unit tests on tiny fixtures (`pytest semantic_conflicts/tests`).
- Compile papers if they have TeX (`make paper` per folder; optional).

They cannot, from this zip alone, re-fetch GitHub or re-query an LLM. Those steps are documented as optional in `REPRODUCE.md`.

## 5. Camera-ready (after accept)

Restore author blocks, bibliographic names, and a DOI. Do not ship this anonymous zip as the camera-ready archive.
