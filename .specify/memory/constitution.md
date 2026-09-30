<!--
SYNC IMPACT REPORT (Constitution v1.0.0)
===================================
Version Change: Template → 1.0.0
Date: 2026-09-29

Changes:
- NEW: Initial ratification of playground-series-s6e9 constitution
- Added 6 core principles for Kaggle competition workflow
- Added Data Handling & Competition Ethics section
- Added Workflow Requirements section
- Added governance rules for agent coordination

Templates Status:
✅ plan-template.md: No updates required (constitution gates will be filled per-feature)
✅ spec-template.md: Aligned (acceptance criteria support OOF metrics)
✅ tasks-template.md: Aligned (user stories map to agent-owned work units)
✅ commands/*.md: No agent-specific changes needed

Follow-up: None
-->

# Playground Series S6E9 Constitution

## Core Principles

### I. Evidence Over Vibes

Model performance is measured by stratified out-of-fold (OOF) validation using the competition metric (ROC-AUC). Persuasive EDA heatmaps and interaction rate graphs serve intuition and storytelling only; they do not demonstrate model lift. Feature engineering is promoted to the baseline only when it beats OOF with a measurable margin (not ±0.00003 noise). Flat OOF means reject the feature.

**Rationale**: Kaggle competitions reward leaderboard accuracy, not compelling visualizations. Time spent on features that do not improve the metric is wasted effort. Stratified cross-validation provides the ground truth for local experiments.

### II. No Competition Data in Git

Competition CSVs (train.csv, test.csv, sample_submission.csv) must never be committed to the public GitHub repository. Data is downloaded via `scripts/01_download.sh` or Kaggle CLI (`kaggle competitions download -c playground-series-s6e9`) and placed in the gitignored `data/` directory.

**Rationale**: Kaggle competition rules prohibit data redistribution. Public repositories are subject to community etiquette. Large files bloat the repository and provide no reproducibility benefit since all competitors download identical data from the competition page.

### III. No Kaggle Submit Without Brett

No predictions may be submitted to the Kaggle leaderboard unless Brett explicitly requests a submission. Local OOF scores are sufficient for feature evaluation and model iteration. The `submitted_to_kaggle` field in `docs/RESULTS.md` and `artifacts/*.json` must remain `false`.

**Rationale**: Submission burns one of the limited daily submission slots and may leak information to competitors if the repository or agent logs become public. The project's goal is competitive-but-honest exploration, not leaderboard climbing without coordination.

### IV. Modeling Process Discipline

The standard workflow is:
1. **Profile** the raw data (nulls, distributions, target balance)
2. **Baselines** with stratified CV (simple models: logistic, LightGBM with default hyperparameters)
3. **EDA** for intuition (interaction rates, distributions, heatmaps) — storytelling only
4. **Promote FE** only when OOF gain exceeds noise margin (e.g., +0.001 ROC-AUC)
5. **Skip FE trees already capture**: gradient boosted trees learn interactions implicitly; explicit pairwise products rarely help
6. **Next try capacity/constraints**: deeper/wider forests, monotonic constraints, or stacking before more feature crosses
7. **True holdout** validation before trusting gains (OOF alone can overfit fold structure)
8. **Document** results in `docs/RESULTS.md` and summarize in `artifacts/*.json` (metadata only, not large CSVs)

**Rationale**: This process balances exploration speed with scientific rigor. Early interaction FE drips (batches 1-4) showed ±0.00003 OOF deltas, confirming that LightGBM already soaks pairwise effects. Documented workflows enable agents and humans to coordinate without duplicating experiments.

### V. Agent Responsibility Split

| Agent | Owns |
|-------|------|
| **Stack0-datasci (Kaggle box)** | Data download, profiling, cross-validation training, feature engineering experiments, plots, local predictions, metric verification |
| **Cursor cloud agent** | Repository-shaped work: documentation in git, scripts into git, pull requests, Speckit prompt files |
| **Goose (NVIDIA free tier)** | Tiny script/packet authoring only; never owns training loops or CV; the box runs all experiments |

**Hard lines**:
- Goose never trains models or computes OOF (insufficient compute)
- Cloud agent never owns the Kaggle box data path (credential/data boundary)
- Coordinator (Brett or Stack0-datasci) verifies cross-agent claims before merging

**Rationale**: Each agent has different compute, credential, and git access profiles. Explicit boundaries prevent wasted work (e.g., Goose attempting to run `lightgbm.train()`) and ensure reproducibility (the box is the source of truth for all training metrics).

### VI. Durable Q&A in Prompts Directory

Text Q&As and agent guidance must be written into `prompts/` at the repository root, not left in chat transcripts. The `prompts/FAQ.md` file answers common questions. Open questions are tracked in `prompts/OPEN.md` (or equivalent) until resolved, then archived or moved to FAQ. Speckit agents and humans read `prompts/` first before asking clarifying questions.

**Rationale**: Chat conversations are ephemeral and hard to search. Durable documentation in git enables new agents and collaborators to onboard without repeating resolved questions. Speckit integration ensures agents consume this context automatically.

## Data Handling & Competition Ethics

- **No redistribution**: CSVs remain local or in private cloud storage; never committed to public repos.
- **No inventing labels**: Do not create political, geographic, or demographic labels beyond the provided columns. Use only the competition-supplied features and engineered derivatives that respect column semantics.
- **Reproducibility via scripts**: Any download, preprocessing, or training step must be scripted (`scripts/*.sh`, `scripts/*.py`) so the workflow is reproducible by another collaborator with Kaggle credentials.
- **Small artifacts only**: JSON summaries, metadata, and figures (<1MB) are committed. OOF predictions, probability CSVs, and model binaries are gitignored.

## Workflow Requirements

- **Stratified CV mandatory**: All local model evaluation uses `StratifiedKFold` on the target (`Will_Buy_EV`) with fixed `random_state=42` for reproducibility.
- **OOF reporting**: Every experiment records the 5-fold OOF ROC-AUC (and optionally PR-AUC) in `docs/RESULTS.md` or equivalent.
- **No unverified agent claims**: If a cloud agent or Goose reports a metric, the box re-runs the experiment and confirms before the result is merged to main.
- **Documentation over chat**: Results, decisions, and lessons learned are written into `docs/RESULTS.md`, `prompts/FAQ.md`, or spec artifacts, not left in chat logs.

## Governance

This constitution supersedes ad-hoc practices. All pull requests and model experiments must comply with these principles. Agents reference this document when planning work (`.specify/memory/constitution.md`) and humans verify compliance during PR review.

**Amendment procedure**: Amendments require (1) justification in a PR description or issue, (2) Brett's approval, and (3) a version bump following semantic versioning. Breaking changes (principle removal or redefinition) increment MAJOR; new principles or material expansions increment MINOR; clarifications increment PATCH.

**Compliance review**: At the end of each modeling sprint or PR, verify:
- No CSVs in git
- No Kaggle submit unless Brett asked
- OOF reported for any FE claim
- Agent boundaries respected (box trains, cloud PRs, Goose scripts only)

**Version**: 1.0.0 | **Ratified**: 2026-09-29 | **Last Amended**: 2026-09-29
