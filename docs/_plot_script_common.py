from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

import matplotlib

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DEFAULT_OUT_DIR = ROOT / "docs" / "figures"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

matplotlib.use("Agg")

from pkpd_xc7.io import load_simulation_run
from pkpd_xc7.viz import ScenarioPlotSpec, plot_scenario_run_figures


def run_plot_script(spec: ScenarioPlotSpec, *, description: str) -> int:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help="Каталог с артефактами симуляции (simulation.csv, meta.yaml), обычно runs/<сценарий>__dose_<N>mgkg",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Каталог для сохранения PNG фигур",
    )
    parser.add_argument(
        "--file-stem-suffix",
        type=str,
        default="",
        help="Опциональный суффикс для имен PNG (например, dose_18mgkg).",
    )
    parser.add_argument(
        "--baseline-run-dir",
        type=Path,
        default=None,
        help="Опциональный каталог baseline-прогона (0 mg/kg) для контрольного overlay.",
    )
    parser.add_argument(
        "--intact-reference-run-dir",
        type=Path,
        default=None,
        help="Опциональный каталог прогона сценария intact (0 mg/kg): доп. линия только на панели G-signaling.",
    )
    parser.add_argument(
        "--render-histamine",
        action="store_true",
        help="Сохранить PNG гистамина (по умолчанию из скрипта не строится).",
    )
    parser.add_argument(
        "--render-internalization",
        action="store_true",
        help="Сохранить PNG интернализации (по умолчанию из скрипта не строится).",
    )
    parser.add_argument(
        "--render-g-signal-without-internalization",
        action="store_true",
        help="На G-signaling рисовать кривую «Без интернализации» и заливку (по умолчанию из скрипта не строятся).",
    )
    parser.add_argument(
        "--render-xc7-concentration",
        action="store_true",
        help="Сохранить PNG концентрации XC7 (по умолчанию из скрипта не строится).",
    )
    args = parser.parse_args()

    resolved_spec = spec
    if args.file_stem_suffix:
        resolved_spec = replace(spec, file_stem=f"{spec.file_stem}_{args.file_stem_suffix}")

    run = load_simulation_run(args.run_dir)
    baseline_run = load_simulation_run(args.baseline_run_dir) if args.baseline_run_dir is not None else None
    intact_reference_run = (
        load_simulation_run(args.intact_reference_run_dir)
        if args.intact_reference_run_dir is not None
        else None
    )
    artifacts = plot_scenario_run_figures(
        run,
        resolved_spec,
        out_dir=args.out_dir,
        baseline_run=baseline_run,
        intact_reference_run=intact_reference_run,
        render_histamine_figure=args.render_histamine,
        render_internalization_figure=args.render_internalization,
        plot_g_signal_without_internalization=args.render_g_signal_without_internalization,
        render_antagonist_figure=args.render_xc7_concentration,
    )

    if artifacts.histamine_png is not None:
        print(f"Saved histamine figure: {artifacts.histamine_png}")
    if artifacts.receptor_png is not None:
        print(f"Saved trafficking figure: {artifacts.receptor_png}")
    print(f"Saved G-signaling figure: {artifacts.g_signal_png}")
    if artifacts.antagonist_png is not None:
        print(f"Saved XC7 concentration figure: {artifacts.antagonist_png}")
    return 0
