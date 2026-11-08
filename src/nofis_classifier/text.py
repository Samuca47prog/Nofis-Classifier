import re
import unicodedata
from collections.abc import Iterable

import pandas as pd


def strip_accents(value: str) -> str:
    """Remove acentos do texto."""
    text = unicodedata.normalize("NFKD", value)
    return "".join(char for char in text if not unicodedata.combining(char))


def normalize_text(value: object, *, case: str = "lower") -> str:
    """Normaliza texto livre para comparação, filtros e preparação dos modelos."""
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
    """Normaliza descrições de produtos para o TF-IDF e a consolidação de duplicatas."""
    return normalize_text(value, case="lower")


def normalize_column_name(column_name: object) -> str:
    """Normaliza o nome de uma coluna para detectar os campos esperados."""
    return normalize_text(column_name, case="upper")


def normalize_filter_values(values: Iterable[object]) -> list[str]:
    """Normaliza valores de filtro e retorna os valores únicos não vazios."""
    normalized = [normalize_text(value, case="upper") for value in values]
    return sorted({value for value in normalized if value})
