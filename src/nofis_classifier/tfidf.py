from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer


REQUIRED_MODELING_COLUMNS = (
    "descricao_normalizada",
    "frequencia",
    "descricao_original_exemplo",
    "codigo_ncm_mais_frequente",
    "ncm_tipo_mais_frequente",
)


@dataclass(frozen=True)
class TfidfExperimentConfig:
    """Configuration for one TF-IDF representation experiment."""

    name: str
    analyzer: str
    ngram_range: tuple[int, int]
    min_df: int
    max_features: int
    max_df: float = 0.95
    sublinear_tf: bool = True
    norm: str = "l2"


def default_tfidf_configs() -> list[TfidfExperimentConfig]:
    """Return the TF-IDF configurations planned for the first experiments."""
    configs: list[TfidfExperimentConfig] = []

    for min_df in (2, 5):
        configs.append(
            TfidfExperimentConfig(
                name=f"word_unigram_min_df_{min_df}",
                analyzer="word",
                ngram_range=(1, 1),
                min_df=min_df,
                max_features=10_000,
            )
        )
        configs.append(
            TfidfExperimentConfig(
                name=f"word_unigram_bigram_min_df_{min_df}",
                analyzer="word",
                ngram_range=(1, 2),
                min_df=min_df,
                max_features=10_000,
            )
        )
        configs.append(
            TfidfExperimentConfig(
                name=f"char_wb_3_5_min_df_{min_df}",
                analyzer="char_wb",
                ngram_range=(3, 5),
                min_df=min_df,
                max_features=30_000,
            )
        )

    return configs


def load_modeling_dataset(path: Path | str) -> pd.DataFrame:
    """Load a processed modeling dataset and validate the required columns."""
    frame = pd.read_parquet(path)
    missing_columns = sorted(set(REQUIRED_MODELING_COLUMNS) - set(frame.columns))

    if missing_columns:
        raise ValueError(f"Colunas obrigatorias ausentes: {missing_columns}")

    return frame


def prepare_modeling_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    """Prepare one-row-per-description data for TF-IDF experiments."""
    missing_columns = sorted(set(REQUIRED_MODELING_COLUMNS) - set(frame.columns))

    if missing_columns:
        raise ValueError(f"Colunas obrigatorias ausentes: {missing_columns}")

    initial_frequency_sum = frame["frequencia"].sum()

    prepared = frame.loc[:, REQUIRED_MODELING_COLUMNS].copy()
    prepared["descricao_normalizada"] = prepared["descricao_normalizada"].astype("string").str.strip()
    prepared = prepared[prepared["descricao_normalizada"].notna()]
    prepared = prepared[prepared["descricao_normalizada"] != ""]
    prepared = prepared[prepared["frequencia"] >= 1]

    if prepared["descricao_normalizada"].duplicated().any():
        duplicated_count = int(prepared["descricao_normalizada"].duplicated().sum())
        raise ValueError(f"A base possui {duplicated_count} descricoes normalizadas duplicadas")

    if prepared["frequencia"].sum() != initial_frequency_sum:
        raise ValueError("A preparacao alterou a soma de frequencia")

    prepared = prepared.sort_values("descricao_normalizada").reset_index(drop=True)
    prepared.insert(0, "descricao_id", np.arange(len(prepared), dtype=np.int64))

    return prepared


def fit_tfidf_experiment(
    descriptions: Iterable[str],
    config: TfidfExperimentConfig,
) -> tuple[TfidfVectorizer, sparse.csr_matrix]:
    """Fit a TF-IDF vectorizer for one experiment configuration."""
    vectorizer = TfidfVectorizer(
        analyzer=config.analyzer,
        ngram_range=config.ngram_range,
        min_df=config.min_df,
        max_df=config.max_df,
        max_features=config.max_features,
        sublinear_tf=config.sublinear_tf,
        norm=config.norm,
        stop_words=None,
    )
    matrix = vectorizer.fit_transform(descriptions)

    if matrix.shape[0] == 0 or matrix.shape[1] == 0:
        raise ValueError(f"A configuracao {config.name} gerou matriz vazia")

    if matrix.shape[1] > config.max_features:
        raise ValueError(f"A configuracao {config.name} excedeu max_features")

    return vectorizer, matrix


