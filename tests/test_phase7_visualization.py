from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import pytest

from pkpd_xc7.config.schemas import ModelConfig
from pkpd_xc7.io import export_simulation_run, load_simulation_run
from pkpd_xc7.io.layout import enforce_timeseries_layout
from pkpd_xc7.simulation.model_mapping import model_config_to_trafficking_core
from pkpd_xc7.simulation.postprocessing import add_g_signal_columns
from pkpd_xc7.viz import ScenarioPlotSpec, plot_scenario_run_figures, time_minutes_from_hours
from pkpd_xc7.viz.panels import _format_peak_label, _g_signal_plot_series
from pkpd_xc7.viz.time_axis import apply_time_axis, time_axis_tick_labels, time_axis_tick_positions

matplotlib.use("Agg")


def _build_config() -> ModelConfig:
    return ModelConfig.model_validate(
        {
            "model_id": "phase7_viz",
            "compound": "xc7",
            "traceability": {"source_in_report": "figures"},
            "assumptions": ["phase 7 plotting contract"],
            "driver": {"driver_type": "scenario", "scenario_id": "formalin"},
            "tissues": ["skin", "spinal_coord"],
            "time_grid_h": [0.0, 0.5, 1.0],
            "trafficking": {
                "ec50_g_nm": 50.0,
                "ec50_barr_nm": 1500.0,
                "hill_n": 1.0,
                "constitutive_activity": 0.1,
            },
            "tissue_overrides": {
                "spinal_coord": {
                    "trafficking": {
                        "ec50_g_nm": 20.0,
                        "ec50_barr_nm": 500.0,
                        "hill_n": 1.3,
                        "constitutive_activity": 0.2,
                    }
                }
            },
        }
    )


def _build_timeseries() -> pd.DataFrame:
    base = pd.DataFrame(
        [
            {"time_h": 0.0, "tissue": "skin", "histamine_nm": 50.0, "R_surf": 1.0, "R_int": 0.0, "antagonist_concentration_nm": 900.0},
            {"time_h": 0.5, "tissue": "skin", "histamine_nm": 250.0, "R_surf": 0.85, "R_int": 0.15, "antagonist_concentration_nm": 780.0},
            {"time_h": 1.0, "tissue": "skin", "histamine_nm": 80.0, "R_surf": 0.90, "R_int": 0.10, "antagonist_concentration_nm": 620.0},
            {"time_h": 0.0, "tissue": "spinal_coord", "histamine_nm": 5.0, "R_surf": 1.0, "R_int": 0.0, "antagonist_concentration_nm": 350.0},
            {"time_h": 0.5, "tissue": "spinal_coord", "histamine_nm": 18.0, "R_surf": 0.95, "R_int": 0.05, "antagonist_concentration_nm": 310.0},
            {"time_h": 1.0, "tissue": "spinal_coord", "histamine_nm": 8.0, "R_surf": 0.97, "R_int": 0.03, "antagonist_concentration_nm": 240.0},
        ]
    )
    cfg = _build_config()
    frames: list[pd.DataFrame] = []
    for tissue in ("skin", "spinal_coord"):
        tissue_df = base.loc[base["tissue"] == tissue].reset_index(drop=True)
        params = model_config_to_trafficking_core(cfg, tissue=tissue)
        enriched = add_g_signal_columns(tissue_df, params)
        enriched["driver_type"] = "scenario"
        enriched["driver_id"] = "formalin"
        frames.append(enriched)
    return enforce_timeseries_layout(pd.concat(frames, ignore_index=True))


def _export_run_dir(tmp_path: Path) -> Path:
    df = _build_timeseries()
    df.attrs["solver_metadata"] = {"solver_method": "LSODA"}
    df.attrs["runtime_assumptions"] = ["phase 7 plotting contract"]
    df.attrs["antagonist_pk"] = {
        "enabled": True,
        "species": "rat",
        "regimen": "single",
        "dose_mg_per_kg": 90.0,
        "tissue_map": {"skin": "skin", "spinal_coord": "spinal cord"},
    }
    export_simulation_run(df, _build_config(), tmp_path / "run")
    return tmp_path / "run"


def test_time_minutes_from_hours_supports_scalar_array_and_series() -> None:
    assert time_minutes_from_hours(1.5) == pytest.approx(90.0)

    array_result = time_minutes_from_hours(np.array([0.0, 0.5, 1.0]))
    assert np.allclose(array_result, np.array([0.0, 30.0, 60.0]))

    series = pd.Series([0.0, 0.25, 1.0], name="time_h")
    series_result = time_minutes_from_hours(series)
    assert series_result.name == "time_h"
    assert series_result.tolist() == [0.0, 15.0, 60.0]


def test_time_axis_ticks_use_15_minute_divisions_and_canonical_labels() -> None:
    tick_positions = time_axis_tick_positions(24.0 * 60.0)
    assert np.allclose(tick_positions[:6], np.array([0.0, 15.0, 30.0, 45.0, 60.0, 75.0]))
    assert tick_positions[-1] == pytest.approx(1440.0)

    labels_by_tick = dict(zip(tick_positions.astype(int).tolist(), time_axis_tick_labels(tick_positions), strict=True))
    assert labels_by_tick[0] == ""
    assert labels_by_tick[15] == ""
    assert labels_by_tick[30] == "30"
    assert labels_by_tick[45] == ""
    assert labels_by_tick[60] == "60"
    assert labels_by_tick[120] == "120"
    assert labels_by_tick[240] == "240"
    assert labels_by_tick[360] == "360"
    assert labels_by_tick[480] == "480"
    assert labels_by_tick[720] == "720"
    assert labels_by_tick[1440] == "1440"


