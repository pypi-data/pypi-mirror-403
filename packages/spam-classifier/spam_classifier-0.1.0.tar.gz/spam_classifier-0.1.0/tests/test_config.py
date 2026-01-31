"""Config validation tests for typed YAML configuration."""

import pytest

from spam_classifier.config.core import create_and_validate_config


def test_config_validates_ok() -> None:
    """Ensure a minimal valid config is accepted by Pydantic."""
    parsed = {
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
            "run_validation": True,
            "use_holdout": True,
            "metrics": ["accuracy"],
            "log_to_file": False,
            "cv_folds": 3,
        },
    }
    config = create_and_validate_config(parsed)
    assert config.data.test_size == 0.1
    assert config.training.use_holdout is True


def test_config_invalid_type_raises() -> None:
    """Reject configs with invalid field types."""
    parsed = {
        "data": {"test_size": "bad", "random_state": 42},
        "model": {
            "model_type": "logistic_regression",
            "model_name": "spam_classifier.pkl",
            "vectorizer_path": "models/vectorizer.pkl",
            "params": {"C": 1.0, "max_iter": 100},
        },
        "training": {
            "save_model": True,
            "test_mode": False,
            "run_validation": True,
            "use_holdout": True,
            "metrics": ["accuracy"],
            "log_to_file": False,
            "cv_folds": 3,
        },
    }
    with pytest.raises(Exception):
        create_and_validate_config(parsed)
