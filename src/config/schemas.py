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


class ParameterResolutionMode(str, Enum):
    """How structural parameters are obtained for a run (no silent fit in default path)."""

    FIXED_PARAMS_ONLY = "fixed_params_only"
    FIT = "fit"


class TraffickingConfig(BaseModel):
    """H3R trafficking parameters (canonical units: nM, 1/h). Defaults match code constants."""

    model_config = ConfigDict(extra="forbid")

    k_int_max: float = Field(default=2.5, gt=0)
    k_rec: float = Field(default=0.5, gt=0)
    k_synth: float = Field(default=0.05, ge=0)
    ec50_barr_nm: float = Field(default=1500.0, gt=0)
    hill_n: float = Field(default=1.0, gt=0)
    ec50_g_nm: float = Field(default=50.0, gt=0)


class PlotProxyConfig(BaseModel):
    """Optional plotting proxies separate from ODE state (G_signal uses EC50 in nM)."""

    model_config = ConfigDict(extra="forbid")

    g_signal_ec50_nm: float | None = Field(
        default=None,
        description="If set, overrides trafficking.ec50_g_nm for G_signal visualization only.",
    )

    @model_validator(mode="after")
    def _g_signal_positive_when_set(self) -> "PlotProxyConfig":
        if self.g_signal_ec50_nm is not None and self.g_signal_ec50_nm <= 0:
            raise ValueError("plot_proxy.g_signal_ec50_nm must be > 0 when set")
        return self


class FormalinPhaseOverrides(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amplitude_nm: float | None = Field(default=None, ge=0)
    t0_h: float | None = Field(default=None, ge=0)
    tau_rise_h: float | None = Field(default=None, gt=0)
    tau_fall_h: float | None = Field(default=None, gt=0)


class FormalinProfileOverrides(BaseModel):
    model_config = ConfigDict(extra="forbid")

    h_base_nm: float | None = Field(default=None, ge=0)
    phase1: FormalinPhaseOverrides | None = None
    phase2: FormalinPhaseOverrides | None = None


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

    parameter_resolution: ParameterResolutionMode = Field(
        default=ParameterResolutionMode.FIXED_PARAMS_ONLY,
        description="fixed_params_only: deterministic parameters from defaults/overrides; fit is legacy-only.",
    )
    trafficking: TraffickingConfig | None = None
    plot_proxy: PlotProxyConfig | None = None
    formalin_profile: FormalinProfileOverrides | None = Field(
        default=None,
        description="Whitelist overrides for default_formalin_params when model uses formalin histamine profile.",
    )

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


def effective_g_signal_ec50_nm(cfg: ModelConfig, trafficking_ec50_g_nm: float) -> float:
    """EC50 (nM) for G_signal proxy: explicit plot_proxy wins, else trafficking EC50_G."""

    if cfg.plot_proxy is not None and cfg.plot_proxy.g_signal_ec50_nm is not None:
        return float(cfg.plot_proxy.g_signal_ec50_nm)
    return float(trafficking_ec50_g_nm)
