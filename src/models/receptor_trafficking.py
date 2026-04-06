from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np

from src.config.schemas import HistaminePhaseOverrides, ModelConfig, RateUnit, TraffickingConfig
from src.histamine_profiles import (
    HistamineProfileParams,
    PulsePhase,
    Tissue,
    get_histamine_profile,
    resolve_formalin_params_from_model_config,
)


@dataclass(frozen=True)
class TraffickingParams:
    """H3R trafficking parameters in canonical units (nM, 1/h)."""

    k_int_max: float = 2.5
    k_rec: float = 0.50
    k_synth: float = 0.05
    ec50_barr_nm: float = 1500.0
    hill_n: float = 1.0
    ec50_g_nm: float = 50.0


DEFAULT_PARAMS = TraffickingParams()


def _trafficking_params_from_config(cfg_block: TraffickingConfig | None) -> TraffickingParams:
    if cfg_block is None:
        return DEFAULT_PARAMS
    return TraffickingParams(
        k_int_max=float(cfg_block.k_int_max),
        k_rec=float(cfg_block.k_rec),
        k_synth=float(cfg_block.k_synth),
        ec50_barr_nm=float(cfg_block.ec50_barr_nm),
        hill_n=float(cfg_block.hill_n),
        ec50_g_nm=float(cfg_block.ec50_g_nm),
    )


@dataclass(frozen=True)
class TissueModelParams:
    """Collapsed tissue parameters used by the single-compartment input profile."""

    effective_volume_l: float
    partition_weighted_volume_l: float


@dataclass(frozen=True)
class ModelParams:
    """Runtime parameters that directly affect receptor RHS/input profile."""

    trafficking: TraffickingParams
    histamine_input_fn: Callable[[float], float]
    histamine_source: str
    histamine_profile: HistamineProfileParams | None
    initial_concentration_nm: float | None
    k_abs_per_h: float | None
    k_elim_per_h: float | None
    tissues: TissueModelParams
    clip_state_explicit: bool


def _merge_histamine_phase(
    phase: PulsePhase,
    overrides: HistaminePhaseOverrides | None,
) -> PulsePhase:
    if overrides is None:
        return phase
    return PulsePhase(
        amplitude_nm=float(overrides.amplitude_nm)
        if overrides.amplitude_nm is not None
        else phase.amplitude_nm,
        t0_h=float(overrides.t0_h) if overrides.t0_h is not None else phase.t0_h,
        tau_rise_h=float(overrides.tau_rise_h)
        if overrides.tau_rise_h is not None
        else phase.tau_rise_h,
        tau_fall_h=float(overrides.tau_fall_h)
        if overrides.tau_fall_h is not None
        else phase.tau_fall_h,
    )


def _resolve_profile_from_config(cfg: ModelConfig) -> tuple[str, HistamineProfileParams] | None:
    if cfg.histamine_profile is not None:
        profile_cfg = cfg.histamine_profile
        if profile_cfg.profile_id.value == "pk_bateman":
            if any(
                value is not None for value in (profile_cfg.h_base_nm, profile_cfg.phase1, profile_cfg.phase2)
            ):
                raise ValueError("histamine_profile.profile_id='pk_bateman' cannot define phase overrides.")
            return None

        _, default_profile = get_histamine_profile(
            profile_cfg.profile_id.value,
            tissue=profile_cfg.tissue.value,
        )
        phase1 = _merge_histamine_phase(default_profile.phase1, profile_cfg.phase1)

        if default_profile.phase2 is None:
            if profile_cfg.phase2 is not None:
                raise ValueError(
                    f"profile '{profile_cfg.profile_id.value}' does not define phase2; override is invalid."
                )
            phase2 = None
        else:
            phase2 = _merge_histamine_phase(default_profile.phase2, profile_cfg.phase2)

        resolved = HistamineProfileParams(
            profile_type=default_profile.profile_type,
            tissue=default_profile.tissue,
            h_base_nm=float(profile_cfg.h_base_nm)
            if profile_cfg.h_base_nm is not None
            else default_profile.h_base_nm,
            phase1=phase1,
            phase2=phase2,
        )
        return (profile_cfg.profile_id.value, resolved)

    if cfg.formalin_profile is not None:
        return (
            "formalin",
            resolve_formalin_params_from_model_config(cfg, tissue=Tissue.SKIN),
        )

    return None


