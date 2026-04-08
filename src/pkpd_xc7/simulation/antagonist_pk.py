from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator, interp1d  # type: ignore[import-untyped]

from pkpd_xc7.config.schemas import ModelConfig, SPECIES_ALIASES

TimeMethod = Literal["linear", "cubic"]
DoseMethod = Literal["log-linear", "linear"]
ExtrapolationMode = Literal["clip", "linear", "error"]


def _normalize_token(value: object) -> str:
    return " ".join(str(value).strip().lower().split())


def _normalize_species(value: object) -> str:
    token = _normalize_token(value)
    return SPECIES_ALIASES.get(token, token)


@dataclass(frozen=True, slots=True)
class PKSchema:
    species_col: str = "species"
    regimen_col: str = "regimen"
    dose_col: str = "dose_mg_per_kg"
    tissue_col: str = "tissue"
    time_col: str = "time_h"
    concentration_col: str = "concentration"


class AntagonistPKModel:
    """Deterministic PK interpolation/extrapolation model for XC7 tissue concentrations."""

    def __init__(
        self,
        df: pd.DataFrame,
        *,
        schema: PKSchema = PKSchema(),
        allow_single_dose_scaling: bool = False,
    ) -> None:
        self.schema = schema
        self.allow_single_dose_scaling = allow_single_dose_scaling
        self._df = self._preprocess(df.copy())
        self._tissue_data = self._build_index(self._df)

    @property
    def tissues(self) -> list[str]:
        return sorted(self._tissue_data.keys())

    def predict(
        self,
        dose_mg_per_kg: float,
        tissue: str,
        time_h: float,
        method_time: TimeMethod = "linear",
        method_dose: DoseMethod = "log-linear",
        extrapolation: ExtrapolationMode = "clip",
    ) -> float:
        self._validate_request(
            dose_mg_per_kg=dose_mg_per_kg,
            tissue=tissue,
            time_h=time_h,
            method_time=method_time,
            method_dose=method_dose,
            extrapolation=extrapolation,
        )

        tissue_key = str(tissue).strip()
        tissue_block = self._tissue_data[tissue_key]
        time_col = self.schema.time_col
        dose_col = self.schema.dose_col
        conc_col = self.schema.concentration_col

        exact_mask = (
            (self._df[self.schema.tissue_col] == tissue_key)
            & np.isclose(self._df[dose_col].to_numpy(dtype=float), dose_mg_per_kg, rtol=0, atol=1e-12)
            & np.isclose(self._df[time_col].to_numpy(dtype=float), time_h, rtol=0, atol=1e-12)
        )
        if exact_mask.any():
            return float(self._df.loc[exact_mask, conc_col].iloc[0])

        dose_values = np.array(sorted(tissue_block.keys()), dtype=float)
        conc_at_time: list[float] = []
        for dose_value in dose_values:
            dose_df = tissue_block[float(dose_value)]
            t = dose_df[time_col].to_numpy(dtype=float)
            y = dose_df[conc_col].to_numpy(dtype=float)
            conc_at_time.append(
                self._interpolate_time(
                    t=t,
                    y=y,
                    x_new=float(time_h),
                    method=method_time,
                    extrapolation=extrapolation,
                )
            )

        conc_at_time_array = np.asarray(conc_at_time, dtype=float)
        if len(dose_values) == 1:
            if not self.allow_single_dose_scaling and not np.isclose(dose_mg_per_kg, dose_values[0]):
                raise ValueError(
                    f"Tissue '{tissue_key}' has only one observed dose ({dose_values[0]} mg/kg); "
                    "set allow_single_dose_scaling=True to enable proportional scaling."
                )
            return float(conc_at_time_array[0] * (dose_mg_per_kg / dose_values[0]))

        return float(
            self._interpolate_dose(
                doses=dose_values,
                concentrations=conc_at_time_array,
                dose_new=float(dose_mg_per_kg),
                method=method_dose,
                extrapolation=extrapolation,
            )
        )

    def _preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        required = [
            self.schema.dose_col,
            self.schema.tissue_col,
            self.schema.time_col,
            self.schema.concentration_col,
        ]
        missing = [column for column in required if column not in df.columns]
        if missing:
            raise ValueError(f"Missing required PK columns: {missing}. Available columns: {list(df.columns)}")

        df[self.schema.tissue_col] = df[self.schema.tissue_col].astype(str).str.strip()
        for column in (self.schema.dose_col, self.schema.time_col, self.schema.concentration_col):
            df[column] = pd.to_numeric(df[column], errors="coerce")

        if df[required].isna().any().any():
            bad_rows = df[df[required].isna().any(axis=1)]
            raise ValueError(f"NaN/non-numeric values detected in PK table rows: {bad_rows.index.tolist()[:10]}")

        if (df[self.schema.dose_col] <= 0).any():
            raise ValueError("All PK doses must be strictly positive.")
        if (df[self.schema.time_col] < 0).any():
            raise ValueError("All PK time values must be non-negative.")
        if (df[self.schema.concentration_col] < 0).any():
            raise ValueError("All PK concentrations must be non-negative.")
        zero_mask = np.isclose(df[self.schema.concentration_col].to_numpy(dtype=float), 0.0, rtol=0.0, atol=1e-12)
        if zero_mask.any():
            zero_time_mask = np.isclose(df[self.schema.time_col].to_numpy(dtype=float), 0.0, rtol=0.0, atol=1e-12)
            invalid_zero_mask = zero_mask & ~zero_time_mask
            if invalid_zero_mask.any():
                raise ValueError(
                    "Zero PK concentrations are only allowed at time_h=0. "
                    "Non-zero times must remain strictly positive for stable interpolation."
                )

        dedup: pd.DataFrame = (
            df.groupby([self.schema.tissue_col, self.schema.dose_col, self.schema.time_col], as_index=False)[
                self.schema.concentration_col
            ]
            .mean()
        )
        dedup = dedup.sort_values(
            by=[self.schema.tissue_col, self.schema.dose_col, self.schema.time_col],
            kind="mergesort",
        ).reset_index(drop=True)

        for (tissue, dose), block in dedup.groupby([self.schema.tissue_col, self.schema.dose_col], sort=False):
            times = block[self.schema.time_col].to_numpy(dtype=float)
            if len(np.unique(times)) < 2:
                raise ValueError(
                    f"PK tissue '{tissue}', dose {dose} has <2 unique time points; interpolation is undefined."
                )
            if not np.all(np.diff(times) > 0):
                raise ValueError(f"PK time values must be strictly increasing within tissue='{tissue}', dose={dose}.")
        return dedup

    def _build_index(self, df: pd.DataFrame) -> dict[str, dict[float, pd.DataFrame]]:
        tissue_data: dict[str, dict[float, pd.DataFrame]] = {}
        for tissue, tissue_df in df.groupby(self.schema.tissue_col, sort=True):
            dose_map: dict[float, pd.DataFrame] = {}
            for _, dose_df in tissue_df.groupby(self.schema.dose_col, sort=True):
                dose_value = float(dose_df[self.schema.dose_col].iloc[0])
                dose_map[dose_value] = dose_df.reset_index(drop=True)
            tissue_data[str(tissue)] = dose_map
        return tissue_data

    def _validate_request(
        self,
        *,
        dose_mg_per_kg: float,
        tissue: str,
        time_h: float,
        method_time: TimeMethod,
        method_dose: DoseMethod,
        extrapolation: ExtrapolationMode,
    ) -> None:
        if not np.isfinite(dose_mg_per_kg) or dose_mg_per_kg <= 0:
            raise ValueError("dose_mg_per_kg must be a finite positive number.")
        if not np.isfinite(time_h):
            raise ValueError("time_h must be a finite number.")
        tissue_key = str(tissue).strip()
        if tissue_key not in self._tissue_data:
            raise KeyError(f"Unknown PK tissue '{tissue_key}'. Available tissues: {self.tissues}")
        if method_time not in ("linear", "cubic"):
            raise ValueError(f"Unsupported method_time={method_time}")
        if method_dose not in ("log-linear", "linear"):
            raise ValueError(f"Unsupported method_dose={method_dose}")
        if extrapolation not in ("clip", "linear", "error"):
            raise ValueError(f"Unsupported extrapolation={extrapolation}")

    def _interpolate_time(
        self,
        *,
        t: np.ndarray,
        y: np.ndarray,
        x_new: float,
        method: TimeMethod,
        extrapolation: ExtrapolationMode,
    ) -> float:
        t_min = float(np.min(t))
        t_max = float(np.max(t))
        if extrapolation == "clip":
            x_eval = float(np.clip(x_new, t_min, t_max))
        elif extrapolation == "error":
            if x_new < t_min or x_new > t_max:
                raise ValueError(f"time_h={x_new} outside [{t_min}, {t_max}]")
            x_eval = float(x_new)
        else:
            x_eval = float(x_new)

        if method == "linear":
            interpolator = interp1d(
                t,
                y,
                kind="linear",
                bounds_error=(extrapolation == "error"),
                fill_value="extrapolate" if extrapolation == "linear" else (y[0], y[-1]),
                assume_sorted=True,
            )
            return float(interpolator(x_eval))

        interpolator = PchipInterpolator(t, y, extrapolate=(extrapolation == "linear"))
        return float(interpolator(x_eval))

    def _interpolate_dose(
        self,
        *,
        doses: np.ndarray,
        concentrations: np.ndarray,
        dose_new: float,
        method: DoseMethod,
        extrapolation: ExtrapolationMode,
    ) -> float:
        d_min = float(np.min(doses))
        d_max = float(np.max(doses))
        if extrapolation == "clip":
            d_eval = float(np.clip(dose_new, d_min, d_max))
        elif extrapolation == "error":
            if dose_new < d_min or dose_new > d_max:
                raise ValueError(f"dose_mg_per_kg={dose_new} outside [{d_min}, {d_max}]")
            d_eval = float(dose_new)
        else:
            d_eval = float(dose_new)

        if method == "linear":
            interpolator = interp1d(
                doses,
                concentrations,
                kind="linear",
                bounds_error=(extrapolation == "error"),
                fill_value="extrapolate" if extrapolation == "linear" else (concentrations[0], concentrations[-1]),
                assume_sorted=True,
            )
            return float(interpolator(d_eval))

        if np.allclose(concentrations, 0.0, rtol=0.0, atol=1e-12):
            return 0.0
        if np.any(doses <= 0) or np.any(concentrations <= 0):
            raise ValueError(
                "Log-linear dose interpolation requires positive concentrations, except for the special case "
                "where all dose nodes at the requested time are exactly zero."
            )
        interpolator = interp1d(
            np.log(doses),
            np.log(concentrations),
            kind="linear",
            bounds_error=(extrapolation == "error"),
            fill_value="extrapolate"
            if extrapolation == "linear"
            else (float(np.log(concentrations[0])), float(np.log(concentrations[-1]))),
            assume_sorted=True,
        )
        return float(np.exp(interpolator(np.log(d_eval))))


