from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pkpd_xc7.io.layout import (
    ANTAGONIST_CONCENTRATION_COL,
    G_SIGNAL_CONSTITUTIVE_PCT_COL,
    G_SIGNAL_PCT_COL,
    HISTAMINE_COL,
    R_INT_COL,
    R_SURF_COL,
    TIME_H_COL,
    TISSUE_COL,
)
from pkpd_xc7.io.loaders import SimulationRun
from pkpd_xc7.models.h3_signaling import g_signal_percent, g_signaling_fraction
from pkpd_xc7.viz.time_axis import apply_time_axis, time_minutes_from_hours

FIGURE_DPI = 180
SPINAL_LABEL = "Спинной мозг"
TISSUE_LABELS: dict[str, str] = {
    "skin": "Кожа",
    "spinal": SPINAL_LABEL,
    "spinal_cord": SPINAL_LABEL,
    "spinal_coord": SPINAL_LABEL,
    "ganglia": "Симп. ганглии",
    "brain": "Головной мозг",
    "muscle": "Мышца",
    "peritoneum": "Брюшина",
    "bladder": "Мочевой пузырь",
}
TISSUE_COLORS: dict[str, str] = {
    "skin": "#d62728",
    "spinal": "#1f77b4",
    "spinal_cord": "#1f77b4",
    "spinal_coord": "#1f77b4",
    "ganglia": "#2ca02c",
    "brain": "#9467bd",
    "muscle": "#8c564b",
    "peritoneum": "#ff7f0e",
    "bladder": "#17becf",
}
EC50_COLOR = "#888888"
CA_COLOR = "#aaaaaa"
INTACT_G_SIGNAL_LINEWIDTH = 0.8
FILL_ALPHA = 0.15
LEGEND_UPPER_RIGHT = "upper right"


@dataclass(frozen=True, slots=True)
class ScenarioPlotSpec:
    figure_group: int
    file_stem: str
    model_title: str
    tissue_order: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ScenarioFigureArtifacts:
    out_dir: Path
    histamine_png: Path | None
    receptor_png: Path | None
    g_signal_png: Path
    antagonist_png: Path | None = None


def _extract_trafficking_params_by_tissue(run: SimulationRun) -> dict[str, Mapping[str, Any]]:
    payload = run.meta.get("trafficking_params_by_tissue")
    if isinstance(payload, Mapping):
        resolved: dict[str, Mapping[str, Any]] = {}
        for tissue, params in payload.items():
            if not isinstance(params, Mapping):
                raise ValueError("Simulation meta 'trafficking_params_by_tissue' must map tissues to parameter mappings.")
            resolved[str(tissue)] = params
        return resolved

    legacy_payload = run.meta.get("trafficking_params")
    if isinstance(legacy_payload, Mapping):
        tissues = tuple(dict.fromkeys(run.timeseries[TISSUE_COL].astype(str).tolist()))
        return dict.fromkeys(tissues, legacy_payload)

    raise ValueError("Simulation meta must include 'trafficking_params_by_tissue' or legacy 'trafficking_params'.")


def _params_for_tissue(params_by_tissue: Mapping[str, Mapping[str, Any]], tissue: str) -> Mapping[str, Any]:
    if tissue not in params_by_tissue:
        allowed = ", ".join(sorted(params_by_tissue))
        raise KeyError(f"Missing trafficking params for tissue '{tissue}'. Expected one of: {allowed}")
    return params_by_tissue[tissue]


def _get_float_param(params: Mapping[str, Any], key: str) -> float:
    if key not in params:
        raise KeyError(f"Missing required trafficking parameter for plotting: {key}")
    return float(params[key])


def _extract_antagonist_pk_meta(run: SimulationRun) -> Mapping[str, Any] | None:
    payload = run.meta.get("antagonist_pk")
    if payload is None:
        return None
    if not isinstance(payload, Mapping):
        raise ValueError("Simulation meta 'antagonist_pk' must be a mapping when present.")
    return payload


