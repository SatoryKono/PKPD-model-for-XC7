from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from pkpd_xc7.config.schemas import ModelConfig
from pkpd_xc7.io.layout import (
    DRIVER_ID_COL,
    DRIVER_TYPE_COL,
    SIMULATION_SCHEMA_VERSION,
    TIMESERIES_COLUMN_ORDER,
    enforce_timeseries_layout,
)
from pkpd_xc7.simulation.model_mapping import trafficking_params_by_tissue


@dataclass(frozen=True, slots=True)
class SimulationExportArtifacts:
    out_dir: Path
    simulation_csv: Path
    meta_yaml: Path


def atomic_write_csv(df: pd.DataFrame, dest_path: Path | str) -> None:
    """
    Атомарно записывает DataFrame в CSV (temp в каталоге назначения → os.replace).
    """
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(dir=dest_path.parent, suffix=".csv", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            df.to_csv(f, index=False, lineterminator="\n")
        os.replace(temp_path, dest_path)
    except Exception:
        try:
            os.remove(temp_path)
        except OSError:
            pass
        raise


def atomic_write_yaml(payload: dict[str, Any], dest_path: Path | str) -> None:
    """
    Атомарно записывает YAML (temp в каталоге назначения → os.replace).
    """
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(dir=dest_path.parent, suffix=".yaml", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            yaml.safe_dump(payload, f, sort_keys=False, allow_unicode=False)
        os.replace(temp_path, dest_path)
    except Exception:
        try:
            os.remove(temp_path)
        except OSError:
            pass
        raise


def build_simulation_meta(df: pd.DataFrame, config: ModelConfig) -> dict[str, Any]:
    """
    Build deterministic sidecar metadata for exported simulation results.
    """
    layout_df = enforce_timeseries_layout(df)
    layout_df.attrs = dict(df.attrs)
    if layout_df.empty:
        driver_type: str = config.driver.driver_type
        driver_id: str = config.driver.scenario_id if config.driver.driver_type == "scenario" else "pk_model"
    else:
        driver_type = str(layout_df[DRIVER_TYPE_COL].iloc[0])
        driver_id = str(layout_df[DRIVER_ID_COL].iloc[0])

    metadata: dict[str, Any] = {
        "config_sha256": config.config_sha256(),
        "config_schema_version": config.schema_version,
        "simulation_schema_version": SIMULATION_SCHEMA_VERSION,
        "column_order": list(TIMESERIES_COLUMN_ORDER),
        "row_count": int(len(layout_df.index)),
        "driver_type": driver_type,
        "driver_id": driver_id,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    metadata["default_trafficking_params"] = config.trafficking.model_dump()
    metadata["trafficking_params_by_tissue"] = trafficking_params_by_tissue(config)
    solver_metadata = df.attrs.get("solver_metadata")
    if solver_metadata is not None:
        metadata["solver_metadata"] = solver_metadata
    assumptions = df.attrs.get("runtime_assumptions")
    if assumptions is not None:
        metadata["runtime_assumptions"] = assumptions
    antagonist_pk = df.attrs.get("antagonist_pk")
    if antagonist_pk is not None:
        metadata["antagonist_pk"] = antagonist_pk
    return metadata


def export_simulation_run(
    df: pd.DataFrame,
    config: ModelConfig,
    out_dir: Path | str,
) -> SimulationExportArtifacts:
    """
    Export simulation dataframe and deterministic sidecar metadata atomically.
    """
    out_dir = Path(out_dir)
    simulation_df = enforce_timeseries_layout(df)
    simulation_df.attrs = dict(df.attrs)
    artifacts = SimulationExportArtifacts(
        out_dir=out_dir,
        simulation_csv=out_dir / "simulation.csv",
        meta_yaml=out_dir / "meta.yaml",
    )
    atomic_write_csv(simulation_df, artifacts.simulation_csv)
    atomic_write_yaml(build_simulation_meta(simulation_df, config), artifacts.meta_yaml)
    return artifacts