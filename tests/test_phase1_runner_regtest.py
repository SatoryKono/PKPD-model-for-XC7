from __future__ import annotations

from pathlib import Path

import pandas as pd

from pkpd_xc7.config.loader import load_model_config
from pkpd_xc7.io.layout import TISSUE_COL
from pkpd_xc7.simulation.runner import run_experiment


def test_run_experiment_structure(regtest):
    path = Path(__file__).resolve().parent / "fixtures" / "phase1_minimal_scenario.yaml"
    cfg = load_model_config(path)
    df = run_experiment(cfg)
    csv_text = df.to_csv(index=False, lineterminator="\n")
    regtest.write(csv_text)


def test_run_experiment_includes_brain_for_formalin_example() -> None:
    path = Path(__file__).resolve().parents[1] / "examples" / "configs" / "scenarios" / "formalin.yaml"
    cfg = load_model_config(path)
    df = run_experiment(cfg)

    assert "brain" in set(df[TISSUE_COL].astype(str))
    assert int((df[TISSUE_COL] == "brain").sum()) == len(cfg.time_grid_h)