def _tissue_label(tissue: str) -> str:
    return TISSUE_LABELS.get(tissue, tissue.replace("_", " ").title())


def _tissue_color(tissue: str) -> str:
    return TISSUE_COLORS.get(tissue, "#4c4c4c")


def _format_peak_label(value: float, unit: str, time_min: float, *, decimals: int) -> str:
    unit_suffix = unit if unit == "%" else f" {unit}"
    return f"{value:.{decimals}f}{unit_suffix} ({time_min:.0f}мин)"


def _iter_tissue_frames(df: pd.DataFrame, preferred_order: Sequence[str]) -> list[tuple[str, pd.DataFrame]]:
    present = list(dict.fromkeys(df[TISSUE_COL].astype(str).tolist()))
    ordered = [tissue for tissue in preferred_order if tissue in present]
    ordered.extend(tissue for tissue in present if tissue not in ordered)
    frames: list[tuple[str, pd.DataFrame]] = []
    for tissue in ordered:
        tissue_df = (
            df.loc[df[TISSUE_COL] == tissue]
            .sort_values(TIME_H_COL, kind="stable")
            .reset_index(drop=True)
        )
        if not tissue_df.empty:
            frames.append((tissue, tissue_df))
    return frames


def _make_axes(count: int) -> tuple[Figure, tuple[Axes, ...]]:
    fig, axes = plt.subplots(1, count, figsize=(5.0 * count, 4.5), sharey=False)
    if isinstance(axes, np.ndarray):
        return fig, tuple(axes.tolist())
    return fig, (axes,)


