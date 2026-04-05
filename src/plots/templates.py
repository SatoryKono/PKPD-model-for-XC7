from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd


@dataclass(frozen=True)
class PlotAnnotationOptions:
    """Optional visual annotations for generated plots."""

    phase_markers_h: tuple[float, ...] = ()
    ec50_nm: float | None = None


@dataclass(frozen=True)
class PlotRenderResult:
    """Persisted image and corresponding numeric rows used for snapshot testing."""

    image_path: Path
    data_rows: pd.DataFrame


def _draw_phase_markers(ax: plt.Axes, markers_h: Iterable[float]) -> None:
    for marker in markers_h:
        ax.axvline(float(marker), color="grey", linestyle="--", linewidth=0.8, alpha=0.7)


def _save(fig: plt.Figure, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def render_histamine(
    timeseries: pd.DataFrame,
    out_path: str | Path,
    annotations: PlotAnnotationOptions | None = None,
) -> PlotRenderResult:
    """Render histamine profile H(t)."""

    data = timeseries.loc[:, ["time_h", "histamine_nm"]].copy()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(data["time_h"], data["histamine_nm"], color="#1f77b4", label="Histamine")
    ax.set_title("Histamine profile")
    ax.set_xlabel("Time (h)")
    ax.set_ylabel("Histamine (nM)")

    opts = annotations or PlotAnnotationOptions()
    if opts.phase_markers_h:
        _draw_phase_markers(ax, opts.phase_markers_h)

    if opts.ec50_nm is not None:
        ax.axhline(float(opts.ec50_nm), color="#d62728", linestyle=":", linewidth=1.0, label="EC50")

    ax.legend()
    image_path = _save(fig, Path(out_path))
    return PlotRenderResult(image_path=image_path, data_rows=data)


def render_receptors(
    timeseries: pd.DataFrame,
    out_path: str | Path,
    annotations: PlotAnnotationOptions | None = None,
) -> PlotRenderResult:
    """Render receptor trafficking states R_surf/R_int over time."""

    data = timeseries.loc[:, ["time_h", "R_surf", "R_int"]].copy()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(data["time_h"], data["R_surf"], label="R_surf", color="#2ca02c")
    ax.plot(data["time_h"], data["R_int"], label="R_int", color="#9467bd")
    ax.set_title("Receptor states")
    ax.set_xlabel("Time (h)")
    ax.set_ylabel("Fraction")

    opts = annotations or PlotAnnotationOptions()
    if opts.phase_markers_h:
        _draw_phase_markers(ax, opts.phase_markers_h)

    ax.legend()
    image_path = _save(fig, Path(out_path))
    return PlotRenderResult(image_path=image_path, data_rows=data)


def render_gsignaling(
    timeseries: pd.DataFrame,
    out_path: str | Path,
    annotations: PlotAnnotationOptions | None = None,
) -> PlotRenderResult:
    """Render a normalized G-signaling proxy derived from histamine and receptor availability."""

    opts = annotations or PlotAnnotationOptions()
    ec50_nm = float(opts.ec50_nm) if opts.ec50_nm is not None else 100.0

    data = timeseries.loc[:, ["time_h", "histamine_nm", "R_surf"]].copy()
    data["G_signal"] = (data["R_surf"] * data["histamine_nm"]) / (ec50_nm + data["histamine_nm"])

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(data["time_h"], data["G_signal"], label="G_signal", color="#ff7f0e")
    ax.set_title("G-signaling (proxy)")
    ax.set_xlabel("Time (h)")
    ax.set_ylabel("Activity (a.u.)")

    if opts.phase_markers_h:
        _draw_phase_markers(ax, opts.phase_markers_h)

    if opts.ec50_nm is not None:
        ax.axhline(0.5 * data["R_surf"].max(), color="#d62728", linestyle=":", linewidth=1.0, label="EC50 guide")

    ax.legend()
    image_path = _save(fig, Path(out_path))
    return PlotRenderResult(image_path=image_path, data_rows=data.loc[:, ["time_h", "G_signal"]])
