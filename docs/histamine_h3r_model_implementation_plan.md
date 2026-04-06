# План реализации моделей гистамина и H3R

## Цель

Добавить в проект явный, детерминированный и тестируемый слой для трёх связанных моделей:

1. Модель концентрации гистамина по экспериментальным парадигмам.
2. Модель интернализации/ресайклинга H3R.
3. Модель G-сигналинга H3R с поправкой на `R_surf(t)`.

Новые YAML в `examples/configs/specs/` являются спецификациями параметров и пока не подключены к текущему `simulate`-пайплайну.

## Новые спецификации

- `examples/configs/specs/model1_histamine_dynamics.yaml`
- `examples/configs/specs/model2_h3r_internalization.yaml`
- `examples/configs/specs/model3_h3r_g_signaling.yaml`

## Текущее состояние кода

- `src/histamine_profiles.py` уже содержит заготовки для `formalin`, `compound48_80`, `capsaicin`, `hotplate`, `acetic_writhing`.
- `src/models/receptor_trafficking.py` уже содержит `k_int_eff(...)`, `receptor_trafficking_rhs(...)` и `steady_state_ic(...)`.
- `src/api.py` и `src/config/schemas.py` пока ориентированы на текущий `ModelConfig` для одного runtime-сценария, а не на отдельные литературы-спецификации моделей 1-3.

## Порядок реализации

### RF-001: Ввести отдельную схему конфигов для literature-model specs

- Тип: `feature`
- Риск: low
- Файлы:
  - `src/config/schemas.py`
  - `src/config/loader.py`
  - `tests/`
- Что сделать:
  - Добавить новые Pydantic-схемы для `HistamineDynamicsSpec`, `H3RInternalizationSpec`, `H3RGSignalingSpec`.
  - Явно разделить текущий `ModelConfig` и новые спецификации, без silent-расширения старого формата.
  - Валидировать единицы, сортировку ключей и обязательные поля.

### RF-002: Подключить Model 1 к runtime-функциям профиля гистамина

- Тип: `feature`
- Риск: medium
- Файлы:
  - `src/histamine_profiles.py`
  - `src/config/loader.py`
  - `tests/test_histamine_profiles_*.py`
- Что сделать:
  - Реализовать построение параметров профиля из `model1_histamine_dynamics.yaml`.
  - Сохранить существующие дефолты как fallback только там, где они явно совпадают со спецификацией.
  - Для `formalin`, `hot_plate`, `acetic_writhing` не подставлять скрытые значения: либо документированная калибровка, либо явный `Blocked by data`.

### RF-003: Связать Model 2 со спецификацией интернализации

- Тип: `feature`
- Риск: low
- Файлы:
  - `src/models/receptor_trafficking.py`
  - `tests/test_receptor_trafficking_unit.py`
  - `tests/test_model_params_integration.py`
- Что сделать:
  - Добавить явный конструктор `TraffickingParams` из YAML-спеки.
  - Проверить инварианты `R_surf`, `R_int` и условие сохранения массы рецепторов.
  - Зафиксировать baseline-инициализацию как `steady_state_at_baseline_histamine`.

### RF-004: Реализовать Model 3 как отдельный вычисляемый слой

- Тип: `feature`
- Риск: medium
- Файлы:
  - новый модуль `src/models/g_signaling.py`
  - `src/config/schemas.py`
  - `src/api.py`
  - `tests/`
- Что сделать:
  - Вынести формулу `G_act(t)` в отдельную функцию/модуль.
  - Принимать `H(t)` и `R_surf(t)` как явные входы.
  - Использовать детерминированный `ca_fraction` по ткани, а диапазоны хранить только как трассируемый контекст.

### RF-005: Расширить orchestration и артефакты без breaking change

- Тип: `feature`
- Риск: medium
- Файлы:
  - `src/api.py`
  - `src/cli/app.py`
  - `src/repro/metadata.py`
  - `src/pipelines/run_layout.py`
- Что сделать:
  - Добавить новый путь выполнения, который умеет строить таблицы для моделей 1-3.
  - Не менять поведение текущей команды `simulate` для существующих `ModelConfig`.
  - В `meta.yaml` и `metadata.json` записывать `pipeline_version`, `row_count` и checksums для новых артефактов.

### RF-006: Тесты и golden-артефакты

- Тип: `test`
- Риск: low
- Файлы:
  - `tests/test_histamine_profiles_*.py`
  - `tests/test_receptor_trafficking_unit.py`
  - `tests/test_snapshots_timeseries.py`
  - новые snapshot/golden fixtures
- Что сделать:
  - Проверить загрузку YAML-спек и строгую валидацию.
  - Проверить детерминизм CSV/YAML-артефактов.
  - Добавить regression/golden-тесты на `H(t)`, `R_surf/R_int`, `G_act(t)`.

## Ключевые риски

- Для `formalin`, `hot_plate`, `acetic_writhing` не все кинетические параметры заданы напрямую в исходных заметках.
- Если попытаться встроить новые YAML в текущий `ModelConfig`, получится неявное смешение двух контрактов.
- Для Model 3 диапазоны `CA` нельзя использовать как runtime-значения без явного правила выбора.

## Definition of Done

- Новые YAML-спецификации валидируются отдельной схемой.
- Реализация моделей 1-3 не меняет поведение текущих конфигов `capsaicin.yaml` и `compound48_80.yaml`.
- Все новые артефакты пишутся атомарно и детерминированно.
- Есть unit + regression tests на загрузку, расчёт и экспорт.
