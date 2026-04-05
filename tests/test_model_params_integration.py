from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from src import api


def _write_config(
    path: Path,
    *,
    k_abs: float,
    k_elim: float,
    partition_coeff: float,
) -> None:
    payload = {
        "model_id": "integration_model",
        "compound": "histamine",
        "loss_mode": "mse",
        "assumptions": ["integration_test_assumption"],
        "traceability": {
            "source_in_report": "Integration test source",
            "source_reference": "internal",
            "source_version": "1",
        },
        "time_grid": [0.0, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0],
        "time_unit": "h",
        "initial_concentration": 120.0,
        "concentration_unit": "nM",
        "kinetics": {
            "k_abs": k_abs,
            "k_elim": k_elim,
            "rate_unit": "1/h",
        },
        "tissues": [
            {
                "name": "plasma",
                "volume": 1.0,
                "volume_unit": "L",
                "partition_coeff": partition_coeff,
            }
        ],
        "plots": [],
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _summary_metric(summary_csv: Path, metric: str) -> float:
    summary = pd.read_csv(summary_csv)
    row = summary.loc[summary["metric"] == metric, "value"]
    assert not row.empty
    return float(row.iloc[0])


def test_kinetics_and_tissue_changes_impact_summary_metrics(tmp_path: Path) -> None:
    config_base = tmp_path / "base.yaml"
    config_variant = tmp_path / "variant.yaml"
    _write_config(config_base, k_abs=0.6, k_elim=0.2, partition_coeff=1.0)
    _write_config(config_variant, k_abs=1.1, k_elim=0.45, partition_coeff=2.0)

    run_base = tmp_path / "run_base"
    run_variant = tmp_path / "run_variant"
    api.simulate(config_base, run_base)
    api.simulate(config_variant, run_variant)

    auc_base = _summary_metric(run_base / "summary.csv", "histamine_auc_nm_h")
    auc_variant = _summary_metric(run_variant / "summary.csv", "histamine_auc_nm_h")
    r_int_max_base = _summary_metric(run_base / "summary.csv", "R_int_max")
    r_int_max_variant = _summary_metric(run_variant / "summary.csv", "R_int_max")

    assert auc_variant != auc_base
    assert r_int_max_variant != r_int_max_base


def test_unsupported_scenario_assumptions_fail_explicitly(tmp_path: Path) -> None:
    config = tmp_path / "invalid_scenario.yaml"
    _write_config(config, k_abs=0.6, k_elim=0.2, partition_coeff=1.0)
    payload = yaml.safe_load(config.read_text(encoding="utf-8"))
    payload["scenario_assumptions"] = {"not_supported": True}
    config.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    try:
        api.simulate(config, tmp_path / "run")
    except ValueError as exc:
        assert "Unsupported scenario_assumptions" in str(exc)
    else:
        raise AssertionError("simulate must fail for unsupported scenario assumptions")
