# Feature Specification: Kaggle Workflow Codification

**Feature Branch**: `001-kaggle-workflow-codification`  
**Created**: 2026-09-29  
**Status**: Draft  
**Input**: User description: "Codify the Kaggle playground-series-s6e9 EV-purchase modeling workflow we have already run: ROC-AUC competition; no CSV in git; no submit without Brett; local LightGBM (~0.9416 OOF) + logistic baselines done; interaction FE drip flat (~±0.00003) so skip explicit interaction features; EDA rate graphs show env×anxiety and subsidy×anxiety as most persuasive for intuition only; next try deeper/wider trees and/or monotonic constraints; validate on a true holdout; document in docs/RESULTS.md; work split is Stack0-datasci/box owns data/CV, Cursor cloud agent owns repo PRs, Goose only tiny scripts never training."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Constitution and Agent Responsibilities (Priority: P1)

A collaborator (human or agent) joins the project and needs to understand the governing principles and work boundaries. They should be able to read the constitution file and immediately know: what the project optimizes for (OOF ROC-AUC, not vibes), what is forbidden (CSVs in git, unsolicited Kaggle submits), and which agent owns which type of work (box trains, cloud PRs, Goose scripts only).

**Why this priority**: Without clear governance, agents duplicate experiments, violate competition ethics, or waste time on tasks outside their capability (e.g., Goose attempting LightGBM training). The constitution is the foundation that all other work rests on.

**Independent Test**: A new cloud agent or human reads `.specify/memory/constitution.md` and can correctly answer: (1) Can I commit train.csv? (No), (2) Should I submit my 0.95 OOF model to Kaggle? (Not without Brett), (3) Who runs cross-validation? (Stack0-datasci box), (4) What proves a feature works? (Stratified OOF gain beyond noise).

**Acceptance Scenarios**:

1. **Given** a repository with completed modeling experiments, **When** the constitution agent runs with the provided principles, **Then** `.specify/memory/constitution.md` is created with version 1.0.0, ratified 2026-09-29, containing 6 core principles covering evidence-based FE, competition ethics, agent boundaries, and workflow discipline.

2. **Given** the constitution exists, **When** a developer reads the "Agent Responsibility Split" section, **Then** they can determine which agent (Stack0-datasci box, Cursor cloud, or Goose) should execute a given task type (training, PRs, or script authoring).

---

### User Story 2 - Baseline Results Documentation (Priority: P2)

A collaborator wants to understand what modeling work has already been completed. They should be able to review `docs/RESULTS.md` and see that logistic regression (OOF ROC-AUC ~0.9381) and raw LightGBM (OOF ROC-AUC ~0.9416) baselines have been run with 5-fold stratified CV (seed=42), and that these are the benchmarks for future feature engineering.

**Why this priority**: Documenting completed baselines prevents re-running expensive experiments and provides the reference metric for evaluating new features. Without this, agents and humans waste time rediscovering what the best simple model is.

**Independent Test**: A developer reads `docs/RESULTS.md` and can state the current best local OOF score (0.9416), the model that achieved it (LightGBM raw), and the cross-validation strategy (5-fold StratifiedKFold, seed=42). They know not to beat themselves up if their FE only reaches 0.9417.

**Acceptance Scenarios**:

1. **Given** completed baseline experiments, **When** results are recorded in `docs/RESULTS.md`, **Then** the file includes a table with Model, OOF ROC-AUC, and OOF PR-AUC columns, showing logistic and LightGBM rows with the actual OOF scores from local CV.

2. **Given** the baseline table exists, **When** a new feature is tested, **Then** the developer compares the new OOF to the baseline 0.9416 and rejects features with deltas smaller than ±0.001 (noise threshold).

---

### User Story 3 - Interaction FE Experiment Results (Priority: P3)

A data scientist wants to know if explicit interaction features (e.g., `age_x_income`, `work_x_city`) have already been tested. They should be able to read documentation (in the spec, in RESULTS.md, or in the constitution) stating that interaction FE batches 1-4 were tested and showed essentially flat OOF (~±0.00003), leading to the decision to skip explicit interaction features because LightGBM trees already capture interactions implicitly.

**Why this priority**: This prevents wasting cycles on feature engineering that has been empirically shown not to help. The lesson "trees already soak interactions" is valuable domain knowledge that should be captured.

**Independent Test**: A collaborator reviews the feature engineering history and can correctly state: "Interaction FE drip batches 1-4 were tested and did not beat OOF; decision was to skip explicit interactions and try capacity/constraints next."

**Acceptance Scenarios**:

1. **Given** completed interaction FE experiments with flat OOF, **When** the results are documented, **Then** the spec or RESULTS.md notes that batches 1-4 showed ±0.00003 deltas, that `work_x_city` hurt performance, and that the conclusion is to skip explicit pairwise products.

2. **Given** the interaction FE lesson documented, **When** a future agent suggests trying `env_x_subsidy` or similar, **Then** the human or coordinating agent can cite the documented evidence and redirect effort toward model capacity or constraints instead.

---

### User Story 4 - Next Modeling Direction Documented (Priority: P3)

