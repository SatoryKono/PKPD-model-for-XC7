from __future__ import annotations

import numpy as np
import pandas as pd

from pkpd_xc7.config.schemas import ModelConfig
from pkpd_xc7.io.layout import (
    ANTAGONIST_CONCENTRATION_COL,
    DRIVER_ID_COL,
    DRIVER_TYPE_COL,
    HISTAMINE_COL,
    R_INT_COL,
    R_SURF_COL,
    TIME_H_COL,
    TISSUE_COL,
    enforce_timeseries_layout,
)
from pkpd_xc7.models.receptor_trafficking import steady_state_ic
from pkpd_xc7.simulation.antagonist_pk import build_antagonist_pk_runtime
from pkpd_xc7.simulation.histamine_driver import resolve_histamine_nm
from pkpd_xc7.simulation.model_mapping import model_config_to_trafficking_core, runtime_assumptions
from pkpd_xc7.simulation.postprocessing import add_g_signal_columns
from pkpd_xc7.solvers.ivp import solve_trafficking_ivp
from pkpd_xc7.solvers.solve_ivp_wrapper import SolverConfig, solver_metadata_snapshot

RECEPTOR_INVARIANT_EPS = 1e-6


def _validate_tissue_receptor_invariants(
    time_grid_h: np.ndarray,
    y_sol: np.ndarray,
    tissue: str,
    *,
    eps: float = RECEPTOR_INVARIANT_EPS,
) -> None:
    """Fail fast when a tissue trajectory leaves the admissible receptor state space."""
    r_surf = np.asarray(y_sol[0], dtype=float)
    r_int = np.asarray(y_sol[1], dtype=float)
    total = r_surf + r_int
    upper_bound = np.nextafter(1.0 + eps, np.inf)
    checks = (
        ("R_surf", r_surf < 0.0),
        ("R_int", r_int < 0.0),
        ("R_surf + R_int", total > upper_bound),
    )

    violations: list[tuple[int, int, str]] = []
    for rank, (name, mask) in enumerate(checks):
        indices = np.flatnonzero(mask)
        if indices.size:
            violations.append((int(indices[0]), rank, name))

    if not violations:
        return

    idx, _, name = min(violations, key=lambda item: (item[0], item[1]))
    time_h = float(time_grid_h[idx])
    if name == "R_surf":
        raise ValueError(
            f"Tissue run invariant violation for tissue '{tissue}' at time_h={time_h:.12g}: "
            f"R_surf={r_surf[idx]:.12g} must be >= 0."
        )
    if name == "R_int":
        raise ValueError(
            f"Tissue run invariant violation for tissue '{tissue}' at time_h={time_h:.12g}: "
            f"R_int={r_int[idx]:.12g} must be >= 0."
        )
    raise ValueError(
        f"Tissue run invariant violation for tissue '{tissue}' at time_h={time_h:.12g}: "
        f"R_surf + R_int={total[idx]:.12g} must be <= 1 + eps ({1.0 + eps:.12g})."
    )


def run_experiment(config: ModelConfig) -> pd.DataFrame:
    """
    Детерминированный расчёт системы ОДУ и траффикинга рецепторов (Фаза 3).
    """
    frames: list[pd.DataFrame] = []

    driver_id: str
    if config.driver.driver_type == "scenario":
        driver_id = config.driver.scenario_id
    else:
        driver_id = "pk_model"

    time_grid = np.asarray(config.time_grid_h, dtype=float)
    antagonist_pk_runtime = build_antagonist_pk_runtime(config)
    
    # Инстанцируем унифицированный конфиг решателя с параметрами Phase 3
    solver_config = SolverConfig(
        t_eval=time_grid.tolist(),
        method="LSODA",
        rtol=1e-3,
        atol=1e-6,
    )
    # Забираем снапшот метаданных на этапе запуска
    solver_meta = solver_metadata_snapshot(solver_config)

    for tissue in config.tissues:
        params = model_config_to_trafficking_core(config, tissue=tissue)
        h_grid = np.array([resolve_histamine_nm(float(t), config, tissue) for t in time_grid])
        if antagonist_pk_runtime is None:
            antagonist_grid = np.full_like(time_grid, np.nan, dtype=float)
        else:
            antagonist_grid = np.array(
                [antagonist_pk_runtime.concentration_nm(tissue, float(t_h)) for t_h in time_grid],
                dtype=float,
            )
        y0 = steady_state_ic(float(h_grid[0]), params)

        y_sol = solve_trafficking_ivp(time_grid, h_grid, y0, params, solver_config=solver_config, tissue=tissue)
        _validate_tissue_receptor_invariants(time_grid, y_sol, tissue)

        tissue_frame = pd.DataFrame(
            {
                TIME_H_COL: time_grid.astype(float),
                TISSUE_COL: tissue,
                HISTAMINE_COL: h_grid.astype(float),
                R_SURF_COL: y_sol[0].astype(float),
                R_INT_COL: y_sol[1].astype(float),
                ANTAGONIST_CONCENTRATION_COL: antagonist_grid.astype(float),
            }
        )
        frames.append(add_g_signal_columns(tissue_frame, params))

    df = pd.concat(frames, ignore_index=True)
    df[DRIVER_TYPE_COL] = config.driver.driver_type
    df[DRIVER_ID_COL] = driver_id
    df = enforce_timeseries_layout(df)
    df.attrs["solver_metadata"] = solver_meta
    assumptions = runtime_assumptions(config)
    if antagonist_pk_runtime is not None:
        assumptions = list(assumptions)
        runtime_assumption = antagonist_pk_runtime.runtime_assumption()
        if runtime_assumption not in assumptions:
            assumptions.append(runtime_assumption)
        df.attrs["antagonist_pk"] = antagonist_pk_runtime.metadata()
    df.attrs["runtime_assumptions"] = assumptions
    return df