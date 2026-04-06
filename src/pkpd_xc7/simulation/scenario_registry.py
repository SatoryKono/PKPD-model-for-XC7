from __future__ import annotations

import math
from dataclasses import dataclass
from typing import cast

from pkpd_xc7.config.schemas import (
    FormalinProfileOverrides,
    ModelConfig,
    ProfileShape,
    SCENARIO_ID_ALIASES,
    ScenarioPhaseOverrides,
    ScenarioProfileShape,
    TissueFormalinProfileOverrides,
)
from pkpd_xc7.simulation.model_mapping import resolve_trafficking_config


@dataclass(frozen=True, slots=True)
class GaussianComponentSpec:
    amplitude_nm: float
    center_h: float
    sigma_h: float


@dataclass(frozen=True, slots=True)
class PulsePhaseSpec:
    amplitude_nm: float
    t0_h: float
    tau_rise_h: float
    tau_fall_h: float


@dataclass(frozen=True, slots=True)
class TissueProfile:
    h_base_nm: float
    gaussian_components: tuple[GaussianComponentSpec, ...] = ()
    pulse_phases: tuple[PulsePhaseSpec, ...] = ()


@dataclass(frozen=True, slots=True)
class ScenarioSpec:
    scenario_id: str
    default_shape: ScenarioProfileShape
    supported_shapes: frozenset[ScenarioProfileShape]
    tissue_profiles: dict[str, TissueProfile]
    profile_shape: ScenarioProfileShape
    tissue_profile_shapes: dict[str, ScenarioProfileShape]
    notes: tuple[str, ...] = ()


def hours_from_minutes(value_min: float | None) -> float | None:
    if value_min is None:
        return None
    return float(value_min) / 60.0


def gaussian_component_nm(t_h: float, component: GaussianComponentSpec) -> float:
    delta = float(t_h) - component.center_h
    return component.amplitude_nm * math.exp(-(delta * delta) / (2.0 * component.sigma_h * component.sigma_h))


def pulse_component_nm(t_h: float, phase: PulsePhaseSpec) -> float:
    dt = float(t_h) - phase.t0_h
    if dt <= 0.0:
        return 0.0
    if dt <= phase.tau_rise_h:
        return phase.amplitude_nm * (dt / phase.tau_rise_h)
    return phase.amplitude_nm * math.exp(-(dt - phase.tau_rise_h) / phase.tau_fall_h)


def sum_gaussian_profile_nm(t_h: float, profile: TissueProfile) -> float:
    return profile.h_base_nm + sum(gaussian_component_nm(t_h, component) for component in profile.gaussian_components)


def sum_pulse_profile_nm(t_h: float, profile: TissueProfile) -> float:
    return profile.h_base_nm + sum(pulse_component_nm(t_h, phase) for phase in profile.pulse_phases)


def _gaussian(amplitude_nm: float, center_min: float, sigma_min: float) -> GaussianComponentSpec:
    return GaussianComponentSpec(
        amplitude_nm=float(amplitude_nm),
        center_h=float(center_min) / 60.0,
        sigma_h=float(sigma_min) / 60.0,
    )


def _pulse(amplitude_nm: float, t0_min: float, tau_rise_min: float, tau_fall_min: float) -> PulsePhaseSpec:
    return PulsePhaseSpec(
        amplitude_nm=float(amplitude_nm),
        t0_h=float(t0_min) / 60.0,
        tau_rise_h=float(tau_rise_min) / 60.0,
        tau_fall_h=float(tau_fall_min) / 60.0,
    )


def _proxy_profile(profile: TissueProfile) -> TissueProfile:
    return TissueProfile(
        h_base_nm=profile.h_base_nm,
        gaussian_components=profile.gaussian_components,
        pulse_phases=profile.pulse_phases,
    )


def _merge_optional_float(current: float, updated: float | None) -> float:
    return current if updated is None else float(updated)


