from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from src.config.loader import load_config as _load_config
from src.config.loader import normalize_units
from src.config.schemas import ModelConfig, ParameterResolutionMode
from src.models.receptor_trafficking import (
    build_model_params,
    histamine_input_profile,
    receptor_trafficking_rhs,
    steady_state_ic,
)
from src.pipelines.run_layout import build_run_tables
from src.repro.logging import close_run_logger, configure_run_logger
from src.repro.metadata import create_run_metadata, write_metadata
from src.solvers.solve_ivp_wrapper import SolverConfig, solve_ivp_wrapper
from src.utils.atomic_io import dataframe_to_csv_atomic, write_text_atomic


@dataclass(frozen=True)
class SimulationArtifacts:
    run_dir: Path
    simulation_csv: Path
    used_config_yaml: Path
    marker_points_csv: Path
    summary_csv: Path
    metadata_json: Path


@dataclass(frozen=True)
class SimulationResult:
    config: ModelConfig
    timeseries: pd.DataFrame
    marker_points: pd.DataFrame
    summary: pd.DataFrame


def load_config(path: str | Path) -> ModelConfig:
    """Load and normalize configuration from disk."""

    return _load_config(path, normalize=True)


def ensure_canonical_config(cfg: ModelConfig) -> ModelConfig:
    """Return config normalized to canonical units (h, nM, 1/h)."""

    return normalize_units(cfg)


def _infer_parameter_source(cfg: ModelConfig) -> str:
    if cfg.formalin_profile is not None or cfg.trafficking is not None:
        return "overrides"
    if cfg.plot_proxy is not None and cfg.plot_proxy.g_signal_ec50_nm is not None:
        return "overrides"
    return "defaults"


def _optimization_applied_from_config(cfg: ModelConfig) -> bool:
    return cfg.parameter_resolution == ParameterResolutionMode.FIT


