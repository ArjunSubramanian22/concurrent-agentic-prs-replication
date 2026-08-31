# Analysis plan — Concurrent Agentic Pull Requests

**Status:** pre-registered.  
**Frozen:** 2026-08-31.  
**Rule:** this file is committed before any mixed-effects, GEE, logistic, conditional-logit, McNemar, Fisher, chi-square, or predictive model in Work Packages 3–6 is executed. Analyses conceived after this commit are labeled *exploratory* in the paper and in `claims.csv`.

This is a study plan, not a results document. Numbers that already exist in `rq3_merge_replay_full.csv` are treated as a **legacy sample**. They motivated the redesign. They are not the confirmatory tests.

No figure in the manuscript may be typed by hand. Every reported quantity is emitted by a named function listed in `claims.csv`.

---

## 1. Question and claims

### 1.1 Target claims (scientific, not numerical)

**Primary.** Concurrent agent-authored pull requests in the same repository conflict at a measurable textual rate, and that rate is higher than, indistinguishable from, or lower than a matched human–human baseline obtained with the identical interval logic and the identical `git merge-tree` replay. The bracket is an empirical result of WP4, not a hypothesis we will shop for.

**Secondary.** The raw cross-agent versus intra-agent gap is largely compositional: it is attributable to which agents appear in the pair and to which repositories run more than one vendor, rather than to heterogeneity itself causing conflict.

**Tertiary.** Structural conflict signals (`modify/delete`, `add/add`, and related structural types) are a large share of agent–agent conflict signals. Whether that share exceeds the human–human profile in the same repositories is a WP4 test, not an assumption.

**Optional tertiary (WP6 only if WP4 and WP5 are complete).** Conflict among co-active pairs is predictable from features available at pull-request open time, above a base-rate baseline, under repository-grouped validation.

### 1.2 Research questions

| ID | Question | WP | Designation |
|---|---|---|---|
| RQ1 | What is the prevalence of co-active agent-authored PRs, under three censoring treatments and a k-day slack sweep? | 1 | Confirmatory (descriptive) |
| RQ2 | What is the textual merge-conflict rate of co-active pairs in three strata: agent–agent, human–human, and human–agent? | 2, 4 | Confirmatory |
| RQ3 | After matching on repository and adjusting for pre-registered covariates, does a residual cross-agent (or stratum) effect remain? | 2, 3, 4 | Confirmatory |
| RQ4 | Do conflict-type profiles differ across the three strata? | 3, 4 | Confirmatory |
| RQ5 | Among textually clean merges, what are the build-conflict and test-failure rates on a scoped ecosystem subset? | 5 | Confirmatory on a scoped subset; under-powered by construction |
| RQ6 | Is conflict predictable at PR-open time? | 6 | Optional; run only if WP4 and WP5 are done |

The previous manuscript’s qualitative “RQ4” (why agents conflict) is **retired**. It will not appear.

### 1.3 What we will not claim

- That this is the largest study of agentic merge conflicts. AgenticFlict exists and is larger on a different unit (PR-versus-base, not inter-PR concurrency).
- That a gap between two Wilson intervals, without a test, is a finding.
- That unresolved PRs treated as open-until-cutoff are a measure of realized integration friction.
- That the earliest overlapping pair in a repository is representative of that repository.
- Any number that did not come out of a committed script.

---

## 2. Data

### 2.1 Snapshot

| Item | Value |
|---|---|
| Source | Hugging Face `hao-li/AIDev`, AIDev-pop tables (`pull_request.parquet`, `repository.parquet`) |
| License | CC-BY-4.0 for the dataset packaging; source-repo licenses apply to file contents |
| Pop filter | Repositories with >100 stars, as defined by AIDev-pop |
| Files SHA-256 | `pull_request.parquet` = `c0b8e81e1d099905ef9ea420bf907d45179771ff5972afce6c219d8cafcef3e8`; `repository.parquet` = `a08e34be4921c708be88a4ebd9e275b32f37fd442bb2770c0b69c94834dc6aa7` (Hugging Face LFS OID = SHA-256) |
| Recorded | 2026-08-31 |
| PR count / repo count | taken from the files at download; written to `data/derived/snapshot.json` by `scripts/vendor_snapshot.py` |
| Observation window | `[min(created_at), max(created_at)]` in the snapshot. Cutoff \(T\) = max of `created_at`, `closed_at`, `merged_at` in the snapshot. |
| Agents in snapshot | whatever `agent` values are present, including `Google_Jules` if present. No silent drop. |

