from pathlib import Path

import spam_classifier

# Project Directories
PACKAGE_ROOT = Path(spam_classifier.__file__).resolve().parent
ROOT = PACKAGE_ROOT.parent
CONFIG_FILE_PATH = ROOT / "config.yaml"
DATASET_DIR = ROOT / "data"
RAW_DATA_PATH = DATASET_DIR / "raw" / "spam.csv"
PROCESSED_DATA_PATH = DATASET_DIR / "processed"
TRAINED_MODEL_DIR = PACKAGE_ROOT / "models"
LOG_DIR = PACKAGE_ROOT / "logs"
VERSION_FILE_PATH = PACKAGE_ROOT / "_VERSION"
