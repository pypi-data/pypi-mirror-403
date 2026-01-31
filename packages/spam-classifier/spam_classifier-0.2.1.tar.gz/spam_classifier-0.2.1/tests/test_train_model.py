"""Integration tests for training, saving artifacts, and logging."""

from pathlib import Path

import pandas as pd
import pytest
import yaml

import spam_classifier.config.core as core_mod
import spam_classifier.train_model as train_mod
import spam_classifier.utils as utils_mod
from spam_classifier.train_model import train_model


def write_config(path: Path) -> None:
    config = {
        "data": {"test_size": 0.1, "random_state": 42},
        "model": {
            "model_type": "logistic_regression",
            "model_name": "spam_classifier.pkl",
            "vectorizer_path": "models/vectorizer.pkl",
            "params": {"C": 1.0, "max_iter": 100},
        },
        "training": {
            "save_model": True,
            "test_mode": False,
            "run_validation": False,
            "use_holdout": False,
            "metrics": ["accuracy"],
            "log_to_file": True,
            "cv_folds": 3,
        },
    }
    with open(path, "w") as f:
        yaml.safe_dump(config, f)


def test_train_model_saves_model_and_log(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Train a tiny model and verify model/log artifacts are created."""
    processed_dir = tmp_path / "processed"
    models_dir = tmp_path / "models"
    logs_dir = tmp_path / "logs"
    processed_dir.mkdir()

    train_df = pd.DataFrame({"text": ["free prize", "hello friend"], "label": [1, 0]})
    train_df.to_csv(processed_dir / "train.csv", index=False)

    cfg_path = tmp_path / "config.yaml"
    write_config(cfg_path)

    version_file = tmp_path / "_VERSION"
    version_file.write_text("1.2.3", encoding="utf-8")

    monkeypatch.setattr(train_mod, "PROCESSED_DATA_PATH", processed_dir)
    monkeypatch.setattr(train_mod, "TRAINED_MODEL_DIR", models_dir)
    monkeypatch.setattr(utils_mod, "LOG_DIR", logs_dir)
    monkeypatch.setattr(core_mod, "VERSION_FILE_PATH", version_file)

    train_model(cfg_path)

    assert (models_dir / "spam_classifier_v1.2.3.pkl").is_file()
    assert (logs_dir / "logs_1.2.3.log").is_file()
