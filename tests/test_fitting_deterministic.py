from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.config.schemas import LossMode
from src.fitting.fit_spec import FitSpec, ParameterSpec
from src.fitting.histamine_fit import fit_histamine_to_markers
from src.histamine_profiles import default_capsaicin_params, capsaicin_histamine


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_histamine_fit_is_deterministic_and_writes_report(tmp_path: Path) -> None:
    truth = default_capsaicin_params()
    t_h = np.array([0.0, 0.1, 0.3, 0.6, 1.0, 1.5])
    y = np.asarray(capsaicin_histamine(t_h, truth), dtype=float)
    marker_df = pd.DataFrame({"t_h": t_h, "histamine_nm": y})

    spec = FitSpec(
        parameters=(
            ParameterSpec("phase1.amplitude_nm", init=120.0, lower=10.0, upper=300.0),
            ParameterSpec("phase1.tau_fall_h", init=0.5, lower=0.2, upper=1.5),
        ),
        fixed_params={"phase1.t0_h": 0.0, "phase1.tau_rise_h": truth.phase1.tau_rise_h, "h_base_nm": truth.h_base_nm},
        seed=123,
        method="trf",
        loss_mode=LossMode.MSE,
    )

    out_a = tmp_path / "runs" / "case_a" / "fitted_params.json"
    out_b = tmp_path / "runs" / "case_b" / "fitted_params.json"

    report_a = fit_histamine_to_markers(
        marker_df=marker_df,
        model_fn=capsaicin_histamine,
        default_params=default_capsaicin_params(),
        fit_spec=spec,
        output_json_path=out_a,
        source_in_report="IMP-01 synthetic markers",
        assumptions=["Scenario assumption: synthetic noise-free markers were used for deterministic test."],
    )
    report_b = fit_histamine_to_markers(
        marker_df=marker_df,
        model_fn=capsaicin_histamine,
        default_params=default_capsaicin_params(),
        fit_spec=spec,
        output_json_path=out_b,
        source_in_report="IMP-01 synthetic markers",
        assumptions=["Scenario assumption: synthetic noise-free markers were used for deterministic test."],
    )

    for path in (out_a, out_b):
        assert path.exists()
        payload = json.loads(path.read_text(encoding="utf-8"))
        required_keys = {
            "fitted_params",
            "fixed_params",
            "bounds",
            "init_guess",
            "objective_definition",
            "residuals_summary",
            "seed",
            "scipy_version",
            "source_in_report",
            "assumptions",
        }
        assert required_keys.issubset(payload.keys())

    assert report_a["fitted_params"] == report_b["fitted_params"]
    assert report_a["residuals_summary"] == report_b["residuals_summary"]


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_identifiability_guard_raises_for_incomplete_data(tmp_path: Path) -> None:
    marker_df = pd.DataFrame({"t_h": [0.0, 0.5], "histamine_nm": [50.0, 70.0]})
    spec = FitSpec(
        parameters=(
            ParameterSpec("phase1.amplitude_nm", init=100.0, lower=10.0, upper=500.0),
            ParameterSpec("phase1.tau_rise_h", init=0.1, lower=0.01, upper=1.0),
            ParameterSpec("phase1.tau_fall_h", init=0.4, lower=0.1, upper=2.0),
        ),
    )

    with pytest.raises(ValueError, match=r"\[неполные данные\]"):
        fit_histamine_to_markers(
            marker_df=marker_df,
            model_fn=capsaicin_histamine,
            default_params=default_capsaicin_params(),
            fit_spec=spec,
            output_json_path=tmp_path / "runs" / "bad" / "fitted_params.json",
            source_in_report="IMP-01",
        )