A modeling agent (or human) wants to know what to try next. They should be able to read the constitution or a planning document stating that the next modeling direction is: (1) deeper/wider forests and/or (2) monotonic constraints, and (3) validate on a true holdout (not just OOF) before trusting gains.

**Why this priority**: Prevents thrashing. The EDA and FE experiments have been done; the next logical step is model capacity or constraints, not more feature crosses.

**Independent Test**: A developer reads the spec or constitution "Modeling Process Discipline" section and can answer: "What should I try after flat interaction FE?" Answer: "Deeper/wider trees, monotonic constraints, or stacking, with true holdout validation."

**Acceptance Scenarios**:

1. **Given** completed EDA and interaction FE experiments, **When** the next steps are documented in the constitution or spec, **Then** the text explicitly states "prefer capacity/constraints over pairwise products next" and "true holdout before trusting gains."

2. **Given** next-step guidance exists, **When** an agent proposes a new modeling experiment, **Then** the proposal aligns with the documented direction (e.g., max_depth tuning, monotonic_constraints on income/age, or holdout split creation) rather than more interaction FE.

---

### Edge Cases

- What if a new collaborator has not read the constitution? → The Speckit agent instructions and `prompts/FAQ.md` direct agents to read `prompts/` and `.specify/memory/constitution.md` first.
- What if OOF metrics conflict between agents? → The constitution states the box is the source of truth; cloud agent or Goose metrics must be verified by the box before merging.
- What if Brett later approves Kaggle submission? → The constitution allows submission when Brett explicitly asks; document the ask in the PR or issue.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project MUST have a `.specify/memory/constitution.md` file containing the 6 core principles: Evidence Over Vibes, No Competition Data in Git, No Kaggle Submit Without Brett, Modeling Process Discipline, Agent Responsibility Split, and Durable Q&A in Prompts Directory.

- **FR-002**: The constitution MUST specify version 1.0.0, ratification date 2026-09-29, and include a Governance section describing amendment procedure and compliance review.

- **FR-003**: The `docs/RESULTS.md` file MUST contain a baseline results table showing Model, OOF ROC-AUC, and OOF PR-AUC for at least logistic regression and LightGBM raw models.

- **FR-004**: The project documentation (spec, RESULTS.md, or constitution) MUST record that interaction FE batches 1-4 were tested with flat OOF (~±0.00003) and that the decision is to skip explicit interaction features.

- **FR-005**: The project documentation MUST state the next modeling direction: deeper/wider forests, monotonic constraints, true holdout validation.

- **FR-006**: The project MUST NOT contain train.csv, test.csv, or sample_submission.csv in the git repository (enforced by .gitignore and PR review).

- **FR-007**: The `prompts/` directory MUST be the canonical location for durable Q&A, with `prompts/FAQ.md` covering common questions and open questions tracked until resolved.

### Key Entities

- **Constitution**: Versioned governance document at `.specify/memory/constitution.md` containing principles, data handling rules, workflow requirements, and governance process.

- **Baseline Results**: Table in `docs/RESULTS.md` recording model name, OOF ROC-AUC, OOF PR-AUC, and FE status for each completed experiment.

- **Agent Responsibility Matrix**: Table in constitution defining which agent (Stack0-datasci box, Cursor cloud, Goose) owns which work type (data/CV, PRs, scripts).

- **Modeling Workflow**: Step-by-step process codified in constitution principle IV, from profiling through holdout validation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new collaborator can read `.specify/memory/constitution.md` and correctly answer 4 governance questions (CSVs in git? No. Who trains? Box. What proves FE works? OOF gain. Submit without Brett? No.) with 100% accuracy.

- **SC-002**: The baseline results table in `docs/RESULTS.md` contains at least 2 models with complete OOF ROC-AUC and OOF PR-AUC metrics from 5-fold stratified CV.

- **SC-003**: No CSVs from `data/` are committed to the repository (verified by `git ls-files 'data/*.csv'` returning empty).

- **SC-004**: Documentation captures the interaction FE experiment outcome (flat OOF) and next modeling direction (capacity/constraints) in text that a human or agent can cite when planning future work.

- **SC-005**: The constitution file passes the Speckit consistency checklist: no unexplained bracket tokens, version matches report, dates ISO format, principles testable, and dependent templates reviewed.

## Assumptions

- The baseline OOF metrics (logistic 0.9381, LightGBM 0.9416) are from completed experiments on the Stack0-datasci box using 5-fold StratifiedKFold with seed=42.

- The interaction FE batches 1-4 referenced are completed work that showed ±0.00003 OOF deltas, justifying the decision to skip explicit interactions.

- The EDA interaction rate graphs (env×anxiety, subsidy×anxiety) exist in `docs/figures/interactions/` or equivalent and are used for storytelling, not OOF claims.

- The `prompts/FAQ.md` file already exists on main and covers questions about no-CSVs-in-git and Kaggle CLI download workflow.

- The constitution version 1.0.0 is the initial ratification; future amendments will increment version per semantic versioning (breaking = MAJOR, new principle = MINOR, clarification = PATCH).

- The agent (Cursor cloud) executing this feature has git push access but does not have Kaggle box credentials or data path access.
