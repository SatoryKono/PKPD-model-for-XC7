from __future__ import annotations

import numpy as np
import pytest

from pathlib import Path

import yaml

from src.config.schemas import FormalinPhaseOverrides, FormalinProfileOverrides, ModelConfig
from src.histamine_profiles import (
    default_formalin_params,
    formalin_histamine,
    resolve_formalin_params,
    resolve_formalin_params_from_model_config,
)


def test_resolve_formalin_defaults_match_factory() -> None:
    a = default_formalin_params()
    b = resolve_formalin_params()
    assert a == b


def test_resolve_formalin_override_h_base_and_no_least_squares(monkeypatch: pytest.MonkeyPatch) -> None:
    import scipy.optimize as scipy_optimize

    calls: list[object] = []

    def _track(*_a: object, **_k: object) -> object:
        calls.append(True)
        raise AssertionError("least_squares must not run for fixed formalin path")

    monkeypatch.setattr(scipy_optimize, "least_squares", _track)

    p = resolve_formalin_params(overrides=FormalinProfileOverrides(h_base_nm=55.0))
    assert p.h_base_nm == 55.0
    t = np.array([0.0, 0.5])
    y = np.asarray(formalin_histamine(t, p), dtype=float)
    assert y.shape == t.shape
    assert calls == []


def test_resolve_formalin_phase_override() -> None:
    base = default_formalin_params()
    p = resolve_formalin_params(
        overrides=FormalinProfileOverrides(
            phase1=FormalinPhaseOverrides(amplitude_nm=base.phase1.amplitude_nm + 10.0),
        ),
    )
    assert p.phase1.amplitude_nm == base.phase1.amplitude_nm + 10.0


def test_resolve_formalin_invalid_phase_raises() -> None:
    with pytest.raises(ValueError, match="tau_fall"):
        resolve_formalin_params(
            overrides=FormalinProfileOverrides(
                phase1=FormalinPhaseOverrides(tau_rise_h=0.5, tau_fall_h=0.1),
            ),
        )


def test_resolve_formalin_idempotent_numpy_output() -> None:
    p = resolve_formalin_params(overrides=FormalinProfileOverrides(h_base_nm=60.0))
    t = np.linspace(0.0, 1.0, 5)
    a = np.asarray(formalin_histamine(t, p), dtype=float)
    b = np.asarray(formalin_histamine(t, p), dtype=float)
    np.testing.assert_array_equal(a, b)


def test_resolve_formalin_params_from_model_config() -> None:
    cfg = ModelConfig.model_validate(
        {
            "model_id": "formalin_cfg",
            "compound": "histamine",
            "loss_mode": "mse",
            "assumptions": ["test"],
            "traceability": {"source_in_report": "unit test"},
            "time_grid": [0.0, 1.0],
            "time_unit": "h",
            "initial_concentration": 10.0,
            "concentration_unit": "nM",
            "kinetics": {"k_abs": 0.5, "k_elim": 0.1, "rate_unit": "1/h"},
            "tissues": [
                {"name": "plasma", "volume": 1.0, "volume_unit": "L", "partition_coeff": 1.0},
            ],
            "plots": [],
            "formalin_profile": {"h_base_nm": 52.0},
        }
    )
    p = resolve_formalin_params_from_model_config(cfg)
    assert p.h_base_nm == 52.0


def test_metadata_parameter_source_overrides_when_trafficking_set(tmp_path: Path) -> None:
    import json

    from src import api

    payload = {
        "model_id": "meta_src",
        "compound": "histamine",
        "loss_mode": "mse",
        "assumptions": ["test"],
        "traceability": {"source_in_report": "unit test"},
        "time_grid": [0.0, 0.5, 1.0],
        "time_unit": "h",
        "initial_concentration": 50.0,
        "concentration_unit": "nM",
        "kinetics": {"k_abs": 0.5, "k_elim": 0.1, "rate_unit": "1/h"},
        "tissues": [
            {"name": "plasma", "volume": 1.0, "volume_unit": "L", "partition_coeff": 1.0},
        ],
        "plots": [],
        "trafficking": {
            "k_int_max": 2.5,
            "k_rec": 0.5,
            "k_synth": 0.05,
            "ec50_barr_nm": 1500.0,
            "hill_n": 1.0,
            "ec50_g_nm": 40.0,
        },
    }
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    api.simulate(cfg_path, tmp_path / "run")
    meta = json.loads((tmp_path / "run" / "metadata.json").read_text(encoding="utf-8"))
    assert meta["parameter_source"] == "overrides"
