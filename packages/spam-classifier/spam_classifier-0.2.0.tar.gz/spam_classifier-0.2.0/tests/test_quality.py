import joblib
import pandas as pd
import pytest
from sklearn.metrics import recall_score

from spam_classifier.config.core import (
    Config,
    DataConfig,
    ModelConfig,
    ModelParams,
    TrainingConfig,
    read_package_version,
)
from spam_classifier.config.paths import PROCESSED_DATA_PATH, TRAINED_MODEL_DIR
from spam_classifier.pipeline import define_pipeline


def test_recall_threshold_on_fixture(test_dataset: pd.DataFrame) -> None:
    """Quality smoke-test on a fixed synthetic dataset (recall >= 0.8)."""
    config = Config(
        data=DataConfig(test_size=0.1, random_state=42),
        model=ModelConfig(
            model_type="logistic_regression",
            model_name="spam_classifier.pkl",
            vectorizer_path="models/vectorizer.pkl",
            params=ModelParams(C=1.0, max_iter=200),
        ),
        training=TrainingConfig(
            save_model=False,
            run_validation=False,
            use_holdout=False,
            metrics=["recall"],
            log_to_file=False,
            cv_folds=3,
        ),
    )
    model = define_pipeline(config)
    model.fit(test_dataset["text"], test_dataset["label"])
    preds = model.predict(test_dataset["text"])
    recall = recall_score(test_dataset["label"], preds, zero_division=0)
    assert recall >= 0.95


@pytest.mark.quality
def test_model_quality_on_real_data() -> None:
    """Quality gate on real holdout data with a trained model (recall >= 0.8)."""
    version = read_package_version()
    model_path = TRAINED_MODEL_DIR / f"spam_classifier_v{version}.pkl"
    if not model_path.is_file():
        pytest.skip("Trained model not found; run training before quality test")

    test_path = PROCESSED_DATA_PATH / "test.csv"
    if not test_path.is_file():
        pytest.skip("test.csv not found; run make process_data before quality test")

    import pandas as pd

    model = joblib.load(model_path)
    test_df = pd.read_csv(test_path)
    preds = model.predict(test_df["text"])
    recall = recall_score(test_df["label"], preds, zero_division=0)
    assert recall >= 0.85
