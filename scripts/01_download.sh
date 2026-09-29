#!/usr/bin/env bash
set -euo pipefail

# Download Kaggle competition data for playground-series-s6e9
# Requires: kaggle CLI installed and ~/.kaggle/kaggle.json configured
# Account: brettbrocato (document only; credentials must be present)

COMPETITION="playground-series-s6e9"
DATA_DIR="data"

echo "Downloading ${COMPETITION} data to ${DATA_DIR}/"

# Check if kaggle CLI is available
if ! command -v kaggle &> /dev/null; then
    echo "Error: kaggle CLI not found. Install with: pip install kaggle"
    exit 1
fi

# Check if credentials exist
if [ ! -f "$HOME/.kaggle/kaggle.json" ]; then
    echo "Error: Kaggle credentials not found at ~/.kaggle/kaggle.json"
    echo "Download your kaggle.json from https://www.kaggle.com/settings and place it at ~/.kaggle/"
    echo "Then run: chmod 600 ~/.kaggle/kaggle.json"
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p "${DATA_DIR}"

# Download competition files
kaggle competitions download -c "${COMPETITION}" -p "${DATA_DIR}"

# Unzip if downloaded as zip
if [ -f "${DATA_DIR}/${COMPETITION}.zip" ]; then
    echo "Unzipping files..."
    unzip -o "${DATA_DIR}/${COMPETITION}.zip" -d "${DATA_DIR}"
    rm "${DATA_DIR}/${COMPETITION}.zip"
fi

echo "Download complete!"
echo "Files in ${DATA_DIR}:"
ls -lh "${DATA_DIR}"/*.csv 2>/dev/null || echo "No CSV files found (check download)"