def _style_axis(ax: Axes, x_max: float, ylabel: str, title: str) -> None:
    ax.set_xlabel("Время (мин)")
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.set_xlim(0.0, x_max)
    apply_time_axis(ax, x_max)
    ax.tick_params(labelsize=8)
    ax.tick_params(axis="x", which="minor", length=2.5)
    ax.grid(True, axis="y", which="major", linestyle="--", linewidth=0.4, alpha=0.5)
    ax.grid(True, axis="x", which="major", linestyle="--", linewidth=0.4, alpha=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _save_figure(fig: Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)


def _g_signal_plot_series(
    tissue_df: pd.DataFrame,
    *,
    ec50_g_nm: float,
    hill_n: float,
    constitutive_activity: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    histamine_nm = tissue_df[HISTAMINE_COL].to_numpy(dtype=float)
    r_surf = tissue_df[R_SURF_COL].to_numpy(dtype=float)

    g_with_payload = tissue_df.get(G_SIGNAL_PCT_COL)
    if g_with_payload is None:
        g_with_pct = g_signal_percent(
            g_signaling_fraction(
                histamine_nm,
                r_surf,
                ec50_g_nm,
                hill_n=hill_n,
                constitutive_activity=constitutive_activity,
            )
        )
    else:
        g_with_pct = g_with_payload.to_numpy(dtype=float)

    g_constitutive_payload = tissue_df.get(G_SIGNAL_CONSTITUTIVE_PCT_COL)
    if g_constitutive_payload is None:
        g_constitutive_pct = g_signal_percent(np.clip(constitutive_activity * r_surf, 0.0, 1.0))
    else:
        g_constitutive_pct = g_constitutive_payload.to_numpy(dtype=float)

    g_without_pct = g_signal_percent(
        g_signaling_fraction(
            histamine_nm,
            np.ones_like(r_surf),
            ec50_g_nm,
            hill_n=hill_n,
            constitutive_activity=constitutive_activity,
        )
    )
    return (
        np.asarray(g_with_pct, dtype=float),
        np.asarray(g_without_pct, dtype=float),
        np.asarray(g_constitutive_pct, dtype=float),
    )


def plot_scenario_run_figures(
    run: SimulationRun,
    spec: ScenarioPlotSpec,
    *,
    out_dir: Path | str,
    baseline_run: SimulationRun | None = None,
    intact_reference_run: SimulationRun | None = None,
    render_histamine_figure: bool = True,
    render_internalization_figure: bool = True,
    plot_g_signal_without_internalization: bool = True,
    render_antagonist_figure: bool = True,
) -> ScenarioFigureArtifacts:
    """Render the canonical three-panel report figures for a simulation run.

    Optional ``intact_reference_run`` (e.g. intact scenario, 0 mg/kg) adds a G-signaling overlay only;
    histamine and internalization panels still use ``baseline_run`` when provided.

    When ``render_histamine_figure`` or ``render_internalization_figure`` is false, that PNG is not
    written and the corresponding path in ``ScenarioFigureArtifacts`` is ``None``.

    When ``plot_g_signal_without_internalization`` is false, the «Без интернализации» line and its
    ``fill_between`` band are omitted on the G-signaling panel.

    When ``render_antagonist_figure`` is false, the XC7 concentration panel is not written even if
    antagonist data are present; ``antagonist_png`` is ``None``.
    """
    params_by_tissue = _extract_trafficking_params_by_tissue(run)

    tissues = _iter_tissue_frames(run.timeseries, spec.tissue_order)
    if not tissues:
        raise ValueError("Simulation timeseries is empty; cannot render figures.")

    resolved_out_dir = Path(out_dir)
    x_max = float(
        np.max(time_minutes_from_hours(run.timeseries[TIME_H_COL].to_numpy(dtype=float)))
    )
    baseline_by_tissue: dict[str, pd.DataFrame] = {}
    if baseline_run is not None:
        baseline_by_tissue = dict(_iter_tissue_frames(baseline_run.timeseries, spec.tissue_order))

    intact_by_tissue: dict[str, pd.DataFrame] = {}
    if intact_reference_run is not None:
        intact_by_tissue = dict(_iter_tissue_frames(intact_reference_run.timeseries, spec.tissue_order))

    histamine_png: Path | None = None
    receptor_png: Path | None = None
    histamine_target = resolved_out_dir / f"fig{spec.figure_group}_1_{spec.file_stem}_histamine.png"
    receptor_target = resolved_out_dir / f"fig{spec.figure_group}_2_{spec.file_stem}_internalization.png"
    g_signal_png = resolved_out_dir / f"fig{spec.figure_group}_3_{spec.file_stem}_gsignaling.png"
    antagonist_png = resolved_out_dir / f"fig{spec.figure_group}_4_{spec.file_stem}_xc7_concentration.png"

    if render_histamine_figure:
        fig_histamine, axes_histamine = _make_axes(len(tissues))
        for ax, (tissue, tissue_df) in zip(axes_histamine, tissues):
            traffic = _params_for_tissue(params_by_tissue, tissue)
            ec50_g_nm = _get_float_param(traffic, "ec50_g_nm")
            ec50_barr_nm = _get_float_param(traffic, "ec50_barr_nm")
            time_min = time_minutes_from_hours(tissue_df[TIME_H_COL].to_numpy(dtype=float))
            histamine_nm = tissue_df[HISTAMINE_COL].to_numpy(dtype=float)
            histamine_um = histamine_nm / 1000.0
            color = _tissue_color(tissue)
            label = _tissue_label(tissue)
            base_um = histamine_um[0]

            ax.plot(time_min, histamine_um, color=color, linewidth=2.0)
            baseline_tissue_df = baseline_by_tissue.get(tissue)
            if baseline_tissue_df is not None:
                baseline_time_min = time_minutes_from_hours(
                    baseline_tissue_df[TIME_H_COL].to_numpy(dtype=float)
                )
                baseline_histamine_um = baseline_tissue_df[HISTAMINE_COL].to_numpy(dtype=float) / 1000.0
                ax.plot(
                    baseline_time_min,
                    baseline_histamine_um,
                    color="#808080",
                    linewidth=1.0,
                    linestyle=":",
                    label="Контроль (0 mg/kg)",
                )
            ax.axhline(ec50_g_nm / 1000.0, color=EC50_COLOR, linestyle="--", linewidth=1.0, label="EC50(G)")
            ax.axhline(
                ec50_barr_nm / 1000.0,
                color=EC50_COLOR,
                linestyle=":",
                linewidth=1.0,
                label="EC50(β-arr)",
            )
            ax.axhline(base_um, color=color, linestyle=":", linewidth=0.8, alpha=0.5)

            peak_idx = int(np.argmax(histamine_um))
            ax.annotate(
                _format_peak_label(histamine_um[peak_idx], "мкМ", time_min[peak_idx], decimals=2),
                xy=(time_min[peak_idx], histamine_um[peak_idx]),
                xytext=(time_min[peak_idx], histamine_um[peak_idx] * 0.82 if histamine_um[peak_idx] > 0 else 0.02),
                fontsize=7.5,
                color=color,
                arrowprops={"arrowstyle": "->", "color": color, "lw": 0.7},
            )
            ax.annotate(
                f"База: {base_um:.3f} мкМ",
                xy=(x_max, base_um),
                ha="right",
                va="bottom",
                fontsize=7.5,
                color="#555555",
            )
            _style_axis(ax, x_max, "Концентрация (мкМ)", label)
            ax.legend(fontsize=7.5, loc=LEGEND_UPPER_RIGHT, framealpha=0.8)
        # Figure-level title intentionally disabled.
        # fig_histamine.suptitle(
        #     f"Рис. {spec.figure_group}.1. Динамика концентрации гистамина — {spec.model_title}",
        #     fontsize=10,
        #     fontweight="bold",
        #     y=1.02,
        # )
        _save_figure(fig_histamine, histamine_target)
        histamine_png = histamine_target

    if render_internalization_figure:
        fig_receptor, axes_receptor = _make_axes(len(tissues))
        for ax, (tissue, tissue_df) in zip(axes_receptor, tissues):
            time_min = time_minutes_from_hours(tissue_df[TIME_H_COL].to_numpy(dtype=float))
            r_surf_pct = tissue_df[R_SURF_COL].to_numpy(dtype=float) * 100.0
            r_int_pct = tissue_df[R_INT_COL].to_numpy(dtype=float) * 100.0
            color = _tissue_color(tissue)
            label = _tissue_label(tissue)

            ax.plot(time_min, r_surf_pct, color=color, linewidth=2.0, label="На поверхности (R_surf)")
            baseline_tissue_df = baseline_by_tissue.get(tissue)
            if baseline_tissue_df is not None:
                baseline_time_min = time_minutes_from_hours(
                    baseline_tissue_df[TIME_H_COL].to_numpy(dtype=float)
                )
                baseline_r_surf_pct = baseline_tissue_df[R_SURF_COL].to_numpy(dtype=float) * 100.0
                ax.plot(
                    baseline_time_min,
                    baseline_r_surf_pct,
                    color="#808080",
                    linewidth=1.6,
                    linestyle="-",
                    label="Контроль (XC7DCH 0 mg/kg), R_surf",
                )
            ax.plot(
                time_min,
                r_int_pct,
                color=color,
                linewidth=1.5,
                linestyle="--",
                label="В эндосомах (R_int)",
            )
            ax.fill_between(time_min, 0.0, r_int_pct, alpha=FILL_ALPHA, color=color)

            peak_idx = int(np.argmax(r_int_pct))
            ax.annotate(
                _format_peak_label(r_int_pct[peak_idx], "%", time_min[peak_idx], decimals=1),
                xy=(time_min[peak_idx], r_int_pct[peak_idx]),
                xytext=(time_min[peak_idx], min(r_int_pct[peak_idx] + 5.0, 100.0)),
                fontsize=7.5,
                color=color,
                arrowprops={"arrowstyle": "->", "color": color, "lw": 0.7},
            )
            ax.annotate(
                f"{r_surf_pct[-1]:.1f}%",
                xy=(x_max, r_surf_pct[-1]),
                ha="right",
                va="bottom",
                fontsize=7.5,
                color=color,
            )
            _style_axis(ax, x_max, "Рецепторы H3R (% от общего пула)", label)
            ax.set_ylim(-1.0, 105.0)
            ax.legend(fontsize=7.5, loc="lower right", framealpha=0.8)
        # Figure-level title intentionally disabled.
        # fig_receptor.suptitle(
        #     f"Рис. {spec.figure_group}.2. Интернализация и ресайклинг H3R — {spec.model_title}",
        #     fontsize=10,
        #     fontweight="bold",
        #     y=1.02,
        # )
        _save_figure(fig_receptor, receptor_target)
        receptor_png = receptor_target

    antagonist_meta = _extract_antagonist_pk_meta(run)
    main_dose_mg_kg = 0.0
    if antagonist_meta is not None and antagonist_meta.get("dose_mg_per_kg") is not None:
        main_dose_mg_kg = float(antagonist_meta["dose_mg_per_kg"])
    main_g_signal_label = f"XC7DCH, {main_dose_mg_kg:g} mg/kg"

    fig_g_signal, axes_g_signal = _make_axes(len(tissues))
    for ax, (tissue, tissue_df) in zip(axes_g_signal, tissues):
        traffic = _params_for_tissue(params_by_tissue, tissue)
        ec50_g_nm = _get_float_param(traffic, "ec50_g_nm")
        hill_n = _get_float_param(traffic, "hill_n")
        constitutive_activity = _get_float_param(traffic, "constitutive_activity")
        time_min = time_minutes_from_hours(tissue_df[TIME_H_COL].to_numpy(dtype=float))
        g_with_pct, g_without_pct, g_constitutive_pct = _g_signal_plot_series(
            tissue_df,
            ec50_g_nm=ec50_g_nm,
            hill_n=hill_n,
            constitutive_activity=constitutive_activity,
        )
        color = _tissue_color(tissue)
        label = _tissue_label(tissue)

        baseline_tissue_df = baseline_by_tissue.get(tissue)
        if baseline_tissue_df is not None:
            baseline_time_min = time_minutes_from_hours(
                baseline_tissue_df[TIME_H_COL].to_numpy(dtype=float)
            )
            baseline_g_with_pct, _, _ = _g_signal_plot_series(
                baseline_tissue_df,
                ec50_g_nm=ec50_g_nm,
                hill_n=hill_n,
                constitutive_activity=constitutive_activity,
            )
            ax.plot(
                baseline_time_min,
                baseline_g_with_pct,
                color="#808080",
                linewidth=1.6,
                linestyle="-",
                label="Контроль (XC7DCH 0 mg/kg)",
            )
        intact_tissue_df = intact_by_tissue.get(tissue)
        if intact_tissue_df is not None:
            intact_time_min = time_minutes_from_hours(
                intact_tissue_df[TIME_H_COL].to_numpy(dtype=float)
            )
            intact_g_with_pct, _, _ = _g_signal_plot_series(
                intact_tissue_df,
                ec50_g_nm=ec50_g_nm,
                hill_n=hill_n,
                constitutive_activity=constitutive_activity,
            )
            ax.plot(
                intact_time_min,
                intact_g_with_pct,
                color="#808080",
                linewidth=INTACT_G_SIGNAL_LINEWIDTH,
                linestyle=":",
                label="Интакт",
            )
        if plot_g_signal_without_internalization:
            ax.plot(
                time_min,
                g_without_pct,
                color=color,
                linewidth=1.5,
                linestyle=":",
                label="Без интернализации",
            )
        ax.plot(
            time_min,
            g_with_pct,
            color=color,
            linewidth=2.0,
            linestyle="-",
            label=main_g_signal_label,
        )
        ax.plot(
            time_min,
            g_constitutive_pct,
            color=CA_COLOR,
            linewidth=1.0,
            linestyle="--",
            label="Конститутивная активность H3R.",
        )
        if plot_g_signal_without_internalization:
            ax.fill_between(time_min, g_with_pct, g_without_pct, alpha=FILL_ALPHA, color=color)

        peak_idx = int(np.argmax(g_with_pct))
        ax.annotate(
            _format_peak_label(g_with_pct[peak_idx], "%", time_min[peak_idx], decimals=1),
            xy=(time_min[peak_idx], g_with_pct[peak_idx]),
            xytext=(time_min[peak_idx], max(g_with_pct[peak_idx] - 10.0, 2.0)),
            fontsize=7.5,
            color=color,
            arrowprops={"arrowstyle": "->", "color": color, "lw": 0.7},
        )
        ax.annotate(
            f"{g_with_pct[-1]:.1f}%",
            xy=(x_max, g_with_pct[-1]),
            ha="right",
            va="top",
            fontsize=7.5,
            color=color,
        )
        _style_axis(ax, x_max, "G-сигналинг H3R (% Emax)", label)
        ax.set_ylim(0.0, 105.0)
        ax.legend(fontsize=7.5, loc=LEGEND_UPPER_RIGHT, framealpha=0.8)
    # Figure-level title intentionally disabled.
    # fig_g_signal.suptitle(
    #     f"Рис. {spec.figure_group}.3. G-сигналинг H3R с учётом интернализации — {spec.model_title}",
    #     fontsize=10,
    #     fontweight="bold",
    #     y=1.02,
    # )
    _save_figure(fig_g_signal, g_signal_png)

    antagonist_available = (
        ANTAGONIST_CONCENTRATION_COL in run.timeseries.columns
        and not run.timeseries[ANTAGONIST_CONCENTRATION_COL].isna().all()
    )
    resolved_antagonist_png: Path | None = None
    if render_antagonist_figure and antagonist_available:
        dose_label = None
        species_label = None
        regimen_label = None
        if antagonist_meta is not None:
            dose_value = antagonist_meta.get("dose_mg_per_kg")
            species_value = antagonist_meta.get("species")
            regimen_value = antagonist_meta.get("regimen")
            dose_label = None if dose_value is None else f"{float(dose_value):g} mg/kg"
            species_label = None if species_value is None else str(species_value)
            regimen_label = None if regimen_value is None else str(regimen_value)

        fig_antagonist, axes_antagonist = _make_axes(len(tissues))
        for ax, (tissue, tissue_df) in zip(axes_antagonist, tissues):
            time_min = time_minutes_from_hours(tissue_df[TIME_H_COL].to_numpy(dtype=float))
            antagonist_nm = tissue_df[ANTAGONIST_CONCENTRATION_COL].to_numpy(dtype=float)
            antagonist_um = antagonist_nm / 1000.0
            color = _tissue_color(tissue)
            label = _tissue_label(tissue)
            line_label = "XC7"
            if dose_label is not None:
                line_label = f"XC7 {dose_label}"
            if species_label is not None and regimen_label is not None:
                line_label = f"{line_label} ({species_label}, {regimen_label})"

            ax.plot(time_min, antagonist_um, color=color, linewidth=2.0, label=line_label)
            peak_idx = int(np.argmax(antagonist_um))
            ax.annotate(
                _format_peak_label(antagonist_um[peak_idx], "мкМ", time_min[peak_idx], decimals=2),
                xy=(time_min[peak_idx], antagonist_um[peak_idx]),
                xytext=(time_min[peak_idx], antagonist_um[peak_idx] * 0.82 if antagonist_um[peak_idx] > 0 else 0.02),
                fontsize=7.5,
                color=color,
                arrowprops={"arrowstyle": "->", "color": color, "lw": 0.7},
            )
            ax.annotate(
                f"{antagonist_um[-1]:.3f} мкМ",
                xy=(x_max, antagonist_um[-1]),
                ha="right",
                va="bottom",
                fontsize=7.5,
                color=color,
            )
            _style_axis(ax, x_max, "Концентрация XC7 (мкМ)", label)
            ax.legend(fontsize=7.5, loc=LEGEND_UPPER_RIGHT, framealpha=0.8)
        _save_figure(fig_antagonist, antagonist_png)
        resolved_antagonist_png = antagonist_png

    return ScenarioFigureArtifacts(
        out_dir=resolved_out_dir,
        histamine_png=histamine_png,
        receptor_png=receptor_png,
        g_signal_png=g_signal_png,
        antagonist_png=resolved_antagonist_png,
    )
