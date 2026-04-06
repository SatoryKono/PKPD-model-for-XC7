from __future__ import annotations

import importlib
from types import SimpleNamespace

import numpy as np
import pytest

from pkpd_xc7.config.schemas import ModelConfig
from pkpd_xc7.models.receptor_trafficking import receptor_trafficking_rhs, steady_state_ic
from pkpd_xc7.simulation.model_mapping import model_config_to_trafficking_core
from pkpd_xc7.solvers.ivp import solve_trafficking_ivp
from pkpd_xc7.solvers.grids import build_marker_refined_grid, build_uniform_grid
from pkpd_xc7.solvers.solve_ivp_wrapper import SolverConfig, solve_ivp_wrapper, solver_metadata_snapshot

K = 0.3


def _payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "model_id": "phase2",
        "compound": "xc7",
        "traceability": {"source_in_report": "table-1"},
        "assumptions": ["baseline assumption"],
        "driver": {"driver_type": "scenario", "scenario_id": "formalin"},
        "tissues": ["skin"],
        "time_grid_h": [0.0, 0.5, 1.0],
    }
    payload.update(overrides)
    return payload


def exp_decay_rhs(t: float, y: np.ndarray) -> np.ndarray:
    del t
    return np.array([-K * y[0]], dtype=float)


def test_wrapper_extracts_marker_points_in_hours_via_teval() -> None:
    config = SolverConfig(
        t_eval=build_uniform_grid((0.0, 2.0), step_h=0.5).tolist(),
        marker_times_h=[0.25, 1.25],
        include_markers_in_t_eval=True,
        dense_output=False,
    )

    res = solve_ivp_wrapper(exp_decay_rhs, (0.0, 2.0), [1.0], config)

    np.testing.assert_allclose(res.marker_t, np.array([0.25, 1.25]))
    np.testing.assert_allclose(res.marker_y[0], np.exp(-K * res.marker_t), rtol=0.0, atol=2e-6)


def test_wrapper_extracts_marker_points_in_minutes_via_dense_output() -> None:
    config = SolverConfig(
        t_eval=build_uniform_grid((0.0, 2.0), step_h=0.5).tolist(),
        marker_times_min=[15.0, 75.0],
        include_markers_in_t_eval=False,
        dense_output=True,
    )

    res = solve_ivp_wrapper(exp_decay_rhs, (0.0, 2.0), [1.0], config)

    expected_t_h = np.array([0.25, 1.25])
    np.testing.assert_allclose(res.marker_t, expected_t_h, rtol=0.0, atol=1e-12)
    np.testing.assert_allclose(res.marker_y[0], np.exp(-K * expected_t_h), rtol=0.0, atol=5e-6)


def test_solver_determinism_for_fixed_config_and_grid() -> None:
    grid = build_marker_refined_grid(
        (0.0, 3.0),
        base_step_h=0.5,
        markers=[30.0, 90.0],
        marker_unit="min",
        refine_half_window_h=0.25,
        refine_step_h=0.05,
    )
    cfg = SolverConfig(
        t_eval=grid.tolist(),
        marker_times_min=[30.0, 90.0],
        include_markers_in_t_eval=True,
        dense_output=True,
        rounding_decimals=12,
        rtol=1e-7,
        atol=1e-10,
        max_step=0.2,
    )

    a = solve_ivp_wrapper(exp_decay_rhs, (0.0, 3.0), [1.0], cfg)
    b = solve_ivp_wrapper(exp_decay_rhs, (0.0, 3.0), [1.0], cfg)

    np.testing.assert_array_equal(a.t, b.t)
    np.testing.assert_array_equal(a.y, b.y)
    np.testing.assert_array_equal(a.marker_t, b.marker_t)
    np.testing.assert_array_equal(a.marker_y, b.marker_y)


