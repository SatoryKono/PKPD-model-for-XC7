from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
from typing import Any, Callable, Mapping

import numpy as np


class ProfileType(str, Enum):
    MONO = "mono"
    BI = "bi"
    PULSE = "pulse"


class Tissue(str, Enum):
    SKIN = "skin"
    CNS = "cns"
    GANGLIA = "ganglia"
    MUSCLE = "muscle"
    PERITONEUM = "peritoneum"


BASAL_HISTAMINE_NM: dict[Tissue, float] = {
    Tissue.SKIN: 50.0,
    Tissue.CNS: 2.0,
    Tissue.GANGLIA: 5.0,
    Tissue.MUSCLE: 50.0,
    Tissue.PERITONEUM: 50.0,
}


@dataclass(frozen=True)
class PulsePhase:
    amplitude_nm: float
    t0_h: float
    tau_rise_h: float
    tau_fall_h: float


@dataclass(frozen=True)
class HistamineProfileParams:
    profile_type: ProfileType
    tissue: Tissue
    h_base_nm: float
    phase1: PulsePhase
    phase2: PulsePhase | None = None


# -----------------------
# Vectorized core kinetics
# -----------------------
def _to_numpy_time(t: float | np.ndarray) -> np.ndarray:
    arr = np.asarray(t, dtype=float)
    if arr.ndim > 1:
        raise ValueError("t must be a scalar or 1D numpy.ndarray")
    if np.any(~np.isfinite(arr)):
        raise ValueError("t must contain only finite values")
    if np.any(arr < 0.0):
        raise ValueError("t must be non-negative (hours)")
    return arr


def _validate_phase(phase: PulsePhase) -> None:
    if phase.amplitude_nm < 0:
        raise ValueError("phase amplitude must be >= 0")
    if phase.t0_h < 0:
        raise ValueError("phase t0_h must be >= 0")
    if phase.tau_rise_h <= 0 or phase.tau_fall_h <= 0:
        raise ValueError("tau_rise_h and tau_fall_h must be > 0")
    if phase.tau_fall_h <= phase.tau_rise_h:
        raise ValueError("tau_fall_h must be > tau_rise_h for pulse-like kinetics")


def _unit_peak_factor(tau_rise_h: float, tau_fall_h: float) -> float:
    t_peak = np.log(tau_fall_h / tau_rise_h) / ((1.0 / tau_rise_h) - (1.0 / tau_fall_h))
    return float(np.exp(-t_peak / tau_fall_h) - np.exp(-t_peak / tau_rise_h))


def _pulse_component(t_h: np.ndarray, phase: PulsePhase) -> np.ndarray:
    _validate_phase(phase)
    dt = t_h - phase.t0_h
    active = dt >= 0.0
    signal = np.zeros_like(t_h, dtype=float)
    if not np.any(active) or phase.amplitude_nm == 0.0:
        return signal

    peak_factor = _unit_peak_factor(phase.tau_rise_h, phase.tau_fall_h)
    if peak_factor <= 0:
        raise ValueError("Invalid phase kinetics: non-positive normalization factor")

    pulse = np.exp(-dt[active] / phase.tau_fall_h) - np.exp(-dt[active] / phase.tau_rise_h)
    signal[active] = phase.amplitude_nm * pulse / peak_factor
    return signal


def _build_profile(params: HistamineProfileParams, t: float | np.ndarray) -> np.ndarray | float:
    t_h = _to_numpy_time(t)
    _validate_phase(params.phase1)
    if params.phase2 is not None:
        _validate_phase(params.phase2)

    h = np.full_like(t_h, fill_value=params.h_base_nm, dtype=float)
    h = h + _pulse_component(t_h, params.phase1)
    if params.phase2 is not None:
        h = h + _pulse_component(t_h, params.phase2)

    h = np.maximum(h, 0.0)
    if np.isscalar(t):
        return float(h.item())
    return h


