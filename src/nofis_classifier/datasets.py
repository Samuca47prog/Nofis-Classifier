from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from nofis_classifier.paths import find_project_root
from nofis_classifier.schema import (
    DESCRIPTION_NORMALIZED,
    FREQUENCY,
    PROCESSED_MODELING_COLUMNS,
    TFIDF_REQUIRED_COLUMNS,
    validate_columns,
)


FILTERED_MARKET_DATASET_NAME = "items-notas-fiscais-filtros-combinados"
FULL_ITEMS_DATASET_NAME = "items-notas-fiscais"
DEFAULT_PERIOD_LABEL = "202501-202504"


def dataset_dir(stage: str, dataset_name: str, root: Path | str | None = None) -> Path:
    """Retorna o diretório padrão de um dataset no estágio informado."""
    project_root = Path(root) if root is not None else find_project_root()
    return project_root / "data" / stage / dataset_name


def processed_dataset_path(
    dataset_name: str = FILTERED_MARKET_DATASET_NAME,
    period_label: str = DEFAULT_PERIOD_LABEL,
    root: Path | str | None = None,
) -> Path:
    """Retorna o caminho do Parquet processado para o dataset e o período informados."""
    filename = f"{dataset_name}-{period_label}.parquet"
    return dataset_dir("processed", dataset_name, root=root) / filename


def compact_month(period: str) -> str:
    """Converte YYYY-MM em YYYYMM para nomes de artefatos."""
    return period.replace("-", "")


def load_processed_items(path: Path | str) -> pd.DataFrame:
    """Carrega um dataset processado de itens e valida o esquema de modelagem."""
    frame = pd.read_parquet(path)
    validate_columns(frame, PROCESSED_MODELING_COLUMNS)
    return frame


def prepare_modeling_items(frame: pd.DataFrame) -> pd.DataFrame:
    """Prepara uma linha por descrição normalizada para o TF-IDF e a clusterização."""
    validate_columns(frame, TFIDF_REQUIRED_COLUMNS)
    initial_frequency_sum = frame[FREQUENCY].sum()

    prepared = frame.copy()
    prepared[DESCRIPTION_NORMALIZED] = prepared[DESCRIPTION_NORMALIZED].astype("string").str.strip()
    prepared = prepared[prepared[DESCRIPTION_NORMALIZED].notna()]
    prepared = prepared[prepared[DESCRIPTION_NORMALIZED] != ""]
    prepared = prepared[prepared[FREQUENCY] >= 1]

    prepared = (
        prepared.groupby(DESCRIPTION_NORMALIZED, as_index=False, sort=False)[FREQUENCY]
        .sum()
    )

    if prepared[FREQUENCY].sum() != initial_frequency_sum:
        raise ValueError("A preparacao alterou a soma de frequencia")

    prepared = prepared.sort_values(DESCRIPTION_NORMALIZED).reset_index(drop=True)
    prepared.insert(0, "descricao_id", np.arange(len(prepared), dtype=np.int64))
    return prepared


def most_frequent_by_description(
    frame: pd.DataFrame,
    value_column: str,
    output_column: str,
) -> pd.DataFrame:
    """Retorna o valor mais comum por descrição normalizada."""
    validate_columns(frame, (DESCRIPTION_NORMALIZED, value_column))

    valid = frame[[DESCRIPTION_NORMALIZED, value_column]].dropna(subset=[value_column]).copy()
    valid = valid[valid[value_column].astype(str).str.strip() != ""]
    if valid.empty:
        return pd.DataFrame(columns=[DESCRIPTION_NORMALIZED, output_column])

    weighted = (
        valid.groupby([DESCRIPTION_NORMALIZED, value_column], as_index=False)
        .size()
        .sort_values([DESCRIPTION_NORMALIZED, "size"], ascending=[True, False])
    )
    return weighted.drop_duplicates(DESCRIPTION_NORMALIZED)[[DESCRIPTION_NORMALIZED, value_column]].rename(
        columns={value_column: output_column}
    )
