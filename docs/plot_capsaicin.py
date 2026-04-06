"""
Графики для капсаициновой модели.

Источник истины: детерминированные артефакты прогона
(`simulation.csv` + `meta.yaml`).
"""

from __future__ import annotations

from _plot_script_common import ScenarioPlotSpec, run_plot_script

SPEC = ScenarioPlotSpec(
    figure_group=3,
    file_stem="capsaicin",
    model_title="Капсаициновая модель",
    tissue_order=("skin", "spinal_coord", "ganglia"),
)


def main() -> int:
    return run_plot_script(SPEC, description="Визуализация капсаициновой модели из артефактов прогона.")


if __name__ == "__main__":
    raise SystemExit(main())
