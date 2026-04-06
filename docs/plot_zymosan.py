"""
Графики для зимозановой модели.

Источник истины: детерминированные артефакты прогона
(`simulation.csv` + `meta.yaml`).
"""

from __future__ import annotations

from _plot_script_common import ScenarioPlotSpec, run_plot_script

SPEC = ScenarioPlotSpec(
    figure_group=7,
    file_stem="zymosan",
    model_title="Зимозановый перитонит",
    tissue_order=("peritoneum", "spinal_coord", "ganglia"),
)


def main() -> int:
    return run_plot_script(SPEC, description="Визуализация зимозановой модели из артефактов прогона.")


if __name__ == "__main__":
    raise SystemExit(main())