# -----------------------
# Parameter handling
# -----------------------
def _coerce_params(params: HistamineProfileParams | Mapping[str, Any] | None, default: HistamineProfileParams) -> HistamineProfileParams:
    if params is None:
        return default

    if isinstance(params, HistamineProfileParams):
        return params

    if is_dataclass(params):
        params = asdict(params)

    if not isinstance(params, Mapping):
        raise ValueError("params must be dict-like, dataclass, or HistamineProfileParams")

    data = dict(params)

    tissue = data.get("tissue", default.tissue)
    if isinstance(tissue, str):
        tissue = Tissue(tissue.lower())

    profile_type = data.get("profile_type", default.profile_type)
    if isinstance(profile_type, str):
        profile_type = ProfileType(profile_type.lower())

    h_base_nm = float(data.get("h_base_nm", default.h_base_nm))
    if h_base_nm < 0:
        raise ValueError("h_base_nm must be >= 0")

    phase1_data = data.get("phase1", asdict(default.phase1))
    phase2_data = data.get("phase2", asdict(default.phase2) if default.phase2 else None)

    phase1 = PulsePhase(**phase1_data) if isinstance(phase1_data, Mapping) else phase1_data
    phase2 = None
    if phase2_data is not None:
        phase2 = PulsePhase(**phase2_data) if isinstance(phase2_data, Mapping) else phase2_data

    result = HistamineProfileParams(
        profile_type=profile_type,
        tissue=tissue,
        h_base_nm=h_base_nm,
        phase1=phase1,
        phase2=phase2,
    )

    _validate_phase(result.phase1)
    if result.phase2 is not None:
        _validate_phase(result.phase2)
    return result


# -----------------------
# Model defaults
# -----------------------
def _baseline_for_tissue(tissue: Tissue) -> float:
    try:
        return BASAL_HISTAMINE_NM[tissue]
    except KeyError as exc:
        raise ValueError(f"Unsupported tissue: {tissue}") from exc


def default_formalin_params(tissue: Tissue = Tissue.SKIN) -> HistamineProfileParams:
    h_base = _baseline_for_tissue(tissue)
    return HistamineProfileParams(
        profile_type=ProfileType.BI,
        tissue=tissue,
        h_base_nm=h_base,
        phase1=PulsePhase(
            amplitude_nm=max(1000.0 - h_base, 0.0),
            t0_h=0.0,
            tau_rise_h=0.03,
            tau_fall_h=0.12,
        ),
        phase2=PulsePhase(
            amplitude_nm=400.0,
            t0_h=20.0 / 60.0,
            tau_rise_h=0.15,
            tau_fall_h=0.80,
        ),
    )


def default_compound48_80_params(tissue: Tissue = Tissue.SKIN) -> HistamineProfileParams:
    h_base = _baseline_for_tissue(tissue)
    return HistamineProfileParams(
        profile_type=ProfileType.BI,
        tissue=tissue,
        h_base_nm=h_base,
        phase1=PulsePhase(
            amplitude_nm=1500.0,
            t0_h=0.0,
            tau_rise_h=5.0 / 60.0,
            tau_fall_h=20.0 / 60.0,
        ),
        phase2=PulsePhase(
            amplitude_nm=250.0,
            t0_h=60.0 / 60.0,
            tau_rise_h=40.0 / 60.0,
            tau_fall_h=120.0 / 60.0,
        ),
    )


def default_capsaicin_params(tissue: Tissue = Tissue.SKIN) -> HistamineProfileParams:
    h_base = _baseline_for_tissue(tissue)
    return HistamineProfileParams(
        profile_type=ProfileType.MONO,
        tissue=tissue,
        h_base_nm=h_base,
        phase1=PulsePhase(
            amplitude_nm=150.0,
            t0_h=0.0,
            tau_rise_h=10.0 / 60.0,
            tau_fall_h=40.0 / 60.0,
        ),
        phase2=None,
    )


def default_carrageenin_muscle_params(tissue: Tissue = Tissue.MUSCLE) -> HistamineProfileParams:
    h_base = _baseline_for_tissue(tissue)
    return HistamineProfileParams(
        profile_type=ProfileType.BI,
        tissue=tissue,
        h_base_nm=h_base,
        phase1=PulsePhase(
            amplitude_nm=max(435.0 - h_base, 0.0),
            t0_h=0.0,
            tau_rise_h=0.50,
            tau_fall_h=2.00,
        ),
        phase2=PulsePhase(
            amplitude_nm=180.0,
            t0_h=3.0,
            tau_rise_h=1.20,
            tau_fall_h=5.50,
        ),
    )


