from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from nofis_classifier.datasets import (
    FILTERED_MARKET_DATASET_NAME,
    DEFAULT_PERIOD_LABEL,
    load_processed_items,
    prepare_modeling_items,
    processed_dataset_path,
)
from nofis_classifier.experiments import ExperimentRecord, append_experiment_records, create_experiment_record
from nofis_classifier.schema import DESCRIPTION_NORMALIZED, FREQUENCY


BASELINE_TFIDF_CONFIG_NAME = "char_wb_3_5_min_df_2"


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


def fit_tfidf_experiment(
    descriptions: Iterable[str],
    config: TfidfExperimentConfig,
) -> tuple[TfidfVectorizer, Any]:
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


def summarize_tfidf_matrix(config: TfidfExperimentConfig, matrix: Any) -> dict[str, object]:
    """Build summary metrics for a fitted TF-IDF matrix."""
    total_cells = matrix.shape[0] * matrix.shape[1]
    non_zero_values = matrix.nnz
    density = non_zero_values / total_cells if total_cells else 0.0
    config_values = asdict(config)
    config_values["ngram_range"] = str(config.ngram_range)

    return {
        **config_values,
        "document_count": matrix.shape[0],
        "feature_count": matrix.shape[1],
        "non_zero_values": non_zero_values,
        "total_cells": total_cells,
        "density": density,
        "sparsity": 1.0 - density,
    }


def collect_vocabulary_samples(
    vectorizer: TfidfVectorizer,
    matrix: Any,
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

    frequent_rows = modeling_frame.nlargest(frequent_descriptions, FREQUENCY)
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
                    "description": row[DESCRIPTION_NORMALIZED],
                    "frequency": int(row[FREQUENCY]),
                    "rank": rank,
                    "term": feature_names[term_index],
                    "value": float(row_vector.data[local_position]),
                }
            )

    return pd.DataFrame.from_records(records)


def run_tfidf_experiments(
    modeling_frame: pd.DataFrame,
    configs: Iterable[TfidfExperimentConfig] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, TfidfVectorizer], dict[str, Any]]:
    """Fit all TF-IDF experiments and return summaries, samples, vectorizers, and matrices."""
    configs = list(configs or default_tfidf_configs())
    descriptions = modeling_frame[DESCRIPTION_NORMALIZED].tolist()
    summary_records: list[dict[str, object]] = []
    sample_frames: list[pd.DataFrame] = []
    vectorizers: dict[str, TfidfVectorizer] = {}
    matrices: dict[str, Any] = {}

    for config in configs:
        vectorizer, matrix = fit_tfidf_experiment(descriptions, config)
        summary_records.append(summarize_tfidf_matrix(config, matrix))
        sample_frames.append(collect_vocabulary_samples(vectorizer, matrix, modeling_frame, config.name))
        vectorizers[config.name] = vectorizer
        matrices[config.name] = matrix

    summary = pd.DataFrame.from_records(summary_records)
    vocabulary_samples = pd.concat(sample_frames, ignore_index=True)

    return summary, vocabulary_samples, vectorizers, matrices


def experiment_records_from_summary(
    summary: pd.DataFrame,
    *,
    dataset_name: str,
    period_label: str,
    artifacts: dict[str, object],
    notes: str = "",
) -> list[ExperimentRecord]:
    """Convert TF-IDF summary rows into experiment registry records."""
    records: list[ExperimentRecord] = []

    for row in summary.to_dict(orient="records"):
        parameters = {
            "analyzer": row["analyzer"],
            "ngram_range": row["ngram_range"],
            "min_df": int(row["min_df"]),
            "max_df": float(row["max_df"]),
            "max_features": int(row["max_features"]),
            "sublinear_tf": bool(row["sublinear_tf"]),
            "norm": row["norm"],
        }
        metrics = {
            "feature_count": int(row["feature_count"]),
            "non_zero_values": int(row["non_zero_values"]),
            "density": float(row["density"]),
            "sparsity": float(row["sparsity"]),
        }
        records.append(
            create_experiment_record(
                stage="tfidf",
                dataset_name=dataset_name,
                period_label=period_label,
                document_count=int(row["document_count"]),
                config_name=row["name"],
                parameters=parameters,
                metrics=metrics,
                artifacts=artifacts,
                notes=notes,
            )
        )

    return records


def save_tfidf_reports(
    summary: pd.DataFrame,
    vocabulary_samples: pd.DataFrame,
    output_dir: Path | str,
    *,
    dataset_name: str = FILTERED_MARKET_DATASET_NAME,
    period_label: str = DEFAULT_PERIOD_LABEL,
) -> pd.DataFrame:
    """Save TF-IDF reports and append experiment records to the registry."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    summary_path = output_path / "tfidf_experiments_summary.csv"
    vocabulary_path = output_path / "tfidf_vocabulary_samples.csv"
    registry_path = output_path / "experiment_registry.csv"

    summary.to_csv(summary_path, index=False)
    vocabulary_samples.to_csv(vocabulary_path, index=False)

    artifacts = {
        "summary_csv": str(summary_path),
        "vocabulary_samples_csv": str(vocabulary_path),
    }
    records = experiment_records_from_summary(
        summary,
        dataset_name=dataset_name,
        period_label=period_label,
        artifacts=artifacts,
        notes="First TF-IDF comparison for filtered market dataset.",
    )
    return append_experiment_records(records, registry_path)


def run_default_tfidf_pipeline(
    *,
    dataset_name: str = FILTERED_MARKET_DATASET_NAME,
    period_label: str = DEFAULT_PERIOD_LABEL,
    report_dir: Path | str,
    root: Path | str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run the default TF-IDF pipeline from processed data to CSV reports."""
    dataset_path = processed_dataset_path(dataset_name=dataset_name, period_label=period_label, root=root)
    raw_items = load_processed_items(dataset_path)
    modeling_items = prepare_modeling_items(raw_items)
    summary, vocabulary_samples, _, _ = run_tfidf_experiments(modeling_items)
    registry = save_tfidf_reports(
        summary,
        vocabulary_samples,
        report_dir,
        dataset_name=dataset_name,
        period_label=period_label,
    )
    return summary, vocabulary_samples, registry
