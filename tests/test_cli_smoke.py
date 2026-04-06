from __future__ import annotations

from pathlib import Path

import yaml
from typer.testing import CliRunner

from pkpd_xc7.cli.app import app


RUNNER = CliRunner()


def _write_valid_config(path: Path) -> None:
    payload = {
        "model_id": "smoke_model",
        "compound": "xc7",
        "loss_mode": "mse",
        "assumptions": ["smoke_test_assumption"],
        "traceability": {
            "source_in_report": "Smoke test source",
            "source_reference": "internal",
            "source_version": "1",
        },
        "driver": {"driver_type": "scenario", "scenario_id": "formalin"},
        "tissues": ["skin", "spinal_coord"],
        "time_grid_h": [0.0, 0.5, 1.0],
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_cli_simulate_success(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    run_dir = tmp_path / "run"
    _write_valid_config(config)

    simulate_result = RUNNER.invoke(
        app,
        ["simulate", "--config", str(config), "--out", str(run_dir)],
    )
    assert simulate_result.exit_code == 0, simulate_result.stdout
    assert (run_dir / "simulation.csv").exists()
    assert (run_dir / "meta.yaml").exists()
    assert "Config SHA256" in simulate_result.stdout


def test_cli_invalid_config_has_nonzero_exit(tmp_path: Path) -> None:
    invalid_config = tmp_path / "invalid.yaml"
    invalid_payload = {
        "model_id": "invalid",
        "compound": "xc7",
        "loss_mode": "mse",
        "assumptions": ["x"],
        "traceability": {"source_in_report": "src"},
        "driver": {"driver_type": "scenario", "scenario_id": "formalin"},
        "tissues": ["skin"],
        "time_grid_h": [0.0, -1.0],
    }
    invalid_config.write_text(yaml.safe_dump(invalid_payload, sort_keys=False), encoding="utf-8")

    result = RUNNER.invoke(
        app,
        ["simulate", "--config", str(invalid_config), "--out", str(tmp_path / "run")],
    )

    assert result.exit_code != 0


def test_cli_version_command_returns_package_banner() -> None:
    result = RUNNER.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "pkpd-model-xc7" in result.stdout.lower()
