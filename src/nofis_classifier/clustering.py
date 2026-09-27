"""Resumable TF-IDF/K-Means experiments and human-reviewed categorization."""

from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import json
import logging
from pathlib import Path
import pickle
import platform
from time import perf_counter
from uuid import uuid4
import warnings

import numpy as np
import pandas as pd
import sklearn
from sklearn.cluster import KMeans
from sklearn.metrics import (
    calinski_harabasz_score, davies_bouldin_score, silhouette_score,
)
from sklearn.metrics.pairwise import euclidean_distances

from nofis_classifier.schema import DESCRIPTION_NORMALIZED, FREQUENCY
from nofis_classifier.text import normalize_description
from nofis_classifier.tfidf import fit_tfidf_experiment

logger = logging.getLogger(__name__)


def _save_json(path, value):
    temporary = path.with_suffix(f".{uuid4().hex}.tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def _save_model(path, value):
    if path.exists():
        raise FileExistsError(f"Modelo existente: {path}")
    temporary = path.with_suffix(f".{uuid4().hex}.tmp")
    with temporary.open("xb") as stream:
        pickle.dump(value, stream, protocol=pickle.HIGHEST_PROTOCOL)
    temporary.rename(path)


def load_local_model(path):
    """Load only a trusted pickle produced locally by this project."""
    with Path(path).open("rb") as stream:
        return pickle.load(stream)


def split_descriptions(frame, validation_count=300, random_state=42):
    """Reserve unique descriptions before vocabulary fitting and model selection."""
    if frame[DESCRIPTION_NORMALIZED].duplicated().any():
        raise ValueError("A separacao exige descricoes unicas.")
    if not 1 <= validation_count < len(frame) - 2:
        raise ValueError("Reserve ao menos uma descricao e mantenha ao menos tres no treino.")
    validation = frame.sample(n=validation_count, random_state=random_state)
    train = frame.drop(validation.index)
    return train.reset_index(drop=True), validation.reset_index(drop=True)


def run_clustering_grid(
    train, configs, k_values, seeds, report_dir, model_dir, *,
    sample_size=1000, sample_seed=42, n_init=10, max_iter=300,
    dense_limit_mb=512,
):
    """Fit each grid cell, checkpoint results, and resume identical runs safely.

    All training rows are used without frequency weights. Metrics use a fixed
    training sample; the held-out validation set must not be passed here.
    Configurations are processed sequentially to bound memory consumption.
    """
    report_dir, model_dir = Path(report_dir), Path(model_dir)
    configs, k_values, seeds = list(configs), sorted(set(k_values)), list(dict.fromkeys(seeds))
    if not configs or not k_values or not seeds:
        raise ValueError("A grade deve conter configuracoes, valores de k e sementes.")
    if len({c.name for c in configs}) != len(configs):
        raise ValueError("Os nomes das configuracoes devem ser unicos.")
    if any(Path(c.name).name != c.name or c.name in (".", "..") for c in configs):
        raise ValueError("Nome de configuracao invalido.")
    if any(k < 2 or k >= len(train) for k in k_values):
        raise ValueError("Cada k deve estar entre 2 e n_descricoes - 1.")
    if sample_size < 3 or dense_limit_mb <= 0 or n_init < 1 or max_iter < 1:
        raise ValueError("Parametros de amostragem, memoria ou ajuste invalidos.")
    report_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "format_version": 1,
        "train_sha256": sha256(pd.util.hash_pandas_object(train, index=True).values.tobytes()).hexdigest(),
        "configs": [asdict(c) for c in configs], "k_values": k_values, "seeds": seeds,
        "sample_size": sample_size, "sample_seed": sample_seed, "n_init": n_init,
        "max_iter": max_iter, "dense_limit_mb": dense_limit_mb,
        "model_dir": str(model_dir.resolve()), "python": platform.python_version(),
        "sklearn": sklearn.__version__, "numpy": np.__version__, "pandas": pd.__version__,
    }
    manifest = json.loads(json.dumps(manifest))
    manifest_path = report_dir / "grid_manifest.json"
    if manifest_path.exists():
        if json.loads(manifest_path.read_text(encoding="utf-8")) != manifest:
            raise ValueError("Dados, parametros ou ambiente mudaram. Use um novo RUN_ID.")
    else:
        if any(model_dir.iterdir()):
            raise ValueError("A pasta de modelos ja contem arquivos. Use um novo RUN_ID.")
        _save_json(manifest_path, manifest)

    sample_indexes = np.sort(np.random.default_rng(sample_seed).choice(
        len(train), size=min(sample_size, len(train)), replace=False,
    ))
    pd.DataFrame({"train_position": sample_indexes}).to_csv(report_dir / "metric_sample.csv", index=False)
    records = []
    total = len(configs) * len(k_values) * len(seeds)
    for config in configs:
        vectorizer_path = model_dir / f"{config.name}_tfidf.pkl"
        try:
            if vectorizer_path.exists():
                vectorizer = load_local_model(vectorizer_path)
                matrix = vectorizer.transform(train[DESCRIPTION_NORMALIZED])
            else:
                vectorizer, matrix = fit_tfidf_experiment(train[DESCRIPTION_NORMALIZED], config)
                _save_model(vectorizer_path, vectorizer)
            sample = matrix[sample_indexes]
            dense_mb = sample.shape[0] * sample.shape[1] * matrix.dtype.itemsize / 1024**2
            # Only the sample is densified, never the complete training matrix.
            dense = sample.toarray() if dense_mb <= dense_limit_mb else None
            vector_error = None
        except Exception as exc:
            logger.exception("Falha no TF-IDF %s", config.name)
            vector_error = f"{type(exc).__name__}: {exc}"

        for k in k_values:
            for seed in seeds:
                experiment_id = f"{config.name}_k{k}_seed{seed}"
                checkpoint = report_dir / f"{experiment_id}.json"
                model_path = model_dir / f"{experiment_id}.pkl"
                if checkpoint.exists():
                    previous = json.loads(checkpoint.read_text(encoding="utf-8"))
                    if previous["status"] == "ok" and model_path.exists() and vector_error is None:
                        records.append(previous)
                        logger.info("[%d/%d] Recuperado: %s", len(records), total, experiment_id)
                        continue
                record = {
                    "experiment_id": experiment_id, "config_name": config.name,
                    "k": k, "seed": seed, "n_init": n_init,
                    "document_count": len(train), "sample_size": len(sample_indexes),
                    "model_path": str(model_path.resolve()),
                    "vectorizer_path": str(vectorizer_path.resolve()),
                }
                started = perf_counter()
                logger.info("[%d/%d] Ajustando: %s", len(records) + 1, total, experiment_id)
                try:
                    if vector_error:
                        raise ValueError(vector_error)
                    with warnings.catch_warnings(record=True) as caught:
                        warnings.simplefilter("always")
                        if model_path.exists():
                            model = load_local_model(model_path)
                        else:
                            model = KMeans(n_clusters=k, random_state=seed, n_init=n_init,
                                           max_iter=max_iter, algorithm="lloyd")
                            model.fit(matrix)
                            _save_model(model_path, model)
                        labels = model.labels_
                        counts = np.bincount(labels, minlength=k)
                        sample_labels = labels[sample_indexes]
                        sample_clusters = len(np.unique(sample_labels))
                        record.update(
                            status="ok", feature_count=matrix.shape[1],
                            zero_vector_fraction=float(np.mean(matrix.getnnz(axis=1) == 0)),
                            inertia=float(model.inertia_), n_iter=int(model.n_iter_),
                            reached_max_iter=bool(model.n_iter_ >= max_iter),
                            actual_clusters=int(np.count_nonzero(counts)),
                            sample_clusters=sample_clusters,
                            min_cluster_size=int(counts.min()), max_cluster_size=int(counts.max()),
                            largest_cluster_fraction=float(counts.max() / len(train)),
                            singleton_clusters=int(np.sum(counts == 1)),
                            silhouette_cosine=None, calinski_harabasz=None, davies_bouldin=None,
                            metric_note="", dense_sample_mb=dense_mb,
                        )
                        if 2 <= sample_clusters < len(sample_labels):
                            record["silhouette_cosine"] = float(silhouette_score(sample, sample_labels, metric="cosine"))
                            if dense is not None:
                                record["calinski_harabasz"] = float(calinski_harabasz_score(dense, sample_labels))
                                record["davies_bouldin"] = float(davies_bouldin_score(dense, sample_labels))
                            else:
                                record["metric_note"] = "CH/DB omitidos: amostra excede limite de memoria."
                        else:
                            record["metric_note"] = "Metricas indefinidas: quantidade de clusters na amostra."
                        record["warnings"] = " | ".join(str(w.message) for w in caught)
                except Exception as exc:
                    logger.exception("Falha em %s; continuando a grade", experiment_id)
                    record.update(status="error", error=f"{type(exc).__name__}: {exc}")
                record["elapsed_seconds"] = perf_counter() - started
                _save_json(checkpoint, record)
                records.append(record)
                pd.DataFrame(records).to_csv(report_dir / "metrics.csv", index=False)
        # Release the previous representation before constructing the next one.
        if vector_error is None:
            del matrix, sample, dense, vectorizer
    results = pd.DataFrame(records)
    results.to_csv(report_dir / "metrics.csv", index=False)
    return results


