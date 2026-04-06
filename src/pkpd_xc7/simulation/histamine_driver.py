from __future__ import annotations

import math

from pkpd_xc7.config.schemas import ModelConfig
from pkpd_xc7.simulation.model_mapping import resolve_effective_h_base_nm
from pkpd_xc7.simulation.scenario_registry import build_scenario_histamine_nm, resolve_scenario_spec


def _bateman_pulse(t_h: float, dose: float, k_abs_per_h: float, k_elim_per_h: float) -> float:
    """Return a non-negative Bateman pulse in nM-space proxy units."""
    if t_h <= 0.0 or dose <= 0.0:
        return 0.0
    if k_abs_per_h <= 0.0 or k_elim_per_h <= 0.0:
        return 0.0
    if math.isclose(k_abs_per_h, k_elim_per_h, rel_tol=0.0, abs_tol=1e-12):
        return dose * k_abs_per_h * t_h * math.exp(-k_abs_per_h * t_h)
    scale = dose * k_abs_per_h / (k_abs_per_h - k_elim_per_h)
    return max(0.0, scale * (math.exp(-k_elim_per_h * t_h) - math.exp(-k_abs_per_h * t_h)))


def resolve_scenario_histamine_nm(t_h: float, config: ModelConfig, tissue: str) -> float:
    """
    Resolve the scenario-driven H(t) branch using config overrides, driver hints, and registry defaults.
    """
    scenario_spec = resolve_scenario_spec(config)
    return build_scenario_histamine_nm(float(t_h), scenario_spec, tissue)


def resolve_histamine_nm(t_h: float, config: ModelConfig, tissue: str) -> float:
    """
    Resolve histamine driver for a given tissue/time pair with physiological clipping.
    """
    if config.driver.driver_type == "scenario":
        h_raw = resolve_scenario_histamine_nm(float(t_h), config, tissue)
        return max(0.0, h_raw)

    h_base = resolve_effective_h_base_nm(config, tissue)
    if h_base is None:
        raise ValueError(f"Unable to resolve PK baseline histamine for tissue '{tissue}'.")

    dose = float(config.driver.dose)
    pulse = _bateman_pulse(
        t_h=float(t_h),
        dose=dose,
        k_abs_per_h=float(config.driver.k_abs_per_h),
        k_elim_per_h=float(config.driver.k_elim_per_h),
    )
    h_raw = h_base + pulse
    return max(0.0, h_raw)