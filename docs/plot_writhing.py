"""
Графики для модели уксусных корчей.

Источник истины: детерминированные артефакты прогона
(`simulation.csv` + `meta.yaml`).
"""

from __future__ import annotations

from _plot_script_common import ScenarioPlotSpec, run_plot_script

SPEC = ScenarioPlotSpec(
    figure_group=6,
    file_stem="acetic_writhing",
    model_title="Модель уксусных корчей",
    tissue_order=("peritoneum", "spinal_coord", "ganglia"),
)


def main() -> int:
    return run_plot_script(SPEC, description="Визуализация модели уксусных корчей из артефактов прогона.")


if __name__ == "__main__":
    raise SystemExit(main())
