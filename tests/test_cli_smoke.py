from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml
from typer.testing import CliRunner

from src.cli.app import app


RUNNER = CliRunner()


def _write_valid_config(path: Path) -> None:
    payload = {
        "model_id": "smoke_model",
        "compound": "histamine",
        "loss_mode": "mse",
        "assumptions": ["smoke_test_assumption"],
        "traceability": {
            "source_in_report": "Smoke test source",
            "source_reference": "internal",
            "source_version": "1",
        },
        "time_grid": [0, 1, 2],
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


def test_cli_simulate_and_validate_success(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    run_dir = tmp_path / "run"
    _write_valid_config(config)

    simulate_result = RUNNER.invoke(
        app,
        ["simulate", "--config", str(config), "--out", str(run_dir)],
    )
    assert simulate_result.exit_code == 0, simulate_result.stdout
    assert (run_dir / "simulation.csv").exists()
    assert (run_dir / "marker_points.csv").exists()
    assert (run_dir / "summary.csv").exists()
    assert (run_dir / "metadata.json").exists()
    assert (run_dir / "meta.yaml").exists()
    assert (run_dir / "config.used.yaml").exists()

    reference = tmp_path / "reference.csv"
    pd.read_csv(run_dir / "simulation.csv").to_csv(reference, index=False)

    validate_result = RUNNER.invoke(
        app,
        ["validate", "--run-dir", str(run_dir), "--reference", str(reference)],
    )
    assert validate_result.exit_code == 0, validate_result.stdout


def test_cli_validation_error_has_nonzero_exit_and_stderr(tmp_path: Path) -> None:
    invalid_config = tmp_path / "invalid.yaml"
    invalid_payload = {
        "model_id": "invalid",
        "compound": "histamine",
        "loss_mode": "mse",
        "assumptions": ["x"],
        "traceability": {"source_in_report": "src"},
        "time_grid": [0, -1],
        "time_unit": "h",
        "initial_concentration": 1.0,
        "concentration_unit": "nM",
        "kinetics": {"k_abs": 0.2, "k_elim": 0.1, "rate_unit": "1/h"},
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
    invalid_config.write_text(yaml.safe_dump(invalid_payload, sort_keys=False), encoding="utf-8")

    result = RUNNER.invoke(
        app,
        ["simulate", "--config", str(invalid_config), "--out", str(tmp_path / "run")],
    )

    assert result.exit_code != 0
    assert "simulate failed" in result.stderr
    assert "time_grid" in result.stderr


def test_cli_batch_and_export_tsv(tmp_path: Path) -> None:
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    _write_valid_config(configs_dir / "a.yaml")
    _write_valid_config(configs_dir / "b.yaml")

    out_root = tmp_path / "runs"
    batch_result = RUNNER.invoke(
        app,
        ["batch", "--configs-dir", str(configs_dir), "--out-root", str(out_root)],
    )
    assert batch_result.exit_code == 0, batch_result.stdout

    run_a = out_root / "a"
    export_result = RUNNER.invoke(
        app,
        ["export", "--run-dir", str(run_a), "--format", "tsv"],
    )
    assert export_result.exit_code == 0, export_result.stdout
    assert (run_a / "simulation.tsv").exists()


def test_cli_fit_command_exits_with_migration_code() -> None:
    result = RUNNER.invoke(app, ["fit"])
    assert result.exit_code == 2
    assert "least_squares" in result.stderr.lower() or "пайплайн" in result.stderr
