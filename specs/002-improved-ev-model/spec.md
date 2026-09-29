# Feature Specification: Improved EV Model Training

**Feature Branch**: `002-improved-ev-model`  
**Created**: 2026-09-29  
**Status**: Draft  
**Input**: User description: "Attempt to build/train an improved EV purchase prediction model for playground-series-s6e9 (ROC-AUC). Build on existing LightGBM + logistic baselines (raw LightGBM ~0.9416 OOF; interaction FE drip flat ~±0.00003). Proposed changes: deeper or wider forest; optional monotonic constraints on subsidy and range-anxiety axes; consider env×anxiety as the one interaction candidate only with proper holdout validation. **Gate:** before any Speckit plan/tasks for this feature, require a cheap smoke test — small LightGBM on a data sample with those proposed changes — to check viability (no crash; whether score moves). Only if smoke looks promising may full holdout validation and plan/tasks proceed. No Kaggle submit unless Brett asks. No CSVs in git. Box owns training; cloud lands scripts/docs."

## User Scenarios & Testing *(mandatory)*

### User Story 0 - Smoke Test Viability Gate (Priority: P0) 🚦 GATE

**CRITICAL**: This story MUST be completed successfully before proceeding to any other user stories or running `/speckit.plan` or `/speckit.tasks` for this feature.

A data scientist wants to quickly verify that the proposed model changes (deeper/wider forest, optional monotonic constraints on subsidy/range-anxiety) are viable before investing time in full 5-fold CV, holdout splits, and extensive experimentation. They should be able to run a cheap smoke test: train a single small LightGBM model on a sample of the training data (e.g., 20-30% random sample) with the proposed parameters (e.g., `max_depth=8-10`, `num_leaves=64`, optional `monotone_constraints`), check that training completes without errors, and observe whether the OOF score (on the sample or a single fold) shows any movement compared to the baseline ~0.9416.

**Why this priority**: This is a gate that protects against wasting cycles on approaches that obviously break or are dead flat. If the smoke test crashes (e.g., constraint conflicts) or shows zero movement from baseline, there's no point proceeding to full plan/tasks until the approach is revised. Smoke testing is standard practice before committing to expensive experimentation.

**Independent Test**: Run a single LightGBM training job on a 20-30% stratified sample of train.csv with `max_depth=8`, `num_leaves=64`, and optional monotonic constraints on 2-3 features (e.g., subsidy-related, anxiety-related). Verify: (1) training completes without crashes, (2) predictions are generated, (3) a quick OOF or single-fold score can be computed, (4) the score is not identical to baseline (some movement observed, even if small).

**Acceptance Scenarios**:

1. **Given** the full train.csv and proposed model parameters, **When** a 20-30% stratified sample is created and a single LightGBM model is trained with `max_depth=8` and `num_leaves=64`, **Then** training completes without errors and predictions are generated on the sample.

2. **Given** the trained smoke test model and sample data, **When** a quick score (single fold OOF or train/validation split) is computed, **Then** the score is recorded and compared to the baseline 0.9416 to check for any movement (positive, negative, or flat).

3. **Given** smoke test results, **When** the model crashed or constraints failed, **Then** the experiment is stopped, the failure is documented, and the approach is revised before proceeding.

4. **Given** smoke test results showing zero movement (e.g., within ±0.0001 of baseline on the sample), **When** the result is reviewed, **Then** the experiment is stopped and reported to Brett for go/no-go decision before proceeding to full plan/tasks.

5. **Given** smoke test results showing promising movement (e.g., ±0.001 or more, or any directional signal), **When** the result is reviewed, **Then** the gate is passed and User Stories 1-4 (full experiments) may proceed.

**Gate Decision**: 
- ✅ **PASS (proceed to P1-P4)**: Smoke test completes without errors AND shows some score movement (not dead flat)
- 🛑 **STOP (report to Brett)**: Smoke test crashes, constraint errors, or dead flat score on sample

---

### User Story 1 - Model Capacity Experiment (Priority: P1)

A data scientist wants to improve on the baseline LightGBM model (OOF ROC-AUC ~0.9416) by increasing model capacity. They should be able to train deeper or wider LightGBM forests (e.g., increasing `max_depth` from default 6 to 8-10, or `num_leaves` from 31 to 64-128) using the same 5-fold stratified CV setup, compute OOF ROC-AUC, and compare against the baseline. The experiment should document whether increased capacity beats the baseline by a meaningful margin (e.g., +0.001 or more).

**Why this priority**: Model capacity is a proven technique for improving gradient boosting performance when the simple baseline has already rejected explicit feature engineering. This is the constitution-recommended next step after flat interaction FE results. It's independently valuable even if constraints or holdout experiments are not done.

