# Traceability Matrix

Цель: связать параметры модели с источником из отчёта (`source_in_report`) и модулем, где параметр используется/валидируется.

## Формат

`параметр → source_in_report → модуль`

## Матрица

| Параметр | Как фиксируется источник (`source_in_report`) | Модуль(и) |
|---|---|---|
| `model_id` | В составе конфига; источник задаётся через `traceability.source_in_report` | `src/config/schemas.py` (`ModelConfig`) |
| `compound` | То же | `src/config/schemas.py` |
| `loss_mode` | То же | `src/config/schemas.py` (`LossMode`, `ModelConfig`); наследуется в `FitSpec` для legacy `least_squares(loss=...)` |
| `parameter_resolution` | То же | `src/config/schemas.py` (`ParameterResolutionMode`); `fixed_params_only` по умолчанию |
| `histamine_profile` | То же | `src/config/schemas.py` → `src/models/receptor_trafficking.py` (`build_model_params`) → `src/histamine_profiles.py` |
| `trafficking` | То же | `src/config/schemas.py` → `src/models/receptor_trafficking.py` (`build_model_params`) |
| `plot_proxy` | То же | `src/config/schemas.py`; EC50 для G_signal через `effective_g_signal_ec50_nm` |
| `formalin_profile` | То же | `src/config/schemas.py` → `src/histamine_profiles.py` (`resolve_formalin_params_from_model_config`) |
| `parameter_source` / `optimization_applied` | Пишутся в `metadata.json` / `meta.yaml` после прогона | `src/repro/metadata.py`, `src/api.py` |
| `assumptions[]` | То же | `src/config/schemas.py` (валидация непустых строк) |
| `time_grid`, `time_unit` | То же | `src/config/schemas.py`; используется в `src/api.py` при вызове solve_ivp |
| `initial_concentration`, `concentration_unit` | То же | `src/config/schemas.py`; используется в `src/api.py` |
| `kinetics.*` | То же | `src/config/schemas.py` |
| `tissues[]` | То же | `src/config/schemas.py` |
| `plots[]` | То же | `src/config/schemas.py` |
| `scenario_assumptions` | То же | `src/config/schemas.py` |
| `traceability.source_in_report` | Обязательное поле (min_length + non-empty) | `src/config/schemas.py` |
| `traceability.source_reference` | Опционально | `src/config/schemas.py` |
| `traceability.source_version` | Опционально | `src/config/schemas.py` |

## Примечания по `profile_id`

- Явный `profile_id` теперь задаётся в `histamine_profile.profile_id`.
- Для legacy Bateman-конфигов трассируемость по-прежнему обеспечивается через `model_id` + `traceability.source_in_report`.
- Для устаревшего `formalin_profile` `profile_id` определяется неявно как `formalin`.

## Blocked by data

1. Репозиторий может не содержать `report_v12_extracted/`; это явно отражено в регрессионном тесте как `xfail`.
2. Без приложенного отчёта v12 невозможно автоматически подтвердить первичный источник для каждой строки marker-table.
