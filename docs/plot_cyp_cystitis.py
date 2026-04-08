"""
Графики для модели циклофосфамид-индуцированного цистита (крысы).

Источник истины: детерминированные артефакты прогона
(`simulation.csv` + `meta.yaml`).
"""

from __future__ import annotations

from _plot_script_common import ScenarioPlotSpec, run_plot_script

SPEC = ScenarioPlotSpec(
    figure_group=9,
    file_stem="cyp_cystitis",
    model_title="Модель цистита, индуцированного циклофосфамидом",
    tissue_order=("bladder", "spinal_coord", "ganglia", "brain"),
)


def main() -> int:
    return run_plot_script(SPEC, description="Визуализация модели CYP-цистита из артефактов прогона.")


if __name__ == "__main__":
    raise SystemExit(main())