A column-pruned extract (no `title`, no `body`) is vendored under `data/derived/` so RQ1/RQ2 sampling is regenerable without Hugging Face. The raw parquet remains the hash-pinned original.

Human-authored PRs are **not** in AIDev-pop. They are collected from the GitHub API for the same repositories and the same window (WP4). Raw JSON responses are cached under `data/cache/github/` and never modified in place.

### 2.2 Legacy replay file

`rq3_merge_replay_full.csv` (747 pairs) is retained as the **legacy earliest-pair sample**. Scripts may re-derive quantities from it. They must label every such quantity `legacy_earliest_pair`. Confirmatory rates use the WP2 sample, not this file, except as a disclosed sensitivity.

---

## 3. Outcome definitions

### 3.1 Pull-request interval

For pull request \(i\):

- \(s_i\) = `created_at` (UTC). Rows with missing `created_at` are excluded.
- \(r_i\) = `closed_at` if present, else `merged_at`. This is the observed resolution time.
- `is_censored_i` = 1 iff both `closed_at` and `merged_at` are null.
- `pr_state_i` ∈ {`merged`, `closed_unmerged`, `open`} where `merged` iff `merged_at` is non-null; `closed_unmerged` iff `closed_at` is non-null and `merged_at` is null; `open` iff `is_censored_i`.

If \(r_i < s_i\) the row is excluded as invalid.

### 3.2 Three end-time treatments

Let \(T\) be the snapshot cutoff. Let \(m_a\) be the median of \((r_j - s_j)\) among non-censored PRs of the same `agent` as \(i\). If an agent has no resolved PR, \(m_a\) is the global resolved median.

| Treatment | End time \(e_i\) | Who is included |
|---|---|---|
| **A (legacy)** | \(r_i\) if observed, else \(T\) | All PRs with valid \(s_i\) |
| **B (drop censored)** | \(r_i\) | Non-censored PRs only |
| **C (impute)** | \(r_i\) if observed, else \(\min(s_i + m_a,\; T)\) | All PRs with valid \(s_i\) |

**Headline rule (pre-registered).** Let \(p_A\) and \(p_B\) be the PR-level co-active shares at \(k=0\) (definition 3.4). If \(|p_A - p_B| \ge 0.05\) (absolute) **or** \(|p_A - p_B| / \max(p_A, 10^{-9}) \ge 0.10\) (relative), treatment **B** is the headline prevalence. Otherwise treatment **A** is the headline and B/C remain in the sensitivity table. All three columns are always printed. The paper states the open-PR share explicitly.

### 3.3 Overlap at slack \(k\)

Two PRs \(A,B\) in the same repository **overlap at slack \(k\)** (days, real-valued) iff

\[
\max(s_A, s_B) < \min(e_A, e_B) + k \cdot 86400\text{ seconds}.
\]

Require a strictly positive overlap at \(k=0\). Pairs are undirected and stored with `prA < prB` by PR number. A PR does not pair with itself.

This is the **gap-slack** definition: \(k\) is the maximum gap allowed between intervals. We do **not** expand both sides of each interval (that would allow a \(2k\) gap). If a reviewer asks for the expand-both-sides variant, it is exploratory.

Sweep: \(k \in \{0, 1, 3, 7\}\) as a table, plus a curve \(k = 0, 0.5, 1, 2, \ldots, 14\).

### 3.4 Co-activity prevalence (RQ1)

Computed separately for treatments A, B, C and each \(k\).