def _merge_gaussian_component(
    base: GaussianComponentSpec,
    override: ScenarioPhaseOverrides | None,
) -> GaussianComponentSpec:
    if override is None:
        return base
    return GaussianComponentSpec(
        amplitude_nm=_merge_optional_float(base.amplitude_nm, override.amplitude_nm),
        center_h=_merge_optional_float(base.center_h, hours_from_minutes(override.center_min)),
        sigma_h=_merge_optional_float(base.sigma_h, hours_from_minutes(override.sigma_min)),
    )


def _merge_pulse_phase(base: PulsePhaseSpec, override: ScenarioPhaseOverrides | None) -> PulsePhaseSpec:
    if override is None:
        return base
    return PulsePhaseSpec(
        amplitude_nm=_merge_optional_float(base.amplitude_nm, override.amplitude_nm),
        t0_h=_merge_optional_float(base.t0_h, hours_from_minutes(override.center_min)),
        tau_rise_h=_merge_optional_float(base.tau_rise_h, hours_from_minutes(override.tau_rise_min)),
        tau_fall_h=_merge_optional_float(base.tau_fall_h, hours_from_minutes(override.tau_fall_min)),
    )


def _build_spec(
    scenario_id: str,
    default_shape: ScenarioProfileShape,
    supported_shapes: tuple[ScenarioProfileShape, ...],
    tissue_profiles: dict[str, TissueProfile],
    notes: tuple[str, ...] = (),
) -> ScenarioSpec:
    return ScenarioSpec(
        scenario_id=scenario_id,
        default_shape=default_shape,
        supported_shapes=frozenset(supported_shapes),
        tissue_profiles=tissue_profiles,
        profile_shape=default_shape,
        tissue_profile_shapes=dict.fromkeys(tissue_profiles, default_shape),
        notes=notes,
    )


def _build_formalin_spec() -> ScenarioSpec:
    spinal_coord = TissueProfile(
        h_base_nm=2.0,
        gaussian_components=(_gaussian(10.0, 30.0, 20.0),),
        pulse_phases=(_pulse(10.0, 10.0, 20.0, 35.0),),
    )
    return _build_spec(
        scenario_id="formalin",
        default_shape="gaussian_sum",
        supported_shapes=("gaussian_sum", "pulse"),
        tissue_profiles={
            "skin": TissueProfile(
                h_base_nm=50.0,
                gaussian_components=(
                    _gaussian(950.0, 5.0, 4.0),
                    _gaussian(250.0, 40.0, 25.0),
                ),
                pulse_phases=(
                    _pulse(950.0, 0.0, 5.0, 12.0),
                    _pulse(250.0, 20.0, 15.0, 30.0),
                ),
            ),
            "spinal_coord": spinal_coord,
            "brain": _proxy_profile(spinal_coord),
            "ganglia": TissueProfile(
                h_base_nm=5.0,
                gaussian_components=(_gaussian(10.0, 15.0, 10.0),),
                pulse_phases=(_pulse(10.0, 5.0, 10.0, 18.0),),
            ),
        },
    )


def _build_capsaicin_spec() -> ScenarioSpec:
    spinal_coord = TissueProfile(h_base_nm=2.0, gaussian_components=(_gaussian(2.3, 90.0, 60.0),))
    return _build_spec(
        scenario_id="capsaicin",
        default_shape="gaussian_sum",
        supported_shapes=("gaussian_sum",),
        tissue_profiles={
            "skin": TissueProfile(h_base_nm=50.0, gaussian_components=(_gaussian(177.0, 15.0, 12.0),)),
            "spinal_coord": spinal_coord,
            "brain": _proxy_profile(spinal_coord),
            "ganglia": TissueProfile(h_base_nm=5.0, gaussian_components=(_gaussian(0.6, 20.0, 15.0),)),
        },
    )


def _build_carrageenan_spec() -> ScenarioSpec:
    spinal_coord = TissueProfile(h_base_nm=2.0, gaussian_components=(_gaussian(4.3, 180.0, 120.0),))
    return _build_spec(
        scenario_id="carrageenan",
        default_shape="gaussian_sum",
        supported_shapes=("gaussian_sum",),
        tissue_profiles={
            "muscle": TissueProfile(
                h_base_nm=50.0,
                gaussian_components=(
                    _gaussian(385.0, 90.0, 50.0),
                    _gaussian(150.0, 360.0, 150.0),
                ),
            ),
            "spinal_coord": spinal_coord,
            "brain": _proxy_profile(spinal_coord),
            "ganglia": TissueProfile(h_base_nm=5.0, gaussian_components=(_gaussian(3.0, 60.0, 40.0),)),
        },
    )


