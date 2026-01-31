import sys
from pathlib import Path
from typing import Union

import joblib
import pandas as pd
from sklearn.metrics import classification_report
from sklearn.model_selection import StratifiedKFold, cross_validate

from spam_classifier.config.core import create_and_validate_config, fetch_config_from_yaml, read_package_version
from spam_classifier.config.paths import CONFIG_FILE_PATH, PROCESSED_DATA_PATH, TRAINED_MODEL_DIR
from spam_classifier.pipeline import define_pipeline
from spam_classifier.utils import compute_metrics, get_cv_scoring, log_cv_results, setup_logger


def train_model(config_path: Union[str, Path]) -> object:
    parsed_config = fetch_config_from_yaml(Path(config_path))
    config = create_and_validate_config(parsed_config)
    version = read_package_version()
    logger = setup_logger(config.training.log_to_file, version)

    # Загрузка данных
    train_data = pd.read_csv(PROCESSED_DATA_PATH.joinpath("train.csv"))
    logger.info("Train data loaded: %s rows", len(train_data))

    model = define_pipeline(config)

    # Кросс-валидация на обучающей выборке
    if config.training.run_validation:
        scoring = get_cv_scoring(config.training.metrics)
        if scoring:
            cv = StratifiedKFold(
                n_splits=config.training.cv_folds,
                shuffle=True,
                random_state=config.data.random_state,
            )
            cv_results = cross_validate(
                model,
                train_data["text"],
                train_data["label"],
                cv=cv,
                scoring=scoring,
                n_jobs=None,
            )
            log_cv_results(logger, cv_results)

    # Обучение финальной модели на всей обучающей выборке
    model.fit(train_data["text"], train_data["label"])
    logger.info("Training completed")

    # Оценка финальной модели на holdout-тесте
    if config.training.use_holdout:
        test_path = PROCESSED_DATA_PATH.joinpath("test.csv")
        if test_path.is_file():
            test_data = pd.read_csv(test_path)
            logger.info("Holdout test data loaded: %s rows", len(test_data))
            preds = model.predict(test_data["text"])
            y_score = None
            if "roc_auc" in config.training.metrics and hasattr(model, "predict_proba"):
                y_score = model.predict_proba(test_data["text"])[:, 1]
            metrics = compute_metrics(
                test_data["label"],
                preds,
                y_score,
                config.training.metrics,
            )
            for name, value in metrics.items():
                logger.info("holdout.%s=%.4f", name, value)
            report = classification_report(
                test_data["label"],
                preds,
                digits=4,
            )
            logger.info("classification_report:\n%s", report)
        else:
            logger.warning("Holdout evaluation skipped: test.csv not found at %s", test_path)

    # Сохранение модели
    if config.training.save_model:
        TRAINED_MODEL_DIR.mkdir(parents=True, exist_ok=True)
        path_to_model = TRAINED_MODEL_DIR.joinpath(f"spam_classifier_v{version}.pkl")
        joblib.dump(model, path_to_model)
        logger.info("Model saved to %s", path_to_model)

    return model


if __name__ == "__main__":
    if len(sys.argv) > 1:
        train_model(sys.argv[1])
    else:
        train_model(CONFIG_FILE_PATH)
