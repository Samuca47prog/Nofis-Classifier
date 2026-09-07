import pandas as pd
import pytest

from nofis_classifier.tfidf import (
    TfidfExperimentConfig,
    fit_tfidf_experiment,
    prepare_modeling_dataframe,
    run_tfidf_experiments,
)


def modeling_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "descricao_normalizada": [
                "arroz branco tipo um",
                "feijao preto pacote",
                "leite integral caixa",
                "arroz parboilizado",
            ],
            "frequencia": [10, 5, 3, 2],
            "descricao_original_exemplo": [
                "ARROZ BRANCO TIPO 1",
                "FEIJAO PRETO PACOTE",
                "LEITE INTEGRAL CAIXA",
                "ARROZ PARBOILIZADO",
            ],
            "codigo_ncm_mais_frequente": [10063021, 7133399, 4012010, 10063021],
            "ncm_tipo_mais_frequente": ["arroz", "feijao", "leite", "arroz"],
        }
    )


def test_prepare_modeling_dataframe_preserves_frequency_and_adds_stable_id() -> None:
    prepared = prepare_modeling_dataframe(modeling_frame())

    assert prepared["frequencia"].sum() == 20
    assert prepared["descricao_normalizada"].is_unique
    assert prepared["descricao_normalizada"].str.len().min() > 0
    assert prepared["descricao_id"].tolist() == list(range(len(prepared)))


def test_prepare_modeling_dataframe_rejects_duplicate_descriptions() -> None:
    frame = modeling_frame()
    frame.loc[1, "descricao_normalizada"] = frame.loc[0, "descricao_normalizada"]

    with pytest.raises(ValueError, match="duplicadas"):
        prepare_modeling_dataframe(frame)


def test_fit_tfidf_experiment_respects_document_count_and_feature_limit() -> None:
    prepared = prepare_modeling_dataframe(modeling_frame())
    config = TfidfExperimentConfig(
        name="word_test",
        analyzer="word",
        ngram_range=(1, 1),
        min_df=1,
        max_features=5,
    )

    vectorizer, matrix = fit_tfidf_experiment(prepared["descricao_normalizada"], config)

    assert matrix.shape[0] == len(prepared)
    assert matrix.shape[1] <= 5
    assert len(vectorizer.get_feature_names_out()) == matrix.shape[1]


def test_run_tfidf_experiments_returns_summary_and_samples() -> None:
    prepared = prepare_modeling_dataframe(modeling_frame())
    configs = [
        TfidfExperimentConfig(
            name="char_test",
            analyzer="char_wb",
            ngram_range=(3, 4),
            min_df=1,
            max_features=20,
        )
    ]

    summary, samples, vectorizers, matrices = run_tfidf_experiments(prepared, configs)

    assert summary.loc[0, "name"] == "char_test"
    assert summary.loc[0, "document_count"] == len(prepared)
    assert not samples.empty
    assert "char_test" in vectorizers
    assert matrices["char_test"].shape[0] == len(prepared)