def _build_hot_plate_spec() -> ScenarioSpec:
    spinal_coord = TissueProfile(h_base_nm=2.0, gaussian_components=(_gaussian(3.0, 2.0, 3.0),))
    return _build_spec(
        scenario_id="hot_plate",
        default_shape="gaussian_sum",
        supported_shapes=("gaussian_sum",),
        tissue_profiles={
            "skin": TissueProfile(h_base_nm=50.0, gaussian_components=(_gaussian(212.0, 1.0, 2.0),)),
            "spinal_coord": spinal_coord,
            "brain": _proxy_profile(spinal_coord),
            "ganglia": TissueProfile(h_base_nm=5.0, gaussian_components=(_gaussian(9.8, 2.0, 2.0),)),
        },
    )


def _build_acetic_writhing_spec() -> ScenarioSpec:
    spinal_coord = TissueProfile(h_base_nm=2.0, gaussian_components=(_gaussian(128.0, 5.0, 10.0),))
    return _build_spec(
        scenario_id="acetic_writhing",
        default_shape="gaussian_sum",
        supported_shapes=("gaussian_sum",),
        tissue_profiles={
            "peritoneum": TissueProfile(h_base_nm=50.0, gaussian_components=(_gaussian(500.0, 5.0, 4.0),)),
            "spinal_coord": spinal_coord,
            "brain": _proxy_profile(spinal_coord),
            "ganglia": TissueProfile(h_base_nm=5.0, gaussian_components=(_gaussian(16.8, 5.0, 7.0),)),
        },
    )


def _build_compound_48_80_spec() -> ScenarioSpec:
    spinal_coord = TissueProfile(h_base_nm=2.0, gaussian_components=(_gaussian(4.0, 120.0, 80.0),))
    return _build_spec(
        scenario_id="compound_48_80",
        default_shape="gaussian_sum",
        supported_shapes=("gaussian_sum",),
        tissue_profiles={
            "skin": TissueProfile(
                h_base_nm=50.0,
                gaussian_components=(
                    _gaussian(950.0, 8.0, 5.0),
                    _gaussian(250.0, 60.0, 40.0),
                ),
            ),
            "spinal_coord": spinal_coord,
            "brain": _proxy_profile(spinal_coord),
            "ganglia": TissueProfile(h_base_nm=5.0, gaussian_components=(_gaussian(5.0, 20.0, 15.0),)),
        },
    )


def _build_zymosan_spec() -> ScenarioSpec:
    spinal_coord = TissueProfile(h_base_nm=2.0, gaussian_components=(_gaussian(1.6, 120.0, 200.0),))
    return _build_spec(
        scenario_id="zymosan",
        default_shape="gaussian_sum",
        supported_shapes=("gaussian_sum",),
        tissue_profiles={
            "peritoneum": TissueProfile(h_base_nm=50.0, gaussian_components=(_gaussian(300.0, 210.0, 150.0),)),
            "spinal_coord": spinal_coord,
            "brain": _proxy_profile(spinal_coord),
            "ganglia": TissueProfile(h_base_nm=5.0, gaussian_components=(_gaussian(1.0, 180.0, 120.0),)),
        },
        notes=("zymosan gaussian_sum is an MVP approximation of the delayed inflammatory profile",),
    )


REGISTERED_SCENARIOS: dict[str, ScenarioSpec] = {
    "formalin": _build_formalin_spec(),
    "capsaicin": _build_capsaicin_spec(),
    "carrageenan": _build_carrageenan_spec(),
    "hot_plate": _build_hot_plate_spec(),
    "acetic_writhing": _build_acetic_writhing_spec(),
    "compound_48_80": _build_compound_48_80_spec(),
    "zymosan": _build_zymosan_spec(),
}


