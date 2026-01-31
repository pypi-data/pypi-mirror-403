"""Tests for pipeline construction and steps."""

from spam_classifier.config.core import Config, DataConfig, ModelConfig, ModelParams, TrainingConfig
from spam_classifier.pipeline import define_pipeline


def test_define_pipeline_steps() -> None:
    """Ensure pipeline contains preprocess, tfidf, and classifier steps."""
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
            use_holdout=True,
            metrics=["accuracy"],
            log_to_file=False,
            cv_folds=3,
        ),
    )
    pipeline = define_pipeline(config)
    assert list(pipeline.named_steps.keys()) == ["preprocess", "tfidf", "clf"]
