from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from pkpd_xc7.io.layout import enforce_timeseries_layout


@dataclass(frozen=True, slots=True)
class SimulationRun:
    run_dir: Path
    timeseries: pd.DataFrame
    meta: dict[str, Any]


def load_simulation_timeseries(path: Path | str) -> pd.DataFrame:
    """Load a simulation CSV and validate the canonical export layout."""
    csv_path = Path(path)
    df = pd.read_csv(csv_path)
    return enforce_timeseries_layout(df)


def load_simulation_meta(path: Path | str) -> dict[str, Any]:
    """Load meta.yaml and ensure it is a mapping."""
    meta_path = Path(path)
    with meta_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Simulation meta must be a mapping: {meta_path}")
    return payload


def load_simulation_run(run_dir: Path | str, *, require_trafficking_params: bool = True) -> SimulationRun:
    """Load deterministic simulation artifacts from a run directory."""
    resolved_run_dir = Path(run_dir)
    csv_path = resolved_run_dir / "simulation.csv"
    meta_path = resolved_run_dir / "meta.yaml"

    missing = [path.name for path in (csv_path, meta_path) if not path.exists()]
    if missing:
        missing_str = ", ".join(missing)
        raise FileNotFoundError(
            f"Missing required simulation artifacts in {resolved_run_dir}: {missing_str}"
        )

    timeseries = load_simulation_timeseries(csv_path)
    meta = load_simulation_meta(meta_path)
    has_resolved_params = "trafficking_params_by_tissue" in meta or "trafficking_params" in meta
    if require_trafficking_params and not has_resolved_params:
        raise KeyError(
            f"Missing 'trafficking_params_by_tissue' or legacy 'trafficking_params' in simulation meta: {meta_path}"
        )
    return SimulationRun(run_dir=resolved_run_dir, timeseries=timeseries, meta=meta)