def test_apply_time_axis_uses_major_ticks_only_for_labeled_divisions() -> None:
    fig, ax = matplotlib.pyplot.subplots()
    try:
        apply_time_axis(ax, 120.0)
        assert np.allclose(ax.get_xticks(minor=False), np.array([30.0, 60.0, 120.0]))
        assert np.allclose(ax.get_xticks(minor=True), np.array([0.0, 15.0, 45.0, 75.0, 90.0, 105.0]))
    finally:
        matplotlib.pyplot.close(fig)


def test_peak_label_format_is_single_line() -> None:
    assert _format_peak_label(0.91, "мкМ", 5.0, decimals=2) == "0.91 мкМ (5мин)"
    assert _format_peak_label(12.3, "%", 30.0, decimals=1) == "12.3% (30мин)"


def test_g_signal_plot_series_uses_total_and_constitutive_columns() -> None:
    timeseries = _build_timeseries()
    tissue_df = timeseries.loc[timeseries["tissue"] == "spinal_coord"].reset_index(drop=True)

    g_with_pct, g_without_pct, g_constitutive_pct = _g_signal_plot_series(
        tissue_df,
        ec50_g_nm=20.0,
        hill_n=1.3,
        constitutive_activity=0.2,
    )

    assert np.allclose(g_with_pct, tissue_df["G_signal_pct"].to_numpy(dtype=float))
    assert np.allclose(
        g_constitutive_pct,
        tissue_df["G_signal_constitutive_pct"].to_numpy(dtype=float),
    )
    assert np.all(g_without_pct >= g_with_pct)
    assert np.all(g_with_pct >= g_constitutive_pct)


def test_load_simulation_run_reads_csv_and_meta(tmp_path: Path) -> None:
    run_dir = _export_run_dir(tmp_path)

    run = load_simulation_run(run_dir)

    assert run.run_dir == run_dir
    assert run.timeseries.columns.tolist()[0] == "time_h"
    assert run.meta["trafficking_params_by_tissue"]["skin"]["ec50_g_nm"] == pytest.approx(50.0)
    assert run.meta["trafficking_params_by_tissue"]["spinal_coord"]["ec50_g_nm"] == pytest.approx(20.0)


def test_load_simulation_run_requires_trafficking_params_by_default(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    _build_timeseries().to_csv(run_dir / "simulation.csv", index=False)
    (run_dir / "meta.yaml").write_text("driver_type: scenario\n", encoding="utf-8")

    with pytest.raises(KeyError, match="trafficking_params_by_tissue"):
        load_simulation_run(run_dir)


def test_load_simulation_run_accepts_legacy_single_trafficking_mapping(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    _build_timeseries().to_csv(run_dir / "simulation.csv", index=False)
    (run_dir / "meta.yaml").write_text("trafficking_params:\n  ec50_g_nm: 50.0\n", encoding="utf-8")

    run = load_simulation_run(run_dir)
    assert run.meta["trafficking_params"]["ec50_g_nm"] == pytest.approx(50.0)


def test_plot_scenario_run_figures_writes_four_pngs_when_antagonist_is_present(tmp_path: Path) -> None:
    run_dir = _export_run_dir(tmp_path)
    run = load_simulation_run(run_dir)

    artifacts = plot_scenario_run_figures(
        run,
        ScenarioPlotSpec(
            figure_group=1,
            file_stem="formalin",
            model_title="Формалиновая модель",
            tissue_order=("skin", "spinal_coord"),
        ),
        out_dir=tmp_path / "figures",
    )

    assert artifacts.histamine_png.exists()
    assert artifacts.receptor_png.exists()
    assert artifacts.g_signal_png.exists()
    assert artifacts.antagonist_png is not None
    assert artifacts.antagonist_png.exists()
    assert artifacts.histamine_png.stat().st_size > 0
    assert artifacts.receptor_png.stat().st_size > 0
    assert artifacts.g_signal_png.stat().st_size > 0
    assert artifacts.antagonist_png.stat().st_size > 0


def test_plot_formalin_script_smoke(tmp_path: Path) -> None:
    run_dir = _export_run_dir(tmp_path)
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = tmp_path / "script-figures"

    subprocess.run(
        [
            sys.executable,
            str(repo_root / "docs" / "plot_formalin.py"),
            "--run-dir",
            str(run_dir),
            "--out-dir",
            str(out_dir),
        ],
        check=True,
        cwd=repo_root,
    )

    assert (out_dir / "fig1_1_formalin_histamine.png").exists()
    assert (out_dir / "fig1_2_formalin_internalization.png").exists()
    assert (out_dir / "fig1_3_formalin_gsignaling.png").exists()
    assert (out_dir / "fig1_4_formalin_xc7_concentration.png").exists()
