# Руководство по созданию YAML-конфигураций

## 1. Назначение

`ModelConfig` является единственным источником правды для симуляции. YAML должен соответствовать реальной схеме `pkpd_xc7.config.schemas.ModelConfig`; любые поля вне неё не участвуют в runtime.

Актуальные точки входа CLI:

- `pkpd-cli simulate --config <path> --out <run_dir>`
- `python -m pkpd_xc7.cli.app simulate --config <path> --out <run_dir>`

Результатом являются детерминированные артефакты каталога прогона: `simulation.csv` и `meta.yaml`.

При загрузке файла через CLI и `pkpd_xc7.config.load_model_config()` поддерживается top-level поле `shared_configs`: строка или список относительных YAML-путей, которые детерминированно deep-merge-ятся до валидации `ModelConfig`. Локальный файл всегда имеет приоритет над подключёнными shared-конфигами.

## 2. Минимальный валидный каркас

Ниже приведён минимальный YAML, который соответствует текущему контракту:

```yaml
model_id: formalin_demo
compound: xc7
loss_mode: mse

traceability:
  source_in_report: "Table 1"
  source_reference: ""
  source_version: "2026-04"

assumptions:
  - "phase-6 scenario registry is accepted as source of H(t)"

shared_configs:
  - ../shared/common.yaml

driver:
  driver_type: scenario
  scenario_id: formalin

tissues:
  - skin
  - spinal_coord

time_grid_h:
  - 0.0
  - 0.25
  - 1.0
```

Важно:

- `driver` обязателен.
- `shared_configs` опционален и разрешается только лоадером YAML; `config_sha256` строится уже по итоговому merged-конфигу.
- `tissues` сейчас задаётся как `list[str]`, а не как список объектов с `volume`/`partition_coeff`.
- Для scenario-ветки `tissues` должны совпадать с ключами runtime-реестра выбранного сценария. Канонический CNS tissue id теперь `spinal_coord`; legacy alias `spinal` при загрузке YAML нормализуется в `spinal_coord`. Tissue `brain` зарегистрирован как временный proxy-профиль, синхронизированный с `spinal_coord` до появления отдельной source-backed parametrization.
- Для времени допустимы либо `time_grid_h`, либо пара `time_grid` + `time_unit`.
- В проекте нет runtime-полей `kinetics`, `initial_concentration`, `concentration_unit`, `plots`, `scenario_assumptions`.

## 3. Контракт `driver`

Поддерживаются две ветки:

- `driver.driver_type: pk`
- `driver.driver_type: scenario`

### PK-драйвер

```yaml
driver:
  driver_type: pk
  dose: 100.0
  k_abs_per_h: 1.0
  k_elim_per_h: 0.5
```

Важно для PK-ветки:

- Базальный `H` теперь резолвится через `trafficking.h_base_nm` и/или `tissue_overrides.<tissue>.trafficking.h_base_nm`.
- Если `h_base_nm` не задан, runtime сохраняет legacy fallback `50.0 nM` для обратной совместимости.
- Применённый baseline экспортируется в `meta.yaml` через `trafficking_params_by_tissue`.

### Scenario-драйвер

```yaml
driver:
  driver_type: scenario
  scenario_id: formalin
  profile_shape: gaussian_sum
```

Поддерживаемые канонические `scenario_id`:

- `formalin`
- `capsaicin`
- `carrageenan`
- `hot_plate`
- `acetic_writhing`
- `zymosan`
- `compound_48_80`

Поддерживаемые runtime-формы:

- `pulse`
- `gaussian_sum`

Поле `driver.profile_shape` опционально. Итоговая форма разрешается по приоритету:

1. `formalin_profile.profile_shape`
2. `driver.profile_shape`
3. default из scenario registry

## 4. Канонизация `scenario_id`

Runtime нормализует несколько legacy-алиасов к каноническим идентификаторам реестра:

- `compound48_80` -> `compound_48_80`
- `compound4880` -> `compound_48_80`
- `hotplate` -> `hot_plate`
- `writhing` -> `acetic_writhing`
- `carrageenin` -> `carrageenan`

Рекомендация: в новых YAML сразу использовать каноническое значение.

Важно для воспроизводимости артефактов: в `simulation.csv`/`meta.yaml` поле `driver_id` для scenario-ветки записывается уже в каноническом виде. Например, входной alias `compound48_80` будет экспортирован как `compound_48_80`.

## 5. `formalin_profile` и единицы времени

