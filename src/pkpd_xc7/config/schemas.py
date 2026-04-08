from __future__ import annotations

import hashlib
import json
from typing import Annotated, Any, ClassVar, List, Literal

from pydantic import BaseModel, Field, model_validator


class Traceability(BaseModel):
    # A-002: source_in_report обязателен и не пустой
    source_in_report: str = Field(min_length=1, description="Ссылка на таблицу/раздел в отчёте")
    source_reference: str = Field(default="", description="Опциональный DOI или внутренняя ссылка")
    source_version: str | None = Field(default=None, description="Версия документа")


class PKDriver(BaseModel):
    driver_type: Literal["pk"] = "pk"
    dose: float = Field(default=100.0, gt=0, description="Доза для PK профиля (нМ-эквивалент)")
    k_abs_per_h: float = Field(ge=0)
    k_elim_per_h: float = Field(ge=0)


ScenarioProfileShape = Literal["pulse", "gaussian_sum"]
CANONICAL_SCENARIO_IDS: tuple[str, ...] = (
    "formalin",
    "intact",
    "capsaicin",
    "carrageenan",
    "hot_plate",
    "acetic_writhing",
    "zymosan",
    "compound_48_80",
)
SHARED_TISSUE_OVERRIDE_IDS: tuple[str, ...] = (
    "skin",
    "muscle",
    "peritoneum",
    "spinal_coord",
    "brain",
    "ganglia",
)
TISSUE_ID_ALIASES: dict[str, str] = {
    "spinal": "spinal_coord",
    "spinal_cord": "spinal_coord",
}
SCENARIO_ID_ALIASES: dict[str, str] = {
    "compound48_80": "compound_48_80",
    "compound4880": "compound_48_80",
    "hotplate": "hot_plate",
    "writhing": "acetic_writhing",
    "carrageenin": "carrageenan",
}
SPECIES_ALIASES: dict[str, str] = {
    "mice": "mouse",
    "mouse": "mouse",
    "rats": "rat",
    "rat": "rat",
}


