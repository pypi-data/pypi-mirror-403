from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from yaml import safe_load

from spam_classifier.config.paths import CONFIG_FILE_PATH, VERSION_FILE_PATH


class DataConfig(BaseModel):
    test_size: float
    random_state: int


class ModelParams(BaseModel):
    C: float
    max_iter: int


class ModelConfig(BaseModel):
    model_type: str
    model_name: str
    vectorizer_path: str
    params: ModelParams


class TrainingConfig(BaseModel):
    save_model: bool
    run_validation: bool = True
    use_holdout: bool = False
    metrics: List[str] = ["accuracy", "precision", "recall", "f1", "roc_auc"]
    log_to_file: bool = True
    cv_folds: int = 5


class Config(BaseModel):
    data: DataConfig
    model: ModelConfig
    training: TrainingConfig


def find_config_file() -> Path:
    if CONFIG_FILE_PATH.is_file():
        return CONFIG_FILE_PATH
    raise FileNotFoundError(f"Config not found at {CONFIG_FILE_PATH!r}")


def fetch_config_from_yaml(cfg_path: Optional[Path] = None) -> Dict[str, Any]:
    if not cfg_path:
        cfg_path = find_config_file()

    if cfg_path:
        with open(cfg_path) as conf_file:
            parsed_config = safe_load(conf_file.read())
            if not isinstance(parsed_config, dict):
                raise ValueError("Expected YAML config to be a dictionary")
            return parsed_config
    raise OSError(f"Did not find config file at path: {cfg_path}")


def create_and_validate_config(parsed_config: Optional[Dict[str, Any]] = None) -> Config:
    if parsed_config is None:
        parsed_config = fetch_config_from_yaml()

    _config = Config(
        data=DataConfig(**parsed_config["data"]),
        model=ModelConfig(**parsed_config["model"]),
        training=TrainingConfig(**parsed_config["training"]),
    )

    return _config


def read_package_version() -> str:
    if VERSION_FILE_PATH.is_file():
        version = VERSION_FILE_PATH.read_text(encoding="utf-8").strip()
        if version:
            return version
    raise FileNotFoundError(f"Version file not found or empty at {VERSION_FILE_PATH!r}")
