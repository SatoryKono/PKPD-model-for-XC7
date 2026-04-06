from __future__ import annotations

from pathlib import Path

import pytest
import pandas as pd
import yaml

from pkpd_xc7.config.schemas import ModelConfig
from pkpd_xc7.io.export import atomic_write_csv, atomic_write_yaml, export_simulation_run
from pkpd_xc7.io.layout import SIMULATION_SCHEMA_VERSION, TIMESERIES_COLUMN_ORDER


def test_atomic_write_csv_roundtrip(tmp_path: Path) -> None:
    df = pd.DataFrame({"a": [1], "b": [2]})
    dest = tmp_path / "out" / "t.csv"
    atomic_write_csv(df, dest)
    assert dest.exists()
    assert dest.read_bytes() == b"a,b\n1,2\n"
    back = pd.read_csv(dest)
    assert list(back.columns) == ["a", "b"]


def test_atomic_write_yaml_roundtrip(tmp_path: Path) -> None:
    payload = {"schema_version": "1.0.0", "row_count": 2}
    dest = tmp_path / "out" / "meta.yaml"
    atomic_write_yaml(payload, dest)
    assert dest.exists()
    back = yaml.safe_load(dest.read_text(encoding="utf-8"))
    assert back == payload


def test_export_simulation_run_writes_csv_and_meta_yaml(tmp_path: Path) -> None:
    cfg = ModelConfig.model_validate(
        {
            "model_id": "phase1_export",
            "compound": "xc7",
            "traceability": {"source_in_report": "table-1"},
            "assumptions": ["export contract"],
            "driver": {"driver_type": "scenario", "scenario_id": "formalin"},
            "tissues": ["skin"],
            "time_grid_h": [0.0, 1.0],
        }
    )
    df = pd.DataFrame(
        [
            {
                "time_h": 0.0,
                "tissue": "skin",
                "histamine_nm": 50.0,
                "R_surf": 1.0,
                "R_int": 0.0,
                "G_signal": 0.5,
                "G_signal_pct": 50.0,
                "G_signal_ligand": 0.45,
                "G_signal_ligand_pct": 45.0,
                "G_signal_constitutive": 0.05,
                "G_signal_constitutive_pct": 5.0,
                "beta_arr_signal": 0.032,
                "beta_arr_signal_pct": 3.2,
                "internalization_drive": 0.032,
                "k_int_eff_per_h": 0.096,
                "driver_type": "scenario",
                "driver_id": "formalin",
            }
        ]
    )
    df.attrs["solver_metadata"] = {"solver_method": "LSODA", "rtol": 1e-3, "atol": 1e-6, "max_step": None}
    df.attrs["runtime_assumptions"] = ["export contract", "k_deg implicitly equals k_synth per ODE mass-balance invariant"]
    df.attrs["antagonist_pk"] = {
        "enabled": True,
        "species": "mouse",
        "regimen": "single",
        "dose_mg_per_kg": 90.0,
        "tissue_map": {"skin": "skin"},
    }

    artifacts = export_simulation_run(df, cfg, tmp_path / "run")

    assert artifacts.simulation_csv.exists()
    assert artifacts.meta_yaml.exists()

    exported = pd.read_csv(artifacts.simulation_csv)
    assert exported.columns.tolist() == TIMESERIES_COLUMN_ORDER

    meta = yaml.safe_load(artifacts.meta_yaml.read_text(encoding="utf-8"))
    assert meta["config_sha256"] == cfg.config_sha256()
    assert meta["config_schema_version"] == cfg.schema_version
    assert meta["simulation_schema_version"] == SIMULATION_SCHEMA_VERSION
    assert meta["column_order"] == TIMESERIES_COLUMN_ORDER
    assert meta["row_count"] == 1
    assert meta["driver_type"] == "scenario"
    assert meta["driver_id"] == "formalin"
    assert meta["generated_at_utc"].endswith("Z")
    assert meta["default_trafficking_params"]["ec50_g_nm"] == pytest.approx(50.0)
    assert meta["trafficking_params_by_tissue"]["skin"]["ec50_g_nm"] == pytest.approx(50.0)
    assert meta["solver_metadata"]["solver_method"] == "LSODA"
    assert "runtime_assumptions" in meta
    assert len(meta["runtime_assumptions"]) == 2
    assert meta["antagonist_pk"]["dose_mg_per_kg"] == pytest.approx(90.0)