class ScenarioDriver(BaseModel):
    _canonical_ids: ClassVar[tuple[str, ...]] = CANONICAL_SCENARIO_IDS
    _scenario_aliases: ClassVar[dict[str, str]] = SCENARIO_ID_ALIASES

    driver_type: Literal["scenario"] = "scenario"
    scenario_id: str = Field(min_length=1, description="Идентификатор сценария из реестра")
    profile_shape: ScenarioProfileShape | None = Field(
        default=None,
        description="Опциональная форма H(t); если не задана, orchestrator использует overrides/registry default.",
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_scenario_id_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            scenario_id = data.get("scenario_id")
            if isinstance(scenario_id, str):
                normalized = cls._scenario_aliases.get(scenario_id.strip(), scenario_id.strip())
                data = dict(data)
                data["scenario_id"] = normalized
        return data

    @model_validator(mode="after")
    def validate_scenario_id(self) -> ScenarioDriver:
        if self.scenario_id not in self._canonical_ids:
            allowed = ", ".join(self._canonical_ids)
            raise ValueError(f"Unsupported scenario_id='{self.scenario_id}'. Expected one of: {allowed}.")
        return self


ProfileShape = Literal["pulse", "gaussian_sum", "zymosan_like"]


class ScenarioPhaseOverrides(BaseModel):
    amplitude_nm: float | None = Field(default=None, ge=0)
    center_min: float | None = Field(default=None, ge=0)
    sigma_min: float | None = Field(default=None, gt=0)
    tau_rise_min: float | None = Field(default=None, gt=0)
    tau_fall_min: float | None = Field(default=None, gt=0)


class FormalinProfileOverrides(BaseModel):
    profile_shape: ProfileShape = Field(
        default="gaussian_sum",
        description="Форма профиля H(t); gaussian_sum повторяет legacy plot_formalin.",
    )
    h_base_nm: float | None = Field(default=None, ge=0)
    phase1: ScenarioPhaseOverrides | None = None
    phase2: ScenarioPhaseOverrides | None = None


class TraffickingConfig(BaseModel):
    k_int_max_per_h: float = Field(default=3.0, gt=0)
    k_rec_per_h: float = Field(default=0.5, gt=0)
    k_synth_per_h: float = Field(default=0.05, ge=0)
    ec50_barr_nm: float = Field(default=1500.0, gt=0)
    ec50_internalization_nm: float | None = Field(default=None, gt=0)
    kb_arr_nm: float | None = Field(default=None, gt=0)
    hill_n: float = Field(default=1.0, gt=0)
    ec50_g_nm: float = Field(default=50.0, gt=0)
    kb_g_nm: float | None = Field(default=None, gt=0)
    constitutive_activity: float = Field(default=0.0, ge=0, le=1)
    h_base_nm: float | None = Field(default=None, ge=0)


class TissueFormalinProfileOverrides(BaseModel):
    profile_shape: ProfileShape | None = Field(
        default=None,
        description="Тканеспецифичная форма профиля H(t); если не задана, используется общий shape formalin.",
    )
    h_base_nm: float | None = Field(default=None, ge=0)
    phase1: ScenarioPhaseOverrides | None = None
    phase2: ScenarioPhaseOverrides | None = None


class TraffickingOverrideConfig(BaseModel):
    k_int_max_per_h: float | None = Field(default=None, gt=0)
    k_rec_per_h: float | None = Field(default=None, gt=0)
    k_synth_per_h: float | None = Field(default=None, ge=0)
    ec50_barr_nm: float | None = Field(default=None, gt=0)
    ec50_internalization_nm: float | None = Field(default=None, gt=0)
    kb_arr_nm: float | None = Field(default=None, gt=0)
    hill_n: float | None = Field(default=None, gt=0)
    ec50_g_nm: float | None = Field(default=None, gt=0)
    kb_g_nm: float | None = Field(default=None, gt=0)
    constitutive_activity: float | None = Field(default=None, ge=0, le=1)
    h_base_nm: float | None = Field(default=None, ge=0)


class TissueOverrideConfig(BaseModel):
    trafficking: TraffickingOverrideConfig | None = None
    formalin_profile: TissueFormalinProfileOverrides | None = None


PKRegimen = Literal["single", "repeated"]
PKTimeMethod = Literal["linear", "cubic"]
PKDoseMethod = Literal["log-linear", "linear"]
PKExtrapolationMode = Literal["clip", "linear", "error"]


class AntagonistPKConfig(BaseModel):
    enabled: bool = Field(default=False)
    source_xlsx: str | None = Field(
        default=None,
        description="Путь к XLSX-таблице PK по тканям для XC7.",
    )
    sheet_name: str | int = Field(default=0)
    species: Literal["rat", "mouse"] | None = Field(
        default=None,
        description="Необязательный override вида; иначе используется ModelConfig.species.",
    )
    regimen: PKRegimen = Field(default="single")
    dose_mg_per_kg: float = Field(
        default=90.0,
        gt=0,
        description="Доза XC7, для которой строится тканевой профиль концентрации.",
    )
    concentration_column: str = Field(default="C_nM", min_length=1)
    tissue_map: dict[str, str] = Field(
        default_factory=dict,
        description="Сопоставление канонической ткани модели -> organ из XLSX.",
    )
    method_time: PKTimeMethod = Field(default="linear")
    method_dose: PKDoseMethod = Field(default="log-linear")
    extrapolation: PKExtrapolationMode = Field(default="clip")
    allow_single_dose_scaling: bool = Field(default=False)

    @model_validator(mode="before")
    @classmethod
    def normalize_aliases(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        species = normalized.get("species")
        if isinstance(species, str):
            normalized["species"] = SPECIES_ALIASES.get(species.strip().lower(), species.strip().lower())

        tissue_map = normalized.get("tissue_map")
        if isinstance(tissue_map, dict):
            normalized["tissue_map"] = {
                TISSUE_ID_ALIASES.get(str(tissue).strip(), str(tissue).strip()): str(source_tissue).strip()
                for tissue, source_tissue in tissue_map.items()
            }
        return normalized

    @model_validator(mode="after")
    def validate_enabled_contract(self) -> AntagonistPKConfig:
        if not self.enabled:
            return self
        if self.source_xlsx is None or not self.source_xlsx.strip():
            raise ValueError("antagonist_pk.enabled=true requires a non-empty source_xlsx path.")
        if not self.tissue_map:
            raise ValueError("antagonist_pk.enabled=true requires a non-empty tissue_map.")
        return self


DriverAnnotated = Annotated[
    PKDriver | ScenarioDriver,
    Field(discriminator="driver_type"),
]


class ModelConfig(BaseModel):
    schema_version: str = Field(default="1.2.0", description="Версия схемы конфигурации")
    model_id: str
    compound: str
    species: Literal["rat", "mouse"] | None = Field(
        default=None,
        description="Вид животных, на которых калибровался или верифицировался сценарий.",
    )
    # Симуляция по умолчанию не ветвится по loss; поле для отчётности/фиттинга (фазы 2+).
    loss_mode: str = Field(default="mse")

    traceability: Traceability

    assumptions: List[str] = Field(min_length=1)

    driver: DriverAnnotated

    trafficking: TraffickingConfig = Field(default_factory=TraffickingConfig)
    antagonist_pk: AntagonistPKConfig | None = Field(
        default=None,
        description="Опциональный PK-источник концентрации XC7 по tissue/time/dose.",
    )
    formalin_profile: FormalinProfileOverrides | None = Field(
        default=None,
        description="Опциональные overrides для scenario_id=formalin.",
    )
    intact_profile: FormalinProfileOverrides | None = Field(
        default=None,
        description="Опциональные overrides для scenario_id=intact (та же схема, что formalin_profile).",
    )
    tissue_overrides: dict[str, TissueOverrideConfig] = Field(
        default_factory=dict,
        description="Опциональные переопределения trafficking/formalin_profile по имени ткани.",
    )

    tissues: List[str] = Field(min_length=1)
    time_grid_h: List[float] = Field(min_length=2)

    @model_validator(mode="before")
    @classmethod
    def normalize_tissue_aliases(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        normalized = dict(data)

        species = normalized.get("species")
        if isinstance(species, str):
            normalized["species"] = SPECIES_ALIASES.get(species.strip().lower(), species.strip().lower())

        tissues = normalized.get("tissues")
        if isinstance(tissues, list):
            normalized["tissues"] = [
                TISSUE_ID_ALIASES.get(str(tissue).strip(), str(tissue).strip())
                for tissue in tissues
            ]

        tissue_overrides = normalized.get("tissue_overrides")
        if isinstance(tissue_overrides, dict):
            normalized["tissue_overrides"] = {
                TISSUE_ID_ALIASES.get(str(tissue).strip(), str(tissue).strip()): value
                for tissue, value in tissue_overrides.items()
            }

        return normalized

    @model_validator(mode="before")
    @classmethod
    def normalize_time_units(cls, data: Any) -> Any:
        """
        Нормализация единиц измерения (Фаза 1).
        Перехватывает time_grid и time_unit из YAML, конвертируя в time_grid_h.
        """
        if isinstance(data, dict):
            time_unit = data.get("time_unit", "h")
            if "time_grid" in data and "time_grid_h" not in data:
                grid = data.pop("time_grid")
                if time_unit == "min":
                    data["time_grid_h"] = [t / 60.0 for t in grid]
                elif time_unit == "h":
                    data["time_grid_h"] = grid
                else:
                    raise ValueError(f"Неподдерживаемая единица времени: {time_unit}. Ожидается 'h' или 'min'.")
        return data

    @model_validator(mode="after")
    def check_assumptions_not_empty_strings(self) -> ModelConfig:
        for idx, assumption in enumerate(self.assumptions):
            if not assumption.strip():
                raise ValueError(f"Assumption at index {idx} cannot be an empty string.")
        return self

    @model_validator(mode="after")
    def validate_time_grid_monotonic(self) -> ModelConfig:
        if sorted(self.time_grid_h) != self.time_grid_h or len(set(self.time_grid_h)) != len(self.time_grid_h):
            raise ValueError("time_grid_h must be strictly monotonically increasing.")
        return self

    @model_validator(mode="after")
    def validate_tissue_override_keys(self) -> ModelConfig:
        allowed = set(self.tissues) | set(SHARED_TISSUE_OVERRIDE_IDS)
        unknown = [name for name in self.tissue_overrides if name not in allowed]
        if unknown:
            allowed_display = ", ".join(sorted(allowed))
            unknown_display = ", ".join(unknown)
            raise ValueError(
                f"Unknown tissue_overrides keys: {unknown_display}. Expected subset of known tissue ids: {allowed_display}."
            )
        return self

    @model_validator(mode="after")
    def validate_pk_histamine_baseline_contract(self) -> ModelConfig:
        if self.driver.driver_type != "pk":
            return self

        base_h = self.trafficking.h_base_nm
        missing: list[str] = []
        for tissue in self.tissues:
            override = self.tissue_overrides.get(tissue)
            override_h = None if override is None or override.trafficking is None else override.trafficking.h_base_nm
            if override_h is None and base_h is None:
                missing.append(tissue)

        if missing:
            missing_display = ", ".join(missing)
            raise ValueError(
                "PK driver requires explicit trafficking.h_base_nm resolved per tissue. "
                f"Missing baseline for tissues: {missing_display}."
            )
        return self

    @model_validator(mode="after")
    def validate_antagonist_pk_contract(self) -> ModelConfig:
        if self.antagonist_pk is None or not self.antagonist_pk.enabled:
            return self

        resolved_species = self.antagonist_pk.species or self.species
        if resolved_species is None:
            raise ValueError(
                "antagonist_pk.enabled=true requires species either in antagonist_pk.species or ModelConfig.species."
            )

        missing_tissues = [tissue for tissue in self.tissues if tissue not in self.antagonist_pk.tissue_map]
        if missing_tissues:
            missing_display = ", ".join(missing_tissues)
            raise ValueError(
                "antagonist_pk.tissue_map must resolve every configured tissue. "
                f"Missing mappings for: {missing_display}."
            )
        return self

    def config_sha256(self) -> str:
        """
        Канонический хеш конфигурации: model_dump JSON + sort_keys, не сырой YAML.
        """
        dump = self.model_dump(mode="json", exclude_unset=True)
        payload = json.dumps(dump, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()