def _bateman_histamine_input_profile(
    t_h: float,
    *,
    initial_concentration_nm: float,
    k_abs_per_h: float,
    k_elim_per_h: float,
    tissues: TissueModelParams,
) -> float:
    if t_h < 0:
        raise ValueError("t_h must be >= 0")

    dose_nmol = initial_concentration_nm * tissues.effective_volume_l
    distribution_volume_l = tissues.partition_weighted_volume_l
    scale = dose_nmol / distribution_volume_l

    delta = k_abs_per_h - k_elim_per_h
    if abs(delta) < 1e-12:
        concentration_nm = scale * k_abs_per_h * t_h * np.exp(-k_elim_per_h * t_h)
    else:
        concentration_nm = (
            scale
            * (k_abs_per_h / delta)
            * (np.exp(-k_elim_per_h * t_h) - np.exp(-k_abs_per_h * t_h))
        )

    return float(max(concentration_nm, 0.0))


def build_model_params(cfg: ModelConfig) -> ModelParams:
    """Build validated model parameters from ``ModelConfig``.

    Contract (fields that affect RHS/input profile):
    - ``histamine_profile``: explicit DOCX-like histamine driver (preferred).
    - legacy path: ``initial_concentration`` + ``kinetics.k_abs`` + ``kinetics.k_elim``.
    - ``tissues[*].volume`` and ``tissues[*].partition_coeff``: collapsed into effective
      distribution volume for the concentration profile.
    - ``scenario_assumptions.clip_state_explicit`` (optional bool): explicit RHS clipping mode.

    Unsupported scenario-assumption keys raise ``ValueError`` to avoid silent ignores.
    """

    if any(tissue.volume_unit.strip().lower() != "l" for tissue in cfg.tissues):
        raise ValueError(
            "Only tissue.volume_unit='L' is supported by the current input-profile model."
        )

    effective_volume_l = float(sum(tissue.volume for tissue in cfg.tissues))
    partition_weighted_volume_l = float(
        sum(tissue.volume * tissue.partition_coeff for tissue in cfg.tissues)
    )
    if effective_volume_l <= 0 or partition_weighted_volume_l <= 0:
        raise ValueError("Tissue-derived volumes must be > 0 for model execution.")

    scenario_assumptions = cfg.scenario_assumptions or {}
    supported_scenario_keys = {"clip_state_explicit"}
    unsupported = sorted(set(scenario_assumptions) - supported_scenario_keys)
    if unsupported:
        raise ValueError(
            "Unsupported scenario_assumptions for receptor model: "
            f"{unsupported}. Supported keys: {sorted(supported_scenario_keys)}"
        )

    clip_state_explicit_raw = scenario_assumptions.get("clip_state_explicit", False)
    if not isinstance(clip_state_explicit_raw, bool):
        raise ValueError("scenario_assumptions.clip_state_explicit must be a boolean.")

    profile_resolution = _resolve_profile_from_config(cfg)
    histamine_source: str
    histamine_profile: HistamineProfileParams | None
    initial_concentration_nm: float | None
    k_abs_per_h: float | None
    k_elim_per_h: float | None

    tissue_params = TissueModelParams(
        effective_volume_l=effective_volume_l,
        partition_weighted_volume_l=partition_weighted_volume_l,
    )

    if profile_resolution is not None:
        histamine_source, histamine_profile = profile_resolution
        profile_fn, _ = get_histamine_profile(
            histamine_source,
            tissue=histamine_profile.tissue.value,
        )
        histamine_input_fn = lambda t_h: float(profile_fn(t_h, histamine_profile))
        initial_concentration_nm = None
        k_abs_per_h = None
        k_elim_per_h = None
    else:
        if cfg.kinetics is None or cfg.initial_concentration is None:
            raise ValueError(
                "Legacy Bateman input requires initial_concentration and kinetics when no histamine_profile is set."
            )
        if cfg.kinetics.rate_unit != RateUnit.PER_H:
            raise ValueError(
                "Model requires kinetics.rate_unit='1/h'. "
                "Use normalized config (load_config(..., normalize=True))."
            )
        histamine_source = "pk_bateman"
        histamine_profile = None
        initial_concentration_nm = float(cfg.initial_concentration)
        k_abs_per_h = float(cfg.kinetics.k_abs)
        k_elim_per_h = float(cfg.kinetics.k_elim)
        histamine_input_fn = lambda t_h: _bateman_histamine_input_profile(
            t_h,
            initial_concentration_nm=initial_concentration_nm,
            k_abs_per_h=k_abs_per_h,
            k_elim_per_h=k_elim_per_h,
            tissues=tissue_params,
        )

    return ModelParams(
        trafficking=_trafficking_params_from_config(cfg.trafficking),
        histamine_input_fn=histamine_input_fn,
        histamine_source=histamine_source,
        histamine_profile=histamine_profile,
        initial_concentration_nm=initial_concentration_nm,
        k_abs_per_h=k_abs_per_h,
        k_elim_per_h=k_elim_per_h,
        tissues=tissue_params,
        clip_state_explicit=clip_state_explicit_raw,
    )


