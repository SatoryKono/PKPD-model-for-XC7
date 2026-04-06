"""
Графики для модели Compound 48/80.

Источник истины: детерминированные артефакты прогона
(`simulation.csv` + `meta.yaml`).
"""

from __future__ import annotations

from _plot_script_common import ScenarioPlotSpec, run_plot_script

SPEC = ScenarioPlotSpec(
    figure_group=2,
    file_stem="compound_48_80",
    model_title="Модель Compound 48/80",
    tissue_order=("skin", "spinal_coord", "ganglia"),
)


def main() -> int:
    return run_plot_script(SPEC, description="Визуализация модели Compound 48/80 из артефактов прогона.")


if __name__ == "__main__":
    raise SystemExit(main())
