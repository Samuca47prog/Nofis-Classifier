import numpy as np
import pandas as pd
import pytest
from sklearn.cluster import KMeans

from nofis_classifier.clustering import (
    build_cluster_review, inspect_documents, load_local_model, predict_categories,
    rank_experiments, run_clustering_grid, save_review_once, split_descriptions,
)
from nofis_classifier.tfidf import TfidfExperimentConfig


@pytest.fixture
def items():
    descriptions = [
        f"{product} marca{letter} pacote" for product in ("arroz branco", "sabao limpeza", "leite integral")
        for letter in ("aa", "bb", "cc", "dd", "ee", "ff")
    ]
    return pd.DataFrame({"descricao_normalizada": descriptions, "frequencia": np.arange(1, 19)})


@pytest.fixture
def config():
    return TfidfExperimentConfig("words", "word", (1, 1), 1, 100)


def test_holdout_is_disjoint_and_not_in_vocabulary(items, config, tmp_path):
    train, holdout = split_descriptions(items, validation_count=3)
    assert set(train.descricao_normalizada).isdisjoint(holdout.descricao_normalizada)
    holdout.loc[:, "descricao_normalizada"] = "exclusivovalidacao"
    metrics = run_clustering_grid(train, [config], [3], [42, 7], tmp_path / "reports", tmp_path / "models")
    assert metrics.status.eq("ok").all()
    assert np.isfinite(metrics.silhouette_cosine).all()
    vectorizer = load_local_model(metrics.iloc[0].vectorizer_path)
    assert "exclusivovalidacao" not in vectorizer.vocabulary_
    ranking = rank_experiments(metrics)
    assert ranking.iloc[0].seed_count == 2
    assert ranking.iloc[0].representative_id in set(metrics.experiment_id)
    assert rank_experiments(metrics.iloc[:1], expected_seeds=[42, 7]).empty


def test_resume_skips_completed_fits_and_rejects_changed_data(items, config, tmp_path, monkeypatch):
    arguments = (items, [config], [3], [42], tmp_path / "reports", tmp_path / "models")
    first = run_clustering_grid(*arguments)
    path = tmp_path / "models" / f"{first.iloc[0].experiment_id}.pkl"
    previous_mtime = path.stat().st_mtime_ns

    def unexpected_fit(*args, **kwargs):
        raise AssertionError("Uma execucao concluida nao deve ser reajustada")

    monkeypatch.setattr(KMeans, "fit", unexpected_fit)
    second = run_clustering_grid(*arguments)
    pd.testing.assert_frame_equal(first, second)
    assert path.stat().st_mtime_ns == previous_mtime
    items.loc[0, "descricao_normalizada"] = "base alterada"
    with pytest.raises(ValueError, match="RUN_ID"):
        run_clustering_grid(*arguments)


def test_review_preserves_labels_and_unknown_text_abstains(items, config, tmp_path):
    metrics = run_clustering_grid(items, [config], [3], [42], tmp_path / "reports", tmp_path / "models")
    row = metrics.iloc[0]
    vectorizer, model = load_local_model(row.vectorizer_path), load_local_model(row.model_path)
    assignments, review = build_cluster_review(items, vectorizer, model, row.experiment_id)
    assert review.descricoes_unicas.sum() == len(items)
    assert review.frequencia_total.sum() == items.frequencia.sum()
    assert assignments.distancia_centroide.notna().all()
    review["avaliacao_qualitativa"] = "coerente"
    review["rotulo_humano"] = "categoria revisada"
    path = tmp_path / "review.csv"
    save_review_once(review, path)
    save_review_once(review.assign(rotulo_humano="perdido"), path)
    assert pd.read_csv(path).rotulo_humano.eq("categoria revisada").all()
    predictions = predict_categories([items.iloc[0].descricao_normalizada, "xyzdesconhecido", ""],
                                     vectorizer, model, review, row.experiment_id)
    assert predictions.categoria.tolist() == ["categoria revisada", "REVISAR", "REVISAR"]
    review["avaliacao_qualitativa"] = "parcialmente coerente"
    assert predict_categories([items.iloc[0].descricao_normalizada], vectorizer, model, review,
                              row.experiment_id).categoria.iloc[0] == "REVISAR"
    with pytest.raises(ValueError, match="experimento"):
        predict_categories(["arroz"], vectorizer, model, review, "outro_modelo")
    assert len(inspect_documents(items, vectorizer, count=5)) == 5


def test_metric_memory_guard_and_failed_config_do_not_stop_grid(items, config, tmp_path):
    invalid = TfidfExperimentConfig("empty", "word", (1, 1), 1000, 100)
    metrics = run_clustering_grid(items, [invalid, config], [3], [42], tmp_path / "reports",
                                  tmp_path / "models", dense_limit_mb=0.000001)
    assert metrics.status.tolist() == ["error", "ok"]
    assert pd.isna(metrics.iloc[1].calinski_harabasz)
    assert "memoria" in metrics.iloc[1].metric_note
    assert np.isfinite(metrics.iloc[1].silhouette_cosine)
    assert len(rank_experiments(metrics)) == 1


def test_degenerate_clusters_are_excluded(items, config, tmp_path):
    items["descricao_normalizada"] = "arroz branco"
    config = TfidfExperimentConfig("identical", "word", (1, 1), 1, 100, max_df=1.0)
    metrics = run_clustering_grid(items, [config], [3], [42], tmp_path / "reports", tmp_path / "models")
    assert metrics.iloc[0].actual_clusters == 1
    assert pd.isna(metrics.iloc[0].silhouette_cosine)
    assert rank_experiments(metrics).empty
