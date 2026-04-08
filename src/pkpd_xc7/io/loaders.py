from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from pkpd_xc7.io.layout import enforce_timeseries_layout


def _suggest_sibling_run_dirs(target: Path) -> list[Path]:
    """If ``target`` is not the leaf run directory, suggest siblings that have CSV+meta."""
    parent = target.parent
    prefix = target.name
    if not parent.is_dir():
        return []
    out: list[Path] = []
    for candidate in sorted(parent.iterdir()):
        if not candidate.is_dir() or candidate.name == prefix:
            continue
        if not candidate.name.startswith(prefix):
            continue
        if (candidate / "simulation.csv").is_file() and (candidate / "meta.yaml").is_file():
            out.append(candidate)
    return out


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
        hint = ""
        if not resolved_run_dir.is_dir():
            hint = " Run directory is missing or is not a directory."
        suggestions = _suggest_sibling_run_dirs(resolved_run_dir)
        if suggestions:
            shown = ", ".join(str(p.as_posix()) for p in suggestions[:8])
            suffix = " …" if len(suggestions) > 8 else ""
            hint += f" Candidate run directories (have simulation.csv + meta.yaml): {shown}{suffix}"
        raise FileNotFoundError(
            f"Missing required simulation artifacts in {resolved_run_dir}: {missing_str}.{hint}"
        )

    timeseries = load_simulation_timeseries(csv_path)
    meta = load_simulation_meta(meta_path)
    has_resolved_params = "trafficking_params_by_tissue" in meta or "trafficking_params" in meta
    if require_trafficking_params and not has_resolved_params:
        raise KeyError(
            f"Missing 'trafficking_params_by_tissue' or legacy 'trafficking_params' in simulation meta: {meta_path}"
        )
    return SimulationRun(run_dir=resolved_run_dir, timeseries=timeseries, meta=meta)
