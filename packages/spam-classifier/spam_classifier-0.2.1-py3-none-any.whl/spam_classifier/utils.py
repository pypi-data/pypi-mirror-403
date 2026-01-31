import logging
from statistics import mean, pstdev
from typing import Dict, Iterable, Sequence

from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score

from spam_classifier.config.paths import LOG_DIR


def setup_logger(log_to_file: bool, version: str) -> logging.Logger:
    logger = logging.getLogger("spam_classifier.training")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_to_file:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        for existing in LOG_DIR.glob("logs_*.log"):
            existing.unlink()
        log_name = f"logs_{version}.log"
        file_handler = logging.FileHandler(LOG_DIR / log_name, mode="w")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def compute_metrics(y_true, y_pred, y_score, metrics: Iterable[str]) -> Dict[str, float]:
    results: Dict[str, float] = {}
    for metric in metrics:
        if metric == "accuracy":
            results[metric] = accuracy_score(y_true, y_pred)
        elif metric == "precision":
            results[metric] = precision_score(y_true, y_pred, zero_division=0)
        elif metric == "recall":
            results[metric] = recall_score(y_true, y_pred, zero_division=0)
        elif metric == "f1":
            results[metric] = f1_score(y_true, y_pred, zero_division=0)
        elif metric == "roc_auc" and y_score is not None:
            results[metric] = roc_auc_score(y_true, y_score)
    return results


def get_cv_scoring(metrics: Iterable[str]) -> Dict[str, str]:
    scoring: Dict[str, str] = {}
    for metric in metrics:
        if metric in {"accuracy", "precision", "recall", "f1", "roc_auc"}:
            scoring[metric] = metric
    return scoring


def log_cv_results(logger: logging.Logger, cv_results: Dict[str, Sequence[float]]) -> None:
    for key, values in cv_results.items():
        if not key.startswith("test_"):
            continue
        name = key.replace("test_", "")
        for idx, value in enumerate(values, start=1):
            logger.info("cv.fold_%d.%s=%.4f", idx, name, value)
        mean_val = mean(values)
        std_val = pstdev(values)
        logger.info("cv.%s_mean=%.4f cv.%s_std=%.4f", name, mean_val, name, std_val)
