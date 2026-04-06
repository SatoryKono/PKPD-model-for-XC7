from __future__ import annotations

from collections.abc import Callable
from typing import cast

import numpy as np
from scipy.interpolate import PchipInterpolator  # type: ignore[import-untyped]

from pkpd_xc7.models.receptor_trafficking import (
    TraffickingCoreParams,
    receptor_trafficking_rhs,
)
from pkpd_xc7.solvers.solve_ivp_wrapper import SolverConfig, solve_ivp_wrapper


def solve_trafficking_ivp(
    time_grid_h: np.ndarray,
    histamine_grid_nm: np.ndarray,
    y0: tuple[float, float],
    params: TraffickingCoreParams,
    solver_config: SolverConfig,
    *,
    xc7_at_time_nm: Callable[[float], float] | None = None,
    tissue: str = "unknown",
) -> np.ndarray:
    """
    Решает систему ОДУ рецепторного траффика на заданной временной сетке.
    Используется PchipInterpolator для C1-гладкой и монотонной интерполяции H(t).
    """
    h_func = PchipInterpolator(time_grid_h, histamine_grid_nm)

    def rhs(t: float, y: np.ndarray) -> np.ndarray:
        h_val = float(h_func(t))
        xc7_val = 0.0 if xc7_at_time_nm is None else float(xc7_at_time_nm(float(t)))
        return receptor_trafficking_rhs(t, cast(list[float], y.tolist()), h_val, params, xc7_nm=xc7_val)

    t_span = (float(time_grid_h[0]), float(time_grid_h[-1]))

    result = solve_ivp_wrapper(rhs, t_span, y0, config=solver_config)

    if not result.success:
        raise RuntimeError(f"IVP solver failed for tissue '{tissue}': {result.message} (t_span={t_span})")

    return result.y