# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_model_xc7.egg-info\dependency_links.txt  dependency_links.txt

```text

```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_model_xc7.egg-info\entry_points.txt  entry_points.txt

```text
[console_scripts]
pkpd-cli = pkpd_xc7.cli.app:main
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_model_xc7.egg-info\PKG-INFO  PKG-INFO

```
Metadata-Version: 2.4
Name: pkpd-model-xc7
Version: 0.2.0
Summary: Deterministic PKPD receptor-trafficking simulation toolkit
Author: PKPD Model Team
Requires-Python: >=3.11
Description-Content-Type: text/markdown
Requires-Dist: matplotlib>=3.8
Requires-Dist: numpy>=1.26
Requires-Dist: openpyxl>=3.1
Requires-Dist: pandas>=2.2
Requires-Dist: pydantic>=2.6
Requires-Dist: pyyaml>=6.0
Requires-Dist: scipy>=1.12
Requires-Dist: typer>=0.12
Provides-Extra: dev
Requires-Dist: build>=1.2; extra == "dev"
Requires-Dist: pytest>=8.0; extra == "dev"
Requires-Dist: pytest-regtest>=0.5; extra == "dev"

# PKPD-model-for-XC7

Документация для разработчика и технического писателя: быстрый запуск, трассируемость и реестры допущений/рисков.

## Quickstart

> Ниже приведены команды для локального запуска. В репозитории сейчас нет lock-файла зависимостей, поэтому устанавливайте зависимости из вашего стандартного окружения проекта (например, `pip install -r requirements.txt`, если файл появится в вашей ветке).

### 1) Simulate

```bash
python -m src.cli.app simulate --config examples/configs/capsaicin.yaml --out runs/capsaicin_quickstart
```

Ожидаемые артефакты в `runs/capsaicin_quickstart/`:
- `simulation.csv`
- `marker_points.csv`
- `summary.csv`
- `config.used.yaml`
- `metadata.json`

### 2) Validate

```bash
python -m src.cli.app validate --run-dir runs/capsaicin_quickstart --reference report_v12_extracted/capsaicin_marker_points.csv
```

Если эталон из отчёта v12 отсутствует, это **Blocked by data**: фиксируйте блокер и не добавляйте новые механизмы обхода.

---

## Полные примеры конфигов

Ниже — два полных рабочих примера конфигов.

### Пример 1: `capsaicin.yaml`

```yaml
model_id: capsaicin_pkpd_v1
compound: capsaicin
loss_mode: huber
assumptions:
  - one_compartment_absorption_model
  - first_order_elimination
traceability:
  source_in_report: "Capsaicin pilot in-vivo study, report table 2"
  source_reference: "doi:10.0000/example-capsaicin"
  source_version: "2026-01"
time_grid: [0, 30, 60, 120, 240]
time_unit: min
initial_concentration: 0.25
concentration_unit: uM
kinetics:
  k_abs: 0.08
  k_elim: 0.015
  rate_unit: 1/min
tissues:
  - name: plasma
    volume: 2.5
    volume_unit: L
    partition_coeff: 1.0
  - name: skin
    volume: 1.2
    volume_unit: L
    partition_coeff: 3.6
plots:
  - id: plasma_curve
    title: Plasma concentration over time
    plot_type: line
    x: time
    y: plasma_concentration
    x_unit: min
    y_unit: uM
scenario_assumptions:
  dermal_absorption_multiplier: 1.15
```

### Пример 2: `compound48_80.yaml`

```yaml
model_id: compound48_80_pkpd_v2
compound: compound48_80
loss_mode: mse
assumptions:
  - instant_distribution_in_plasma
  - receptor_driven_response_proxy
traceability:
  source_in_report: "Compound 48/80 challenge dataset (internal assay A17)"
  source_reference: "lab-notebook://assay-A17"
  source_version: "2025-12"
time_grid: [0, 0.5, 1.0, 2.0, 4.0, 8.0]
time_unit: h
initial_concentration: 0.0012
concentration_unit: mM
kinetics:
  k_abs: 0.6
  k_elim: 0.11
  rate_unit: 1/h
tissues:
  - name: plasma
    volume: 2.8
    volume_unit: L
    partition_coeff: 1.0
  - name: gut
    volume: 0.9
    volume_unit: L
    partition_coeff: 0.8
plots:
  - id: activation_response
    title: Mast-cell activation proxy
    plot_type: log_line
    x: time
    y: mast_cell_activation
    x_unit: h
    y_unit: nM
```

---

## Пример `marker_points.csv` (≥10 строк)

```csv
time_h,R_surf,R_int,histamine_nm
0.0,0.880000,0.120000,250.0
0.5,0.854200,0.145800,250.0
1.0,0.831100,0.168900,250.0
1.5,0.810500,0.189500,250.0
2.0,0.792300,0.207700,250.0
2.5,0.776100,0.223900,250.0
3.0,0.761700,0.238300,250.0
3.5,0.748800,0.251200,250.0
4.0,0.737300,0.262700,250.0
4.5,0.726900,0.273100,250.0
5.0,0.717500,0.282500,250.0
```

---

## Пояснение полей `loss_mode` и `profile_id`

- `loss_mode` — обязательное поле конфига оптимизации/сопоставления; поддерживаемые значения: `mse`, `mae`, `huber`, `nll`.
- `profile_id` — в текущей схеме `ModelConfig` поле **отсутствует**. Для трассируемости профиля используйте `model_id` + `traceability.source_in_report` до появления явного поля в утверждённом ТЗ/отчёте.

Статус по `profile_id`: **Blocked by data** (входные артефакты с формальным определением поля не приложены в репозитории).
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_model_xc7.egg-info\requires.txt  requires.txt

```text
matplotlib>=3.8
numpy>=1.26
openpyxl>=3.1
pandas>=2.2
pydantic>=2.6
pyyaml>=6.0
scipy>=1.12
typer>=0.12

[dev]
build>=1.2
pytest>=8.0
pytest-regtest>=0.5
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_model_xc7.egg-info\SOURCES.txt  SOURCES.txt

```text
README.md
pyproject.toml
src/pkpd_model_xc7.egg-info/PKG-INFO
src/pkpd_model_xc7.egg-info/SOURCES.txt
src/pkpd_model_xc7.egg-info/dependency_links.txt
src/pkpd_model_xc7.egg-info/entry_points.txt
src/pkpd_model_xc7.egg-info/requires.txt
src/pkpd_model_xc7.egg-info/top_level.txt
src/pkpd_xc7/__init__.py
src/pkpd_xc7/cli/__init__.py
src/pkpd_xc7/cli/app.py
src/pkpd_xc7/config/__init__.py
src/pkpd_xc7/config/schemas.py
src/pkpd_xc7/io/__init__.py
src/pkpd_xc7/io/export.py
src/pkpd_xc7/simulation/__init__.py
src/pkpd_xc7/simulation/runner.py
tests/test_api_canonical_units.py
tests/test_api_simulation_refactor.py
tests/test_cli_smoke.py
tests/test_export_integrity.py
tests/test_fitting_deterministic.py
tests/test_formalin_params_resolve.py
tests/test_model_params_integration.py
tests/test_phase1_cli.py
tests/test_phase1_export.py
tests/test_phase1_runner_regtest.py
tests/test_phase1_schemas.py
tests/test_plot_data_snapshots.py
tests/test_receptor_trafficking_unit.py
tests/test_regression_marker_tables.py
tests/test_repro_metadata.py
tests/test_snapshots_timeseries.py
tests/test_solver_marker_interpolation.py
tests/test_unit_compare.py
tests/test_unit_reference_loader.py
tests/test_unit_rounding_spec.py
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_model_xc7.egg-info\top_level.txt  top_level.txt

```text
pkpd_xc7
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\__init__.py  __init__.py

```python

```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\cli\__init__.py  __init__.py

```python
from pkpd_xc7.cli.app import app, main

__all__ = ["app", "main"]
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\cli\app.py  app.py

