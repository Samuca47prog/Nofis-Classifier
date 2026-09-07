from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd


EXPERIMENT_REGISTRY_COLUMNS = (
    "experiment_id",
    "created_at",
    "stage",
    "dataset_name",
    "period_label",
    "document_count",
    "config_name",
    "parameters_json",
    "metrics_json",
    "artifacts_json",
    "notes",
)


@dataclass(frozen=True)
class ExperimentRecord:
    """Append-only metadata for one reproducible experiment."""

    experiment_id: str
    created_at: str
    stage: str
    dataset_name: str
    period_label: str
    document_count: int
    config_name: str
    parameters_json: str
    metrics_json: str
    artifacts_json: str
    notes: str = ""


def json_dumps(value: dict[str, Any]) -> str:
    """Serialize experiment metadata with stable key ordering."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def create_experiment_record(
    *,
    stage: str,
    dataset_name: str,
    period_label: str,
    document_count: int,
    config_name: str,
    parameters: dict[str, Any],
    metrics: dict[str, Any],
    artifacts: dict[str, Any],
    notes: str = "",
    created_at: datetime | None = None,
) -> ExperimentRecord:
    """Create a registry record for one experiment run."""
    timestamp = created_at or datetime.now(UTC)
    created_at_text = timestamp.isoformat(timespec="seconds").replace("+00:00", "Z")
    timestamp_label = timestamp.strftime("%Y%m%dT%H%M%SZ")
    experiment_id = f"{stage}-{dataset_name}-{period_label}-{config_name}-{timestamp_label}"

    return ExperimentRecord(
        experiment_id=experiment_id,
        created_at=created_at_text,
        stage=stage,
        dataset_name=dataset_name,
        period_label=period_label,
        document_count=document_count,
        config_name=config_name,
        parameters_json=json_dumps(parameters),
        metrics_json=json_dumps(metrics),
        artifacts_json=json_dumps(artifacts),
        notes=notes,
    )


def load_experiment_registry(path: Path | str) -> pd.DataFrame:
    """Load an experiment registry or return an empty registry dataframe."""
    registry_path = Path(path)
    if not registry_path.exists():
        return pd.DataFrame(columns=EXPERIMENT_REGISTRY_COLUMNS)
    return pd.read_csv(registry_path)


def append_experiment_records(records: list[ExperimentRecord], path: Path | str) -> pd.DataFrame:
    """Append experiment records to a CSV registry."""
    registry_path = Path(path)
    registry_path.parent.mkdir(parents=True, exist_ok=True)

    existing = load_experiment_registry(registry_path)
    incoming = pd.DataFrame([asdict(record) for record in records], columns=EXPERIMENT_REGISTRY_COLUMNS)
    registry = incoming if existing.empty else pd.concat([existing, incoming], ignore_index=True)

    registry = registry.sort_values(["stage", "dataset_name", "period_label", "config_name"]).reset_index(drop=True)
    registry.to_csv(registry_path, index=False)
    return registry