@dataclass(frozen=True, slots=True)
class AntagonistPKRuntime:
    model: AntagonistPKModel
    source_xlsx: str
    sheet_name: str | int
    resolved_species: str
    regimen: str
    dose_mg_per_kg: float
    concentration_column: str
    administration_lag_h: float
    tissue_map: dict[str, str]
    method_time: TimeMethod
    method_dose: DoseMethod
    extrapolation: ExtrapolationMode
    allow_single_dose_scaling: bool

    def concentration_nm(self, tissue: str, time_h: float) -> float:
        model_time_h = float(time_h)
        if self.administration_lag_h > 0.0 and model_time_h < self.administration_lag_h:
            return 0.0
        pk_time_h = model_time_h - self.administration_lag_h
        return self.model.predict(
            dose_mg_per_kg=self.dose_mg_per_kg,
            tissue=tissue,
            time_h=pk_time_h,
            method_time=self.method_time,
            method_dose=self.method_dose,
            extrapolation=self.extrapolation,
        )

    def metadata(self) -> dict[str, object]:
        return {
            "enabled": True,
            "source_xlsx": self.source_xlsx,
            "sheet_name": self.sheet_name,
            "species": self.resolved_species,
            "regimen": self.regimen,
            "dose_mg_per_kg": self.dose_mg_per_kg,
            "concentration_column": self.concentration_column,
            "administration_lag_h": self.administration_lag_h,
            "tissue_map": dict(self.tissue_map),
            "method_time": self.method_time,
            "method_dose": self.method_dose,
            "extrapolation": self.extrapolation,
            "allow_single_dose_scaling": self.allow_single_dose_scaling,
        }

    def runtime_assumption(self) -> str:
        return (
            "XC7 concentration-time profiles are interpolated from the configured XLSX source using "
            f"time={self.method_time}, dose={self.method_dose}, extrapolation={self.extrapolation}, "
            f"species={self.resolved_species}, regimen={self.regimen}, dose={self.dose_mg_per_kg:g} mg/kg, "
            f"administration_lag_h={self.administration_lag_h:g}."
        )