def histamine_input_profile(t_h: float, params: ModelParams) -> float:
    """Return deterministic histamine driver concentration (legacy PK or explicit profile)."""

    if t_h < 0:
        raise ValueError("t_h must be >= 0")
    return float(params.histamine_input_fn(t_h))


def _register_assumption(assumptions: list[str] | None, message: str) -> None:
    if assumptions is None:
        return
    if message not in assumptions:
        assumptions.append(message)


def k_int_eff(histamine_nm: float, params: TraffickingParams = DEFAULT_PARAMS) -> float:
    """Effective internalization rate as β-arrestin-like Hill response."""

    if histamine_nm < 0:
        raise ValueError("histamine_nm must be >= 0")

    numerator = histamine_nm**params.hill_n
    denominator = params.ec50_barr_nm**params.hill_n + numerator
    if denominator <= 0:
        raise ValueError("Invalid parameters: Hill denominator must be positive")
    return params.k_int_max * (numerator / denominator)


def receptor_trafficking_rhs(
    t_h: float,
    y: Sequence[float],
    histamine_nm: float,
    params: TraffickingParams = DEFAULT_PARAMS,
    *,
    clip_state_explicit: bool = False,
    assumptions: list[str] | None = None,
) -> np.ndarray:
    """RHS for (R_surf, R_int) dynamics.

    The optional clipping mode is an explicit scenario assumption and must be
    logged in ``assumptions`` by the caller.
    """

    del t_h  # autonomous system, kept for ODE solver signature compatibility

    if len(y) != 2:
        raise ValueError("State y must contain exactly two values: (R_surf, R_int)")

    r_surf, r_int = float(y[0]), float(y[1])

    if clip_state_explicit:
        _register_assumption(
            assumptions,
            "Scenario assumption: receptor states are clipped to [0, 1] in RHS before derivative evaluation.",
        )
        r_surf = float(np.clip(r_surf, 0.0, 1.0))
        r_int = float(np.clip(r_int, 0.0, 1.0))
    else:
        if not (0.0 <= r_surf <= 1.0 and 0.0 <= r_int <= 1.0):
            raise ValueError("R_surf and R_int must be in [0, 1] unless clip_state_explicit=True")

    k_int = k_int_eff(histamine_nm=histamine_nm, params=params)

    d_r_surf = -k_int * r_surf + params.k_rec * r_int + params.k_synth * (1.0 - r_surf - r_int)
    d_r_int = k_int * r_surf - params.k_rec * r_int

    return np.array([d_r_surf, d_r_int], dtype=float)


def steady_state_ic(
    h_base_nm: float,
    params: TraffickingParams = DEFAULT_PARAMS,
) -> tuple[float, float]:
    """Return stationary initial conditions (R_surf0, R_int0) at baseline histamine."""

    if params.k_rec <= 0:
        raise ValueError("k_rec must be > 0 to compute steady-state IC")

    k_int = k_int_eff(histamine_nm=h_base_nm, params=params)
    denom = k_int + params.k_rec
    if denom <= 0:
        raise ValueError("Invalid parameters: k_int + k_rec must be positive")

    r_surf0 = params.k_rec / denom
    r_int0 = k_int / denom

    if not (0.0 <= r_surf0 <= 1.0 and 0.0 <= r_int0 <= 1.0):
        raise ValueError("steady_state_ic produced values outside [0, 1]")

    if abs((r_surf0 + r_int0) - 1.0) >= 1e-6:
        raise ValueError("steady_state_ic must satisfy |(R_surf + R_int) - 1| < 1e-6")

    return (r_surf0, r_int0)
