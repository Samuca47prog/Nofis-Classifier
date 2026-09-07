from datetime import UTC, datetime

from nofis_classifier.experiments import append_experiment_records, create_experiment_record, load_experiment_registry


def test_create_experiment_record_serializes_metadata() -> None:
    record = create_experiment_record(
        stage="tfidf",
        dataset_name="items",
        period_label="202501",
        document_count=3,
        config_name="word",
        parameters={"b": 2, "a": 1},
        metrics={"sparsity": 0.9},
        artifacts={"summary": "report.csv"},
        created_at=datetime(2026, 9, 7, tzinfo=UTC),
    )

    assert record.experiment_id == "tfidf-items-202501-word-20260907T000000Z"
    assert record.created_at == "2026-09-07T00:00:00Z"
    assert record.parameters_json == '{"a": 1, "b": 2}'


def test_append_experiment_records_keeps_run_history(tmp_path) -> None:
    registry_path = tmp_path / "experiment_registry.csv"
    first = create_experiment_record(
        stage="tfidf",
        dataset_name="items",
        period_label="202501",
        document_count=3,
        config_name="word",
        parameters={},
        metrics={"sparsity": 0.9},
        artifacts={},
    )
    second = create_experiment_record(
        stage="tfidf",
        dataset_name="items",
        period_label="202501",
        document_count=4,
        config_name="word",
        parameters={},
        metrics={"sparsity": 0.8},
        artifacts={},
    )

    append_experiment_records([first], registry_path)
    registry = append_experiment_records([second], registry_path)

    assert len(registry) == 2
    assert registry["document_count"].tolist() == [3, 4]
    assert len(load_experiment_registry(registry_path)) == 2