```python
from __future__ import annotations

from pathlib import Path

import typer

from pkpd_xc7.config.loader import load_model_config
from pkpd_xc7.io.export import export_simulation_run
from pkpd_xc7.simulation.runner import run_experiment

app = typer.Typer(help="PKPD Model for XC7 CLI")


@app.command()
def version() -> None:
    """Print package version (second command keeps Typer multi-command mode for simulate)."""
    import importlib.metadata
    try:
        ver = importlib.metadata.version("pkpd-model-xc7")
    except importlib.metadata.PackageNotFoundError:
        ver = "unknown"
    typer.echo(f"pkpd-model-xc7 v{ver}")


@app.command()
def simulate(
    config: Path = typer.Option(
        ...,
        "--config",
        "-c",
        help="Путь к YAML конфигурации",
        exists=True,
        dir_okay=False,
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        "-o",
        help="Директория для сохранения результатов",
    ),
) -> None:
    typer.echo(f"Загрузка конфигурации: {config}")
    model_config = load_model_config(config)

    df = run_experiment(model_config)
    artifacts = export_simulation_run(df, model_config, out)

    typer.echo(f"Симуляция успешно завершена. Результаты сохранены в {artifacts.simulation_csv}")
    typer.echo(f"Meta YAML: {artifacts.meta_yaml}")
    typer.echo(f"Config SHA256: {model_config.config_sha256()}")
    typer.echo(f"Schema Version: {model_config.schema_version}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\config\__init__.py  __init__.py

```python
from pkpd_xc7.config.loader import load_model_config, load_model_config_payload
from pkpd_xc7.config.schemas import ModelConfig, PKDriver, ScenarioDriver, Traceability, TraffickingConfig

__all__ = [
    "ModelConfig",
    "PKDriver",
    "ScenarioDriver",
    "Traceability",
    "TraffickingConfig",
    "load_model_config",
    "load_model_config_payload",
]
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\config\loader.py  loader.py

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from pkpd_xc7.config.schemas import ModelConfig

SHARED_CONFIGS_FIELD = "shared_configs"


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ValueError(f"YAML config at '{path}' must be a mapping at the top level.")
    return payload


def _normalize_shared_paths(value: Any, *, path: Path) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return list(value)
    raise ValueError(
        f"Field '{SHARED_CONFIGS_FIELD}' in '{path}' must be a string path or a list of string paths."
    )


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for key, value in base.items():
        merged[key] = value
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_model_config_payload(path: Path | str, *, _seen: set[Path] | None = None) -> dict[str, Any]:
    resolved_path = Path(path).resolve()
    seen = set() if _seen is None else set(_seen)
    if resolved_path in seen:
        cycle = " -> ".join(str(item) for item in [*seen, resolved_path])
        raise ValueError(f"Cyclic shared config reference detected: {cycle}")
    seen.add(resolved_path)

    payload = _read_yaml_mapping(resolved_path)
    raw_shared = payload.pop(SHARED_CONFIGS_FIELD, None)
    shared_paths = _normalize_shared_paths(raw_shared, path=resolved_path)

    merged: dict[str, Any] = {}
    for shared_rel_path in shared_paths:
        shared_path = (resolved_path.parent / shared_rel_path).resolve()
        shared_payload = load_model_config_payload(shared_path, _seen=seen)
        merged = _deep_merge(merged, shared_payload)
    return _deep_merge(merged, payload)


def load_model_config(path: Path | str) -> ModelConfig:
    payload = load_model_config_payload(path)
    return ModelConfig.model_validate(payload)
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\config\schemas.py  schemas.py

```python
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
    hill_n: float = Field(default=1.0, gt=0)
    ec50_g_nm: float = Field(default=50.0, gt=0)
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
    hill_n: float | None = Field(default=None, gt=0)
    ec50_g_nm: float | None = Field(default=None, gt=0)
    constitutive_activity: float | None = Field(default=None, ge=0, le=1)
    h_base_nm: float | None = Field(default=None, ge=0)


class TissueOverrideConfig(BaseModel):
    trafficking: TraffickingOverrideConfig | None = None
    formalin_profile: TissueFormalinProfileOverrides | None = None


DriverAnnotated = Annotated[
    PKDriver | ScenarioDriver,
    Field(discriminator="driver_type"),
]


class ModelConfig(BaseModel):
    schema_version: str = Field(default="1.2.0", description="Версия схемы конфигурации")
    model_id: str
    compound: str
    # Симуляция по умолчанию не ветвится по loss; поле для отчётности/фиттинга (фазы 2+).
    loss_mode: str = Field(default="mse")

    traceability: Traceability

    assumptions: List[str] = Field(min_length=1)

    driver: DriverAnnotated

    trafficking: TraffickingConfig = Field(default_factory=TraffickingConfig)
    formalin_profile: FormalinProfileOverrides | None = Field(
        default=None,
        description="Опциональные overrides для scenario_id=formalin.",
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

    def config_sha256(self) -> str:
        """
        Канонический хеш конфигурации: model_dump JSON + sort_keys, не сырой YAML.
        """
        dump = self.model_dump(mode="json", exclude_unset=True)
        payload = json.dumps(dump, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\io\__init__.py  __init__.py

```python
from pkpd_xc7.io.export import (
    SimulationExportArtifacts,
    atomic_write_csv,
    atomic_write_yaml,
    build_simulation_meta,
    export_simulation_run,
)
from pkpd_xc7.io.loaders import (
    SimulationRun,
    load_simulation_meta,
    load_simulation_run,
    load_simulation_timeseries,
)

__all__ = [
    "SimulationExportArtifacts",
    "SimulationRun",
    "atomic_write_csv",
    "atomic_write_yaml",
    "build_simulation_meta",
    "export_simulation_run",
    "load_simulation_meta",
    "load_simulation_run",
    "load_simulation_timeseries",
]
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\io\export.py  export.py

```python
from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from pkpd_xc7.config.schemas import ModelConfig
from pkpd_xc7.io.layout import (
    DRIVER_ID_COL,
    DRIVER_TYPE_COL,
    SIMULATION_SCHEMA_VERSION,
    TIMESERIES_COLUMN_ORDER,
    enforce_timeseries_layout,
)
from pkpd_xc7.simulation.model_mapping import trafficking_params_by_tissue


@dataclass(frozen=True, slots=True)
class SimulationExportArtifacts:
    out_dir: Path
    simulation_csv: Path
    meta_yaml: Path


def atomic_write_csv(df: pd.DataFrame, dest_path: Path | str) -> None:
    """
    Атомарно записывает DataFrame в CSV (temp в каталоге назначения → os.replace).
    """
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(dir=dest_path.parent, suffix=".csv", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            df.to_csv(f, index=False, lineterminator="\n")
        os.replace(temp_path, dest_path)
    except Exception:
        try:
            os.remove(temp_path)
        except OSError:
            pass
        raise


def atomic_write_yaml(payload: dict[str, Any], dest_path: Path | str) -> None:
    """
    Атомарно записывает YAML (temp в каталоге назначения → os.replace).
    """
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(dir=dest_path.parent, suffix=".yaml", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            yaml.safe_dump(payload, f, sort_keys=False, allow_unicode=False)
        os.replace(temp_path, dest_path)
    except Exception:
        try:
            os.remove(temp_path)
        except OSError:
            pass
        raise


def build_simulation_meta(df: pd.DataFrame, config: ModelConfig) -> dict[str, Any]:
    """
    Build deterministic sidecar metadata for exported simulation results.
    """
    layout_df = enforce_timeseries_layout(df)
    layout_df.attrs = dict(df.attrs)
    if layout_df.empty:
        driver_type: str = config.driver.driver_type
        driver_id: str = config.driver.scenario_id if config.driver.driver_type == "scenario" else "pk_model"
    else:
        driver_type = str(layout_df[DRIVER_TYPE_COL].iloc[0])
        driver_id = str(layout_df[DRIVER_ID_COL].iloc[0])

    metadata: dict[str, Any] = {
        "config_sha256": config.config_sha256(),
        "config_schema_version": config.schema_version,
        "simulation_schema_version": SIMULATION_SCHEMA_VERSION,
        "column_order": list(TIMESERIES_COLUMN_ORDER),
        "row_count": int(len(layout_df.index)),
        "driver_type": driver_type,
        "driver_id": driver_id,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    metadata["default_trafficking_params"] = config.trafficking.model_dump()
    metadata["trafficking_params_by_tissue"] = trafficking_params_by_tissue(config)
    solver_metadata = df.attrs.get("solver_metadata")
    if solver_metadata is not None:
        metadata["solver_metadata"] = solver_metadata
    assumptions = df.attrs.get("runtime_assumptions")
    if assumptions is not None:
        metadata["runtime_assumptions"] = assumptions
    return metadata


def export_simulation_run(
    df: pd.DataFrame,
    config: ModelConfig,
    out_dir: Path | str,
) -> SimulationExportArtifacts:
    """
    Export simulation dataframe and deterministic sidecar metadata atomically.
    """
    out_dir = Path(out_dir)
    simulation_df = enforce_timeseries_layout(df)
    simulation_df.attrs = dict(df.attrs)
    artifacts = SimulationExportArtifacts(
        out_dir=out_dir,
        simulation_csv=out_dir / "simulation.csv",
        meta_yaml=out_dir / "meta.yaml",
    )
    atomic_write_csv(simulation_df, artifacts.simulation_csv)
    atomic_write_yaml(build_simulation_meta(simulation_df, config), artifacts.meta_yaml)
    return artifacts
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\io\layout.py  layout.py

```python
from __future__ import annotations