**Independent Test**: Train a LightGBM model with `max_depth=8` and `num_leaves=64` on the full training set using 5-fold stratified CV (seed=42), compute OOF ROC-AUC, and verify the result is either above 0.9416+margin or documented as not improving over baseline. The experiment can be completed without holdout data or monotonic constraints.

**Acceptance Scenarios**:

1. **Given** the raw train.csv data with LightGBM baseline parameters, **When** the data scientist increases `max_depth` to 8 or 10, **Then** the training script runs 5-fold stratified CV and outputs OOF ROC-AUC and PR-AUC that can be compared to the 0.9416 baseline.

2. **Given** OOF results from the capacity experiment, **When** the delta vs baseline is computed, **Then** the results are recorded in `docs/RESULTS.md` with a decision (promote if gain ≥ +0.001, reject if flat/negative).

3. **Given** a completed capacity experiment, **When** the cloud agent reviews the work, **Then** scripts are committed to `scripts/` and results are documented in `docs/RESULTS.md`, but no train.csv or model binaries are committed.

---

### User Story 2 - Monotonic Constraints Experiment (Priority: P2)

A data scientist wants to apply domain knowledge by adding monotonic constraints to the LightGBM model. They should be able to specify that certain features (e.g., charging infrastructure subsidy amount, environmental concern level) have monotonic relationships with EV purchase likelihood, train the constrained model with 5-fold stratified CV, and compare OOF ROC-AUC against both the baseline and the capacity-only model.

**Why this priority**: Monotonic constraints encode real-world assumptions (e.g., higher subsidy → higher purchase likelihood) and can improve generalization. However, they require understanding feature semantics and may not always help, so they are secondary to raw capacity experiments. They can be tested independently of holdout validation.

**Independent Test**: Train a LightGBM model with monotonic constraints on 2-3 features (e.g., `monotone_constraints=[0, 0, 1, 0, -1, ...]` where 1 = increasing, -1 = decreasing, 0 = no constraint), run 5-fold CV, and verify OOF ROC-AUC is either improved or documented as not helping.

**Acceptance Scenarios**:

1. **Given** the playground-series-s6e9 feature set and domain understanding, **When** the data scientist identifies subsidy-related and anxiety-related features for constraints, **Then** they document which features get which constraint direction (1, -1, or 0) with rationale.

2. **Given** a monotonic constraint configuration, **When** the model trains with 5-fold stratified CV, **Then** OOF ROC-AUC is computed and compared to the baseline and capacity-only results.

3. **Given** OOF results from the constraints experiment, **When** the cloud agent reviews the work, **Then** the constraint configuration and results are documented in `docs/RESULTS.md` with a decision on whether to keep the constraints.

---

### User Story 3 - True Holdout Validation (Priority: P3)

A data scientist wants to verify that OOF gains are real and not artifacts of overfitting the fold structure. They should be able to create a held-out validation set (e.g., 20% stratified split from train.csv, separate from the 5-fold CV), train the best model candidate on the remaining 80%, and evaluate on the holdout to confirm the OOF gain holds.

**Why this priority**: The constitution requires true holdout validation before trusting gains, but holdout is a validation step that comes after identifying candidate improvements. It's lower priority than running the capacity and constraints experiments because you need a candidate model to validate. However, it's necessary before declaring victory.

**Independent Test**: Split train.csv into 80/20 stratified (seed=42), train the best model on the 80% with 5-fold CV (nested CV), evaluate on the 20% holdout, and verify the holdout ROC-AUC is close to the OOF estimate (within ~0.005).

**Acceptance Scenarios**:

1. **Given** the full train.csv, **When** a 20% stratified holdout split is created (seed=42), **Then** the split is reproducible via script and the holdout set has similar target balance (~17.5% positive) as the full train.

2. **Given** the 80% training subset and a candidate model (e.g., deeper forest), **When** 5-fold stratified CV is run on the 80%, **Then** an OOF score is computed for comparison with the holdout score.

3. **Given** the trained model and 20% holdout, **When** predictions are generated on the holdout, **Then** the holdout ROC-AUC is computed and compared to the OOF estimate, and the result (confirmed gain or overfit warning) is documented in `docs/RESULTS.md`.

---

### User Story 4 - Env×Anxiety Interaction with Holdout (Priority: P4)

A data scientist wants to test whether the `env×anxiety` interaction feature (suggested by EDA rate graphs) improves model performance when validated on a true holdout. They should create the interaction feature, train a model with 5-fold CV on the training subset, evaluate on holdout, and promote the feature only if both OOF and holdout show meaningful gains (e.g., +0.001 or more).

