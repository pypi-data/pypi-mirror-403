import sys
from pathlib import Path
from typing import Optional, Tuple, Union

import pandas as pd
from sklearn.model_selection import train_test_split

from spam_classifier.config.core import create_and_validate_config, fetch_config_from_yaml
from spam_classifier.config.paths import CONFIG_FILE_PATH, PROCESSED_DATA_PATH, RAW_DATA_PATH
from spam_classifier.data.preprocess import preprocess_text


def load_data(config_path: Union[str, Path]) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
    parsed_config = fetch_config_from_yaml(Path(config_path))
    config = create_and_validate_config(parsed_config)

    data = pd.read_csv(RAW_DATA_PATH, encoding="iso-8859-1")
    data = data[["v1", "v2"]].rename(columns={"v1": "label", "v2": "text"})
    data["label"] = data["label"].map({"ham": 0, "spam": 1})

    data.drop_duplicates(inplace=True)

    # Препроцессинг текста
    data["processed_text"] = data["text"].apply(preprocess_text)

    # Разделение данных
    if config.training.use_holdout:
        train, test = train_test_split(
            data,
            test_size=config.data.test_size,
            random_state=config.data.random_state,
            stratify=data["label"],
        )
    else:
        train = data
        test = None

    # Сохранение данных
    PROCESSED_DATA_PATH.mkdir(parents=True, exist_ok=True)
    train.to_csv(PROCESSED_DATA_PATH.joinpath("train.csv"), index=False)
    test_path = PROCESSED_DATA_PATH.joinpath("test.csv")
    if test is not None:
        test.to_csv(test_path, index=False)
    elif test_path.is_file():
        test_path.unlink()

    return train, test


if __name__ == "__main__":
    if len(sys.argv) > 1:
        load_data(sys.argv[1])
    else:
        load_data(CONFIG_FILE_PATH)
