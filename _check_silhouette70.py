"""Check completed representation winners on a larger fixed training sample."""
import logging
import os
from pathlib import Path

for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ[name] = "2"

import numpy as np
import pandas as pd
from sklearn import config_context
from sklearn.metrics import silhouette_score
from nofis_classifier.clustering import load_local_model, rank_experiments

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
run = Path("reports/grid_tfidf_kmeans/202501-202504_20260926T194715Z_7df01672")
metrics = pd.read_csv(run / "metrics.csv")
complete = metrics.groupby("config_name").size().loc[lambda s: s.eq(24)].index
ranking = rank_experiments(metrics[metrics.config_name.isin(complete)], expected_seeds=[42, 123, 2026])
winners = ranking.groupby("config_name", sort=False).head(1)
train = pd.read_csv(run / "training_descriptions.csv")
indexes = np.sort(np.random.default_rng(20260926).choice(len(train), size=5000, replace=False))
pd.DataFrame({"train_position": indexes}).to_csv(run / "supplementary_sample_5000.csv", index=False)
path = run / "silhouette_5000.csv"
records = pd.read_csv(path).to_dict(orient="records") if path.exists() else []
completed_ids = {r["experiment_id"] for r in records}
for winner in winners.itertuples(index=False):
    rows = metrics[metrics.config_name.eq(winner.config_name) & metrics.k.eq(winner.k)]
    vectorizer = load_local_model(rows.iloc[0].vectorizer_path)
    sample = vectorizer.transform(train.iloc[indexes].descricao_normalizada)
    for row in rows.itertuples(index=False):
        if row.experiment_id in completed_ids:
            continue
        model = load_local_model(row.model_path)
        labels = model.labels_[indexes]
        logging.info("Conferindo em 5.000 descrições: %s", row.experiment_id)
        with config_context(working_memory=128):
            score = silhouette_score(sample, labels, metric="cosine", n_jobs=1)
        records.append({
            "experiment_id": row.experiment_id, "config_name": row.config_name,
            "k": row.k, "seed": row.seed, "sample_seed": 20260926, "sample_size": 5000,
            "sample_clusters": len(np.unique(labels)), "silhouette_5000": float(score),
            "silhouette_1000": row.silhouette_cosine,
        })
        pd.DataFrame(records).to_csv(path, index=False)
        logging.info("Silhouette 5000: %.6f", score)
logging.info("Conferência salva: %s ajustes", len(records))
