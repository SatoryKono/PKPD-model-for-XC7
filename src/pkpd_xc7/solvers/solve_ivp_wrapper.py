from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
from scipy.integrate import solve_ivp


SolverMethod = Literal["LSODA", "BDF", "Radau"]


@dataclass(frozen=True, slots=True)
class SolverConfig:
    t_eval: Sequence[float]
    method: SolverMethod = "LSODA"
    rtol: float = 1e-7
    atol: float = 1e-10
    max_step: float | None = None
    marker_times_h: Sequence[float] | None = None
    marker_times_min: Sequence[float] | None = None
    include_markers_in_t_eval: bool = True
    dense_output: bool = False
    rounding_decimals: int | None = 12


@dataclass(frozen=True, slots=True)
class SolvedIvpResult:
    t: np.ndarray
    y: np.ndarray
    success: bool
    message: str
    status: int
    nfev: int
    marker_t: np.ndarray
    marker_y: np.ndarray


def _to_marker_hours(config: SolverConfig) -> np.ndarray:
    markers: list[np.ndarray] = []
    if config.marker_times_h:
        markers.append(np.asarray(config.marker_times_h, dtype=float))
    if config.marker_times_min:
        markers.append(np.asarray(config.marker_times_min, dtype=float) / 60.0)
    if not markers:
        return np.array([], dtype=float)
    return np.unique(np.concatenate(markers))


def _round_array(values: np.ndarray, decimals: int | None) -> np.ndarray:
    if decimals is None:
        return values
    return np.round(values.astype(float), decimals=decimals)


def solver_metadata_snapshot(config: SolverConfig) -> dict[str, Any]:
    return {
        "solver_method": config.method,
        "rtol": config.rtol,
        "atol": config.atol,
        "max_step": config.max_step,
    }


def solve_ivp_wrapper(
    rhs: Callable[..., np.ndarray],
    t_span: tuple[float, float],
    y0: Sequence[float],
    config: SolverConfig,
    args: Sequence[Any] = (),
) -> SolvedIvpResult:
    t_eval = np.asarray(config.t_eval, dtype=float)
    marker_t = _to_marker_hours(config)
    solve_t_eval = t_eval
    if config.include_markers_in_t_eval and marker_t.size:
        solve_t_eval = np.unique(np.concatenate([t_eval, marker_t]))

    solve_kwargs: dict[str, Any] = {
        "method": config.method,
        "t_eval": solve_t_eval,
        "dense_output": config.dense_output or bool(marker_t.size and not config.include_markers_in_t_eval),
        "rtol": config.rtol,
        "atol": config.atol,
        "args": tuple(args),
    }
    if config.max_step is not None:
        solve_kwargs["max_step"] = config.max_step

    solved = solve_ivp(rhs, t_span, np.asarray(y0, dtype=float), **solve_kwargs)

    result_t = _round_array(np.asarray(solved.t, dtype=float), config.rounding_decimals)
    result_y = _round_array(np.asarray(solved.y, dtype=float), config.rounding_decimals)

    if marker_t.size == 0:
        marker_y = np.empty((result_y.shape[0], 0), dtype=float)
    elif config.include_markers_in_t_eval:
        marker_index = np.searchsorted(result_t, _round_array(marker_t, config.rounding_decimals))
        marker_y = result_y[:, marker_index]
    elif solved.sol is not None:
        marker_y = np.asarray(solved.sol(marker_t), dtype=float)
    else:
        marker_y = np.vstack([np.interp(marker_t, result_t, row) for row in result_y])

    marker_t = _round_array(marker_t, config.rounding_decimals)
    marker_y = _round_array(marker_y, config.rounding_decimals)

    return SolvedIvpResult(
        t=result_t,
        y=result_y,
        success=bool(solved.success),
        message=str(solved.message),
        status=int(solved.status),
        nfev=int(getattr(solved, "nfev", 0)),
        marker_t=marker_t,
        marker_y=marker_y,
    )
