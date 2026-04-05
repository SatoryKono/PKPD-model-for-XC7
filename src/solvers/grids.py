from __future__ import annotations

from collections.abc import Iterable

import numpy as np


_TIME_UNIT_TO_HOURS = {
    "h": 1.0,
    "min": 1.0 / 60.0,
}


def to_hours(time_points: Iterable[float], unit: str = "h") -> np.ndarray:
    """Convert an iterable of time points to hours."""

    if unit not in _TIME_UNIT_TO_HOURS:
        raise ValueError("unit must be one of {'h', 'min'}")

    arr = np.asarray(list(time_points), dtype=float)
    if arr.ndim != 1:
        raise ValueError("time_points must be one-dimensional")
    if arr.size == 0:
        return arr
    if np.any(arr < 0):
        raise ValueError("time_points must be non-negative")

    return arr * _TIME_UNIT_TO_HOURS[unit]


def build_uniform_grid(
    t_span_h: tuple[float, float],
    step_h: float,
    *,
    include_stop: bool = True,
) -> np.ndarray:
    """Build a uniform monotonic time grid in hours."""

    t0, t1 = float(t_span_h[0]), float(t_span_h[1])
    if not t1 > t0:
        raise ValueError("t_span_h must satisfy t1 > t0")
    if step_h <= 0:
        raise ValueError("step_h must be > 0")

    # arange is deterministic for fixed start/step and avoids floating drift from linspace-count guessing.
    grid = np.arange(t0, t1 + step_h * 0.5, step_h, dtype=float)
    if include_stop and not np.isclose(grid[-1], t1):
        grid = np.append(grid, t1)
    elif not include_stop and np.isclose(grid[-1], t1):
        grid = grid[:-1]

    return np.unique(np.round(grid, 12))


def build_marker_refined_grid(
    t_span_h: tuple[float, float],
    base_step_h: float,
    *,
    markers: Iterable[float] | None = None,
    marker_unit: str = "h",
    refine_half_window_h: float = 0.0,
    refine_step_h: float | None = None,
) -> np.ndarray:
    """Build grid with exact marker points and optional local refinement around markers."""

    base = build_uniform_grid(t_span_h=t_span_h, step_h=base_step_h, include_stop=True)
    t0, t1 = t_span_h

    if markers is None:
        return base

    marker_h = to_hours(markers, unit=marker_unit)
    marker_h = marker_h[(marker_h >= t0) & (marker_h <= t1)]

    points = [base, marker_h]

    if refine_half_window_h > 0:
        if refine_step_h is None or refine_step_h <= 0:
            raise ValueError("refine_step_h must be > 0 when refine_half_window_h > 0")
        for marker in marker_h:
            left = max(t0, marker - refine_half_window_h)
            right = min(t1, marker + refine_half_window_h)
            local = build_uniform_grid((left, right), refine_step_h, include_stop=True)
            local = np.append(local, marker)
            points.append(local)

    grid = np.unique(np.round(np.concatenate(points), 12))
    grid.sort()
    return grid
