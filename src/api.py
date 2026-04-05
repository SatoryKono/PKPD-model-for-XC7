from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

from src.config.loader import load_config as _load_config
from src.config.schemas import ModelConfig
from src.models.receptor_trafficking import receptor_trafficking_rhs, steady_state_ic
from src.pipelines.run_layout import RunTables, build_run_tables
from src.repro.logging import close_run_logger, configure_run_logger
from src.repro.metadata import create_run_metadata, write_metadata
from src.solvers.solve_ivp_wrapper import SolverConfig, solve_ivp_wrapper


@dataclass(frozen=True)
class SimulationResult:
    """In-memory deterministic simulation output without filesystem side effects."""

    cfg: ModelConfig
    run_tables: RunTables


@dataclass(frozen=True)
class SimulationArtifacts:
    run_dir: Path
    run_id: str
    simulation_csv: Path
    used_config_yaml: Path
    marker_points_csv: Path
    summary_csv: Path
    metadata_json: Path


def load_config(path: str | Path) -> ModelConfig:
    """Load and normalize configuration from disk."""

    return _load_config(path, normalize=True)


def _save_used_config(config: ModelConfig, path: Path) -> None:
    payload = config.model_dump(mode="json")
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def run_simulation(cfg: ModelConfig) -> SimulationResult:
    """Run a deterministic receptor-trafficking simulation without file I/O."""

    histamine_nm = cfg.initial_concentration
    y0 = steady_state_ic(histamine_nm)

    result = solve_ivp_wrapper(
        ode_fun=lambda t, y: receptor_trafficking_rhs(t, y, histamine_nm=histamine_nm),
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
            "histamine_nm": histamine_nm,
        }
    )

    return SimulationResult(cfg=cfg, run_tables=build_run_tables(timeseries=frame))


def persist_run(result: SimulationResult, run_dir: str | Path) -> SimulationArtifacts:
    """Persist simulation artifacts (CSV, used config, and metadata) to disk."""

    run_path = Path(run_dir)
    run_path.mkdir(parents=True, exist_ok=True)

    used_config_path = run_path / "config.used.yaml"
    _save_used_config(result.cfg, used_config_path)

    simulation_csv = run_path / "simulation.csv"
    marker_points_csv = run_path / "marker_points.csv"
    summary_csv = run_path / "summary.csv"

    result.run_tables.timeseries.to_csv(simulation_csv, index=False)
    result.run_tables.marker_points.to_csv(marker_points_csv, index=False)
    result.run_tables.summary.to_csv(summary_csv, index=False)

    metadata_payload = create_run_metadata(
        run_dir=run_path,
        deterministic_mode=True,
        config_payload=result.cfg.model_dump(mode="json"),
        artifacts=[simulation_csv, marker_points_csv, summary_csv, used_config_path],
    )
    metadata_json = write_metadata(metadata_payload, run_path / "metadata.json")

    return SimulationArtifacts(
        run_dir=run_path,
        run_id=metadata_payload["run_id"],
        simulation_csv=simulation_csv,
        used_config_yaml=used_config_path,
        marker_points_csv=marker_points_csv,
        summary_csv=summary_csv,
        metadata_json=metadata_json,
    )


def simulate(config: str | Path | ModelConfig, out: str | Path) -> SimulationArtifacts:
    """Run and persist deterministic simulation as a thin orchestration layer."""

    run_dir = Path(out)
    run_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_run_logger(run_dir)
    logger.info("simulation_started")

    try:
        cfg = load_config(config) if isinstance(config, (str, Path)) else config
        result = run_simulation(cfg)
        artifacts = persist_run(result, run_dir)
        logger.info(
            "simulation_completed",
            extra={"run_id": artifacts.run_id},
        )
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
        frame.to_csv(out_path, index=False)
    elif normalized_format == "tsv":
        frame.to_csv(out_path, index=False, sep="\t")
    else:
        frame.to_excel(out_path, index=False)

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
        if not (candidate[col] - baseline[col]).abs().le(1e-9).all():
            return False, f"numeric mismatch in column '{col}'"

    object_cols = [col for col in candidate.columns if col not in numeric_cols]
    for col in object_cols:
        if not candidate[col].astype(str).equals(baseline[col].astype(str)):
            return False, f"value mismatch in column '{col}'"

    return True, "validation passed"
