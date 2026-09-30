# Feature Specification: Kaggle Entry

**Feature Branch**: `003-kaggle-entry`  
**Created**: 2026-09-29  
**Status**: Draft  
**Input**: User description: "With about three hours before the deadline, an entry does not need a better model. Deeper trees and interaction features did not beat raw LightGBM (OOF ROC-AUC 0.9416, 5-fold StratifiedKFold, seed 42). The metric is ROC-AUC, so the file must be probabilities, not Yes/No. scripts/03_baselines.py only scores train out-of-fold. scripts/04_blend_calib.py is a stub. Nothing writes or uploads a submission."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Submit the raw LightGBM (Priority: P1)

A collaborator needs a leaderboard file from the existing raw LightGBM and must not upload it until Brett explicitly asks. The model to ship is the 0.9416 OOF baseline, not the smoke-test depth-8 model and not interaction features.

**Why this priority**: The deadline is close. More modeling is not on the path to an entry. The missing work is a test-set probability file and a gated upload.

**Independent Test**: A reader of this spec can state the entry model (raw LightGBM), the file shape (`id`, `Will_Buy_EV` probabilities), and that `kaggle competitions submit` does not run until Brett asks. `submitted_to_kaggle` in `docs/RESULTS.md` stays false until that ask.

**Acceptance Scenarios**:

1. **Given** the Kaggle account that will submit, **When** the entry is prepared, **Then** competition rules are already accepted on that account (`brettbrocato` in the download notes).
2. **Given** a machine with Kaggle credentials, **When** data is prepared, **Then** `data/test.csv` and `data/sample_submission.csv` exist locally via `scripts/01_download.sh`. They stay gitignored. Credentials stay in `~/.kaggle/kaggle.json` with mode `600`.
3. **Given** train and test data, **When** test scores are produced, **Then** they come from the raw LightGBM with the same features and encoding as the 0.9416 baseline. The five fold models' `predict_proba` values are averaged on every test row (`StratifiedKFold`, seed 42). Scores are not thresholded.
4. **Given** those probabilities, **When** the file is written, **Then** it matches the sample file: columns `id` and `Will_Buy_EV`, one row per test `id`, probabilities in `(0, 1)`. The CSV stays out of git.
5. **Given** an explicit submit ask from Brett, **When** the file is uploaded, **Then** the command is `kaggle competitions submit -c playground-series-s6e9 -f <file> -m "lgbm raw 5fold"`.
6. **Given** a successful upload, **When** the deadline is near, **Then** that submission is selected on the Kaggle Submissions tab so it is the one that counts.

---

## Edge Cases

- **What if someone ships the depth-8 smoke model or an interaction feature?** → Do not. Those did not beat raw LightGBM. The entry model stays the raw baseline.
- **What if the file uses Yes/No labels?** → Invalid for ROC-AUC. The `Will_Buy_EV` column must be a probability.
- **What if the upload is attempted without an explicit ask?** → Do not run `kaggle competitions submit`. Leave `submitted_to_kaggle: false`.
- **What if the submission CSV is about to be committed?** → Stop. Train, test, sample, and submission CSVs stay out of git.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The entry model MUST be raw LightGBM (OOF ROC-AUC 0.9416, 5-fold StratifiedKFold, seed 42), not the smoke-test depth-8 model and not interaction features.
- **FR-002**: The submission column MUST be a probability. Hard Yes/No labels are invalid for ROC-AUC.
- **FR-003**: No train, test, sample, or submission CSV may be committed.
- **FR-004**: No `kaggle competitions submit` runs unless Brett explicitly asks. Until then `submitted_to_kaggle` stays false.
- **FR-005**: The Stack0-datasci box owns fitting and prediction. This spec is the written entry path.

### Key Entities

- **Entry model**: Raw LightGBM from the existing baseline, same features and encoding, five-fold averaged test probabilities.
- **Submission file**: CSV with columns `id` and `Will_Buy_EV`, one probability per test id, kept out of git.
- **Submit gate**: An explicit ask from Brett before any leaderboard upload.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reader of this spec can produce the submission file from the raw LightGBM and knows the upload is still gated.
- **SC-002**: The spec does not claim a leaderboard score.
- **SC-003**: `docs/RESULTS.md` still says `submitted_to_kaggle: false` and points at this spec.
- **SC-004**: `git ls-files` shows no competition or submission CSVs.

## Assumptions

- Blend, calibration, stacking, monotone constraints, and another feature pass are out of scope for this entry.
- `scripts/03_baselines.py` only scores train out-of-fold and does not write a submission. `scripts/04_blend_calib.py` is a stub.
- Writing this spec does not upload anything and does not start training.
- Training, if it happens later, stays on the Stack0-datasci box.

## Out of Scope

Blend, calibration, stacking, monotone constraints, and another feature pass. They are not on the critical path to an entry.