**Why this priority**: This is the only explicit interaction feature still under consideration, but the constitution requires holdout validation and prohibits promoting features based on EDA rates alone. It's lowest priority because (a) previous interaction FE was flat, and (b) it requires holdout infrastructure from User Story 3.

**Independent Test**: Create `env_x_anxiety` as the product of environmental concern and range anxiety features, add it to the feature set, train with 5-fold CV on 80% training, evaluate on 20% holdout, and verify both OOF and holdout beat the baseline without the feature.

**Acceptance Scenarios**:

1. **Given** the raw feature set and the observation that env×anxiety has interesting rate patterns, **When** the `env_x_anxiety` feature is created, **Then** the feature is added to the training pipeline as an optional column that can be toggled on/off for comparison.

2. **Given** a model trained with `env_x_anxiety` on 80% training, **When** 5-fold OOF and 20% holdout scores are computed, **Then** both scores are compared to the same model without the feature, and the delta is recorded (OOF delta and holdout delta separately).

3. **Given** OOF and holdout results for the `env_x_anxiety` experiment, **When** both deltas are positive and ≥ +0.001, **Then** the feature is promoted and results documented in `docs/RESULTS.md`; **OR When** either delta is flat/negative, **Then** the feature is rejected with rationale.

---

### Edge Cases

- **What if the deeper forest overfits?** → OOF will show degradation or flat performance; holdout validation in User Story 3 will confirm. Document as "capacity increase did not help" and try constraints or revert to baseline.

- **What if monotonic constraints conflict with data patterns?** → Model training may fail or produce worse OOF. Document the constraint configuration attempted, the OOF result, and reject the constraints.

- **What if holdout score is much worse than OOF?** → This indicates overfitting to the fold structure. Document the gap, revert to simpler model or less aggressive hyperparameters, and re-validate.

- **What if env×anxiety helps OOF but hurts holdout?** → Reject the feature per constitution principle I (evidence over vibes) and document that EDA rates did not translate to model lift.

- **What if Brett asks to submit during this experiment?** → Pause modeling work, prepare submission from best validated model, submit, resume experiments after submission results are back.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-000**: Before proceeding to any Speckit plan or tasks for this feature, a smoke test MUST be run on the Stack0-datasci box: train a single LightGBM model on a 20-30% stratified sample of train.csv with proposed parameters (e.g., `max_depth=8-10`, `num_leaves=64`, optional monotonic constraints), verify no crashes, and check whether OOF score shows any movement vs baseline (~0.9416). If smoke test fails or is dead flat, STOP and report to Brett before proceeding.

- **FR-001**: The experiment MUST train LightGBM models with increased capacity (e.g., `max_depth=8-10` or `num_leaves=64-128`) using 5-fold stratified CV (seed=42) on the full train.csv, ONLY after smoke test gate passes (FR-000).

- **FR-002**: The experiment MUST compute and record OOF ROC-AUC and OOF PR-AUC for each model variant, comparing against the baseline 0.9416 OOF ROC-AUC.

- **FR-003**: The experiment MUST support monotonic constraints on LightGBM features, with constraint direction (1, -1, 0) configurable per feature and documented with rationale.

- **FR-004**: The experiment MUST create a reproducible 80/20 stratified train/holdout split (seed=42) with target balance verified, for true holdout validation separate from OOF.

- **FR-005**: The experiment MUST train candidate models on the 80% subset with 5-fold CV, then evaluate on the 20% holdout, recording both OOF and holdout ROC-AUC for comparison.

- **FR-006**: The experiment MUST support adding the `env_x_anxiety` interaction feature as an optional toggle, training with and without it, and comparing both OOF and holdout scores.

- **FR-007**: The experiment MUST NOT commit train.csv, test.csv, model binaries, or large OOF prediction files to the git repository (enforced by .gitignore).

- **FR-008**: The experiment MUST record all results in `docs/RESULTS.md` with model variant descriptions, OOF scores, holdout scores (if applicable), and promote/reject decisions.

- **FR-009**: The experiment MUST NOT submit predictions to Kaggle unless Brett explicitly requests a submission.

- **FR-010**: Training scripts and result documentation MUST be committed to the repository by the cloud agent after the box completes experiments and verifies metrics.

### Key Entities

- **Model Variant**: A specific LightGBM configuration (e.g., "deeper forest" with max_depth=8, or "constrained model" with monotone_constraints), trained with 5-fold stratified CV, producing OOF and optionally holdout scores.

- **Capacity Parameters**: LightGBM hyperparameters that control model complexity, such as `max_depth`, `num_leaves`, `min_data_in_leaf`, affecting how deeply the tree can split.

