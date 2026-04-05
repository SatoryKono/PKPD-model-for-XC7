from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from src import api


def _write_valid_config(path: Path) -> None:
    payload = {
        "model_id": "repro_model",
        "compound": "histamine",
        "loss_mode": "mse",
        "assumptions": ["repro_test_assumption"],
        "traceability": {
            "source_in_report": "Repro test source",
            "source_reference": "internal",
            "source_version": "1",
        },
        "time_grid": [0, 0.5, 1.0, 1.5, 2.0],
        "time_unit": "h",
        "initial_concentration": 100.0,
        "concentration_unit": "nM",
        "kinetics": {
            "k_abs": 0.4,
            "k_elim": 0.1,
            "rate_unit": "1/h",
        },
        "tissues": [
            {
                "name": "plasma",
                "volume": 1.0,
                "volume_unit": "L",
                "partition_coeff": 1.0,
            }
        ],
        "plots": [],
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_repeated_deterministic_runs_keep_marker_points_hash_and_metadata_fields(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    _write_valid_config(config_path)

    out_a = tmp_path / "run_a"
    out_b = tmp_path / "run_b"

    api.simulate(config_path, out_a)
    api.simulate(config_path, out_b)

    marker_a = out_a / "marker_points.csv"
    marker_b = out_b / "marker_points.csv"
    marker_hash_a = _sha256(marker_a)
    marker_hash_b = _sha256(marker_b)

    assert marker_hash_a == marker_hash_b

    metadata_a = json.loads((out_a / "metadata.json").read_text(encoding="utf-8"))
    metadata_b = json.loads((out_b / "metadata.json").read_text(encoding="utf-8"))

    for metadata in (metadata_a, metadata_b):
        required = {
            "schema_version",
            "run_id",
            "created_at_utc",
            "run_dir",
            "deterministic_mode",
            "command",
            "environment",
            "config_sha256",
            "artifacts",
        }
        assert required.issubset(metadata.keys())
        assert metadata["deterministic_mode"] is True

    assert metadata_a["config_sha256"] == metadata_b["config_sha256"]

    marker_record_a = next(item for item in metadata_a["artifacts"] if item["path"] == "marker_points.csv")
    marker_record_b = next(item for item in metadata_b["artifacts"] if item["path"] == "marker_points.csv")

    assert marker_record_a["sha256"] == marker_hash_a
    assert marker_record_b["sha256"] == marker_hash_b
    assert marker_record_a["sha256"] == marker_record_b["sha256"]
