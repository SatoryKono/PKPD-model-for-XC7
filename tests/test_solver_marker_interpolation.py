from __future__ import annotations

import numpy as np

from src.solvers.grids import build_marker_refined_grid, build_uniform_grid
from src.solvers.solve_ivp_wrapper import SolverConfig, solve_ivp_wrapper


# dy/dt = -k*y, y(t)=exp(-k*t) for y0=1
K = 0.3


def exp_decay_rhs(t: float, y: np.ndarray) -> np.ndarray:
    del t
    return np.array([-K * y[0]], dtype=float)


def test_wrapper_extracts_marker_points_in_hours_via_teval() -> None:
    config = SolverConfig(
        t_eval=build_uniform_grid((0.0, 2.0), step_h=0.5),
        marker_times_h=[0.25, 1.25],
        include_markers_in_t_eval=True,
        dense_output=False,
    )

    res = solve_ivp_wrapper(exp_decay_rhs, (0.0, 2.0), [1.0], config)

    assert hasattr(res, "marker_t")
    assert hasattr(res, "marker_y")
    np.testing.assert_allclose(res.marker_t, np.array([0.25, 1.25]))
    expected = np.exp(-K * res.marker_t)
    np.testing.assert_allclose(res.marker_y[0], expected, rtol=0, atol=2e-6)


def test_wrapper_extracts_marker_points_in_minutes_via_dense_output() -> None:
    # t_eval intentionally excludes markers; extraction should use sol.sol(t)
    config = SolverConfig(
        t_eval=build_uniform_grid((0.0, 2.0), step_h=0.5),
        marker_times_min=[15.0, 75.0],
        include_markers_in_t_eval=False,
        dense_output=True,
    )

    res = solve_ivp_wrapper(exp_decay_rhs, (0.0, 2.0), [1.0], config)

    expected_t_h = np.array([0.25, 1.25])
    np.testing.assert_allclose(res.marker_t, expected_t_h, rtol=0, atol=1e-12)
    np.testing.assert_allclose(res.marker_y[0], np.exp(-K * expected_t_h), rtol=0, atol=5e-6)


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
        t_eval=grid,
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