def get_scenario_spec(scenario_id: str) -> ScenarioSpec:
    canonical_id = SCENARIO_ID_ALIASES.get(scenario_id, scenario_id)
    try:
        return REGISTERED_SCENARIOS[canonical_id]
    except KeyError as exc:
        allowed = ", ".join(sorted(REGISTERED_SCENARIOS))
        raise ValueError(f"Unsupported scenario_id='{scenario_id}'. Expected one of: {allowed}.") from exc


def _clone_with_shape(
    base: ScenarioSpec,
    shape: ScenarioProfileShape,
    profiles: dict[str, TissueProfile] | None = None,
    tissue_shapes: dict[str, ScenarioProfileShape] | None = None,
) -> ScenarioSpec:
    resolved_profiles = base.tissue_profiles if profiles is None else profiles
    return ScenarioSpec(
        scenario_id=base.scenario_id,
        default_shape=base.default_shape,
        supported_shapes=base.supported_shapes,
        tissue_profiles=resolved_profiles,
        profile_shape=shape,
        tissue_profile_shapes=(
            dict.fromkeys(resolved_profiles, shape)
            if tissue_shapes is None
            else tissue_shapes
        ),
        notes=base.notes,
    )


def _resolve_formalin_shape(config: ModelConfig, base: ScenarioSpec) -> ScenarioProfileShape:
    if config.driver.driver_type != "scenario":
        raise ValueError("_resolve_formalin_shape expects a scenario driver.")

    override_shape: ProfileShape | None = None
    if config.formalin_profile is not None:
        override_shape = config.formalin_profile.profile_shape
    chosen_shape = override_shape or config.driver.profile_shape or base.default_shape
    if chosen_shape not in base.supported_shapes:
        allowed = ", ".join(sorted(base.supported_shapes))
        raise ValueError(
            f"Unsupported profile_shape='{chosen_shape}' for scenario_id='formalin'. Expected one of: {allowed}."
        )
    return cast(ScenarioProfileShape, chosen_shape)


def _resolve_formalin_tissue_shape(
    tissue_name: str,
    config: ModelConfig,
    base: ScenarioSpec,
    default_shape: ScenarioProfileShape,
) -> ScenarioProfileShape:
    override_shape: ProfileShape | None = None
    tissue_override = config.tissue_overrides.get(tissue_name)
    if tissue_override is not None and tissue_override.formalin_profile is not None:
        override_shape = tissue_override.formalin_profile.profile_shape
    chosen_shape = override_shape or default_shape
    if chosen_shape not in base.supported_shapes:
        allowed = ", ".join(sorted(base.supported_shapes))
        raise ValueError(
            f"Unsupported profile_shape='{chosen_shape}' for scenario_id='formalin' tissue='{tissue_name}'. Expected one of: {allowed}."
        )
    return cast(ScenarioProfileShape, chosen_shape)


def _resolve_formalin_profile(
    tissue_profile: TissueProfile,
    shape: ScenarioProfileShape,
    h_base_nm: float | None,
    phase1: ScenarioPhaseOverrides | None,
    phase2: ScenarioPhaseOverrides | None,
) -> TissueProfile:
    if shape == "gaussian_sum":
        gaussian_components = list(tissue_profile.gaussian_components)
        if gaussian_components:
            gaussian_components[0] = _merge_gaussian_component(gaussian_components[0], phase1)
        if len(gaussian_components) > 1:
            gaussian_components[1] = _merge_gaussian_component(gaussian_components[1], phase2)
        return TissueProfile(
            h_base_nm=_merge_optional_float(tissue_profile.h_base_nm, h_base_nm),
            gaussian_components=tuple(gaussian_components),
            pulse_phases=tissue_profile.pulse_phases,
        )

    pulse_phases = list(tissue_profile.pulse_phases)
    if pulse_phases:
        pulse_phases[0] = _merge_pulse_phase(pulse_phases[0], phase1)
    if len(pulse_phases) > 1:
        pulse_phases[1] = _merge_pulse_phase(pulse_phases[1], phase2)
    return TissueProfile(
        h_base_nm=_merge_optional_float(tissue_profile.h_base_nm, h_base_nm),
        gaussian_components=tissue_profile.gaussian_components,
        pulse_phases=tuple(pulse_phases),
    )