import pandas as pd

# Schema Versioning Rules:
# - MINOR bump: new columns appended at the end, or backwards-compatible metadata additions.
# - MAJOR bump: column renaming/removal, or semantics/unit changes for existing fields.
SIMULATION_SCHEMA_VERSION = "2.0.0"

TIME_H_COL = "time_h"
TISSUE_COL = "tissue"
HISTAMINE_COL = "histamine_nm"
R_SURF_COL = "R_surf"
R_INT_COL = "R_int"
G_SIGNAL_COL = "G_signal"
G_SIGNAL_PCT_COL = "G_signal_pct"
G_SIGNAL_LIGAND_COL = "G_signal_ligand"
G_SIGNAL_LIGAND_PCT_COL = "G_signal_ligand_pct"
G_SIGNAL_CONSTITUTIVE_COL = "G_signal_constitutive"
G_SIGNAL_CONSTITUTIVE_PCT_COL = "G_signal_constitutive_pct"
BETA_ARR_SIGNAL_COL = "beta_arr_signal"
BETA_ARR_SIGNAL_PCT_COL = "beta_arr_signal_pct"
INTERNALIZATION_DRIVE_COL = "internalization_drive"
K_INT_EFF_PER_H_COL = "k_int_eff_per_h"
DRIVER_TYPE_COL = "driver_type"
DRIVER_ID_COL = "driver_id"

TIMESERIES_COLUMN_ORDER: list[str] = [
    TIME_H_COL,
    TISSUE_COL,
    HISTAMINE_COL,
    R_SURF_COL,
    R_INT_COL,
    G_SIGNAL_COL,
    G_SIGNAL_PCT_COL,
    G_SIGNAL_LIGAND_COL,
    G_SIGNAL_LIGAND_PCT_COL,
    G_SIGNAL_CONSTITUTIVE_COL,
    G_SIGNAL_CONSTITUTIVE_PCT_COL,
    BETA_ARR_SIGNAL_COL,
    BETA_ARR_SIGNAL_PCT_COL,
    INTERNALIZATION_DRIVE_COL,
    K_INT_EFF_PER_H_COL,
    DRIVER_TYPE_COL,
    DRIVER_ID_COL,
]

TIMESERIES_REQUIRED_COLUMNS: tuple[str, ...] = tuple(TIMESERIES_COLUMN_ORDER)