- **Monotonic Constraints**: A list of integers (1, -1, 0) matching the feature order, specifying whether each feature must have an increasing (1), decreasing (-1), or unconstrained (0) relationship with the target.

- **Holdout Split**: A stratified 80/20 split of train.csv, with the 80% used for training (with nested 5-fold CV) and the 20% reserved for final validation, created once and reused across experiments.

- **Interaction Feature**: The `env_x_anxiety` feature created as the product of environmental concern level and range anxiety level, tested as an optional addition to the baseline feature set.

- **OOF Predictions**: Out-of-fold predicted probabilities from 5-fold stratified CV, used to compute OOF ROC-AUC and verify the model is not overfitting the training data.

- **Holdout Predictions**: Predicted probabilities on the 20% holdout set, used to compute holdout ROC-AUC and confirm that OOF gains generalize beyond the CV fold structure.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-000**: 🚦 **GATE** — A smoke test is completed on a 20-30% stratified sample of train.csv with proposed model parameters (deeper/wider forest, optional constraints), training completes without errors, a quick score is computed, and the result is either: (a) PASS (some movement observed, proceed to P1-P4), or (b) STOP (crash or dead flat, report to Brett and do not proceed to plan/tasks).

- **SC-001**: At least one model capacity experiment (deeper or wider forest) is completed with 5-fold stratified CV (after smoke test passes), OOF ROC-AUC recorded, and result documented in `docs/RESULTS.md` as either beating baseline by ≥+0.001 or marked as not improving.

- **SC-002**: If monotonic constraints are tested, at least one constraint configuration is trained with 5-fold CV, OOF ROC-AUC compared to baseline and capacity-only model, and decision (keep/reject constraints) documented in `docs/RESULTS.md`.

- **SC-003**: A reproducible 80/20 stratified holdout split is created (seed=42) with target balance verified to be ~17.5% positive in both subsets (within ±1 percentage point).

- **SC-004**: At least one candidate model is validated on the true holdout, with holdout ROC-AUC recorded alongside OOF ROC-AUC, and the gap between them documented (holdout should be within ±0.01 of OOF for a well-generalizing model).

- **SC-005**: If the `env_x_anxiety` interaction is tested, both OOF and holdout scores are computed with and without the feature, deltas are compared, and the feature is promoted only if both deltas are positive and ≥+0.001, otherwise rejected.

- **SC-006**: All experiment results are recorded in `docs/RESULTS.md` with a consistent table format showing model variant, OOF ROC-AUC, holdout ROC-AUC (if applicable), and promote/reject decision.

- **SC-007**: No train.csv, test.csv, or competition data files are committed to the repository (verified by `git ls-files 'data/*.csv'` returning empty).

- **SC-008**: Training scripts (e.g., `scripts/02_train_deeper_forest.py`, `scripts/03_holdout_validation.py`) are committed to the repository by the cloud agent, enabling reproducibility by other collaborators.

## Assumptions

- **Smoke test gate**: The P0 smoke test on a sample is cheap (minutes, not hours) and protects against wasting expensive full-CV cycles on broken or flat approaches. Only after smoke test passes does the feature proceed to plan/tasks.

- The baseline LightGBM model with raw features achieves OOF ROC-AUC ~0.9416 (from 5-fold stratified CV, seed=42) as documented in the previous work.

- The interaction FE drip (batches 1-4) has been tested and showed essentially flat OOF (~±0.00003), justifying the focus on capacity and constraints over explicit feature crosses.

- The EDA interaction rate graphs showing env×anxiety and subsidy×anxiety patterns exist and are used for intuition, but do not constitute evidence of model lift without OOF/holdout validation.

- The Stack0-datasci box has Kaggle credentials, can download train.csv via `scripts/01_download.sh`, and owns all training/CV execution; the cloud agent only commits scripts and documentation after the box verifies results.

- LightGBM is the chosen gradient boosting framework (already used for baseline), and Python is the implementation language (scripts in `scripts/` are Python files).

- The target column is `Will_Buy_EV` with ~17.5% positive rate, and stratified CV ensures each fold maintains this balance.

- A meaningful OOF gain is defined as ≥+0.001 ROC-AUC (vs the baseline 0.9416), distinguishing signal from noise based on previous interaction FE experiments.

- Holdout validation is performed only after identifying promising model variants via OOF, not for every hyperparameter tweak (to avoid burning the holdout set).

- No Kaggle submission is triggered by these experiments unless Brett explicitly asks; `submitted_to_kaggle: false` remains in `docs/RESULTS.md`.

- Model binaries and large OOF/holdout prediction CSVs are gitignored and remain local to the box or cloud storage, not committed to the public repository.