def test_solver_metadata_snapshot_contains_contract() -> None:
    cfg = SolverConfig(t_eval=[0.0, 1.0], method="Radau", rtol=1e-6, atol=1e-9, max_step=0.25)
    assert solver_metadata_snapshot(cfg) == {
        "solver_method": "Radau",
        "rtol": 1e-6,
        "atol": 1e-9,
        "max_step": 0.25,
    }


def test_wrapper_passes_method_tspan_t_eval_and_max_step(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    solve_ivp_module = importlib.import_module("pkpd_xc7.solvers.solve_ivp_wrapper")

    def fake_solve_ivp(rhs, t_span, y0, **kwargs):  # type: ignore[no-untyped-def]
        captured["t_span"] = t_span
        captured["y0"] = tuple(y0)
        captured["kwargs"] = kwargs
        return SimpleNamespace(
            t=np.array(kwargs["t_eval"], dtype=float),
            y=np.array([[1.0 for _ in kwargs["t_eval"]]], dtype=float),
            success=True,
            message="ok",
            status=0,
            nfev=3,
            sol=lambda t: np.array([np.ones_like(t, dtype=float)]),
        )

    monkeypatch.setattr(solve_ivp_module, "solve_ivp", fake_solve_ivp)
    cfg = SolverConfig(t_eval=[0.0, 0.5, 1.0], method="BDF", max_step=0.1)
    res = solve_ivp_wrapper(exp_decay_rhs, (0.0, 1.0), [1.0], cfg)

    assert res.success is True
    assert captured["t_span"] == (0.0, 1.0)
    assert captured["y0"] == (1.0,)
    assert isinstance(captured["kwargs"], dict)
    kwargs = captured["kwargs"]
    assert kwargs["method"] == "BDF"
    assert kwargs["max_step"] == pytest.approx(0.1)
    np.testing.assert_array_equal(np.asarray(kwargs["t_eval"]), np.array([0.0, 0.5, 1.0]))


def test_stiff_smoke_matches_analytic_steady_state() -> None:
    cfg = ModelConfig.model_validate(
        _payload(
            trafficking={
                "k_int_max_per_h": 12.0,
                "k_rec_per_h": 0.08,
                "k_synth_per_h": 0.15,
                "ec50_barr_nm": 150.0,
                "hill_n": 1.0,
                "ec50_g_nm": 50.0,
                "constitutive_activity": 0.0,
            }
        )
    )
    params = model_config_to_trafficking_core(cfg)
    histamine_nm = 5_000.0
    expected = np.array(steady_state_ic(histamine_nm, params))

    def rhs(t_h: float, y: np.ndarray) -> np.ndarray:
        return receptor_trafficking_rhs(t_h, y.tolist(), histamine_nm, params)

    config = SolverConfig(
        t_eval=build_uniform_grid((0.0, 24.0), step_h=0.5).tolist(),
        method="BDF",
        rtol=1e-7,
        atol=1e-10,
        max_step=0.25,
    )
    solved = solve_ivp_wrapper(rhs, (0.0, 24.0), [1.0, 0.0], config)

    assert solved.success is True
    np.testing.assert_allclose(solved.y[:, -1], expected, rtol=0.0, atol=2e-4)


def test_solve_trafficking_ivp_uses_xc7_runtime_callable() -> None:
    cfg = ModelConfig.model_validate(_payload(trafficking={"h_base_nm": 50.0, "kb_arr_nm": 100.0}))
    params = model_config_to_trafficking_core(cfg)
    time_grid = np.array([0.0, 1.0], dtype=float)
    histamine_grid = np.array([50.0, 50.0], dtype=float)
    y0 = steady_state_ic(50.0, params, xc7_nm=100.0)
    calls: list[float] = []

    def xc7_at_time_nm(t_h: float) -> float:
        calls.append(float(t_h))
        return 100.0

    solved = solve_trafficking_ivp(
        time_grid,
        histamine_grid,
        y0,
        params,
        solver_config=SolverConfig(t_eval=time_grid.tolist()),
        xc7_at_time_nm=xc7_at_time_nm,
        tissue="skin",
    )

    assert solved.shape == (2, 2)
    assert calls