- **PR-level share:** among included PRs, the fraction that overlap at least one other included agent-authored PR in the same repository.
- **Repo-level share, all repos:** among repositories present in the snapshot, the fraction with at least one overlapping included pair.
- **Repo-level share, repos with ≥2 included PRs:** same, restricted to repositories that could possibly have a pair.

**Overlap duration** of a pair: \(\min(e_A,e_B) - \max(s_A,s_B)\), clipped at zero. Report median, IQR, and a histogram (log-scale hours) for \(k=0\), treatment headline.

### 3.5 Pair strata

A pair is

- `agent_agent_intra` (`same`): both authors are agents and `agentA == agentB`
- `agent_agent_cross` (`cross`): both authors are agents and `agentA != agentB`
- `human_human`: both authors are human
- `human_agent`: one human, one agent

**Agent** means the PR appears in AIDev-pop with a non-null `agent` label, **or** its GitHub `user.login` is in the agent-login set derived from the snapshot (`user` values of AIDev-pop PRs) plus the frozen extra logins in `analysis/lib/agent_logins.py`. **Human** means a GitHub PR in-window, in-repo, whose login is not in that set and is not a known bot pattern (`[bot]` suffix or login in a frozen bot list) unless that login is an AIDev agent account.

PRs whose author cannot be classified are dropped from WP4 and counted as `author_unknown`. They are never silently recoded as human.

### 3.6 Textual conflict (primary outcome)

Replay (WP2/WP4) on a pair of PR heads:

1. Bare repository, `git init`.
2. `git fetch` of `refs/pull/{n}/head` for both PRs, depth 80; on missing merge-base, retry depth 600.
3. `git merge-base pra prb`. If none: label `UNAVAIL_nobase`.
4. `git -c merge.conflictStyle=merge -c diff.renameLimit=400 -c merge.renames=true merge-tree --write-tree pra prb`.

Labels:

| Label | Meaning | In rate denominator? |
|---|---|---|
| `CLEAN` | merge-tree exit 0 | Yes |
| `CONFLICT` | merge-tree exit 1 | Yes |
| `UNAVAIL_fetch` | fetch failed (deleted ref, private, network) | No |
| `UNAVAIL_nobase` | no merge-base after retry | No |
| `UNAVAIL_timeout` | command timeout | No |
| `ERR*` | any other merge-tree exit | No |

**Primary conflict indicator** \(Y=1\) iff label is `CONFLICT`, among evaluable pairs (CLEAN ∪ CONFLICT).

**Realized-friction variant:** same \(Y\), restricted to pairs with both PRs `pr_state == merged`. Reported alongside, never substituted silently for the primary.

**Conflict types** are parsed from `CONFLICT (...)` lines in merge-tree stdout. File paths are the tab-separated paths in the leading conflict listing. Taxonomy functions live in `analysis/lib/taxonomy.py` and are frozen.

**Structural signal:** type ∈ {`modify/delete`, `add/add`, `rename/delete`, `file location`}. **Content signal:** type == `content`. Pair-level `has_structural` = 1 if any structural signal is present.

### 3.7 Build and test outcomes (RQ5)

Defined only for pairs with textual label `CLEAN`, on the WP5 subset.

| Label | Meaning |
|---|---|
| `BUILD_FAIL` | build or typecheck non-zero and not a timeout/infra error |
| `TEST_FAIL` | build succeeded, test suite non-zero, not timeout/infra |
| `PASS` | build and tests zero |
| `TIMEOUT` | wall-clock cap hit |
| `ENV_FAIL` | image, dependency, or checkout failure |
| `FLAKY` | bases disagree on repeated test runs (see WP5) |

Timeouts and environment failures are never coded as `PASS`.

---

## 4. Exclusion rules (frozen)

