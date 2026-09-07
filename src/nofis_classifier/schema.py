from collections.abc import Iterable, Sequence

import pandas as pd

from nofis_classifier.text import normalize_column_name


DESCRIPTION_NORMALIZED = "descricao_normalizada"
FREQUENCY = "frequencia"
DESCRIPTION_EXAMPLE = "descricao_original_exemplo"
DISTINCT_ORIGINAL_DESCRIPTIONS = "descricoes_originais_distintas"
FIRST_MONTH = "primeiro_mes"
LAST_MONTH = "ultimo_mes"
PRESENT_MONTHS = "meses_presentes"
MOST_FREQUENT_NCM_CODE = "codigo_ncm_mais_frequente"
MOST_FREQUENT_NCM_TYPE = "ncm_tipo_mais_frequente"

PROCESSED_MODELING_COLUMNS = (
    DESCRIPTION_NORMALIZED,
    FREQUENCY,
    DESCRIPTION_EXAMPLE,
    DISTINCT_ORIGINAL_DESCRIPTIONS,
    FIRST_MONTH,
    LAST_MONTH,
    PRESENT_MONTHS,
    MOST_FREQUENT_NCM_CODE,
    MOST_FREQUENT_NCM_TYPE,
)

TFIDF_REQUIRED_COLUMNS = (
    DESCRIPTION_NORMALIZED,
    FREQUENCY,
    DESCRIPTION_EXAMPLE,
    MOST_FREQUENT_NCM_CODE,
    MOST_FREQUENT_NCM_TYPE,
)


def find_column(columns: Iterable[object], required_tokens: Sequence[str]) -> object:
    """Find the first column whose normalized name contains all required tokens."""
    normalized_tokens = tuple(normalize_column_name(token) for token in required_tokens)

    for column in columns:
        normalized = normalize_column_name(column)
        if all(token in normalized for token in normalized_tokens):
            return column

    raise KeyError(f"Nao encontrei coluna com tokens {tuple(required_tokens)}. Colunas: {list(columns)}")


def validate_columns(frame: pd.DataFrame, required_columns: Sequence[str]) -> None:
    """Raise a clear error when a dataframe is missing required columns."""
    missing_columns = sorted(set(required_columns) - set(frame.columns))

    if missing_columns:
        raise ValueError(f"Colunas obrigatorias ausentes: {missing_columns}")