def _apply_trafficking_h_base_override(
    tissue_profile: TissueProfile,
    h_base_nm: float | None,
) -> TissueProfile:
    if h_base_nm is None:
        return tissue_profile
    return TissueProfile(
        h_base_nm=float(h_base_nm),
        gaussian_components=tissue_profile.gaussian_components,
        pulse_phases=tissue_profile.pulse_phases,
    )


def _apply_formalin_overrides(
    tissue_profile: TissueProfile,
    shape: ScenarioProfileShape,
    overrides: FormalinProfileOverrides | TissueFormalinProfileOverrides | None,
) -> TissueProfile:
    if overrides is None:
        return tissue_profile
    return _resolve_formalin_profile(
        tissue_profile=tissue_profile,
        shape=shape,
        h_base_nm=overrides.h_base_nm,
        phase1=overrides.phase1,
        phase2=overrides.phase2,
    )


def resolve_formalin_spec(config: ModelConfig) -> ScenarioSpec:
    base = get_scenario_spec("formalin")
    shape = _resolve_formalin_shape(config, base)
    resolved_shapes: dict[str, ScenarioProfileShape] = {}
    resolved_profiles = {
        tissue_name: _apply_formalin_overrides(
            _apply_formalin_overrides(
                tissue_profile=_apply_trafficking_h_base_override(
                    tissue_profile,
                    resolve_trafficking_config(config, tissue_name).h_base_nm,
                ),
                shape=_resolve_formalin_tissue_shape(tissue_name, config, base, shape),
                overrides=config.formalin_profile,
            ),
            shape=_resolve_formalin_tissue_shape(tissue_name, config, base, shape),
            overrides=(
                None
                if tissue_name not in config.tissue_overrides
                else config.tissue_overrides[tissue_name].formalin_profile
            ),
        )
        for tissue_name, tissue_profile in base.tissue_profiles.items()
    }
    for tissue_name in base.tissue_profiles:
        resolved_shapes[tissue_name] = _resolve_formalin_tissue_shape(tissue_name, config, base, shape)
    return _clone_with_shape(base, shape, resolved_profiles, tissue_shapes=resolved_shapes)


def resolve_scenario_spec(config: ModelConfig) -> ScenarioSpec:
    if config.driver.driver_type != "scenario":
        raise ValueError("resolve_scenario_spec expects a scenario driver.")

    driver = config.driver
    base = get_scenario_spec(driver.scenario_id)
    if base.scenario_id == "formalin":
        return resolve_formalin_spec(config)

    chosen_shape = driver.profile_shape or base.default_shape
    if chosen_shape not in base.supported_shapes:
        allowed = ", ".join(sorted(base.supported_shapes))
        raise ValueError(
            f"Unsupported profile_shape='{chosen_shape}' for scenario_id='{base.scenario_id}'. "
            f"Expected one of: {allowed}."
        )
    resolved_profiles = {
        tissue_name: _apply_trafficking_h_base_override(
            tissue_profile,
            resolve_trafficking_config(config, tissue_name).h_base_nm,
        )
        for tissue_name, tissue_profile in base.tissue_profiles.items()
    }
    return _clone_with_shape(base, chosen_shape, resolved_profiles)


def build_scenario_histamine_nm(t_h: float, spec: ScenarioSpec, tissue: str) -> float:
    try:
        profile = spec.tissue_profiles[tissue]
    except KeyError as exc:
        allowed = ", ".join(sorted(spec.tissue_profiles))
        raise ValueError(
            f"Unsupported tissue='{tissue}' for scenario_id='{spec.scenario_id}'. Expected one of: {allowed}."
        ) from exc

    shape = spec.tissue_profile_shapes.get(tissue, spec.profile_shape)

    if shape == "gaussian_sum":
        return sum_gaussian_profile_nm(t_h, profile)
    if shape == "pulse":
        return sum_pulse_profile_nm(t_h, profile)
    raise ValueError(f"Unsupported profile_shape='{shape}'.")
