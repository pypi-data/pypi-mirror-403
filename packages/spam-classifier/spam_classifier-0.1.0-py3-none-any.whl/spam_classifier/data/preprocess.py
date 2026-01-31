import re
import string
from typing import Any


def preprocess_text(text: Any) -> str:
    if not isinstance(text, str):
        return ""

    # Приведение к нижнему регистру и базовая очистка
    text = text.strip().lower()

    # Удаление html-тегов
    text = re.sub(r"<[^>]+>", " ", text)

    # Замена типовых паттернов на токены
    text = re.sub(r"(https?://\S+|www\.\S+)", " __URL__ ", text)
    text = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", " __EMAIL__ ", text)
    text = re.sub(r"\b(?:\+?\d[\d\-\s\(\)]{7,}\d)\b", " __PHONE__ ", text)
    text = re.sub(r"\b(?:[$€£₽]\s?\d+|\d+\s?[$€£₽])\b", " __MONEY__ ", text)
    text = re.sub(r"\b\d+\b", " __NUM__ ", text)

    # Ограничение повторов символов (loooove -> loove)
    text = re.sub(r"(.)\1{2,}", r"\1\1", text)

    # Удаление пунктуации (кроме подчёркивания, чтобы не ломать токены)
    punctuation = string.punctuation.replace("_", "")
    text = re.sub(f"[{re.escape(punctuation)}]", " ", text)

    # Нормализация пробелов
    text = re.sub(r"\s+", " ", text).strip()

    return text
