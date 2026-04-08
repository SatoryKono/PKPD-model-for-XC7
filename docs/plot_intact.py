"""
Графики для интактной модели.

Источник истины: детерминированные артефакты прогона
(`simulation.csv` + `meta.yaml`).
"""

from __future__ import annotations

from _plot_script_common import ScenarioPlotSpec, run_plot_script

SPEC = ScenarioPlotSpec(
    figure_group=8,
    file_stem="intact",
    model_title="Интактная модель",
    tissue_order=("skin", "spinal_coord", "ganglia"),
)


def main() -> int:
    return run_plot_script(SPEC, description="Визуализация интактной модели из артефактов прогона.")


if __name__ == "__main__":
    raise SystemExit(main())
