"""CLI prediction tests for single and batch inference."""

from pathlib import Path

import joblib
import pandas as pd
import pytest

import spam_classifier.config.core as core_mod
import spam_classifier.predict as predict_mod
from spam_classifier.config.core import Config, DataConfig, ModelConfig, ModelParams, TrainingConfig
from spam_classifier.pipeline import define_pipeline
from spam_classifier.predict import main


def build_and_save_model(model_path: Path) -> None:
    config = Config(
        data=DataConfig(test_size=0.1, random_state=42),
        model=ModelConfig(
            model_type="logistic_regression",
            model_name="spam_classifier.pkl",
            vectorizer_path="models/vectorizer.pkl",
            params=ModelParams(C=1.0, max_iter=100),
        ),
        training=TrainingConfig(
            save_model=False,
            run_validation=False,
            use_holdout=False,
            metrics=["accuracy"],
            log_to_file=False,
            cv_folds=3,
        ),
    )
    model = define_pipeline(config)
    X = pd.Series(["free prize", "hello friend"])
    y = pd.Series([1, 0])
    model.fit(X, y)
    joblib.dump(model, model_path)


def test_predict_single_message(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Predict on a single message passed via CLI."""
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    model_path = model_dir / "spam_classifier_v1.0.0.pkl"
    build_and_save_model(model_path)

    version_file = tmp_path / "_VERSION"
    version_file.write_text("1.0.0", encoding="utf-8")

    monkeypatch.setattr(predict_mod, "TRAINED_MODEL_DIR", model_dir)
    monkeypatch.setattr(core_mod, "VERSION_FILE_PATH", version_file)

    monkeypatch.setattr("sys.argv", ["prog", "Free prize now"])
    exit_code = main()
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "label=" in out
    assert "score" in out


def test_predict_batch_file_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Predict on a file and write CSV output without message column."""
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    model_path = model_dir / "spam_classifier_v1.0.0.pkl"
    build_and_save_model(model_path)

    version_file = tmp_path / "_VERSION"
    version_file.write_text("1.0.0", encoding="utf-8")

    input_file = tmp_path / "messages.txt"
    input_file.write_text("free prize\nhello friend\n", encoding="utf-8")
    output_file = tmp_path / "preds.csv"

    monkeypatch.setattr(predict_mod, "TRAINED_MODEL_DIR", model_dir)
    monkeypatch.setattr(predict_mod, "ROOT", tmp_path)
    monkeypatch.setattr(core_mod, "VERSION_FILE_PATH", version_file)

    monkeypatch.setattr(
        "sys.argv",
        ["prog", str(input_file), "-o", str(output_file), "--no-message"],
    )
    exit_code = main()
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "Saved predictions to" in out
    assert output_file.is_file()
    content = output_file.read_text(encoding="utf-8").strip().splitlines()
    assert content[0] == "line,label,score"
    assert len(content) == 3
