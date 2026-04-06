from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from pkpd_xc7.config.schemas import ModelConfig
from pkpd_xc7.io.layout import ANTAGONIST_CONCENTRATION_COL
from pkpd_xc7.simulation.antagonist_pk import build_antagonist_pk_runtime
from pkpd_xc7.simulation.runner import run_experiment


def _write_pk_source(tmp_path: Path) -> Path:
    source = tmp_path / "pk_source.xlsx"
    df = pd.DataFrame(
        [
            {"species": "mice", "regimen": "single", "organ": "skin", "dose": 30.0, "time_h": 0.0, "C_nM": 0.0},
            {"species": "mice", "regimen": "single", "organ": "skin", "dose": 30.0, "time_h": 1.0, "C_nM": 300.0},
            {"species": "mice", "regimen": "single", "organ": "skin", "dose": 30.0, "time_h": 2.0, "C_nM": 240.0},
            {"species": "mice", "regimen": "single", "organ": "skin", "dose": 30.0, "time_h": 4.0, "C_nM": 120.0},
            {"species": "mice", "regimen": "single", "organ": "skin", "dose": 90.0, "time_h": 0.0, "C_nM": 0.0},
            {"species": "mice", "regimen": "single", "organ": "skin", "dose": 90.0, "time_h": 1.0, "C_nM": 900.0},
            {"species": "mice", "regimen": "single", "organ": "skin", "dose": 90.0, "time_h": 2.0, "C_nM": 720.0},
            {"species": "mice", "regimen": "single", "organ": "skin", "dose": 90.0, "time_h": 4.0, "C_nM": 360.0},
            {"species": "mice", "regimen": "single", "organ": "brain", "dose": 30.0, "time_h": 0.0, "C_nM": 0.0},
            {"species": "mice", "regimen": "single", "organ": "brain", "dose": 30.0, "time_h": 1.0, "C_nM": 150.0},
            {"species": "mice", "regimen": "single", "organ": "brain", "dose": 30.0, "time_h": 2.0, "C_nM": 120.0},
            {"species": "mice", "regimen": "single", "organ": "brain", "dose": 30.0, "time_h": 4.0, "C_nM": 60.0},
            {"species": "mice", "regimen": "single", "organ": "brain", "dose": 90.0, "time_h": 0.0, "C_nM": 0.0},
            {"species": "mice", "regimen": "single", "organ": "brain", "dose": 90.0, "time_h": 1.0, "C_nM": 450.0},
            {"species": "mice", "regimen": "single", "organ": "brain", "dose": 90.0, "time_h": 2.0, "C_nM": 360.0},
            {"species": "mice", "regimen": "single", "organ": "brain", "dose": 90.0, "time_h": 4.0, "C_nM": 180.0},
            {"species": "rats", "regimen": "single", "organ": "skin", "dose": 90.0, "time_h": 0.0, "C_nM": 0.0},
            {"species": "rats", "regimen": "single", "organ": "skin", "dose": 90.0, "time_h": 1.0, "C_nM": 600.0},
            {"species": "rats", "regimen": "single", "organ": "skin", "dose": 90.0, "time_h": 2.0, "C_nM": 480.0},
        ]
    )
    df.to_excel(source, index=False)
    return source


def _config(source: Path) -> ModelConfig:
    return ModelConfig.model_validate(
        {
            "model_id": "antagonist_pk_test",
            "compound": "xc7",
            "species": "mouse",
            "traceability": {"source_in_report": "pk source"},
            "assumptions": ["antagonist pk test"],
            "driver": {"driver_type": "scenario", "scenario_id": "formalin"},
            "tissues": ["skin", "brain"],
            "time_grid_h": [0.0, 1.0, 2.0],
            "antagonist_pk": {
                "enabled": True,
                "source_xlsx": str(source),
                "dose_mg_per_kg": 90.0,
                "regimen": "single",
                "concentration_column": "C_nM",
                "tissue_map": {
                    "skin": "skin",
                    "brain": "brain",
                },
            },
        }
    )


def test_build_antagonist_pk_runtime_predicts_exact_nodes_and_zero_at_time_zero(tmp_path: Path) -> None:
    source = _write_pk_source(tmp_path)
    runtime = build_antagonist_pk_runtime(_config(source))
    assert runtime is not None

    assert runtime.concentration_nm("skin", 1.0) == pytest.approx(900.0)
    assert runtime.concentration_nm("brain", 2.0) == pytest.approx(360.0)
    assert runtime.concentration_nm("skin", 0.0) == pytest.approx(0.0)
    assert runtime.concentration_nm("brain", 0.0) == pytest.approx(0.0)
    assert runtime.metadata()["species"] == "mouse"


def test_run_experiment_adds_antagonist_column_and_runtime_meta(tmp_path: Path) -> None:
    source = _write_pk_source(tmp_path)
    df = run_experiment(_config(source))

    assert ANTAGONIST_CONCENTRATION_COL in df.columns
    skin = df.loc[df["tissue"] == "skin", ANTAGONIST_CONCENTRATION_COL].tolist()
    brain = df.loc[df["tissue"] == "brain", ANTAGONIST_CONCENTRATION_COL].tolist()
    assert skin == pytest.approx([0.0, 900.0, 720.0])
    assert brain == pytest.approx([0.0, 450.0, 360.0])
    assert df.attrs["antagonist_pk"]["dose_mg_per_kg"] == pytest.approx(90.0)
    assert any("XC7 concentration-time profiles are interpolated" in item for item in df.attrs["runtime_assumptions"])
