import pandas as pd
import pytest

from nofis_classifier.schema import (
    DESCRIPTION_NORMALIZED,
    FREQUENCY,
    find_column,
    validate_columns,
)


def test_find_column_matches_normalized_tokens() -> None:
    columns = pd.Index(["NÚMERO PRODUTO", "DESCRIÇÃO DO PRODUTO/SERVIÇO", "CÓDIGO NCM/SH"])

    assert find_column(columns, ("descricao", "produto")) == "DESCRIÇÃO DO PRODUTO/SERVIÇO"


def test_find_column_raises_clear_error_when_missing() -> None:
    with pytest.raises(KeyError, match="tokens"):
        find_column(["A", "B"], ("descricao",))


def test_validate_columns_raises_clear_error_when_missing() -> None:
    frame = pd.DataFrame({DESCRIPTION_NORMALIZED: ["arroz"]})

    with pytest.raises(ValueError, match=FREQUENCY):
        validate_columns(frame, (DESCRIPTION_NORMALIZED, FREQUENCY))
