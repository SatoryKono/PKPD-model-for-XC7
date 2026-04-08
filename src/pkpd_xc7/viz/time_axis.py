from __future__ import annotations

from typing import TypeVar, cast

import numpy as np
import pandas as pd
from matplotlib.axes import Axes

TimeLike = TypeVar("TimeLike", float, np.ndarray, pd.Series)
TIME_AXIS_STEP_MIN = 15.0
TIME_AXIS_LABELED_MINUTES = (30.0, 60.0, 120.0, 240.0, 360.0, 480.0, 720.0, 1440.0)


def time_minutes_from_hours(time_h: TimeLike) -> TimeLike:
    """Convert model time in hours to report time in minutes."""
    if isinstance(time_h, pd.Series):
        minutes_series = (time_h.astype(float) * 60.0).rename(time_h.name)
        return cast(TimeLike, minutes_series)
    if np.isscalar(time_h):
        return cast(TimeLike, float(np.asarray(time_h, dtype=float).item()) * 60.0)
    return cast(TimeLike, np.asarray(time_h, dtype=float) * 60.0)


def time_axis_tick_positions(x_max_min: float) -> np.ndarray:
    """Return 15-minute tick positions up to the visible axis maximum."""
    safe_x_max = max(float(x_max_min), 0.0)
    tick_count = int(np.floor(safe_x_max / TIME_AXIS_STEP_MIN))
    return np.arange(tick_count + 1, dtype=float) * TIME_AXIS_STEP_MIN


def time_axis_tick_labels(tick_positions: np.ndarray) -> list[str]:
    """Label only the canonical report time markers requested for figures."""
    labeled_minutes = {int(value) for value in TIME_AXIS_LABELED_MINUTES}
    labels: list[str] = []
    for tick in tick_positions:
        tick_min = int(round(float(tick)))
        if tick_min in labeled_minutes:
            labels.append(str(tick_min))
        else:
            labels.append("")
    return labels


def labeled_time_axis_tick_positions(x_max_min: float) -> np.ndarray:
    """Return only the canonical labeled positions that fit in the visible range."""
    tick_positions = time_axis_tick_positions(x_max_min)
    labeled_minutes = {int(value) for value in TIME_AXIS_LABELED_MINUTES}
    return np.asarray(
        [tick for tick in tick_positions if int(round(float(tick))) in labeled_minutes],
        dtype=float,
    )


def apply_time_axis(ax: Axes, x_max_min: float) -> None:
    """Apply the canonical 15-minute time axis to a Matplotlib axes."""
    tick_positions = time_axis_tick_positions(x_max_min)
    labeled_positions = labeled_time_axis_tick_positions(x_max_min)
    labeled_minutes = {int(value) for value in TIME_AXIS_LABELED_MINUTES}
    minor_positions = np.asarray(
        [tick for tick in tick_positions if int(round(float(tick))) not in labeled_minutes],
        dtype=float,
    )

    ax.set_xticks(labeled_positions)
    ax.set_xticklabels(time_axis_tick_labels(labeled_positions))
    ax.set_xticks(minor_positions, minor=True)