1. Missing `created_at`.
2. Invalid interval \(r_i < s_i\) (treatment A/C still require \(s_i \le T\)).
3. Treatment B: all censored PRs.
4. Repositories with fewer than two included PRs: excluded from pair construction; still counted in the “all repos” denominator of RQ1.
5. Duplicate undirected pairs: keep one row with `prA < prB`.
6. Replay non-evaluable labels: excluded from conflict **rates**, reported as availability.
7. WP4: PRs with `author_unknown`.
8. WP5: pairs whose repo has no detected Python / JS / TS / Go build manifest, or whose textual label is not `CLEAN`.
9. No outcome-based exclusion. We do not drop pairs because they conflicted, because they were huge, or because they were Jules/Copilot/etc.

If a repo is missing from GitHub at replay time, the pair is `UNAVAIL_fetch`. We do not replace it with another pair inside the same seed draw; the bootstrap (WP2) is how we represent pair-choice uncertainty.

---

## 5. Sampling (WP2)

### 5.1 Seeds

| Name | Value | Role |
|---|---|---|
| `MASTER_SEED` | 42 | documented parent |
| `SEED_INTRA_REPOS` | 42 | draw of intra-only population repos |
| `SEED_INTRA_PAIRS` | 42 | uniform pair within repo, unmatched intra |
| `SEED_MATCHED` | 43 | pair draws inside the matched (multi-vendor) repos |
| `SEED_BOOTSTRAP_BASE` | 1042 | replicate \(b\) uses `1042 + b` for \(b=1..200\) |
| `SEED_WP5` | 2026 | WP5 subset order |
| `SEED_WP6` | 7 | grouped CV shuffles, if WP6 runs |

All `numpy.random.Generator` via `default_rng(seed)`.

### 5.2 Eligible pairs

For a given treatment (headline treatment for confirmatory conflict sampling; default: apply the headline rule of §3.2 at \(k=0\)) and \(k=0\):

In each repository, enumerate all undirected overlapping agent–agent pairs. Split into intra and cross.

The **legacy** sampler returned the earliest overlapping pair (`first_overlap`). That procedure is reimplemented only to reproduce the legacy sample and to plot conflict rate against ordinal position. It is **not** used for confirmatory rates.

### 5.3 Confirmatory samples

**S1. Unmatched intra (population rate).** Among repositories with ≥1 intra pair, draw 625 repositories without replacement (`SEED_INTRA_REPOS`). If fewer than 625 exist, take all. In each drawn repo, draw **one** intra pair uniformly (`SEED_INTRA_PAIRS`).

**S2. Cross census.** Every repository with ≥1 cross pair: draw **one** cross pair uniformly (`SEED_MATCHED`). This is a census of repos, a sample of pairs.

**S3. Designed match (primary confound control).** For every repository that has ≥1 cross pair **and** ≥1 intra pair, draw one intra pair and one cross pair independently, uniformly (`SEED_MATCHED`). Repositories with cross but no intra are counted, reported, and excluded from the matched test.

**S4. Clustered / multi-pair.** In each S1/S2/S3 repository, additionally draw up to 4 further pairs per available stratum (or all, if fewer), without replacement, for bootstrap support and the clustered model. Cap `MAX_PAIRS_PER_REPO_STRATUM = 5` including the primary draw. If a repository has ≤5 pairs in a stratum, replay is exhaustive for that stratum.

**S5. Human strata (WP4).** In the **same repositories as S3** (matched multi-vendor set) and, separately, in the S1 intra repos, enumerate human–human and human–agent overlaps with the identical interval treatment and \(k=0\). Then apply the same uniform-one-pair-per-repo (and MAX=5) draws, seed `SEED_MATCHED` for S3 repos and `SEED_INTRA_PAIRS` for S1 repos, independent streams by hashing `("hh"|"ha", repo_id)` into the generator as documented in `analysis/lib/sample.py`.

### 5.4 Bootstrap over pair selection

\(B = 200\). For each replicate \(b\), independently, for each repository, draw one evaluable pair from the replayed pairs of the target stratum in that repo (generator `SEED_BOOTSTRAP_BASE + b`). If a repo has no evaluable pair, it is missing in that replicate. Report the distribution of the conflict rate (mean, 2.5th and 97.5th percentiles) **alongside** the Wilson interval of the primary draw.

