from pathlib import Path

import pandas as pd
import pytest

from nofis_classifier.datasets import (
    DEFAULT_PERIOD_LABEL,
    FILTERED_MARKET_DATASET_NAME,
    compact_month,
    most_frequent_by_description,
    prepare_modeling_items,
    processed_dataset_path,
)


def processed_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "descricao_normalizada": ["arroz branco", "feijao preto", "leite integral"],
            "frequencia": [10, 5, 3],
            "descricao_original_exemplo": ["ARROZ BRANCO", "FEIJAO PRETO", "LEITE INTEGRAL"],
            "descricoes_originais_distintas": [1, 1, 1],
            "primeiro_mes": ["2025-01", "2025-01", "2025-01"],
            "ultimo_mes": ["2025-04", "2025-04", "2025-04"],
            "meses_presentes": [4, 4, 4],
            "codigo_ncm_mais_frequente": [10063021, 7133399, 4012010],
            "ncm_tipo_mais_frequente": ["arroz", "feijao", "leite"],
        }
    )


def test_processed_dataset_path_uses_standard_layout(tmp_path: Path) -> None:
    expected = (
        tmp_path
        / "data"
        / "processed"
        / FILTERED_MARKET_DATASET_NAME
        / f"{FILTERED_MARKET_DATASET_NAME}-{DEFAULT_PERIOD_LABEL}.parquet"
    )

    assert processed_dataset_path(root=tmp_path) == expected


def test_prepare_modeling_items_preserves_frequency_and_adds_stable_id() -> None:
    prepared = prepare_modeling_items(processed_frame())

    assert prepared["frequencia"].sum() == 18
    assert prepared["descricao_normalizada"].is_unique
    assert prepared["descricao_id"].tolist() == list(range(len(prepared)))


def test_prepare_modeling_items_rejects_duplicates() -> None:
    frame = processed_frame()
    frame.loc[1, "descricao_normalizada"] = frame.loc[0, "descricao_normalizada"]

    with pytest.raises(ValueError, match="duplicadas"):
        prepare_modeling_items(frame)


def test_most_frequent_by_description_returns_modal_value() -> None:
    frame = pd.DataFrame(
        {
            "descricao_normalizada": ["arroz", "arroz", "feijao"],
            "ncm": ["1006", "1006", "0713"],
        }
    )

    result = most_frequent_by_description(frame, "ncm", "ncm_mais_frequente")

    assert result.to_dict(orient="records") == [
        {"descricao_normalizada": "arroz", "ncm_mais_frequente": "1006"},
        {"descricao_normalizada": "feijao", "ncm_mais_frequente": "0713"},
    ]


def test_compact_month_removes_separator() -> None:
    assert compact_month("2025-04") == "202504"
