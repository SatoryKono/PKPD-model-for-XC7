# Traceability Matrix

Цель: связать параметры модели с источником из отчёта (`source_in_report`) и модулем, где параметр используется/валидируется.

## Формат

`параметр → source_in_report → модуль`

## Матрица

| Параметр | Как фиксируется источник (`source_in_report`) | Модуль(и) |
|---|---|---|
| `model_id` | В составе конфига; источник задаётся через `traceability.source_in_report` | `src/config/schemas.py` (`ModelConfig`) |
| `compound` | То же | `src/config/schemas.py` |
| `loss_mode` | То же | `src/config/schemas.py` (`LossMode`, `ModelConfig`) |
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

- В текущем коде/схеме нет отдельного поля `profile_id`.
- Временная практика трассируемости: использовать `model_id` как идентификатор профиля в связке с `traceability.source_in_report`.
- Статус: **Blocked by data** — требуется формальное определение `profile_id` из ТЗ/отчёта v12.

## Blocked by data

1. Репозиторий может не содержать `report_v12_extracted/`; это явно отражено в регрессионном тесте как `xfail`.
2. Без приложенного отчёта v12 невозможно автоматически подтвердить первичный источник для каждой строки marker-table.
