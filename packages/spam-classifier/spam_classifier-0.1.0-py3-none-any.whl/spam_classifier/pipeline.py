from typing import Iterable

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer

from spam_classifier.config.core import Config
from spam_classifier.data.preprocess import preprocess_text


def preprocess_series(texts: Iterable[str] | pd.Series | str) -> pd.Series:
    if isinstance(texts, pd.Series):
        return texts.apply(preprocess_text)
    if isinstance(texts, str):
        return pd.Series([texts]).apply(preprocess_text)
    return pd.Series(list(texts)).apply(preprocess_text)


# Создание пайплайна
def define_pipeline(config: Config):
    model = Pipeline(
        [
            ("preprocess", FunctionTransformer(preprocess_series, validate=False)),
            ("tfidf", TfidfVectorizer()),
            ("clf", LogisticRegression(C=config.model.params.C, max_iter=config.model.params.max_iter)),
        ]
    )
    return model