def default_hotplate_params(tissue: Tissue = Tissue.SKIN) -> HistamineProfileParams:
    h_base = _baseline_for_tissue(tissue)
    return HistamineProfileParams(
        profile_type=ProfileType.PULSE,
        tissue=tissue,
        h_base_nm=h_base,
        phase1=PulsePhase(
            amplitude_nm=max(262.0 - h_base, 0.0),
            t0_h=0.0,
            tau_rise_h=0.005,
            tau_fall_h=0.03,
        ),
        phase2=None,
    )


def default_acetic_writhing_params(tissue: Tissue = Tissue.PERITONEUM) -> HistamineProfileParams:
    h_base = _baseline_for_tissue(tissue)
    return HistamineProfileParams(
        profile_type=ProfileType.MONO,
        tissue=tissue,
        h_base_nm=h_base,
        phase1=PulsePhase(
            amplitude_nm=max(550.0 - h_base, 0.0),
            t0_h=0.0,
            tau_rise_h=0.08,
            tau_fall_h=0.35,
        ),
        phase2=None,
    )


def formalin_histamine(t: float | np.ndarray, params: HistamineProfileParams | Mapping[str, Any] | None = None) -> np.ndarray | float:
    cfg = _coerce_params(params, default_formalin_params())
    return _build_profile(cfg, t)


def compound48_80_histamine(t: float | np.ndarray, params: HistamineProfileParams | Mapping[str, Any] | None = None) -> np.ndarray | float:
    cfg = _coerce_params(params, default_compound48_80_params())
    return _build_profile(cfg, t)


def capsaicin_histamine(t: float | np.ndarray, params: HistamineProfileParams | Mapping[str, Any] | None = None) -> np.ndarray | float:
    cfg = _coerce_params(params, default_capsaicin_params())
    return _build_profile(cfg, t)


def carrageenin_histamine(t: float | np.ndarray, params: HistamineProfileParams | Mapping[str, Any] | None = None) -> np.ndarray | float:
    cfg = _coerce_params(params, default_carrageenin_muscle_params())
    return _build_profile(cfg, t)


def hotplate_histamine(t: float | np.ndarray, params: HistamineProfileParams | Mapping[str, Any] | None = None) -> np.ndarray | float:
    cfg = _coerce_params(params, default_hotplate_params())
    return _build_profile(cfg, t)


def acetic_writhing_histamine(t: float | np.ndarray, params: HistamineProfileParams | Mapping[str, Any] | None = None) -> np.ndarray | float:
    cfg = _coerce_params(params, default_acetic_writhing_params())
    return _build_profile(cfg, t)


def get_histamine_profile(model_name: str, tissue: str | Tissue = Tissue.SKIN) -> tuple[Callable[[float | np.ndarray, HistamineProfileParams | Mapping[str, Any] | None], np.ndarray | float], HistamineProfileParams]:
    if isinstance(tissue, str):
        tissue = Tissue(tissue.lower())

    key = model_name.strip().lower().replace("-", "_").replace(" ", "_")

    registry: dict[str, tuple[Callable[..., np.ndarray | float], Callable[[Tissue], HistamineProfileParams]]] = {
        "formalin": (formalin_histamine, default_formalin_params),
        "compound48_80": (compound48_80_histamine, default_compound48_80_params),
        "compound_48_80": (compound48_80_histamine, default_compound48_80_params),
        "capsaicin": (capsaicin_histamine, default_capsaicin_params),
        "carrageenin": (carrageenin_histamine, default_carrageenin_muscle_params),
        "carrageenan": (carrageenin_histamine, default_carrageenin_muscle_params),
        "hotplate": (hotplate_histamine, default_hotplate_params),
        "hot_plate": (hotplate_histamine, default_hotplate_params),
        "acetic_writhing": (acetic_writhing_histamine, default_acetic_writhing_params),
        "acetic": (acetic_writhing_histamine, default_acetic_writhing_params),
    }

    if key not in registry:
        supported = ", ".join(sorted(registry.keys()))
        raise ValueError(f"Unknown model_name '{model_name}'. Supported: {supported}")

    fn, default_factory = registry[key]
    default = default_factory(tissue)
    return fn, default


__all__ = [
    "ProfileType",
    "Tissue",
    "PulsePhase",
    "HistamineProfileParams",
    "BASAL_HISTAMINE_NM",
    "formalin_histamine",
    "compound48_80_histamine",
    "capsaicin_histamine",
    "carrageenin_histamine",
    "hotplate_histamine",
    "acetic_writhing_histamine",
    "get_histamine_profile",
]