def rank_experiments(metrics, expected_seeds=None):
    """Rank complete, nondegenerate combinations by median cosine silhouette.

    Seeds measure score variation, not label agreement. CH and DB remain separate
    evidence, without mixing incompatible metric scales into an arbitrary score.
    """
    records = []
    expected_seeds = set(metrics["seed"] if expected_seeds is None else expected_seeds)
    for (config, k), group in metrics.groupby(["config_name", "k"], sort=True):
        if set(group["seed"]) != expected_seeds or group["seed"].duplicated().any():
            continue
        if not group["status"].eq("ok").all():
            continue
        if not group["actual_clusters"].eq(k).all() or group["silhouette_cosine"].isna().any():
            continue
        median = group["silhouette_cosine"].median()
        representative = group.loc[(group["silhouette_cosine"] - median).abs().idxmin()]
        records.append({
            "config_name": config, "k": int(k), "seed_count": len(group),
            "silhouette_median": median,
            "silhouette_std": group["silhouette_cosine"].std(ddof=0),
            "ch_median": group["calinski_harabasz"].median() if group["calinski_harabasz"].notna().any() else np.nan,
            "db_median": group["davies_bouldin"].median() if group["davies_bouldin"].notna().any() else np.nan,
            "inertia_median": group["inertia"].median(),
            "largest_cluster_fraction": group["largest_cluster_fraction"].median(),
            "zero_vector_fraction": group["zero_vector_fraction"].iloc[0],
            "reached_max_iter": bool(group["reached_max_iter"].any()),
            "representative_id": representative["experiment_id"],
        })
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records).sort_values(
        ["silhouette_median", "silhouette_std"], ascending=[False, True],
    ).reset_index(drop=True)


