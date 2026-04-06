from __future__ import annotations

import argparse
import sys
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
        help="Каталог с артефактами симуляции: simulation.csv и meta.yaml",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Каталог для сохранения PNG фигур",
    )
    args = parser.parse_args()

    run = load_simulation_run(args.run_dir)
    artifacts = plot_scenario_run_figures(run, spec, out_dir=args.out_dir)

    print(f"Saved histamine figure: {artifacts.histamine_png}")
    print(f"Saved trafficking figure: {artifacts.receptor_png}")
    print(f"Saved G-signaling figure: {artifacts.g_signal_png}")
    if artifacts.antagonist_png is not None:
        print(f"Saved XC7 concentration figure: {artifacts.antagonist_png}")
    return 0
