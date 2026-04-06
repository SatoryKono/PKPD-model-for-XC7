"""
Графики для карагениновой модели.

Источник истины: детерминированные артефакты прогона
(`simulation.csv` + `meta.yaml`).
"""

from __future__ import annotations

from _plot_script_common import ScenarioPlotSpec, run_plot_script

SPEC = ScenarioPlotSpec(
    figure_group=4,
    file_stem="carrageenan",
    model_title="Карагениновая модель",
    tissue_order=("muscle", "spinal_coord", "ganglia"),
)


def main() -> int:
    return run_plot_script(SPEC, description="Визуализация карагениновой модели из артефактов прогона.")


if __name__ == "__main__":
    raise SystemExit(main())
