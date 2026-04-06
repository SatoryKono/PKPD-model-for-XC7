"""
Графики для модели «Горячая пластина».

Источник истины: детерминированные артефакты прогона
(`simulation.csv` + `meta.yaml`).
"""

from __future__ import annotations

from _plot_script_common import ScenarioPlotSpec, run_plot_script

SPEC = ScenarioPlotSpec(
    figure_group=5,
    file_stem="hot_plate",
    model_title="Модель «Горячая пластина»",
    tissue_order=("skin", "spinal_coord", "ganglia"),
)


def main() -> int:
    return run_plot_script(SPEC, description="Визуализация модели «Горячая пластина» из артефактов прогона.")


if __name__ == "__main__":
    raise SystemExit(main())
