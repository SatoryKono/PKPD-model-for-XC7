from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LossMode(str, Enum):
    MSE = "mse"
    MAE = "mae"
    HUBER = "huber"
    NLL = "nll"


class TimeUnit(str, Enum):
    H = "h"
    MIN = "min"
    S = "s"


class ConcentrationUnit(str, Enum):
    NM = "nM"
    UM = "uM"
    MM = "mM"


class RateUnit(str, Enum):
    PER_H = "1/h"
    PER_MIN = "1/min"
    PER_S = "1/s"


class PlotType(str, Enum):
    LINE = "line"
    SCATTER = "scatter"
    LOG_LINE = "log_line"


class Traceability(BaseModel):
    """Source-traceability payload for auditability in generated reports."""

    source_in_report: str = Field(min_length=3)
    source_reference: str | None = None
    source_version: str | None = None


class TissueConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    volume: float = Field(gt=0, description="Volume value for this tissue compartment")
    volume_unit: str = Field(min_length=1)
    partition_coeff: float = Field(gt=0)


class KineticsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    k_abs: float = Field(gt=0, description="Absorption rate")
    k_elim: float = Field(gt=0, description="Elimination rate")
    rate_unit: RateUnit


class PlotSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    plot_type: PlotType
    x: str = Field(min_length=1)
    y: str = Field(min_length=1)
    x_unit: TimeUnit
    y_unit: ConcentrationUnit


class ModelConfig(BaseModel):
    """Top-level model configuration schema with strict validation."""

    model_config = ConfigDict(extra="forbid")

    model_id: str = Field(min_length=1)
    compound: str = Field(min_length=1)

    # REQUIRED by task:
    loss_mode: LossMode
    assumptions: list[str] = Field(min_length=1)
    traceability: Traceability

    time_grid: list[float] = Field(min_length=2, description="Monotonic non-negative time points")
    time_unit: TimeUnit

    initial_concentration: float = Field(gt=0)
    concentration_unit: ConcentrationUnit

    kinetics: KineticsConfig
    tissues: list[TissueConfig] = Field(min_length=1)
    plots: list[PlotSpec] = Field(default_factory=list)

    scenario_assumptions: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Optional extra assumptions that extend base schema. "
            "Use only when values are explicitly marked as scenario assumptions."
        ),
    )

    @model_validator(mode="after")
    def validate_constraints(self) -> "ModelConfig":
        if self.traceability.source_in_report.strip() == "":
            raise ValueError("traceability.source_in_report is required and cannot be empty")

        if sorted(self.time_grid) != self.time_grid:
            raise ValueError("time_grid must be monotonically non-decreasing")

        if any(t < 0 for t in self.time_grid):
            raise ValueError("time_grid cannot contain negative values")

        if any(not assumption.strip() for assumption in self.assumptions):
            raise ValueError("assumptions cannot include empty strings")

        return self