def enforce_timeseries_layout(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and reorder exported timeseries columns deterministically."""
    missing = [column for column in TIMESERIES_REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Timeseries dataframe is missing required columns: {missing}")
    return df.loc[:, TIMESERIES_COLUMN_ORDER].copy()
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\io\loaders.py  loaders.py

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from pkpd_xc7.io.layout import enforce_timeseries_layout


@dataclass(frozen=True, slots=True)
class SimulationRun:
    run_dir: Path
    timeseries: pd.DataFrame
    meta: dict[str, Any]


def load_simulation_timeseries(path: Path | str) -> pd.DataFrame:
    """Load a simulation CSV and validate the canonical export layout."""
    csv_path = Path(path)
    df = pd.read_csv(csv_path)
    return enforce_timeseries_layout(df)


def load_simulation_meta(path: Path | str) -> dict[str, Any]:
    """Load meta.yaml and ensure it is a mapping."""
    meta_path = Path(path)
    with meta_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Simulation meta must be a mapping: {meta_path}")
    return payload


def load_simulation_run(run_dir: Path | str, *, require_trafficking_params: bool = True) -> SimulationRun:
    """Load deterministic simulation artifacts from a run directory."""
    resolved_run_dir = Path(run_dir)
    csv_path = resolved_run_dir / "simulation.csv"
    meta_path = resolved_run_dir / "meta.yaml"

    missing = [path.name for path in (csv_path, meta_path) if not path.exists()]
    if missing:
        missing_str = ", ".join(missing)
        raise FileNotFoundError(
            f"Missing required simulation artifacts in {resolved_run_dir}: {missing_str}"
        )

    timeseries = load_simulation_timeseries(csv_path)
    meta = load_simulation_meta(meta_path)
    has_resolved_params = "trafficking_params_by_tissue" in meta or "trafficking_params" in meta
    if require_trafficking_params and not has_resolved_params:
        raise KeyError(
            f"Missing 'trafficking_params_by_tissue' or legacy 'trafficking_params' in simulation meta: {meta_path}"
        )
    return SimulationRun(run_dir=resolved_run_dir, timeseries=timeseries, meta=meta)
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\models\__init__.py  __init__.py

```python

```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\models\h3_signaling.py  h3_signaling.py

```python
from __future__ import annotations

import numpy as np

from pkpd_xc7.models.receptor_trafficking import TraffickingCoreParams


def hill_activation(histamine_nm: float | np.ndarray, ec50_nm: float, hill_n: float) -> float | np.ndarray:
    """Return Hill activation in [0, 1] with a zero branch for H <= 0."""
    histamine = np.asarray(histamine_nm, dtype=float)
    positive = np.clip(histamine, 0.0, None)
    numerator = positive**hill_n
    denominator = (ec50_nm**hill_n) + numerator
    with np.errstate(divide="ignore", invalid="ignore"):
        activation = np.divide(numerator, denominator, out=np.zeros_like(positive), where=denominator > 0.0)
    if np.isscalar(histamine_nm):
        return float(activation.item())
    return activation


def constitutive_signal_fraction(
    r_surf: float | np.ndarray,
    params_or_constitutive: TraffickingCoreParams | float,
) -> float | np.ndarray:
    """Return constitutive receptor activity in [0, 1] on the report Emax scale."""
    constitutive = (
        params_or_constitutive.constitutive_activity
        if isinstance(params_or_constitutive, TraffickingCoreParams)
        else float(params_or_constitutive)
    )
    r_surf_arr = np.clip(np.asarray(r_surf, dtype=float), 0.0, 1.0)
    fraction = np.clip(constitutive * r_surf_arr, 0.0, 1.0)
    if np.isscalar(r_surf):
        return float(fraction.item())
    return fraction


def agonist_g_signal_fraction(
    histamine_nm: float | np.ndarray,
    r_surf: float | np.ndarray,
    params_or_ec50: TraffickingCoreParams | float,
    hill_n: float | None = None,
) -> float | np.ndarray:
    """Return agonist-driven G-signal fraction in [0, 1], excluding constitutive activity."""
    if isinstance(params_or_ec50, TraffickingCoreParams):
        ec50_g_nm = params_or_ec50.ec50_g_nm
        hill = params_or_ec50.hill_n
    else:
        if hill_n is None:
            raise TypeError("hill_n is required when params are not provided.")
        ec50_g_nm = float(params_or_ec50)
        hill = float(hill_n)

    activation = hill_activation(histamine_nm, ec50_g_nm, hill)
    r_surf_arr = np.clip(np.asarray(r_surf, dtype=float), 0.0, 1.0)
    fraction = np.clip(np.asarray(activation, dtype=float) * r_surf_arr, 0.0, 1.0)
    if np.isscalar(histamine_nm) and np.isscalar(r_surf):
        return float(fraction.item())
    return fraction


def beta_arr_fraction(
    histamine_nm: float | np.ndarray,
    params_or_ec50: TraffickingCoreParams | float,
    hill_n: float | None = None,
) -> float | np.ndarray:
    """Return beta-arrestin pathway activation fraction in [0, 1]."""
    if isinstance(params_or_ec50, TraffickingCoreParams):
        ec50_barr_nm = params_or_ec50.ec50_barr_nm
        hill = params_or_ec50.hill_n
    else:
        if hill_n is None:
            raise TypeError("hill_n is required when params are not provided.")
        ec50_barr_nm = float(params_or_ec50)
        hill = float(hill_n)
    return hill_activation(histamine_nm, ec50_barr_nm, hill)


def g_signaling_fraction(
    histamine_nm: float | np.ndarray,
    r_surf: float | np.ndarray,
    params_or_ec50: TraffickingCoreParams | float,
    hill_n: float | None = None,
    constitutive_activity: float | None = None,
) -> float | np.ndarray:
    """
    Return G-signal fraction in [0, 1].

    Supports both the current `TraffickingCoreParams` contract and the legacy
    explicit-parameter calling convention.
    """
    if isinstance(params_or_ec50, TraffickingCoreParams):
        ec50_g_nm = params_or_ec50.ec50_g_nm
        hill = params_or_ec50.hill_n
        constitutive = params_or_ec50.constitutive_activity
    else:
        if hill_n is None or constitutive_activity is None:
            raise TypeError("hill_n and constitutive_activity are required when params are not provided.")
        ec50_g_nm = float(params_or_ec50)
        hill = float(hill_n)
        constitutive = float(constitutive_activity)

    agonist_fraction = agonist_g_signal_fraction(histamine_nm, r_surf, ec50_g_nm, hill_n=hill)
    constitutive_fraction = constitutive_signal_fraction(r_surf, constitutive)
    fraction = np.asarray(constitutive_fraction, dtype=float) + (
        (1.0 - constitutive) * np.asarray(agonist_fraction, dtype=float)
    )
    fraction = np.clip(fraction, 0.0, 1.0)
    if np.isscalar(histamine_nm) and np.isscalar(r_surf):
        return float(fraction.item())
    return fraction


def g_signal_percent(g_signal_fraction_value: float | np.ndarray) -> float | np.ndarray:
    """Convert model-space fraction to report-space percentage."""
    value = np.asarray(g_signal_fraction_value, dtype=float) * 100.0
    if np.isscalar(g_signal_fraction_value):
        return float(value.item())
    return value
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\models\receptor_trafficking.py  receptor_trafficking.py

```python
from __future__ import annotations

from typing import NamedTuple, Sequence

import numpy as np

MODEL_RUNTIME_ASSUMPTION = "k_deg implicitly equals k_synth per ODE mass-balance invariant"


class TraffickingCoreParams(NamedTuple):
    """Lightweight immutable parameter container for the ODE hot path."""

    k_int_max_per_h: float
    k_rec_per_h: float
    k_synth_per_h: float
    ec50_barr_nm: float
    ec50_internalization_nm: float
    hill_n: float
    ec50_g_nm: float
    constitutive_activity: float = 0.0


def internalization_drive(histamine_nm: float, params: TraffickingCoreParams) -> float:
    """Return internalization driver in [0, 1]."""
    if histamine_nm <= 0.0:
        return 0.0
    ec50_nm = params.ec50_internalization_nm
    numerator = histamine_nm**params.hill_n
    denominator = (ec50_nm**params.hill_n) + numerator
    return numerator / denominator


def k_int_eff(histamine_nm: float, params: TraffickingCoreParams) -> float:
    """Return ligand-driven internalization rate in 1/h."""
    if histamine_nm <= 0.0:
        return 0.0
    return params.k_int_max_per_h * internalization_drive(histamine_nm, params)


def analytic_steady_state_fractions(k_eff_per_h: float, k_rec_per_h: float) -> tuple[float, float]:
    """Return analytic steady state on the invariant manifold R_surf + R_int = 1."""
    if k_eff_per_h < 0.0:
        raise ValueError("k_eff_per_h must be non-negative.")
    if k_rec_per_h < 0.0:
        raise ValueError("k_rec_per_h must be non-negative.")
    if k_eff_per_h == 0.0 and k_rec_per_h == 0.0:
        return (1.0, 0.0)

    denom = k_eff_per_h + k_rec_per_h
    return (k_rec_per_h / denom, k_eff_per_h / denom)


def steady_state_ic(histamine_nm: float, params: TraffickingCoreParams) -> tuple[float, float]:
    """Return analytic initial conditions at constant baseline histamine."""
    return analytic_steady_state_fractions(
        k_eff_per_h=k_int_eff(histamine_nm, params),
        k_rec_per_h=params.k_rec_per_h,
    )


def receptor_pool_balance_rhs_sum(y: Sequence[float], params: TraffickingCoreParams) -> float:
    """Return d(R_surf + R_int)/dt under the model's mass-balance assumption."""
    r_surf = max(float(y[0]), 0.0)
    r_int = max(float(y[1]), 0.0)
    return params.k_synth_per_h * (1.0 - r_surf - r_int)


def receptor_trafficking_rhs(
    t_h: float,
    y: Sequence[float],
    histamine_nm: float,
    params: TraffickingCoreParams,
    *,
    clip_state_explicit: bool = False,
    assumptions: list[str] | None = None,
) -> np.ndarray:
    """
    RHS for receptor trafficking with k_deg == k_synth mass-balance assumption.

    Negative state values are clipped before evaluating linear terms so adaptive
    solvers cannot propagate unphysical receptor fractions.
    """
    r_surf_raw = float(y[0])
    r_int_raw = float(y[1])

    r_surf = max(r_surf_raw, 0.0)
    r_int = max(r_int_raw, 0.0)

    if clip_state_explicit and assumptions is not None and (r_surf_raw < 0.0 or r_int_raw < 0.0):
        msg = f"Scenario assumption: Negative receptor state clipped at t={t_h:.3f}"
        if msg not in assumptions:
            assumptions.append(msg)

    k_eff = k_int_eff(histamine_nm, params)
    pool_repair = params.k_synth_per_h * (1.0 - r_surf - r_int)

    d_r_surf = pool_repair - (k_eff * r_surf) + (params.k_rec_per_h * r_int)
    d_r_int = (k_eff * r_surf) - (params.k_rec_per_h * r_int)
    return np.array([d_r_surf, d_r_int], dtype=float)
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\py.typed  py.typed

```

```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\simulation\__init__.py  __init__.py

```python
from pkpd_xc7.simulation.model_mapping import model_config_to_trafficking_core, runtime_assumptions
from pkpd_xc7.simulation.postprocessing import add_g_signal_columns
from pkpd_xc7.simulation.runner import run_experiment

__all__ = ["add_g_signal_columns", "model_config_to_trafficking_core", "run_experiment", "runtime_assumptions"]
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\simulation\histamine_driver.py  histamine_driver.py

```python
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
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\simulation\model_mapping.py  model_mapping.py

```python
from __future__ import annotations

from pkpd_xc7.config.schemas import ModelConfig, TraffickingConfig, TraffickingOverrideConfig
from pkpd_xc7.models.receptor_trafficking import MODEL_RUNTIME_ASSUMPTION, TraffickingCoreParams

LEGACY_PK_H_BASE_NM = 50.0


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
    For PK drivers, preserve the legacy 50 nM fallback when config does not
    specify a baseline, but surface it through meta/runtime assumptions.
    """
    trafficking = resolve_trafficking_config(config, tissue)
    if trafficking.h_base_nm is not None:
        return float(trafficking.h_base_nm)
    if config.driver.driver_type == "pk":
        return LEGACY_PK_H_BASE_NM
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
        hill_n=trafficking.hill_n,
        ec50_g_nm=trafficking.ec50_g_nm,
        constitutive_activity=trafficking.constitutive_activity,
    )


def runtime_assumptions(config: ModelConfig) -> list[str]:
    """Merge config assumptions with model-runtime assumptions deterministically."""
    merged = list(config.assumptions)
    if config.driver.driver_type == "pk":
        missing_pk_h_base = [
            tissue for tissue in config.tissues if resolve_trafficking_config(config, tissue).h_base_nm is None
        ]
        if missing_pk_h_base:
            merged.append(
                "pk driver uses legacy h_base_nm=50.0 for tissues without explicit trafficking baseline"
            )
    if MODEL_RUNTIME_ASSUMPTION not in merged:
        merged.append(MODEL_RUNTIME_ASSUMPTION)
    return merged
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\simulation\postprocessing.py  postprocessing.py

```python
from __future__ import annotations

import pandas as pd

from pkpd_xc7.io.layout import (
    BETA_ARR_SIGNAL_COL,
    BETA_ARR_SIGNAL_PCT_COL,
    G_SIGNAL_COL,
    G_SIGNAL_CONSTITUTIVE_COL,
    G_SIGNAL_CONSTITUTIVE_PCT_COL,
    G_SIGNAL_LIGAND_COL,
    G_SIGNAL_LIGAND_PCT_COL,
    G_SIGNAL_PCT_COL,
    HISTAMINE_COL,
    INTERNALIZATION_DRIVE_COL,
    K_INT_EFF_PER_H_COL,
    R_SURF_COL,
)
from pkpd_xc7.models.h3_signaling import (
    agonist_g_signal_fraction,
    beta_arr_fraction,
    constitutive_signal_fraction,
    g_signal_percent,
    g_signaling_fraction,
)
from pkpd_xc7.models.receptor_trafficking import TraffickingCoreParams, internalization_drive, k_int_eff


def add_g_signal_columns(
    df: pd.DataFrame,
    params: TraffickingCoreParams,
    *,
    histamine_col: str = HISTAMINE_COL,
    r_surf_col: str = R_SURF_COL,
) -> pd.DataFrame:
    """Add model-space and report-space G columns from receptor trajectories."""
    result = df.copy()
    histamine = result[histamine_col].to_numpy()
    r_surf = result[r_surf_col].to_numpy()
    g_signal_total = g_signaling_fraction(histamine, r_surf, params)
    g_signal_ligand = agonist_g_signal_fraction(histamine, r_surf, params)
    g_signal_constitutive = constitutive_signal_fraction(r_surf, params)
    beta_arr_signal = beta_arr_fraction(histamine, params)
    int_drive = [internalization_drive(float(h), params) for h in histamine]
    k_int_values = [k_int_eff(float(h), params) for h in histamine]

    result[G_SIGNAL_COL] = g_signal_total
    result[G_SIGNAL_PCT_COL] = g_signal_percent(g_signal_total)
    result[G_SIGNAL_LIGAND_COL] = g_signal_ligand
    result[G_SIGNAL_LIGAND_PCT_COL] = g_signal_percent(g_signal_ligand)
    result[G_SIGNAL_CONSTITUTIVE_COL] = g_signal_constitutive
    result[G_SIGNAL_CONSTITUTIVE_PCT_COL] = g_signal_percent(g_signal_constitutive)
    result[BETA_ARR_SIGNAL_COL] = beta_arr_signal
    result[BETA_ARR_SIGNAL_PCT_COL] = g_signal_percent(beta_arr_signal)
    result[INTERNALIZATION_DRIVE_COL] = int_drive
    result[K_INT_EFF_PER_H_COL] = k_int_values
    return result
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\simulation\runner.py  runner.py

```python
from __future__ import annotations

import numpy as np
import pandas as pd

from pkpd_xc7.config.schemas import ModelConfig
from pkpd_xc7.io.layout import (
    DRIVER_ID_COL,
    DRIVER_TYPE_COL,
    HISTAMINE_COL,
    R_INT_COL,
    R_SURF_COL,
    TIME_H_COL,
    TISSUE_COL,
    enforce_timeseries_layout,
)
from pkpd_xc7.models.receptor_trafficking import steady_state_ic
from pkpd_xc7.simulation.histamine_driver import resolve_histamine_nm
from pkpd_xc7.simulation.model_mapping import model_config_to_trafficking_core, runtime_assumptions
from pkpd_xc7.simulation.postprocessing import add_g_signal_columns
from pkpd_xc7.solvers.ivp import solve_trafficking_ivp
from pkpd_xc7.solvers.solve_ivp_wrapper import SolverConfig, solver_metadata_snapshot


def run_experiment(config: ModelConfig) -> pd.DataFrame:
    """
    Детерминированный расчёт системы ОДУ и траффикинга рецепторов (Фаза 3).
    """
    frames: list[pd.DataFrame] = []

    driver_id: str
    if config.driver.driver_type == "scenario":
        driver_id = config.driver.scenario_id
    else:
        driver_id = "pk_model"

    time_grid = np.asarray(config.time_grid_h, dtype=float)
    
    # Инстанцируем унифицированный конфиг решателя с параметрами Phase 3
    solver_config = SolverConfig(
        t_eval=time_grid,
        method="LSODA",
        rtol=1e-3,
        atol=1e-6,
    )
    # Забираем снапшот метаданных на этапе запуска
    solver_meta = solver_metadata_snapshot(solver_config)

    for tissue in config.tissues:
        params = model_config_to_trafficking_core(config, tissue=tissue)
        h_grid = np.array([resolve_histamine_nm(float(t), config, tissue) for t in time_grid])
        y0 = steady_state_ic(float(h_grid[0]), params)

        y_sol = solve_trafficking_ivp(time_grid, h_grid, y0, params, solver_config=solver_config, tissue=tissue)

        tissue_frame = pd.DataFrame(
            {
                TIME_H_COL: time_grid.astype(float),
                TISSUE_COL: tissue,
                HISTAMINE_COL: h_grid.astype(float),
                R_SURF_COL: y_sol[0].astype(float),
                R_INT_COL: y_sol[1].astype(float),
            }
        )
        frames.append(add_g_signal_columns(tissue_frame, params))

    df = pd.concat(frames, ignore_index=True)
    df[DRIVER_TYPE_COL] = config.driver.driver_type
    df[DRIVER_ID_COL] = driver_id
    df = enforce_timeseries_layout(df)
    df.attrs["solver_metadata"] = solver_meta
    df.attrs["runtime_assumptions"] = runtime_assumptions(config)
    return df
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\simulation\scenario_registry.py  scenario_registry.py

```python
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
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\solvers\__init__.py  __init__.py

```python
"""Deterministic solver helpers for PKPD trajectories."""

from pkpd_xc7.solvers.grids import build_marker_refined_grid, build_uniform_grid
from pkpd_xc7.solvers.solve_ivp_wrapper import SolverConfig, SolvedIvpResult, solve_ivp_wrapper, solver_metadata_snapshot

__all__ = [
    "SolverConfig",
    "SolvedIvpResult",
    "build_marker_refined_grid",
    "build_uniform_grid",
    "solve_ivp_wrapper",
    "solver_metadata_snapshot",
]
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\solvers\grids.py  grids.py

```python
from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def _round_grid(values: np.ndarray, decimals: int = 12) -> np.ndarray:
    return np.round(values.astype(float), decimals=decimals)


def build_uniform_grid(t_span_h: tuple[float, float], *, step_h: float, decimals: int = 12) -> np.ndarray:
    """Build an inclusive deterministic grid over hours."""
    if step_h <= 0.0:
        raise ValueError("step_h must be positive.")

    start_h, stop_h = t_span_h
    if stop_h < start_h:
        raise ValueError("t_span_h must be increasing.")

    count = int(np.floor((stop_h - start_h) / step_h))
    grid = start_h + (np.arange(count + 1, dtype=float) * step_h)
    if not np.isclose(grid[-1], stop_h):
        grid = np.append(grid, stop_h)
    else:
        grid[-1] = stop_h
    return _round_grid(grid, decimals)


def build_marker_refined_grid(
    t_span_h: tuple[float, float],
    *,
    base_step_h: float,
    markers: Sequence[float],
    marker_unit: str = "h",
    refine_half_window_h: float,
    refine_step_h: float,
    decimals: int = 12,
) -> np.ndarray:
    """Build a base grid plus a deterministic finer stencil around marker times."""
    grid = build_uniform_grid(t_span_h, step_h=base_step_h, decimals=decimals)
    if marker_unit == "min":
        marker_hours = np.asarray(markers, dtype=float) / 60.0
    elif marker_unit == "h":
        marker_hours = np.asarray(markers, dtype=float)
    else:
        raise ValueError("marker_unit must be 'h' or 'min'.")

    refined_parts: list[np.ndarray] = [grid]
    start_h, stop_h = t_span_h
    for marker_h in marker_hours:
        window_start = max(start_h, marker_h - refine_half_window_h)
        window_stop = min(stop_h, marker_h + refine_half_window_h)
        refined_parts.append(build_uniform_grid((window_start, window_stop), step_h=refine_step_h, decimals=decimals))
        refined_parts.append(np.array([marker_h], dtype=float))

    return _round_grid(np.unique(np.concatenate(refined_parts)), decimals)
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\solvers\ivp.py  ivp.py

```python
from __future__ import annotations

import numpy as np
from scipy.interpolate import PchipInterpolator

from pkpd_xc7.models.receptor_trafficking import (
    TraffickingCoreParams,
    receptor_trafficking_rhs,
)
from pkpd_xc7.solvers.solve_ivp_wrapper import SolverConfig, solve_ivp_wrapper


def solve_trafficking_ivp(
    time_grid_h: np.ndarray,
    histamine_grid_nm: np.ndarray,
    y0: tuple[float, float],
    params: TraffickingCoreParams,
    solver_config: SolverConfig,
    tissue: str = "unknown"
) -> np.ndarray:
    """
    Решает систему ОДУ рецепторного траффика на заданной временной сетке.
    Используется PchipInterpolator для C1-гладкой и монотонной интерполяции H(t).
    """
    h_func = PchipInterpolator(time_grid_h, histamine_grid_nm)
    
    def rhs(t: float, y: np.ndarray) -> np.ndarray:
        h_val = float(h_func(t))
        return receptor_trafficking_rhs(t, y, h_val, params)

    t_span = (float(time_grid_h[0]), float(time_grid_h[-1]))
    
    result = solve_ivp_wrapper(rhs, t_span, y0, config=solver_config)
    
    if not result.success:
        raise RuntimeError(f"IVP solver failed for tissue '{tissue}': {result.message} (t_span={t_span})")
        
    return result.y
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\solvers\solve_ivp_wrapper.py  solve_ivp_wrapper.py

```python
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
from scipy.integrate import solve_ivp


SolverMethod = Literal["LSODA", "BDF", "Radau"]


@dataclass(frozen=True, slots=True)
class SolverConfig:
    t_eval: Sequence[float]
    method: SolverMethod = "LSODA"
    rtol: float = 1e-7
    atol: float = 1e-10
    max_step: float | None = None
    marker_times_h: Sequence[float] | None = None
    marker_times_min: Sequence[float] | None = None
    include_markers_in_t_eval: bool = True
    dense_output: bool = False
    rounding_decimals: int | None = 12


@dataclass(frozen=True, slots=True)
class SolvedIvpResult:
    t: np.ndarray
    y: np.ndarray
    success: bool
    message: str
    status: int
    nfev: int
    marker_t: np.ndarray
    marker_y: np.ndarray


def _to_marker_hours(config: SolverConfig) -> np.ndarray:
    markers: list[np.ndarray] = []
    if config.marker_times_h:
        markers.append(np.asarray(config.marker_times_h, dtype=float))
    if config.marker_times_min:
        markers.append(np.asarray(config.marker_times_min, dtype=float) / 60.0)
    if not markers:
        return np.array([], dtype=float)
    return np.unique(np.concatenate(markers))


def _round_array(values: np.ndarray, decimals: int | None) -> np.ndarray:
    if decimals is None:
        return values
    return np.round(values.astype(float), decimals=decimals)


def solver_metadata_snapshot(config: SolverConfig) -> dict[str, Any]:
    return {
        "solver_method": config.method,
        "rtol": config.rtol,
        "atol": config.atol,
        "max_step": config.max_step,
    }


def solve_ivp_wrapper(
    rhs: Callable[..., np.ndarray],
    t_span: tuple[float, float],
    y0: Sequence[float],
    config: SolverConfig,
    args: Sequence[Any] = (),
) -> SolvedIvpResult:
    t_eval = np.asarray(config.t_eval, dtype=float)
    marker_t = _to_marker_hours(config)
    solve_t_eval = t_eval
    if config.include_markers_in_t_eval and marker_t.size:
        solve_t_eval = np.unique(np.concatenate([t_eval, marker_t]))

    solve_kwargs: dict[str, Any] = {
        "method": config.method,
        "t_eval": solve_t_eval,
        "dense_output": config.dense_output or bool(marker_t.size and not config.include_markers_in_t_eval),
        "rtol": config.rtol,
        "atol": config.atol,
        "args": tuple(args),
    }
    if config.max_step is not None:
        solve_kwargs["max_step"] = config.max_step

    solved = solve_ivp(rhs, t_span, np.asarray(y0, dtype=float), **solve_kwargs)

    result_t = _round_array(np.asarray(solved.t, dtype=float), config.rounding_decimals)
    result_y = _round_array(np.asarray(solved.y, dtype=float), config.rounding_decimals)

    if marker_t.size == 0:
        marker_y = np.empty((result_y.shape[0], 0), dtype=float)
    elif config.include_markers_in_t_eval:
        marker_index = np.searchsorted(result_t, _round_array(marker_t, config.rounding_decimals))
        marker_y = result_y[:, marker_index]
    elif solved.sol is not None:
        marker_y = np.asarray(solved.sol(marker_t), dtype=float)
    else:
        marker_y = np.vstack([np.interp(marker_t, result_t, row) for row in result_y])

    marker_t = _round_array(marker_t, config.rounding_decimals)
    marker_y = _round_array(marker_y, config.rounding_decimals)

    return SolvedIvpResult(
        t=result_t,
        y=result_y,
        success=bool(solved.success),
        message=str(solved.message),
        status=int(solved.status),
        nfev=int(getattr(solved, "nfev", 0)),
        marker_t=marker_t,
        marker_y=marker_y,
    )
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\validation\__init__.py  __init__.py

```python
from __future__ import annotations

from .compare import apply_rounding_spec
from .rounding_spec import RoundingSpec

__all__ = ["apply_rounding_spec", "RoundingSpec"]
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\validation\compare.py  compare.py

```python
from __future__ import annotations

import pandas as pd

from pkpd_xc7.validation.rounding_spec import RoundingSpec


def apply_rounding_spec(df: pd.DataFrame, spec: RoundingSpec) -> pd.DataFrame:
    """Apply deterministic rounding to a dataframe based on the specification."""
    rounded = df.copy()
    for col in rounded.columns:
        if pd.api.types.is_numeric_dtype(rounded[col]):
            decimals = spec.decimals.get(col, spec.default_decimals)
            rounded[col] = rounded[col].round(decimals)
    return rounded
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\validation\rounding_spec.py  rounding_spec.py

```python
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RoundingSpec:
    """Specification for deterministic rounding in validation snapshots."""

    decimals: dict[str, int] = field(default_factory=dict)
    default_decimals: int = 2

    @classmethod
    def from_model(cls, model_key: str) -> RoundingSpec:
        """Create a rounding specification for a specific experimental model."""
        if model_key == "formalin":
            return cls(
                decimals={
                    "histamine_nm": 1,
                    "R_surf": 1,
                    "R_int": 1,
                    "G_signal": 1,
                    "G_signal_pct": 1,
                    "G_signal_ligand": 1,
                    "G_signal_ligand_pct": 1,
                    "G_signal_constitutive": 1,
                    "G_signal_constitutive_pct": 1,
                    "beta_arr_signal": 2,
                    "beta_arr_signal_pct": 2,
                    "internalization_drive": 2,
                    "k_int_eff_per_h": 2,
                    "loss": 1,
                }
            )
        if model_key == "hot_plate":
            return cls(
                decimals={
                    "histamine_nm": 1,
                    "R_surf": 2,
                    "R_int": 2,
                    "G_signal": 2,
                    "G_signal_pct": 2,
                    "G_signal_ligand": 2,
                    "G_signal_ligand_pct": 2,
                    "G_signal_constitutive": 2,
                    "G_signal_constitutive_pct": 2,
                    "beta_arr_signal": 2,
                    "beta_arr_signal_pct": 2,
                    "internalization_drive": 2,
                    "k_int_eff_per_h": 2,
                    "loss": 2,
                }
            )
        if model_key == "capsaicin":
            return cls(
                decimals={
                    "histamine_nm": 1,
                }
            )
        return cls()
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\viz\__init__.py  __init__.py

```python
from pkpd_xc7.viz.time_axis import time_minutes_from_hours
from pkpd_xc7.viz.panels import ScenarioFigureArtifacts, ScenarioPlotSpec, plot_scenario_run_figures

__all__ = [
    "ScenarioFigureArtifacts",
    "ScenarioPlotSpec",
    "plot_scenario_run_figures",
    "time_minutes_from_hours",
]
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\viz\panels.py  panels.py

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pkpd_xc7.io.layout import (
    G_SIGNAL_CONSTITUTIVE_PCT_COL,
    G_SIGNAL_PCT_COL,
    HISTAMINE_COL,
    R_INT_COL,
    R_SURF_COL,
    TIME_H_COL,
    TISSUE_COL,
)
from pkpd_xc7.io.loaders import SimulationRun
from pkpd_xc7.models.h3_signaling import g_signal_percent, g_signaling_fraction
from pkpd_xc7.viz.time_axis import apply_time_axis, time_minutes_from_hours

FIGURE_DPI = 180
SPINAL_LABEL = "Спинной мозг"
TISSUE_LABELS: dict[str, str] = {
    "skin": "Кожа",
    "spinal": SPINAL_LABEL,
    "spinal_cord": SPINAL_LABEL,
    "spinal_coord": SPINAL_LABEL,
    "ganglia": "Симп. ганглии",
    "brain": "Головной мозг",
    "muscle": "Мышца",
    "peritoneum": "Брюшина",
}
TISSUE_COLORS: dict[str, str] = {
    "skin": "#d62728",
    "spinal": "#1f77b4",
    "spinal_cord": "#1f77b4",
    "spinal_coord": "#1f77b4",
    "ganglia": "#2ca02c",
    "brain": "#9467bd",
    "muscle": "#8c564b",
    "peritoneum": "#ff7f0e",
}
EC50_COLOR = "#888888"
CA_COLOR = "#aaaaaa"
FILL_ALPHA = 0.15


@dataclass(frozen=True, slots=True)
class ScenarioPlotSpec:
    figure_group: int
    file_stem: str
    model_title: str
    tissue_order: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ScenarioFigureArtifacts:
    out_dir: Path
    histamine_png: Path
    receptor_png: Path
    g_signal_png: Path


def _extract_trafficking_params_by_tissue(run: SimulationRun) -> dict[str, Mapping[str, Any]]:
    payload = run.meta.get("trafficking_params_by_tissue")
    if isinstance(payload, Mapping):
        resolved: dict[str, Mapping[str, Any]] = {}
        for tissue, params in payload.items():
            if not isinstance(params, Mapping):
                raise ValueError("Simulation meta 'trafficking_params_by_tissue' must map tissues to parameter mappings.")
            resolved[str(tissue)] = params
        return resolved

    legacy_payload = run.meta.get("trafficking_params")
    if isinstance(legacy_payload, Mapping):
        tissues = tuple(dict.fromkeys(run.timeseries[TISSUE_COL].astype(str).tolist()))
        return dict.fromkeys(tissues, legacy_payload)

    raise ValueError("Simulation meta must include 'trafficking_params_by_tissue' or legacy 'trafficking_params'.")


def _params_for_tissue(params_by_tissue: Mapping[str, Mapping[str, Any]], tissue: str) -> Mapping[str, Any]:
    if tissue not in params_by_tissue:
        allowed = ", ".join(sorted(params_by_tissue))
        raise KeyError(f"Missing trafficking params for tissue '{tissue}'. Expected one of: {allowed}")
    return params_by_tissue[tissue]


def _get_float_param(params: Mapping[str, Any], key: str) -> float:
    if key not in params:
        raise KeyError(f"Missing required trafficking parameter for plotting: {key}")
    return float(params[key])


def _tissue_label(tissue: str) -> str:
    return TISSUE_LABELS.get(tissue, tissue.replace("_", " ").title())


def _tissue_color(tissue: str) -> str:
    return TISSUE_COLORS.get(tissue, "#4c4c4c")


def _format_peak_label(value: float, unit: str, time_min: float, *, decimals: int) -> str:
    unit_suffix = unit if unit == "%" else f" {unit}"
    return f"{value:.{decimals}f}{unit_suffix} ({time_min:.0f}мин)"


def _iter_tissue_frames(df: pd.DataFrame, preferred_order: Sequence[str]) -> list[tuple[str, pd.DataFrame]]:
    present = list(dict.fromkeys(df[TISSUE_COL].astype(str).tolist()))
    ordered = [tissue for tissue in preferred_order if tissue in present]
    ordered.extend(tissue for tissue in present if tissue not in ordered)
    frames: list[tuple[str, pd.DataFrame]] = []
    for tissue in ordered:
        tissue_df = (
            df.loc[df[TISSUE_COL] == tissue]
            .sort_values(TIME_H_COL, kind="stable")
            .reset_index(drop=True)
        )
        if not tissue_df.empty:
            frames.append((tissue, tissue_df))
    return frames


def _make_axes(count: int) -> tuple[Figure, tuple[Axes, ...]]:
    fig, axes = plt.subplots(1, count, figsize=(5.0 * count, 4.5), sharey=False)
    if isinstance(axes, np.ndarray):
        return fig, tuple(axes.tolist())
    return fig, (axes,)


def _style_axis(ax: Axes, x_max: float, ylabel: str, title: str) -> None:
    ax.set_xlabel("Время (мин)")
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.set_xlim(0.0, x_max)
    apply_time_axis(ax, x_max)
    ax.tick_params(labelsize=8)
    ax.tick_params(axis="x", which="minor", length=2.5)
    ax.grid(True, axis="y", which="major", linestyle="--", linewidth=0.4, alpha=0.5)
    ax.grid(True, axis="x", which="major", linestyle="--", linewidth=0.4, alpha=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _save_figure(fig: Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)


def _g_signal_plot_series(
    tissue_df: pd.DataFrame,
    *,
    ec50_g_nm: float,
    hill_n: float,
    constitutive_activity: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    histamine_nm = tissue_df[HISTAMINE_COL].to_numpy(dtype=float)
    r_surf = tissue_df[R_SURF_COL].to_numpy(dtype=float)

    g_with_payload = tissue_df.get(G_SIGNAL_PCT_COL)
    if g_with_payload is None:
        g_with_pct = g_signal_percent(
            g_signaling_fraction(
                histamine_nm,
                r_surf,
                ec50_g_nm,
                hill_n=hill_n,
                constitutive_activity=constitutive_activity,
            )
        )
    else:
        g_with_pct = g_with_payload.to_numpy(dtype=float)

    g_constitutive_payload = tissue_df.get(G_SIGNAL_CONSTITUTIVE_PCT_COL)
    if g_constitutive_payload is None:
        g_constitutive_pct = g_signal_percent(np.clip(constitutive_activity * r_surf, 0.0, 1.0))
    else:
        g_constitutive_pct = g_constitutive_payload.to_numpy(dtype=float)

    g_without_pct = g_signal_percent(
        g_signaling_fraction(
            histamine_nm,
            np.ones_like(r_surf),
            ec50_g_nm,
            hill_n=hill_n,
            constitutive_activity=constitutive_activity,
        )
    )
    return (
        np.asarray(g_with_pct, dtype=float),
        np.asarray(g_without_pct, dtype=float),
        np.asarray(g_constitutive_pct, dtype=float),
    )


def plot_scenario_run_figures(
    run: SimulationRun,
    spec: ScenarioPlotSpec,
    *,
    out_dir: Path | str,
) -> ScenarioFigureArtifacts:
    """Render the canonical three-panel report figures for a simulation run."""
    params_by_tissue = _extract_trafficking_params_by_tissue(run)

    tissues = _iter_tissue_frames(run.timeseries, spec.tissue_order)
    if not tissues:
        raise ValueError("Simulation timeseries is empty; cannot render figures.")

    resolved_out_dir = Path(out_dir)
    x_max = float(
        np.max(time_minutes_from_hours(run.timeseries[TIME_H_COL].to_numpy(dtype=float)))
    )

    histamine_png = resolved_out_dir / f"fig{spec.figure_group}_1_{spec.file_stem}_histamine.png"
    receptor_png = (
        resolved_out_dir / f"fig{spec.figure_group}_2_{spec.file_stem}_internalization.png"
    )
    g_signal_png = resolved_out_dir / f"fig{spec.figure_group}_3_{spec.file_stem}_gsignaling.png"

    fig_histamine, axes_histamine = _make_axes(len(tissues))
    for ax, (tissue, tissue_df) in zip(axes_histamine, tissues):
        traffic = _params_for_tissue(params_by_tissue, tissue)
        ec50_g_nm = _get_float_param(traffic, "ec50_g_nm")
        ec50_barr_nm = _get_float_param(traffic, "ec50_barr_nm")
        time_min = time_minutes_from_hours(tissue_df[TIME_H_COL].to_numpy(dtype=float))
        histamine_nm = tissue_df[HISTAMINE_COL].to_numpy(dtype=float)
        histamine_um = histamine_nm / 1000.0
        color = _tissue_color(tissue)
        label = _tissue_label(tissue)
        base_um = histamine_um[0]

        ax.plot(time_min, histamine_um, color=color, linewidth=2.0)
        ax.axhline(ec50_g_nm / 1000.0, color=EC50_COLOR, linestyle="--", linewidth=1.0, label="EC50(G)")
        ax.axhline(
            ec50_barr_nm / 1000.0,
            color=EC50_COLOR,
            linestyle=":",
            linewidth=1.0,
            label="EC50(β-arr)",
        )
        ax.axhline(base_um, color=color, linestyle=":", linewidth=0.8, alpha=0.5)

        peak_idx = int(np.argmax(histamine_um))
        ax.annotate(
            _format_peak_label(histamine_um[peak_idx], "мкМ", time_min[peak_idx], decimals=2),
            xy=(time_min[peak_idx], histamine_um[peak_idx]),
            xytext=(time_min[peak_idx], histamine_um[peak_idx] * 0.82 if histamine_um[peak_idx] > 0 else 0.02),
            fontsize=7.5,
            color=color,
            arrowprops={"arrowstyle": "->", "color": color, "lw": 0.7},
        )
        ax.annotate(
            f"База: {base_um:.3f} мкМ",
            xy=(x_max, base_um),
            ha="right",
            va="bottom",
            fontsize=7.5,
            color="#555555",
        )
        _style_axis(ax, x_max, "Концентрация (мкМ)", label)
        ax.legend(fontsize=7.5, loc="upper right", framealpha=0.8)
    # Figure-level title intentionally disabled.
    # fig_histamine.suptitle(
    #     f"Рис. {spec.figure_group}.1. Динамика концентрации гистамина — {spec.model_title}",
    #     fontsize=10,
    #     fontweight="bold",
    #     y=1.02,
    # )
    _save_figure(fig_histamine, histamine_png)

    fig_receptor, axes_receptor = _make_axes(len(tissues))
    for ax, (tissue, tissue_df) in zip(axes_receptor, tissues):
        time_min = time_minutes_from_hours(tissue_df[TIME_H_COL].to_numpy(dtype=float))
        r_surf_pct = tissue_df[R_SURF_COL].to_numpy(dtype=float) * 100.0
        r_int_pct = tissue_df[R_INT_COL].to_numpy(dtype=float) * 100.0
        color = _tissue_color(tissue)
        label = _tissue_label(tissue)

        ax.plot(time_min, r_surf_pct, color=color, linewidth=2.0, label="На поверхности (R_surf)")
        ax.plot(
            time_min,
            r_int_pct,
            color=color,
            linewidth=1.5,
            linestyle="--",
            label="В эндосомах (R_int)",
        )
        ax.fill_between(time_min, 0.0, r_int_pct, alpha=FILL_ALPHA, color=color)

        peak_idx = int(np.argmax(r_int_pct))
        ax.annotate(
            _format_peak_label(r_int_pct[peak_idx], "%", time_min[peak_idx], decimals=1),
            xy=(time_min[peak_idx], r_int_pct[peak_idx]),
            xytext=(time_min[peak_idx], min(r_int_pct[peak_idx] + 5.0, 100.0)),
            fontsize=7.5,
            color=color,
            arrowprops={"arrowstyle": "->", "color": color, "lw": 0.7},
        )
        ax.annotate(
            f"{r_surf_pct[-1]:.1f}%",
            xy=(x_max, r_surf_pct[-1]),
            ha="right",
            va="bottom",
            fontsize=7.5,
            color=color,
        )
        _style_axis(ax, x_max, "Рецепторы H3R (% от общего пула)", label)
        ax.set_ylim(-1.0, 105.0)
        ax.legend(fontsize=7.5, loc="lower right", framealpha=0.8)
    # Figure-level title intentionally disabled.
    # fig_receptor.suptitle(
    #     f"Рис. {spec.figure_group}.2. Интернализация и ресайклинг H3R — {spec.model_title}",
    #     fontsize=10,
    #     fontweight="bold",
    #     y=1.02,
    # )
    _save_figure(fig_receptor, receptor_png)

    fig_g_signal, axes_g_signal = _make_axes(len(tissues))
    for ax, (tissue, tissue_df) in zip(axes_g_signal, tissues):
        traffic = _params_for_tissue(params_by_tissue, tissue)
        ec50_g_nm = _get_float_param(traffic, "ec50_g_nm")
        hill_n = _get_float_param(traffic, "hill_n")
        constitutive_activity = _get_float_param(traffic, "constitutive_activity")
        time_min = time_minutes_from_hours(tissue_df[TIME_H_COL].to_numpy(dtype=float))
        g_with_pct, g_without_pct, g_constitutive_pct = _g_signal_plot_series(
            tissue_df,
            ec50_g_nm=ec50_g_nm,
            hill_n=hill_n,
            constitutive_activity=constitutive_activity,
        )
        color = _tissue_color(tissue)
        label = _tissue_label(tissue)

        ax.plot(
            time_min,
            g_without_pct,
            color=color,
            linewidth=1.5,
            linestyle=":",
            label="Без интернализации",
        )
        ax.plot(
            time_min,
            g_with_pct,
            color=color,
            linewidth=2.0,
            linestyle="-",
            label="С интернализацией",
        )
        ax.plot(
            time_min,
            g_constitutive_pct,
            color=CA_COLOR,
            linewidth=1.0,
            linestyle="--",
            label="Конститутивная акт.",
        )
        ax.fill_between(time_min, g_with_pct, g_without_pct, alpha=FILL_ALPHA, color=color)

        peak_idx = int(np.argmax(g_with_pct))
        ax.annotate(
            _format_peak_label(g_with_pct[peak_idx], "%", time_min[peak_idx], decimals=1),
            xy=(time_min[peak_idx], g_with_pct[peak_idx]),
            xytext=(time_min[peak_idx], max(g_with_pct[peak_idx] - 10.0, 2.0)),
            fontsize=7.5,
            color=color,
            arrowprops={"arrowstyle": "->", "color": color, "lw": 0.7},
        )
        ax.annotate(
            f"{g_with_pct[-1]:.1f}%",
            xy=(x_max, g_with_pct[-1]),
            ha="right",
            va="top",
            fontsize=7.5,
            color=color,
        )
        _style_axis(ax, x_max, "G-сигналинг H3R (% Emax)", label)
        ax.set_ylim(0.0, 105.0)
        ax.legend(fontsize=7.5, loc="upper right", framealpha=0.8)
    # Figure-level title intentionally disabled.
    # fig_g_signal.suptitle(
    #     f"Рис. {spec.figure_group}.3. G-сигналинг H3R с учётом интернализации — {spec.model_title}",
    #     fontsize=10,
    #     fontweight="bold",
    #     y=1.02,
    # )
    _save_figure(fig_g_signal, g_signal_png)

    return ScenarioFigureArtifacts(
        out_dir=resolved_out_dir,
        histamine_png=histamine_png,
        receptor_png=receptor_png,
        g_signal_png=g_signal_png,
    )
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\src\pkpd_xc7\viz\time_axis.py  time_axis.py

```python
from __future__ import annotations

from typing import TypeVar, cast

import numpy as np
import pandas as pd
from matplotlib.axes import Axes

TimeLike = TypeVar("TimeLike", float, np.ndarray, pd.Series)
TIME_AXIS_STEP_MIN = 15.0
TIME_AXIS_LABELED_MINUTES = (30.0, 60.0, 120.0, 240.0, 360.0, 480.0, 720.0, 1440.0)


def time_minutes_from_hours(time_h: TimeLike) -> TimeLike:
    """Convert model time in hours to report time in minutes."""
    if isinstance(time_h, pd.Series):
        minutes_series = (time_h.astype(float) * 60.0).rename(time_h.name)
        return cast(TimeLike, minutes_series)
    if np.isscalar(time_h):
        return cast(TimeLike, float(np.asarray(time_h, dtype=float).item()) * 60.0)
    return cast(TimeLike, np.asarray(time_h, dtype=float) * 60.0)


def time_axis_tick_positions(x_max_min: float) -> np.ndarray:
    """Return 15-minute tick positions up to the visible axis maximum."""
    safe_x_max = max(float(x_max_min), 0.0)
    tick_count = int(np.floor(safe_x_max / TIME_AXIS_STEP_MIN))
    return np.arange(tick_count + 1, dtype=float) * TIME_AXIS_STEP_MIN


def time_axis_tick_labels(tick_positions: np.ndarray) -> list[str]:
    """Label only the canonical report time markers requested for figures."""
    labeled_minutes = {int(value) for value in TIME_AXIS_LABELED_MINUTES}
    labels: list[str] = []
    for tick in tick_positions:
        tick_min = int(round(float(tick)))
        if tick_min in labeled_minutes:
            labels.append(str(tick_min))
        else:
            labels.append("")
    return labels


def labeled_time_axis_tick_positions(x_max_min: float) -> np.ndarray:
    """Return only the canonical labeled positions that fit in the visible range."""
    tick_positions = time_axis_tick_positions(x_max_min)
    labeled_minutes = {int(value) for value in TIME_AXIS_LABELED_MINUTES}
    return np.asarray(
        [tick for tick in tick_positions if int(round(float(tick))) in labeled_minutes],
        dtype=float,
    )


def apply_time_axis(ax: Axes, x_max_min: float) -> None:
    """Apply the canonical 15-minute time axis to a Matplotlib axes."""
    tick_positions = time_axis_tick_positions(x_max_min)
    labeled_positions = labeled_time_axis_tick_positions(x_max_min)
    labeled_minutes = {int(value) for value in TIME_AXIS_LABELED_MINUTES}
    minor_positions = np.asarray(
        [tick for tick in tick_positions if int(round(float(tick))) not in labeled_minutes],
        dtype=float,
    )

    ax.set_xticks(labeled_positions)
    ax.set_xticklabels(time_axis_tick_labels(labeled_positions))
    ax.set_xticks(minor_positions, minor=True)
```
