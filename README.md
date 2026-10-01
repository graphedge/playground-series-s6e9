# playground-series-s6e9

Kaggle Playground Series S6E9 — Predicting Electric Vehicle Purchases.

**Competition**: https://www.kaggle.com/competitions/playground-series-s6e9  
**Metric**: ROC-AUC  
**Target**: `Will_Buy_EV` (binary classification, ~17.5% positive class)

## Overview

This competition predicts whether customers will purchase an electric vehicle based on demographics, commute patterns, charging access, and environmental attitudes. The dataset is clean (no missing values) and CPU-friendly for rapid iteration.

**Key characteristics**:
- Imbalanced classes: ~17.5% Yes, ~82.5% No
- Scale positive weight: ~4.73
- CPU-friendly: LightGBM baselines complete in minutes
- Clean tabular data suitable for tree models and logistic regression

## Getting Started

### 1. Download Data

Competition CSVs are **not committed** to this repository. Download them with the Kaggle CLI:

```bash
# Install Kaggle CLI if needed
pip install kaggle

# Place your kaggle.json in ~/.kaggle/ (chmod 600)
# Account for downloads: brettbrocato

# Run the download script
bash scripts/01_download.sh
```

This downloads `train.csv`, `test.csv`, and `sample_submission.csv` into `data/`.

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

All packages are CPU-friendly. No GPU or CUDA required.

### 3. Run Baseline Models

```bash
# Optional: profile the training data
python scripts/02_profile.py

# Run baselines (logistic + LightGBM, 5-fold CV)
python scripts/03_baselines.py

# Results are written to artifacts/baseline_summary.json
```

Expected baseline performance:
- **Logistic (balanced)**: ~0.938 ROC-AUC
- **LightGBM (raw)**: ~0.942 ROC-AUC

See `docs/RESULTS.md` for full baseline table and notes.

### 4. Blend & Calibrate (Stub)

```bash
python scripts/04_blend_calib.py
```

This script is a work-in-progress stub for OOF blending, calibration, and threshold optimization.

## Repository Structure

```
.
├── README.md                          # This file
├── requirements.txt                   # CPU-friendly Python dependencies
├── .gitignore                         # Excludes data CSVs, credentials, reports
├── prompts/                           # Speckit prompts and Q&As (read first)
├── docs/
│   ├── skills/                        # Reusable Kaggle Playground skills
│   │   ├── README.md                  # Skill catalog and usage guide
│   │   ├── playground-og-data-stack.md        # Original dataset integration
│   │   └── arrival-delay-missingness.md       # Sparse continuous NA handling
│   └── RESULTS.md                     # Local experiment results (not submitted)
├── artifacts/
│   ├── baseline_summary.json          # Baseline CV metrics
│   └── laya_next_steps_rank.json      # Ranked next-step candidates
├── scripts/
│   ├── 01_download.sh                 # Kaggle CLI download script
│   ├── 02_profile.py                  # ydata-profiling EDA (optional)
│   ├── 03_baselines.py                # Logistic + LightGBM baselines
│   └── 04_blend_calib.py              # Blend, calibration, threshold sweep (stub)
├── data/                              # train.csv, test.csv (downloaded, not committed)
└── reports/                           # HTML profiling reports (not committed)
```

## Reusable Skills

This repository includes **reusable Kaggle Playground skills** under `docs/skills/` that apply to future competitions:

- **[Playground OG-data Stack](docs/skills/playground-og-data-stack.md)**: Integrate original/parent public datasets with competition data (e.g., S6E10 airline + Invistico dataset alignment)
- **[Arrival-Delay Missingness](docs/skills/arrival-delay-missingness.md)**: Handle continuous features with meaningful `NaN` (e.g., S6E10 arrival delay where `NaN` ≠ zero)

See [docs/skills/README.md](docs/skills/README.md) for full skill catalog and usage guide.

**Note**: While these skills were developed in the S6E9 repo, they're designed for **S6E10 and beyond** where original datasets and sparse continuous features are common.

## Submission Policy

**Do NOT open a Kaggle submission or claim any leaderboard score unless Brett explicitly asks.**

This repository is for local experimentation and reproducible baselines. All results in `docs/RESULTS.md` are out-of-fold (OOF) local cross-validation scores, not leaderboard scores.

## Next Steps

See `artifacts/laya_next_steps_rank.json` for a ranked list of 39 candidate next steps (features, modeling, data strategies). Top recommendations:
1. **Blend logistic + LightGBM OOF** (rank 0.92)
2. **Stacking with OOF meta-learner** (rank 0.90)
3. **Environmental concern × range anxiety interaction** (rank 0.89)

Full rationale and experiment tracking in `docs/RESULTS.md`.

## License

Code is provided as-is for educational and experimental purposes. Competition data is subject to Kaggle's terms.