This bootstrap captures pair-within-repo selection uncertainty. It does not capture repository sampling uncertainty (S2 is a census of cross repos). A second, exploratory bootstrap over S1 repo draws may be reported and must be labeled exploratory.

### 5.5 Ordinal-position diagnostic

For every repository in which we replayed more than one pair, order eligible pairs by \(\min(s_A,s_B)\) and plot/tabulate conflict rate by quintile of that ordinal position. If the earliest pair is an outlier, the legacy `first_overlap` design is retired with evidence. If not, we still do not return to it; S3 remains primary.

### 5.6 Sample-size honesty

Cross-agent reality is on the order of 122 repositories in the legacy draw. The matched test’s power is limited by the discordant-pair count. We will report exact McNemar \(p\) and a 95% interval for the discordant ratio. We will not describe a non-significant matched test as “no difference” without the interval.

---

## 6. Covariates (WP3) — frozen list

Collected for every replayed pair. Missingness is a category or a missing flag, never an imputed mean except where stated.

### 6.1 Per PR

From GitHub PR JSON (cached) and, for divergence, from the replay clone:

- `n_files`, `additions`, `deletions`, `n_commits`
- `lifetime_hours` = \((r_i - s_i)\) in hours; missing if censored
- `base_divergence_commits`: commits on `merge-base..head` (replay)
- `n_directories`: unique parent directories of changed files
- `touches_config_or_lockfile`: taxonomy in `analysis/lib/taxonomy.py`

### 6.2 Per pair

- `jaccard_files` = \(|F_A \cap F_B| / |F_A \cup F_B|\); 0 if both file sets empty
- `overlap_duration_hours`
- `same_directory`: 1 iff the two file sets share at least one top-level directory
- `cross`: 1 iff agent–agent and `agentA != agentB`
- `stratum` as in §3.5

### 6.3 Per repository

- `n_agent_prs` (from AIDev-pop)
- `n_human_prs` (from GitHub list; missing if API failed)
- `stars`, `language` (AIDev-pop `repository`)
- `repo_age_days`: from GitHub repo `created_at`; missing if API failed
- `n_contributors`: GitHub `contributors` count if obtainable; else missing
- `multi_vendor`: 1 iff ≥2 distinct AIDev agents among the repo’s AIDev-pop PRs

### 6.4 What is not a covariate

- Any function of the conflict label.
- Post-merge CI status.
- Reviewer counts (optional exploratory only).

---

## 7. Models and tests

### 6.0 Multiple-comparison policy

Holm (1979) correction **within each family** below, two-sided \(\alpha = 0.05\). Families are separate questions. Exploratory tests are uncorrected and labeled. We never use “non-overlapping 95% CIs” as a substitute for a test. Every comparison reports a statistic, an effect size, and an interval.

Wilson score intervals use \(z = \Phi^{-1}(0.975)\) from `scipy.stats.norm.ppf(0.975)`. The legacy script’s \(z=1.96\) may be re-run as a check; the paper uses scipy.

### Family 1 — Prevalence (RQ1)

Descriptive. No multiplicity correction. Headline treatment as §3.2.

### Family 2 — Cross-agent composition (RQ3), agent–agent only

**Primary confirmatory test:** McNemar exact (binomial test on discordant matched pairs) on sample **S3**. Effect: difference in paired proportions; interval via Newcombe paired method or the exact binomial interval on the discordant split, both reported.

**Secondary confirmatory:**

1. Unmatched S1 vs S2: Fisher exact test on the 2×2 (conflict × cross), plus Newcombe independent risk-difference interval. This is **not** the causal claim; it is the raw gap.
2. GEE logistic, binomial, exchangeable working correlation, cluster = repository, on all evaluable agent–agent pairs in S3∪S4 (and S1/S2 primary draws). Linear predictor:

   `conflict ~ cross + jaccard_files + log1p(n_files_A) + log1p(n_files_B) + overlap_duration_hours + multi_vendor`

   Report exponentiated coefficient on `cross` (odds ratio) with GEE robust interval.