def summarize_tfidf_matrix(
    config: TfidfExperimentConfig,
    matrix: sparse.csr_matrix,
) -> dict[str, object]:
    """Build summary metrics for a fitted TF-IDF matrix."""
    total_cells = matrix.shape[0] * matrix.shape[1]
    non_zero_values = matrix.nnz
    density = non_zero_values / total_cells if total_cells else 0.0

    return {
        **asdict(config),
        "ngram_range": str(config.ngram_range),
        "document_count": matrix.shape[0],
        "feature_count": matrix.shape[1],
        "non_zero_values": non_zero_values,
        "total_cells": total_cells,
        "density": density,
        "sparsity": 1.0 - density,
    }


def collect_vocabulary_samples(
    vectorizer: TfidfVectorizer,
    matrix: sparse.csr_matrix,
    modeling_frame: pd.DataFrame,
    config_name: str,
    vocabulary_terms: int = 20,
    idf_terms: int = 20,
    frequent_descriptions: int = 10,
    terms_per_description: int = 8,
) -> pd.DataFrame:
    """Collect vocabulary, high-IDF terms, and terms for frequent descriptions."""
    feature_names = np.asarray(vectorizer.get_feature_names_out())
    records: list[dict[str, object]] = []

    for rank, term in enumerate(feature_names[:vocabulary_terms], start=1):
        records.append(
            {
                "config_name": config_name,
                "sample_type": "vocabulary_sample",
                "description": None,
                "frequency": None,
                "rank": rank,
                "term": term,
                "value": None,
            }
        )

    idf_values = vectorizer.idf_
    highest_idf_indexes = np.argsort(idf_values)[::-1][:idf_terms]
    for rank, term_index in enumerate(highest_idf_indexes, start=1):
        records.append(
            {
                "config_name": config_name,
                "sample_type": "highest_idf",
                "description": None,
                "frequency": None,
                "rank": rank,
                "term": feature_names[term_index],
                "value": float(idf_values[term_index]),
            }
        )

    frequent_rows = modeling_frame.nlargest(frequent_descriptions, "frequencia")
    for _, row in frequent_rows.iterrows():
        row_vector = matrix.getrow(int(row["descricao_id"]))
        if row_vector.nnz == 0:
            continue

        local_order = np.argsort(row_vector.data)[::-1][:terms_per_description]
        for rank, local_position in enumerate(local_order, start=1):
            term_index = row_vector.indices[local_position]
            records.append(
                {
                    "config_name": config_name,
                    "sample_type": "top_terms_frequent_description",
                    "description": row["descricao_normalizada"],
                    "frequency": int(row["frequencia"]),
                    "rank": rank,
                    "term": feature_names[term_index],
                    "value": float(row_vector.data[local_position]),
                }
            )

    return pd.DataFrame.from_records(records)


def run_tfidf_experiments(
    modeling_frame: pd.DataFrame,
    configs: Iterable[TfidfExperimentConfig] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, TfidfVectorizer], dict[str, sparse.csr_matrix]]:
    """Fit all TF-IDF experiments and return summaries, samples, vectorizers, and matrices."""
    configs = list(configs or default_tfidf_configs())
    descriptions = modeling_frame["descricao_normalizada"].tolist()
    summary_records: list[dict[str, object]] = []
    sample_frames: list[pd.DataFrame] = []
    vectorizers: dict[str, TfidfVectorizer] = {}
    matrices: dict[str, sparse.csr_matrix] = {}

    for config in configs:
        vectorizer, matrix = fit_tfidf_experiment(descriptions, config)
        summary_records.append(summarize_tfidf_matrix(config, matrix))
        sample_frames.append(collect_vocabulary_samples(vectorizer, matrix, modeling_frame, config.name))
        vectorizers[config.name] = vectorizer
        matrices[config.name] = matrix

    summary = pd.DataFrame.from_records(summary_records)
    vocabulary_samples = pd.concat(sample_frames, ignore_index=True)

    return summary, vocabulary_samples, vectorizers, matrices


def save_tfidf_reports(summary: pd.DataFrame, vocabulary_samples: pd.DataFrame, output_dir: Path | str) -> None:
    """Save TF-IDF experiment reports as CSV files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    summary.to_csv(output_path / "tfidf_experiments_summary.csv", index=False)
    vocabulary_samples.to_csv(output_path / "tfidf_vocabulary_samples.csv", index=False)