def _save_used_config(config: ModelConfig, path: Path) -> None:
    payload = config.model_dump(mode="json")
    write_text_atomic(path, yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _build_summary(frame: pd.DataFrame, cfg: ModelConfig) -> pd.DataFrame:
    auc = float(np.trapezoid(frame["histamine_nm"].to_numpy(), frame["time_h"].to_numpy()))
    return pd.DataFrame(
        [
            {"metric": "rows", "value": float(len(frame))},
            {"metric": "R_surf_max", "value": float(frame["R_surf"].max())},
            {"metric": "R_int_max", "value": float(frame["R_int"].max())},
            {"metric": "histamine_auc_nm_h", "value": auc},
            {"metric": "k_abs_per_h_used", "value": float(cfg.kinetics.k_abs)},
            {"metric": "k_elim_per_h_used", "value": float(cfg.kinetics.k_elim)},
            {
                "metric": "tissue_partition_weighted_volume_l_used",
                "value": float(sum(t.volume * t.partition_coeff for t in cfg.tissues)),
            },
        ]
    )


def run_simulation(cfg: ModelConfig) -> SimulationResult:
    """Run deterministic simulation without filesystem side effects."""

    model_params = build_model_params(cfg)
    baseline_histamine_nm = histamine_input_profile(0.0, model_params)
    y0 = steady_state_ic(baseline_histamine_nm, params=model_params.trafficking)
    assumptions_log = list(cfg.assumptions)

    result = solve_ivp_wrapper(
        ode_fun=lambda t, y: receptor_trafficking_rhs(
            t,
            y,
            histamine_nm=histamine_input_profile(t, model_params),
            params=model_params.trafficking,
            clip_state_explicit=model_params.clip_state_explicit,
            assumptions=assumptions_log,
        ),
        t_span=(cfg.time_grid[0], cfg.time_grid[-1]),
        y0=y0,
        config=SolverConfig(t_eval=cfg.time_grid),
    )

    if not result.success:
        raise RuntimeError(f"Simulation failed: {result.message}")

    frame = pd.DataFrame(
        {
            "time_h": result.t,
            "R_surf": result.y[0],
            "R_int": result.y[1],
            "histamine_nm": [histamine_input_profile(t, model_params) for t in result.t],
            "k_abs_per_h": model_params.k_abs_per_h,
            "k_elim_per_h": model_params.k_elim_per_h,
            "tissue_partition_weighted_volume_l": model_params.tissues.partition_weighted_volume_l,
        }
    )

    run_tables = build_run_tables(timeseries=frame, summary=_build_summary(frame, cfg))
    return SimulationResult(
        config=cfg,
        timeseries=run_tables.timeseries,
        marker_points=run_tables.marker_points,
        summary=run_tables.summary,
    )


def persist_run(result: SimulationResult, run_dir: str | Path) -> SimulationArtifacts:
    """Persist simulation outputs (CSV/YAML/metadata) to the run directory."""

    out_dir = Path(run_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    used_config_path = out_dir / "config.used.yaml"
    simulation_csv = out_dir / "simulation.csv"
    marker_points_csv = out_dir / "marker_points.csv"
    summary_csv = out_dir / "summary.csv"

    _save_used_config(result.config, used_config_path)
    dataframe_to_csv_atomic(result.timeseries, simulation_csv, index=False)
    dataframe_to_csv_atomic(result.marker_points, marker_points_csv, index=False)
    dataframe_to_csv_atomic(result.summary, summary_csv, index=False)

    metadata_payload = create_run_metadata(
        run_dir=out_dir,
        deterministic_mode=True,
        config_payload=result.config.model_dump(mode="json"),
        artifacts=[simulation_csv, marker_points_csv, summary_csv, used_config_path],
        canonical_units=True,
        canonical_unit_tags={"time": "h", "concentration": "nM", "rate": "1/h"},
        parameter_source=_infer_parameter_source(result.config),
        optimization_applied=_optimization_applied_from_config(result.config),
    )
    metadata_json = write_metadata(metadata_payload, out_dir / "metadata.json")
    meta_sidecar = {
        "schema_version": metadata_payload["schema_version"],
        "config_sha256": metadata_payload["config_sha256"],
        "parameter_source": metadata_payload["parameter_source"],
        "optimization_applied": metadata_payload["optimization_applied"],
        "canonical_units": metadata_payload["canonical_units"],
    }
    write_text_atomic(
        out_dir / "meta.yaml",
        yaml.safe_dump(meta_sidecar, sort_keys=True, allow_unicode=True),
        encoding="utf-8",
    )

    return SimulationArtifacts(
        run_dir=out_dir,
        simulation_csv=simulation_csv,
        used_config_yaml=used_config_path,
        marker_points_csv=marker_points_csv,
        summary_csv=summary_csv,
        metadata_json=metadata_json,
    )


def simulate(config: str | Path | ModelConfig, out: str | Path) -> SimulationArtifacts:
    """Run simulation and persist outputs as orchestration thin layer."""

    cfg = (
        load_config(config)
        if isinstance(config, (str, Path))
        else ensure_canonical_config(config)
    )
    run_dir = Path(out)
    run_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_run_logger(run_dir)
    logger.info("simulation_started")

    try:
        simulation_result = run_simulation(cfg)
        artifacts = persist_run(simulation_result, run_dir)
        logger.info("simulation_completed")
        return artifacts
    except Exception:
        logger.exception("simulation_failed")
        raise
    finally:
        close_run_logger(logger)


def run_batch(configs_dir: str | Path, out_root: str | Path) -> list[SimulationArtifacts]:
    """Run simulations for every YAML/JSON config in a directory."""

    directory = Path(configs_dir)
    if not directory.exists() or not directory.is_dir():
        raise ValueError(f"configs-dir must be an existing directory: {directory}")

    out_root_path = Path(out_root)
    out_root_path.mkdir(parents=True, exist_ok=True)

    configs = sorted(
        [
            p
            for p in directory.iterdir()
            if p.is_file() and p.suffix.lower() in {".yaml", ".yml", ".json"}
        ]
    )
    if not configs:
        raise ValueError(f"No config files found in: {directory}")

    artifacts: list[SimulationArtifacts] = []
    failures: list[str] = []

    for config_path in configs:
        run_dir = out_root_path / config_path.stem
        try:
            artifacts.append(simulate(config_path, run_dir))
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{config_path.name}: {exc}")

    if failures:
        raise RuntimeError("Batch failed for one or more configs: " + "; ".join(failures))

    return artifacts


def export(run_dir: str | Path, fmt: str) -> Path:
    """Export simulation results from CSV into another tabular format."""

    normalized_format = fmt.lower()
    if normalized_format not in {"csv", "tsv", "xlsx"}:
        raise ValueError("format must be one of: csv, tsv, xlsx")

    run_path = Path(run_dir)
    simulation_csv = run_path / "simulation.csv"
    if not simulation_csv.exists():
        raise ValueError(f"simulation.csv not found in run-dir: {run_path}")

    frame = pd.read_csv(simulation_csv)
    out_path = run_path / f"simulation.{normalized_format}"

    if normalized_format == "csv":
        dataframe_to_csv_atomic(frame, out_path, index=False)
    elif normalized_format == "tsv":
        dataframe_to_csv_atomic(frame, out_path, index=False, sep="\t")
    else:
        tmp = out_path.with_suffix(out_path.suffix + ".tmp")
        frame.to_excel(tmp, index=False)
        os.replace(tmp, out_path)

    return out_path


def validate(run_dir: str | Path, reference: str | Path) -> tuple[bool, str]:
    """Validate run output against a reference CSV/TSV/XLSX file."""

    run_path = Path(run_dir)
    simulation_csv = run_path / "simulation.csv"
    if not simulation_csv.exists():
        return False, f"simulation.csv not found in run-dir: {run_path}"

    reference_path = Path(reference)
    if not reference_path.exists():
        return False, f"reference file not found: {reference_path}"

    candidate = pd.read_csv(simulation_csv)
    suffix = reference_path.suffix.lower()

    if suffix == ".csv":
        baseline = pd.read_csv(reference_path)
    elif suffix == ".tsv":
        baseline = pd.read_csv(reference_path, sep="\t")
    elif suffix == ".xlsx":
        baseline = pd.read_excel(reference_path)
    else:
        return False, "reference format must be .csv, .tsv, or .xlsx"

    if list(candidate.columns) != list(baseline.columns):
        return False, "column mismatch between simulation output and reference"

    if len(candidate) != len(baseline):
        return False, "row-count mismatch between simulation output and reference"

    numeric_cols = [
        col for col in candidate.columns if pd.api.types.is_numeric_dtype(candidate[col])
    ]
    for col in numeric_cols:
        if not np.allclose(
            candidate[col].to_numpy(dtype=float),
            baseline[col].to_numpy(dtype=float),
            rtol=1e-9,
            atol=1e-9,
            equal_nan=True,
        ):
            return False, f"numeric mismatch in column '{col}'"

    object_cols = [col for col in candidate.columns if col not in numeric_cols]
    for col in object_cols:
        if not candidate[col].astype(str).equals(baseline[col].astype(str)):
            return False, f"value mismatch in column '{col}'"

    return True, "validation passed"
