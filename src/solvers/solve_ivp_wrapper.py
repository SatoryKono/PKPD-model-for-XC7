from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp
from scipy.integrate._ivp.ivp import OdeResult

from src.solvers.grids import to_hours


@dataclass(frozen=True)
class SolverConfig:
    """Scenario-level ODE solver configuration for SciPy solve_ivp.

    Notes:
    - Defaults are scenario assumptions, not universal recommendations.
    - Numerical method/tolerances/max_step are controlled only through this config.
    """

    method: str = "RK45"
    rtol: float = 1e-6
    atol: float = 1e-9
    max_step: float = np.inf
    t_eval: Sequence[float] | None = None
    dense_output: bool = False

    marker_times_h: Sequence[float] | None = None
    marker_times_min: Sequence[float] | None = None
    include_markers_in_t_eval: bool = True

    rounding_decimals: int | None = None


def _validate_t_span(t_span: tuple[float, float]) -> tuple[float, float]:
    t0, t1 = float(t_span[0]), float(t_span[1])
    if not t1 > t0:
        raise ValueError("t_span must satisfy t1 > t0")
    return t0, t1


def _normalize_eval_grid(
    t_eval: Sequence[float] | None,
    markers_h: np.ndarray,
    t_span: tuple[float, float],
    include_markers: bool,
) -> np.ndarray | None:
    t0, t1 = t_span
    values: list[np.ndarray] = []

    if t_eval is not None:
        values.append(np.asarray(list(t_eval), dtype=float))

    if include_markers and markers_h.size > 0:
        values.append(markers_h)

    if not values:
        return None

    grid = np.concatenate(values)
    if grid.ndim != 1:
        raise ValueError("t_eval must be one-dimensional")

    grid = np.unique(np.round(grid, 12))
    grid = grid[(grid >= t0) & (grid <= t1)]
    grid.sort()

    if grid.size == 0:
        return None
    if np.any(np.diff(grid) <= 0):
        raise ValueError("t_eval must be strictly increasing")

    return grid


def _collect_marker_hours(config: SolverConfig) -> np.ndarray:
    marker_parts: list[np.ndarray] = []
    if config.marker_times_h is not None:
        marker_parts.append(to_hours(config.marker_times_h, unit="h"))
    if config.marker_times_min is not None:
        marker_parts.append(to_hours(config.marker_times_min, unit="min"))

    if not marker_parts:
        return np.array([], dtype=float)

    out = np.unique(np.round(np.concatenate(marker_parts), 12))
    out.sort()
    return out


def _round_result(result: OdeResult, decimals: int) -> None:
    result.t = np.round(result.t, decimals=decimals)
    result.y = np.round(result.y, decimals=decimals)
    if hasattr(result, "marker_t"):
        result.marker_t = np.round(result.marker_t, decimals=decimals)
    if hasattr(result, "marker_y"):
        result.marker_y = np.round(result.marker_y, decimals=decimals)


def solve_ivp_wrapper(
    ode_fun: Callable[[float, np.ndarray], np.ndarray],
    t_span: tuple[float, float],
    y0: Sequence[float],
    config: SolverConfig,
) -> OdeResult:
    """Solve ODE using solve_ivp and optionally extract values in marker points.

    Marker extraction strategy:
    1) include markers into ``t_eval`` (exact samples in output grid), and/or
    2) interpolate with dense solution ``sol.sol(t_markers)`` if enabled.
    """

    normalized_t_span = _validate_t_span(t_span)
    marker_times_h = _collect_marker_hours(config)
    t_eval = _normalize_eval_grid(
        t_eval=config.t_eval,
        markers_h=marker_times_h,
        t_span=normalized_t_span,
        include_markers=config.include_markers_in_t_eval,
    )

    result = solve_ivp(
        fun=ode_fun,
        t_span=normalized_t_span,
        y0=np.asarray(y0, dtype=float),
        method=config.method,
        t_eval=t_eval,
        dense_output=config.dense_output,
        rtol=config.rtol,
        atol=config.atol,
        max_step=config.max_step,
    )

    if marker_times_h.size > 0:
        marker_times_h = marker_times_h[
            (marker_times_h >= normalized_t_span[0]) & (marker_times_h <= normalized_t_span[1])
        ]
        if marker_times_h.size > 0:
            marker_values = _extract_marker_values(result, marker_times_h)
            result.marker_t = marker_times_h
            result.marker_y = marker_values

    if config.rounding_decimals is not None:
        _round_result(result, decimals=config.rounding_decimals)

    return result


def _extract_marker_values(result: OdeResult, marker_times_h: Iterable[float]) -> np.ndarray:
    markers = np.asarray(list(marker_times_h), dtype=float)
    if markers.size == 0:
        return np.empty((result.y.shape[0], 0), dtype=float)

    if result.t.size > 0:
        indices = []
        has_all = True
        for m in markers:
            i = int(np.argmin(np.abs(result.t - m)))
            if not np.isclose(result.t[i], m, rtol=0.0, atol=1e-12):
                has_all = False
                break
            indices.append(i)
        if has_all:
            return result.y[:, indices]

    if result.sol is None:
        raise ValueError(
            "Marker times are not present in t_eval and dense_output is disabled; "
            "cannot extract marker values exactly."
        )

    return result.sol(markers)
