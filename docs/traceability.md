# Traceability Matrix

Цель: связать поля текущего `ModelConfig` и экспортируемые sidecar-метаданные с модулем, где они валидируются, нормализуются и используются в runtime.

## Формат

`параметр → как фиксируется источник → модуль`

## Конфигурация симуляции

| Параметр | Как фиксируется источник | Модуль(и) |
|---|---|---|
| `model_id` | В составе YAML; источник задаётся через `traceability.source_in_report` | `src/pkpd_xc7/config/schemas.py` (`ModelConfig`) |
| `compound` | То же | `src/pkpd_xc7/config/schemas.py` |
| `loss_mode` | То же | `src/pkpd_xc7/config/schemas.py` |
| `traceability.source_in_report` | Обязательное непустое поле | `src/pkpd_xc7/config/schemas.py` (`Traceability`) |
| `traceability.source_reference` | Опциональная ссылка на DOI / внутренний источник | `src/pkpd_xc7/config/schemas.py` |
| `traceability.source_version` | Опциональная версия источника | `src/pkpd_xc7/config/schemas.py` |
| `assumptions[]` | Явные текстовые допущения, минимум одна непустая строка | `src/pkpd_xc7/config/schemas.py`; `src/pkpd_xc7/simulation/model_mapping.py` (`runtime_assumptions`) |
| `driver.driver_type` | Ветка `pk` или `scenario` | `src/pkpd_xc7/config/schemas.py`; `src/pkpd_xc7/simulation/histamine_driver.py`; `src/pkpd_xc7/simulation/runner.py` |
| `driver.scenario_id` | Канонический scenario id либо нормализуемый alias | `src/pkpd_xc7/config/schemas.py`; `src/pkpd_xc7/simulation/scenario_registry.py` |
| `driver.profile_shape` | Опциональная подсказка формы H(t) | `src/pkpd_xc7/config/schemas.py`; `src/pkpd_xc7/simulation/scenario_registry.py` |
| `driver.dose`, `driver.k_abs_per_h`, `driver.k_elim_per_h` | PK-ветка H(t) | `src/pkpd_xc7/config/schemas.py`; `src/pkpd_xc7/simulation/histamine_driver.py` |
| `trafficking.*` | Базовые параметры trafficking для всех тканей | `src/pkpd_xc7/config/schemas.py`; `src/pkpd_xc7/simulation/model_mapping.py`; `src/pkpd_xc7/models/receptor_trafficking.py` |
| `tissue_overrides.<tissue>.trafficking.*` | Tissue-specific override поверх общего baseline | `src/pkpd_xc7/config/schemas.py`; `src/pkpd_xc7/simulation/model_mapping.py` |
| `formalin_profile.*` | Top-level override только для `scenario_id: formalin` | `src/pkpd_xc7/config/schemas.py`; `src/pkpd_xc7/simulation/scenario_registry.py` |
| `tissue_overrides.<tissue>.formalin_profile.*` | Tissue-specific formalin override | `src/pkpd_xc7/config/schemas.py`; `src/pkpd_xc7/simulation/scenario_registry.py` |
| `tissues[]` | Явный список прогоняемых тканей | `src/pkpd_xc7/config/schemas.py`; `src/pkpd_xc7/simulation/runner.py` |
| `time_grid_h` | Каноническая временная сетка в часах | `src/pkpd_xc7/config/schemas.py`; `src/pkpd_xc7/simulation/runner.py` |
| `time_grid + time_unit` | Входная форма, нормализуемая в `time_grid_h` | `src/pkpd_xc7/config/schemas.py` |

## Реестр и runtime-ограничения

- Источник истины для scenario-driven H(t): `src/pkpd_xc7/simulation/scenario_registry.py`.
- Разрешение ветки `pk`/`scenario`: `src/pkpd_xc7/simulation/histamine_driver.py`.
- В текущем runtime канонический CNS tissue id для сценариев: `spinal_coord`; legacy alias `spinal` нормализуется в `ModelConfig` при загрузке YAML.
- `brain` зарегистрирован как временный proxy-профиль, синхронизированный с `spinal_coord` до появления отдельного source-backed runtime-профиля.

## Экспортируемые метаданные прогона

После `export_simulation_run()` sidecar `meta.yaml` собирается из текущего конфига и timeseries:

| Поле `meta.yaml` | Источник | Модуль(и) |
|---|---|---|
| `config_sha256` | Канонический JSON-хеш `ModelConfig` | `src/pkpd_xc7/config/schemas.py` (`config_sha256`) |
| `config_schema_version` | `ModelConfig.schema_version` | `src/pkpd_xc7/config/schemas.py`; `src/pkpd_xc7/io/export.py` |
| `simulation_schema_version` | Версия layout timeseries | `src/pkpd_xc7/io/layout.py`; `src/pkpd_xc7/io/export.py` |
| `column_order` | Канонический порядок колонок timeseries | `src/pkpd_xc7/io/layout.py`; `src/pkpd_xc7/io/export.py` |
| `row_count` | Длина экспортируемого DataFrame | `src/pkpd_xc7/io/export.py` |
| `driver_type`, `driver_id` | Разрешённая ветка и идентификатор драйвера | `src/pkpd_xc7/simulation/runner.py`; `src/pkpd_xc7/io/export.py` |
| `generated_at_utc` | UTC timestamp без микросекунд | `src/pkpd_xc7/io/export.py` |
| `default_trafficking_params` | Базовый блок `config.trafficking` | `src/pkpd_xc7/io/export.py` |
| `trafficking_params_by_tissue` | Детерминированно разрешённые tissue overrides | `src/pkpd_xc7/simulation/model_mapping.py`; `src/pkpd_xc7/io/export.py` |
| `solver_metadata` | Снимок solver config из `DataFrame.attrs` | `src/pkpd_xc7/solvers/solve_ivp_wrapper.py`; `src/pkpd_xc7/simulation/runner.py`; `src/pkpd_xc7/io/export.py` |
| `runtime_assumptions` | `assumptions` + runtime invariant model | `src/pkpd_xc7/simulation/model_mapping.py`; `src/pkpd_xc7/io/export.py` |

## Примечание

В актуальном пакете не используются legacy-поля `initial_concentration`, `concentration_unit`, `kinetics`, `plots`, `scenario_assumptions`, а также старые пути `src/api.py` и `src/histamine_profiles.py`. Если они встречаются в старых документах или тестах, это признак незавершённой миграции.