3. Compositional expectation (not a regression): for each cross pair with agents \(a,b\), \(\hat p = \hat p_a + \hat p_b - \hat p_a\hat p_b\) where \(\hat p_a\) is the intra-agent conflict rate of agent \(a\) on unmatched intra evaluable pairs. Average \(\hat p\) versus observed cross rate. No p-value; this is a calibration check.

**Exploratory, labeled, not used for the abstract:**

- GEE as above plus agent-presence indicators. **Collinearity caveat (mandatory in the paper):** a cross pair mechanically has two agent identities; indicators are partly collinear with `cross`. Variance-inflation or coefficient-stability is reported. This specification is not the source of the abstract sentence.
- Mixed-effects logit if `statsmodels` `BinomialBayesMixedGLM` converges with the seeded configuration; otherwise we report GEE only and say so.
- Conditional logit on S3 (two rows per repo) with the Family-2 covariate set except `multi_vendor` (absorbed). If it fails to converge, McNemar remains the primary.

**Abstract rule:** the abstract’s characterization of the cross-agent effect must match the **S3 McNemar** (direction, significance after Holm in Family 2, and the paired difference), with the GEE OR reported as the covariate-adjusted complement. If they disagree in sign, the abstract reports the disagreement rather than picking the favorite.

### Family 3 — Human baseline (RQ2, RQ4)

On pairs that have completed replay.

1. Three-stratum Wilson rates (AA pooled, HH, HA) on the primary one-pair-per-repo draws in the S3 repository set (within-repo support) **and** separately on S1 (population AA vs whatever HH/HA exist there).
2. Within-repo paired tests, S3 repos that have both an evaluable AA pair and an evaluable HH pair: McNemar exact, AA vs HH. Analogous AA vs HA. Holm within this family.
3. GEE logistic: `conflict ~ C(stratum)` with AA as reference, same covariates as Family 2 (jaccard, sizes, overlap, multi_vendor), cluster = repo, on S3∪S4 plus the human draws.
4. Conflict-type profile: among conflict **signals** (not pairs), a \(\chi^2\) test of independence on type-group × stratum, where type-group ∈ {content, structural, other}. If expected counts <5 in any cell, Fisher–Freeman–Halton on a 2×3 (content vs structural, collapsing other into structural if still sparse, documented). Effect: Cramér’s V.

If WP4 data collection fails (no token, quota, or zero human pairs), Family 3 is reported as **unavailable** and the primary claim is reduced to “agent–agent rate, with composition analysis, without a human baseline.” We do not borrow a literature rate as a substitute baseline.

### Family 4 — Realized friction

Same tests as Family 2 primary McNemar and Family 3 (1)–(2), restricted to both-merged pairs. Secondary designation.

### Family 5 — WP5 build/test

Descriptive rates with Wilson intervals. No comparison test unless both agent–agent and human–human WP5 subsets exceed 50 evaluable-built pairs, in which case Fisher exact on BUILD_FAIL among textually clean pairs is confirmatory in this family.

### Family 6 — WP6 (optional)

Repo-grouped \(K=5\) cross-validation, seed `SEED_WP6`. Metric: ROC-AUC and average precision versus a constant base-rate predictor. Features at **open time only**: agent identity of each PR (or human), `stars`, `language`, count of already-open PRs in the repo at `s_i` of the later PR, hour-of-week of the later open, log1p files changed on each PR **as reported at open** (GitHub `changed_files` at first observation; if only the final count is available, this feature is **excluded**, not quietly used). Jaccard of final file sets is **forbidden** in WP6.

---

## 8. Work Package 5 scope (frozen, narrow)

