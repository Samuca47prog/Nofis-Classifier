import re
import unicodedata
from collections.abc import Iterable

import pandas as pd


def strip_accents(value: str) -> str:
    """Return text without accent marks."""
    text = unicodedata.normalize("NFKD", value)
    return "".join(char for char in text if not unicodedata.combining(char))


def normalize_text(value: object, *, case: str = "lower") -> str:
    """Normalize free text for matching, filtering, and model preparation."""
    if pd.isna(value):
        return ""

    text = strip_accents(str(value).strip())
    if case == "lower":
        text = text.lower()
        allowed_pattern = r"[^a-z0-9]+"
    elif case == "upper":
        text = text.upper()
        allowed_pattern = r"[^A-Z0-9]+"
    else:
        raise ValueError("case must be 'lower' or 'upper'")

    text = re.sub(allowed_pattern, " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_description(value: object) -> str:
    """Normalize product descriptions for TF-IDF and duplicate consolidation."""
    return normalize_text(value, case="lower")


def normalize_column_name(column_name: object) -> str:
    """Normalize a column name enough to detect expected fields."""
    return normalize_text(column_name, case="upper")


def normalize_filter_values(values: Iterable[object]) -> list[str]:
    """Normalize filter values and return unique non-empty values."""
    normalized = [normalize_text(value, case="upper") for value in values]
    return sorted({value for value in normalized if value})