def inspect_documents(frame, vectorizer, count=10, seed=42):
    """Show strongest TF-IDF terms for a fixed sample without relying on row IDs."""
    rows = frame.sample(n=min(count, len(frame)), random_state=seed).copy()
    matrix = vectorizer.transform(rows[DESCRIPTION_NORMALIZED])
    terms = vectorizer.get_feature_names_out()
    evidence = []
    for row in matrix:
        order = np.argsort(row.data)[::-1][:10]
        evidence.append(" | ".join(f"{terms[row.indices[i]]}: {row.data[i]:.3f}" for i in order))
    rows["termos_tfidf"] = evidence
    rows["sem_vocabulario"] = matrix.getnnz(axis=1) == 0
    return rows


def build_cluster_review(train, vectorizer, model, experiment_id, examples=6):
    """Return full assignments and central, distant, and random cluster examples."""
    matrix = vectorizer.transform(train[DESCRIPTION_NORMALIZED])
    assignments = train.reset_index(drop=True).copy()
    assignments["cluster"] = model.predict(matrix)
    assignments["sem_vocabulario"] = matrix.getnnz(axis=1) == 0
    assignments["distancia_centroide"] = np.nan
    terms = vectorizer.get_feature_names_out()
    reports = []
    for cluster in range(model.n_clusters):
        indexes = np.flatnonzero(assignments["cluster"].to_numpy() == cluster)
        if len(indexes):
            assignments.loc[indexes, "distancia_centroide"] = euclidean_distances(
                matrix[indexes], model.cluster_centers_[cluster:cluster + 1],
            ).ravel()
        subset = assignments.iloc[indexes]
        central = subset.sort_values("distancia_centroide")
        distant = subset.sort_values("distancia_centroide", ascending=False)
        random = subset.sample(n=min(examples, len(subset)), random_state=42 + cluster)
        centroid = model.cluster_centers_[cluster]
        strongest = [i for i in np.argsort(centroid)[::-1][:15] if centroid[i] > 0]
        reports.append({
            "experiment_id": experiment_id, "cluster": cluster,
            "termos_relevantes": " | ".join(terms[strongest]),
            "exemplos_centrais": " | ".join(central[DESCRIPTION_NORMALIZED].head(examples)),
            "exemplos_distantes": " | ".join(distant[DESCRIPTION_NORMALIZED].head(examples)),
            "exemplos_aleatorios": " | ".join(random[DESCRIPTION_NORMALIZED]),
            "descricoes_unicas": len(subset), "frequencia_total": int(subset[FREQUENCY].sum()),
            "sem_vocabulario": int(subset["sem_vocabulario"].sum()),
            "avaliacao_qualitativa": "REVISAR", "rotulo_humano": "", "observacoes": "",
        })
    return assignments, pd.DataFrame(reports).sort_values("descricoes_unicas", ascending=False)