def build_antagonist_pk_runtime(config: ModelConfig) -> AntagonistPKRuntime | None:
    pk_config = config.antagonist_pk
    if pk_config is None or not pk_config.enabled:
        return None

    resolved_species = pk_config.species or config.species
    if resolved_species is None:
        raise ValueError("Antagonist PK runtime requires a resolved species.")

    source_path = Path(pk_config.source_xlsx or "")
    df = pd.read_excel(source_path, sheet_name=pk_config.sheet_name)
    concentration_column = pk_config.concentration_column
    required = ["species", "regimen", "organ", "dose", "time_h", concentration_column]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required antagonist PK source columns: {missing}")

    normalized = df.loc[:, required].rename(
        columns={
            "organ": "source_tissue",
            "dose": "dose_mg_per_kg",
            concentration_column: "concentration",
        }
    )
    normalized["species"] = normalized["species"].map(_normalize_species)
    normalized["regimen"] = normalized["regimen"].map(_normalize_token)
    normalized["source_tissue"] = normalized["source_tissue"].map(_normalize_token)

    selected = normalized.loc[
        (normalized["species"] == _normalize_species(resolved_species))
        & (normalized["regimen"] == _normalize_token(pk_config.regimen))
    ].reset_index(drop=True)
    if selected.empty:
        raise ValueError(
            "No antagonist PK rows matched the requested species/regimen selection: "
            f"species={resolved_species}, regimen={pk_config.regimen}."
        )

    resolved_tissue_map = {
        tissue: _normalize_token(source_tissue)
        for tissue, source_tissue in pk_config.tissue_map.items()
    }
    missing_organs = sorted({organ for organ in resolved_tissue_map.values() if organ not in set(selected["source_tissue"])})
    if missing_organs:
        missing_display = ", ".join(missing_organs)
        raise ValueError(f"antagonist_pk.tissue_map references organs absent in the PK source: {missing_display}.")

    canonical_rows: list[pd.DataFrame] = []
    for canonical_tissue, source_tissue in resolved_tissue_map.items():
        tissue_df = selected.loc[selected["source_tissue"] == source_tissue].copy()
        tissue_df["tissue"] = canonical_tissue
        canonical_rows.append(tissue_df.loc[:, ["dose_mg_per_kg", "tissue", "time_h", "concentration"]])

    model_df = (
        pd.concat(canonical_rows, ignore_index=True)
        .sort_values(["tissue", "dose_mg_per_kg", "time_h"], kind="mergesort")
        .reset_index(drop=True)
    )
    model = AntagonistPKModel(
        model_df,
        allow_single_dose_scaling=pk_config.allow_single_dose_scaling,
    )
    return AntagonistPKRuntime(
        model=model,
        source_xlsx=str(source_path),
        sheet_name=pk_config.sheet_name,
        resolved_species=resolved_species,
        regimen=pk_config.regimen,
        dose_mg_per_kg=float(pk_config.dose_mg_per_kg),
        concentration_column=concentration_column,
        administration_lag_h=float(pk_config.administration_lag_h),
        tissue_map=resolved_tissue_map,
        method_time=pk_config.method_time,
        method_dose=pk_config.method_dose,
        extrapolation=pk_config.extrapolation,
        allow_single_dose_scaling=pk_config.allow_single_dose_scaling,
    )
