from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def _round_grid(values: np.ndarray, decimals: int = 12) -> np.ndarray:
    return np.round(values.astype(float), decimals=decimals)


def build_uniform_grid(t_span_h: tuple[float, float], *, step_h: float, decimals: int = 12) -> np.ndarray:
    """Build an inclusive deterministic grid over hours."""
    if step_h <= 0.0:
        raise ValueError("step_h must be positive.")

    start_h, stop_h = t_span_h
    if stop_h < start_h:
        raise ValueError("t_span_h must be increasing.")

    count = int(np.floor((stop_h - start_h) / step_h))
    grid = start_h + (np.arange(count + 1, dtype=float) * step_h)
    if not np.isclose(grid[-1], stop_h):
        grid = np.append(grid, stop_h)
    else:
        grid[-1] = stop_h
    return _round_grid(grid, decimals)


def build_marker_refined_grid(
    t_span_h: tuple[float, float],
    *,
    base_step_h: float,
    markers: Sequence[float],
    marker_unit: str = "h",
    refine_half_window_h: float,
    refine_step_h: float,
    decimals: int = 12,
) -> np.ndarray:
    """Build a base grid plus a deterministic finer stencil around marker times."""
    grid = build_uniform_grid(t_span_h, step_h=base_step_h, decimals=decimals)
    if marker_unit == "min":
        marker_hours = np.asarray(markers, dtype=float) / 60.0
    elif marker_unit == "h":
        marker_hours = np.asarray(markers, dtype=float)
    else:
        raise ValueError("marker_unit must be 'h' or 'min'.")

    refined_parts: list[np.ndarray] = [grid]
    start_h, stop_h = t_span_h
    for marker_h in marker_hours:
        window_start = max(start_h, marker_h - refine_half_window_h)
        window_stop = min(stop_h, marker_h + refine_half_window_h)
        refined_parts.append(build_uniform_grid((window_start, window_stop), step_h=refine_step_h, decimals=decimals))
        refined_parts.append(np.array([marker_h], dtype=float))

    return _round_grid(np.unique(np.concatenate(refined_parts)), decimals)
