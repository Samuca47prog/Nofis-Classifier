import pytest

from nofis_classifier.text import normalize_column_name, normalize_description, normalize_filter_values, normalize_text


def test_normalize_description_removes_accents_case_and_extra_spaces() -> None:
    assert normalize_description("  Açúcar CRISTAL  1KG!!! ") == "acucar cristal 1kg"


def test_normalize_description_returns_empty_string_for_missing_value() -> None:
    assert normalize_description(None) == ""


def test_normalize_column_name_keeps_uppercase_tokens() -> None:
    assert normalize_column_name("Descrição do Produto/Serviço") == "DESCRICAO DO PRODUTO SERVICO"


def test_normalize_filter_values_returns_unique_non_empty_uppercase_values() -> None:
    assert normalize_filter_values([" Mercado A ", "mercado-á", "", None]) == ["MERCADO A"]


def test_normalize_text_rejects_unknown_case() -> None:
    with pytest.raises(ValueError, match="case"):
        normalize_text("abc", case="title")
