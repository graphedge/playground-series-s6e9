# Kaggle Playground FAQ

## Why are there no train/test CSVs in the repo?

Kaggle competition data must not be redistributed in a public GitHub repository. This is both a competition rule and general etiquette within the Kaggle community. Additionally, the data files are large and including them would provide no benefit for reproducibility since everyone downloads the same data from the same competition slug.

To get the data, use the provided download script or run the Kaggle CLI directly:

```bash
# Option 1: Use the download script
./scripts/01_download.sh

# Option 2: Use Kaggle CLI directly
kaggle competitions download -c playground-series-s6e9
```

Place the downloaded CSVs under `data/`. All `data/*.csv` files are gitignored by default.

## What is this repo for?

This repository contains code, documentation, small JSON artifacts, and Speckit prompts for the Kaggle Playground Series S6E9 competition: **Predicting Electric Vehicle Purchases**. The competition metric is ROC-AUC.

Important: Do not submit to Kaggle unless Brett explicitly asks for a submission.

## Where do results live?

Results and analysis are tracked in two locations:

- **docs/RESULTS.md** — human-readable results and findings
- **artifacts/baseline_summary.json** — metadata and summary statistics

Large files such as out-of-fold predictions and probability CSVs remain local and are gitignored to keep the repository lightweight.

## Speckit

Brett has added Speckit to this project. All agent-facing prompts and FAQ documentation should be kept under `prompts/` at the repository root. This ensures Speckit and chat conversations stay in sync and reduces repetitive questions and copy-paste overhead.