def save_review_once(frame, path):
    """Create an editable CSV only if absent, preserving all prior human edits."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        logger.info("Preservando revisao existente: %s", path)
        return
    frame.to_csv(path, index=False, encoding="utf-8-sig", mode="x")


def predict_categories(descriptions, vectorizer, model, review, experiment_id):
    """Map clusters explicitly marked coherent to labels; otherwise return REVISAR."""
    if not review["experiment_id"].eq(experiment_id).all() or review["cluster"].duplicated().any():
        raise ValueError("A revisao deve pertencer apenas ao experimento escolhido, sem clusters duplicados.")
    accepted = review[
        review["avaliacao_qualitativa"].fillna("").str.strip().str.lower().eq("coerente")
        & review["rotulo_humano"].fillna("").str.strip().ne("")
    ]
    mapping = accepted.set_index("cluster")["rotulo_humano"].str.strip().to_dict()
    result = pd.DataFrame({"descricao": list(descriptions)})
    result[DESCRIPTION_NORMALIZED] = result["descricao"].map(normalize_description)
    if result.empty:
        return result.assign(cluster=pd.Series(dtype="int64"), categoria=pd.Series(dtype="str"))
    matrix = vectorizer.transform(result[DESCRIPTION_NORMALIZED])
    result["cluster"] = model.predict(matrix)
    result["categoria"] = result["cluster"].map(mapping).fillna("REVISAR")
    result.loc[matrix.getnnz(axis=1) == 0, "categoria"] = "REVISAR"
    return result
