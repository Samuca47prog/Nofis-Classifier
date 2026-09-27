"""Execute the research notebook and preserve its outputs in a new run folder."""
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
from uuid import uuid4

import nbformat
from nbclient import NotebookClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
root = Path(__file__).resolve().parent
run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
run_dir = root / "reports" / "grid_tfidf_kmeans" / f"202501-202504_{run_id}"
run_dir.mkdir(parents=True, exist_ok=False)
output = run_dir / "70_matriz_tfidf_kmeans_executado.ipynb"
notebook = nbformat.read(root / "notebooks" / "70_matriz_tfidf_kmeans_e_validacao.ipynb", as_version=4)
for cell in notebook.cells:
    if cell.get("id") == "parameters":
        cell.source = cell.source.replace("RUN_ID = None", f"RUN_ID = {run_id!r}", 1)
for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ[name] = "4"
(run_dir / "execution_environment.json").write_text(json.dumps({
    "run_id": run_id, "started_utc": datetime.now(timezone.utc).isoformat(),
    "thread_limits": {name: os.environ[name] for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")},
}, indent=2), encoding="utf-8")
logging.info("RUN_DIR=%s", run_dir)


def checkpoint(cell, cell_index, **kwargs):
    """Save cell outputs as execution progresses."""
    nbformat.write(notebook, output)
    logging.info("Celula concluida: %s", cell.get("id", cell_index))


client = NotebookClient(notebook, timeout=None, kernel_name="python3",
                        resources={"metadata": {"path": str(root)}},
                        on_cell_executed=checkpoint)
try:
    client.execute()
finally:
    nbformat.write(notebook, output)
logging.info("Execucao concluida: %s", output)
