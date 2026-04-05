from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from .schemas import ConcentrationUnit, ModelConfig, RateUnit, TimeUnit


class ConfigLoadError(ValueError):
    """Raised when a config cannot be loaded or normalized."""


def _convert_time_to_h(value: float, unit: TimeUnit) -> float:
    if unit == TimeUnit.H:
        return value
    if unit == TimeUnit.MIN:
        return value / 60.0
    if unit == TimeUnit.S:
        return value / 3600.0
    raise ConfigLoadError(f"Unsupported time unit: {unit}")


def _convert_concentration_to_nM(value: float, unit: ConcentrationUnit) -> float:
    if unit == ConcentrationUnit.NM:
        return value
    if unit == ConcentrationUnit.UM:
        return value * 1_000.0
    if unit == ConcentrationUnit.MM:
        return value * 1_000_000.0
    raise ConfigLoadError(f"Unsupported concentration unit: {unit}")


def _convert_rate_to_per_h(value: float, unit: RateUnit) -> float:
    if unit == RateUnit.PER_H:
        return value
    if unit == RateUnit.PER_MIN:
        return value * 60.0
    if unit == RateUnit.PER_S:
        return value * 3600.0
    raise ConfigLoadError(f"Unsupported rate unit: {unit}")


def normalize_units(config: ModelConfig) -> ModelConfig:
    """
    Normalize units to canonical units required by task:
    - time -> h
    - concentration -> nM
    - rates -> 1/h
    """

    dumped = config.model_dump(mode="python")

    time_unit = config.time_unit
    dumped["time_grid"] = [_convert_time_to_h(value=t, unit=time_unit) for t in config.time_grid]
    dumped["time_unit"] = TimeUnit.H

    conc_unit = config.concentration_unit
    dumped["initial_concentration"] = _convert_concentration_to_nM(
        value=config.initial_concentration,
        unit=conc_unit,
    )
    dumped["concentration_unit"] = ConcentrationUnit.NM

    dumped["kinetics"]["k_abs"] = _convert_rate_to_per_h(
        value=config.kinetics.k_abs,
        unit=config.kinetics.rate_unit,
    )
    dumped["kinetics"]["k_elim"] = _convert_rate_to_per_h(
        value=config.kinetics.k_elim,
        unit=config.kinetics.rate_unit,
    )
    dumped["kinetics"]["rate_unit"] = RateUnit.PER_H

    for plot in dumped["plots"]:
        plot_x_unit = TimeUnit(plot["x_unit"])
        plot["x_unit"] = TimeUnit.H
        plot_y_unit = ConcentrationUnit(plot["y_unit"])
        if plot_y_unit != ConcentrationUnit.NM:
            plot["y_unit"] = ConcentrationUnit.NM
        if plot_x_unit != TimeUnit.H:
            # x_unit is metadata only; values are not stored in PlotSpec.
            plot["x_unit"] = TimeUnit.H

    return ModelConfig.model_validate(dumped)


def _load_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigLoadError(f"Config file not found: {path}")

    suffix = path.suffix.lower()
    raw = path.read_text(encoding="utf-8")

    if suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(raw)
    elif suffix == ".json":
        data = json.loads(raw)
    else:
        raise ConfigLoadError("Unsupported config format. Use .yaml/.yml or .json")

    if not isinstance(data, dict):
        raise ConfigLoadError("Top-level config payload must be a mapping/object")

    return data


def load_config(path: str | Path, *, normalize: bool = True) -> ModelConfig:
    """Load and validate config from YAML or JSON."""

    payload = _load_dict(Path(path))
    config = ModelConfig.model_validate(payload)
    return normalize_units(config) if normalize else config
