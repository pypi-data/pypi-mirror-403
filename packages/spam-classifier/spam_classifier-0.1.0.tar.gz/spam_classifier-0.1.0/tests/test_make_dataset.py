"""Tests for dataset preparation and holdout handling."""

from pathlib import Path

import pandas as pd
import pytest
import yaml

import spam_classifier.data.make_dataset as make_dataset_mod
from spam_classifier.config import paths as paths_mod
from spam_classifier.data.make_dataset import load_data


def write_config(path: Path, use_holdout: bool) -> None:
    config = {
        "data": {"test_size": 0.5, "random_state": 42},
        "model": {
            "model_type": "logistic_regression",
            "model_name": "spam_classifier.pkl",
            "vectorizer_path": "models/vectorizer.pkl",
            "params": {"C": 1.0, "max_iter": 100},
        },
        "training": {
            "save_model": False,
            "test_mode": False,
            "run_validation": True,
            "use_holdout": use_holdout,
            "metrics": ["accuracy"],
            "log_to_file": False,
            "cv_folds": 3,
        },
    }
    with open(path, "w") as f:
        yaml.safe_dump(config, f)


def test_make_dataset_holdout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    raw_dataset: pd.DataFrame,
) -> None:
    """Create train/test splits when holdout is enabled."""
    raw_path = tmp_path / "raw.csv"
    processed_dir = tmp_path / "processed"
    raw_dataset.to_csv(raw_path, index=False)

    monkeypatch.setattr(paths_mod, "RAW_DATA_PATH", raw_path)
    monkeypatch.setattr(paths_mod, "PROCESSED_DATA_PATH", processed_dir)
    monkeypatch.setattr(make_dataset_mod, "RAW_DATA_PATH", raw_path)
    monkeypatch.setattr(make_dataset_mod, "PROCESSED_DATA_PATH", processed_dir)

    cfg_path = tmp_path / "config.yaml"
    write_config(cfg_path, use_holdout=True)

    train, test = load_data(cfg_path)
    assert (processed_dir / "train.csv").is_file()
    assert (processed_dir / "test.csv").is_file()
    assert len(train) + len(test) == len(raw_dataset)


def test_make_dataset_no_holdout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    raw_dataset: pd.DataFrame,
) -> None:
    """Create train-only dataset and remove test.csv when holdout is disabled."""
    raw_path = tmp_path / "raw.csv"
    processed_dir = tmp_path / "processed"
    raw_dataset.to_csv(raw_path, index=False)

    monkeypatch.setattr(paths_mod, "RAW_DATA_PATH", raw_path)
    monkeypatch.setattr(paths_mod, "PROCESSED_DATA_PATH", processed_dir)
    monkeypatch.setattr(make_dataset_mod, "RAW_DATA_PATH", raw_path)
    monkeypatch.setattr(make_dataset_mod, "PROCESSED_DATA_PATH", processed_dir)

    cfg_path = tmp_path / "config.yaml"
    write_config(cfg_path, use_holdout=False)

    train, test = load_data(cfg_path)
    assert (processed_dir / "train.csv").is_file()
    assert not (processed_dir / "test.csv").exists()
    assert test is None
    assert len(train) == len(raw_dataset)
