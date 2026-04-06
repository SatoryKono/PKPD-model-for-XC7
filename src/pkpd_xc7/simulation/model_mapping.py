from __future__ import annotations

from pkpd_xc7.config.schemas import ModelConfig, TraffickingConfig, TraffickingOverrideConfig
from pkpd_xc7.models.receptor_trafficking import MODEL_RUNTIME_ASSUMPTION, TraffickingCoreParams


def _merge_trafficking_config(
    base: TraffickingConfig,
    override: TraffickingOverrideConfig | None,
) -> TraffickingConfig:
    if override is None:
        return base
    update = override.model_dump(exclude_none=True)
    if not update:
        return base
    return base.model_copy(update=update)


def resolve_trafficking_config(config: ModelConfig, tissue: str | None = None) -> TraffickingConfig:
    """Resolve base trafficking config with an optional tissue-specific override."""
    if tissue is None:
        return config.trafficking
    tissue_override = config.tissue_overrides.get(tissue)
    return _merge_trafficking_config(config.trafficking, None if tissue_override is None else tissue_override.trafficking)


def resolve_effective_h_base_nm(config: ModelConfig, tissue: str | None = None) -> float | None:
    """
    Resolve the effective baseline histamine level used at runtime.

    For scenario drivers, baseline H is owned by the scenario registry unless the
    trafficking config explicitly overrides `h_base_nm`.
    For PK drivers, baseline H must be provided explicitly by the resolved
    trafficking config so that runtime and meta share the same source of truth.
    """
    trafficking = resolve_trafficking_config(config, tissue)
    if trafficking.h_base_nm is not None:
        return float(trafficking.h_base_nm)
    return None


def trafficking_params_by_tissue(config: ModelConfig) -> dict[str, dict[str, float]]:
    """Return deterministic resolved trafficking parameters for every configured tissue."""
    resolved: dict[str, dict[str, float]] = {}
    for tissue in config.tissues:
        payload = resolve_trafficking_config(config, tissue).model_dump()
        effective_h_base_nm = resolve_effective_h_base_nm(config, tissue)
        if effective_h_base_nm is not None:
            payload["h_base_nm"] = effective_h_base_nm
        resolved[tissue] = payload
    return resolved


def model_config_to_trafficking_core(config: ModelConfig, tissue: str | None = None) -> TraffickingCoreParams:
    """Build a lightweight immutable container for the ODE hot path."""
    trafficking = resolve_trafficking_config(config, tissue)
    return TraffickingCoreParams(
        k_int_max_per_h=trafficking.k_int_max_per_h,
        k_rec_per_h=trafficking.k_rec_per_h,
        k_synth_per_h=trafficking.k_synth_per_h,
        ec50_barr_nm=trafficking.ec50_barr_nm,
        ec50_internalization_nm=(
            trafficking.ec50_barr_nm
            if trafficking.ec50_internalization_nm is None
            else trafficking.ec50_internalization_nm
        ),
        kb_arr_nm=trafficking.ec50_barr_nm if trafficking.kb_arr_nm is None else trafficking.kb_arr_nm,
        hill_n=trafficking.hill_n,
        ec50_g_nm=trafficking.ec50_g_nm,
        kb_g_nm=trafficking.ec50_g_nm if trafficking.kb_g_nm is None else trafficking.kb_g_nm,
        constitutive_activity=trafficking.constitutive_activity,
    )


def runtime_assumptions(config: ModelConfig) -> list[str]:
    """Merge config assumptions with model-runtime assumptions deterministically."""
    merged = list(config.assumptions)
    if MODEL_RUNTIME_ASSUMPTION not in merged:
        merged.append(MODEL_RUNTIME_ASSUMPTION)
    return merged