- Ecosystems: Python (`pyproject.toml` / `setup.py` / `requirements.txt`), JavaScript/TypeScript (`package.json`), Go (`go.mod`).
- Detect on the merge-base tree, not on an arbitrary default branch.
- Textually `CLEAN` pairs only, drawn from replayed pairs, order shuffled with `SEED_WP5`.
- Caps: 15 minutes wall clock per pair after container start; 400 pairs or the feasible set, whichever is smaller.
- Flakiness check: run the test command twice on each unmerged head (or on merge-base plus each head if heads are not independently testable). If the two runs of the same head disagree, the pair is `FLAKY` and excluded from PASS/FAIL rates, counted separately.
- Sandbox: Docker when present; if Docker is unavailable the WP5 table is `UNAVAILABLE` and the paper says so. We will not fake a build-conflict rate.

---

## 9. Git and environment (replay determinism)

Recorded at runtime into `data/derived/environment_record.json`:

- `git --version`
- `python --version`
- `merge.conflictStyle`, `diff.renameLimit`, `merge.renames`, `diff.renames`
- OS

Replay **always** passes `-c merge.conflictStyle=merge -c diff.renameLimit=400 -c merge.renames=true` regardless of user gitconfig. Timeouts: fetch 90s (retry 150s), merge-base 15s, merge-tree 60s. Fetch depth 80 / 600 as above.

Docker image pins Python 3.12.8 and the Debian git package version listed in `Dockerfile`. Local reproduction may differ in the fourth decimal of floating-point GEE coefficients; rates (ratios of integers) must match bit-for-bit.

---

## 10. Mapping to code

| Claim family | Module | Output |
|---|---|---|
| RQ1 prevalence | `analysis/wp1_coactivity.py` | `data/derived/wp1_prevalence.csv`, `wp1_overlap_duration.csv`, `wp1_k_curve.csv` |
| WP2 samples | `analysis/wp2_sample.py` | `data/samples/*.csv` |
| Legacy 747 | `analysis/wp_legacy.py` | `data/derived/legacy_*.csv` |
| Replay | `analysis/replay.py` | `data/replay/pairs_replay.csv` |
| Family 2–4 tests | `analysis/wp3_confound.py`, `analysis/wp4_human_baseline.py` | `data/derived/wp3_*.csv`, `wp4_*.csv` |
| WP5 | `analysis/wp5_build_test.py` | `data/derived/wp5_*.csv` |
| Figures | `analysis/figures.py` | `paper/figures/*.pdf` |
| Paper numbers | `analysis/emit_macros.py` | `paper/generated/macros.tex` |
| Claim index | `claims.csv` | updated `status` by `analysis/emit_macros.py` |

If a computation cannot run, the emitter writes the macro `\CAPRSunavail{<id>}` and the CSV cell `UNAVAILABLE`. It does not invent a value.

---

## 11. Anonymity and artifacts

- Manuscript: `\documentclass[10pt,conference]{IEEEtran}` (no `compsoc`). Author block empty. No acknowledgments. Self-citations in the third person.
- README and URLs: no author names, no identifiable GitHub org, no live Zenodo DOI at submission (camera-ready restores it).
- `make all` on the archived snapshot must regenerate every table and figure that the paper cites. Live GitHub fetches are **not** required for `make all` if `data/replay/` and `data/cache/` are present in the archive. `make replay` and `make collect` are the live steps; they are documented as quota-bound and non-bit-stable because GitHub refs disappear.

Expected drift: the legacy run already had 25/747 `UNAVAIL_fetch`. That number can only stay or grow.

---

## 12. Deviations log

Any change to outcome definitions, exclusion rules, covariate sets, or primary tests after this commit is appended here with date and justification, and flagged exploratory unless it is a bug fix that restores the written definition.

| Date | Change | Reason | Status |
|---|---|---|---|
| — | — | — | — |

---

## 13. If results are flat

If WP4 shows agent–agent rates comparable to human–human and Family 2 shows no residual cross-agent effect after matching, the paper’s claim is:

Concurrent agentic PRs are common; they conflict at a rate comparable to concurrent human work in the same repositories; the conflicts are structurally different if and only if Family 3 test (4) says so; volume, not a cross-vendor penalty, is the integration story.

We will write that paper. We will not search the specification space for a significant `cross` coefficient.