Каноническое место для базального уровня гистамина `h_base_nm` теперь находится в `trafficking`
или в `tissue_overrides.<tissue>.trafficking`. Блок `formalin_profile` остаётся точечным
override только для формы и фаз `scenario_id: formalin`; legacy-чтение `formalin_profile.h_base_nm`
сохраняется только для обратной совместимости.

Поддерживаемые поля:

```yaml
formalin_profile:
  profile_shape: gaussian_sum
  phase1:
    amplitude_nm: 900.0
    center_min: 6.0
    sigma_min: 8.0
  phase2:
    amplitude_nm: 250.0
    center_min: 40.0
    sigma_min: 25.0
```

Для pulse-профиля вместо гауссовых параметров используются:

- `center_min`
- `tau_rise_min`
- `tau_fall_min`

Инварианты:

- В YAML overrides время задаётся в минутах через `*_min`.
- В runtime все вычисления `H(t)` выполняются только в часах (`t_h`).
- Реестр сценариев хранит параметры только в часах и нМ.

## 6. Трассируемость и допущения

Обязательные требования:

- `traceability.source_in_report` не может быть пустым.
- `assumptions` должен содержать хотя бы одну непустую строку.
- Любое преобразование единиц, alias-нормализация или fallback следует явно фиксировать в `assumptions` при подготовке production-конфига.

Примеры полезных формулировок:

- `compound48_80 alias normalized to canonical scenario_id compound_48_80`
- `formalin override timings were transcribed in minutes and converted to hours at runtime`
- `zymosan uses gaussian_sum MVP profile until logistic_exp is introduced`

## 7. Примеры

### Пример 1. Formalin с override

```yaml
model_id: formalin_pkpd_v1
compound: xc7
loss_mode: mse

traceability:
  source_in_report: "Internal formalin reference"
  source_reference: "internal_review_2026"
  source_version: "1.0"

assumptions:
  - "phase1 timings taken from legacy formalin plot"
  - "phase2 timings taken from legacy formalin plot"

shared_configs:
  - ../shared/common.yaml

driver:
  driver_type: scenario
  scenario_id: formalin

trafficking:
  h_base_nm: 60.0

tissues:
  - skin
  - spinal_coord
  - ganglia

time_grid: [0, 5, 15, 30, 60, 120]
time_unit: min

formalin_profile:
  profile_shape: gaussian_sum
  phase1:
    amplitude_nm: 900.0
    center_min: 6.0
    sigma_min: 8.0
```

### Пример 2. Compound 48/80 без alias-двусмысленности

```yaml
model_id: compound_48_80_pkpd_v1
compound: xc7
loss_mode: mse

traceability:
  source_in_report: "Internal compound 48/80 reference"
  source_reference: "internal_review_2026"
  source_version: "1.0"

assumptions:
  - "canonical scenario_id compound_48_80 is used directly"

shared_configs:
  - ../shared/common.yaml

driver:
  driver_type: scenario
  scenario_id: compound_48_80

tissues:
  - skin
  - spinal_coord
  - ganglia

time_grid_h:
  - 0.0
  - 0.25
  - 1.0
  - 2.0
```

## 8. Канонические scenario-конфиги

Для 7 сценарных моделей актуальные примеры вынесены в отдельный каталог:

- `examples/configs/scenarios/formalin.yaml`
- `examples/configs/scenarios/capsaicin.yaml`
- `examples/configs/scenarios/compound_48_80.yaml`
- `examples/configs/scenarios/carrageenan.yaml`
- `examples/configs/scenarios/hot_plate.yaml`
- `examples/configs/scenarios/acetic_writhing.yaml`
- `examples/configs/scenarios/zymosan.yaml`

Важно:

- Эти файлы соответствуют текущему `ModelConfig` и проходят через scenario-runtime без новых полей.
- Общие параметры подключаются из единого `examples/configs/shared/common.yaml`; сценарные отличия остаются в самих модельных YAML.
- Канонический CNS tissue id в конфиге: `spinal_coord`; `brain` также поддержан и на минимальном этапе использует proxy-профиль, синхронизированный с `spinal_coord`.
- Часть параметров сводной таблицы остаётся в `scenario_registry`, а не дублируется в YAML.
- Все осознанные компромиссы и proxy-отображения тканей должны фиксироваться в `assumptions`.
- Legacy-пути `examples/configs/capsaicin.yaml` и `examples/configs/compound48_80.yaml` сохранены только как совместимые примеры для поиска и quickstart; каноническим источником остаётся каталог `examples/configs/scenarios/`.

Подробная матрица переноса параметров и backlog на расширение схемы описаны в
`docs/scenario_configuration_matrix.md`.
