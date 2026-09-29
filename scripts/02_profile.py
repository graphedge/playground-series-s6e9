#!/usr/bin/env python3
"""
Optional EDA profiling script using ydata-profiling.
Generates an HTML report for train.csv.

Usage:
    python scripts/02_profile.py

Output: reports/train_profile.html
"""

import sys
from pathlib import Path

import pandas as pd
from ydata_profiling import ProfileReport

# Paths
DATA_DIR = Path("data")
TRAIN_PATH = DATA_DIR / "train.csv"
REPORT_DIR = Path("reports")
REPORT_PATH = REPORT_DIR / "train_profile.html"

def main():
    if not TRAIN_PATH.exists():
        print(f"Error: {TRAIN_PATH} not found.")
        print("Run scripts/01_download.sh first to download competition data.")
        sys.exit(1)
    
    print(f"Loading {TRAIN_PATH}...")
    df = pd.read_csv(TRAIN_PATH)
    print(f"Shape: {df.shape}")
    
    print("Generating profile report (this may take a few minutes)...")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    
    profile = ProfileReport(
        df,
        title="EV Purchase Prediction - Training Data Profile",
        explorative=True,
        minimal=False,
    )
    
    print(f"Writing report to {REPORT_PATH}...")
    profile.to_file(REPORT_PATH)
    
    print(f"Done! Open {REPORT_PATH} in a browser to view the report.")

if __name__ == "__main__":
    main()
