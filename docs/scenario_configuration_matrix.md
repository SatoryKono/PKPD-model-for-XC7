# Матрица конфигурирования сценарных моделей

## Назначение

Этот документ фиксирует, как сводная таблица параметров переносится в текущий контракт
`pkpd_xc7.config.schemas.ModelConfig` без silent-расширений схемы.

Статусы переноса:

- `encoded_in_yaml`: параметр явно записан в YAML.
- `taken_from_registry`: значение определяется runtime-реестром
  `src/pkpd_xc7/simulation/scenario_registry.py`.
- `recorded_as_assumption`: значение важно для интерпретации, но в текущем контракте
  хранится только как текстовое допущение.
- `requires_schema_change`: для параметра нужен новый публичный контракт.

## Создаваемые конфиги

- `examples/configs/scenarios/formalin.yaml`
- `examples/configs/scenarios/capsaicin.yaml`
- `examples/configs/scenarios/compound_48_80.yaml`
- `examples/configs/scenarios/carrageenan.yaml`
- `examples/configs/scenarios/hot_plate.yaml`
- `examples/configs/scenarios/acetic_writhing.yaml`
- `examples/configs/scenarios/zymosan.yaml`
- `examples/configs/scenarios/cyp_cystitis.yaml`

## Сводная матрица по сценариям

| Сценарий | Marker tissue из сводной таблицы | Runtime tissues в текущем коде | `encoded_in_yaml` | `taken_from_registry` | `recorded_as_assumption` | `requires_schema_change` |
| --- | --- | --- | --- | --- | --- | --- |
| Formalin | `skin` | `skin`, `spinal_coord`, `ganglia`, `brain` | `scenario_id`, `time_grid`, общий `trafficking`, `formalin_profile` для `phase1.amplitude_nm`, `phase1.sigma_min`, `phase2.amplitude_nm` | формы `spinal_coord/ganglia/brain`, центры фаз formalin, допустимые tissues | перевод `t1/2` в `sigma_min`, единый блок trafficking для всех тканей, `brain` временно проксируется от `spinal_coord` | tissue-specific CA и trafficking, отдельные альтернативные литературные варианты |
| Capsaicin | `skin` | `skin`, `spinal_coord`, `ganglia`, `brain` | `scenario_id`, `time_grid`, общий `trafficking`, `capsaicin_profile.phase1`, `tissue_overrides.<tissue>.capsaicin_profile.phase1` | registry fallback для `H(t)`, если capsaicin overrides не заданы; допустимые tissues | что `brain` пока дублирует `spinal_coord` по форме пика, пока не появится source-backed brain profile | tissue-specific CA |
| Compound 48/80 | `skin` | `skin`, `spinal_coord`, `ganglia`, `brain` | `scenario_id`, `time_grid`, общий `trafficking` | двухфазный skin-профиль и CNS-профили | что канонический `compound_48_80` используется напрямую, а `brain` временно проксируется от `spinal_coord` | tissue-specific CA и trafficking |
| Carrageenan | `muscle` | `muscle`, `spinal_coord`, `ganglia`, `brain` | `scenario_id`, `time_grid_h`, общий `trafficking` | ранняя и поздняя мышечные фазы, базовые уровни CNS | что поздняя фаза реестра трактуется как диапазон `4-8 h` baseline; `brain` пока дублирует `spinal_coord` | tissue-specific CA и trafficking |
| Hot plate | `skin` | `skin`, `spinal_coord`, `ganglia`, `brain` | `scenario_id`, `time_grid`, общий `trafficking` | весь gauss-профиль по тканям | что в качестве основного baseline выбран текстовый пик `262 nM`, а `brain` временно дублирует `spinal_coord` | хранение нескольких source variants в одном конфиге |
| Acetic writhing | `peritoneum` | `peritoneum`, `spinal_coord`, `ganglia`, `brain` | `scenario_id`, `time_grid`, общий `trafficking` | peritoneum/CNS-профили, допустимые tissues | что `peritoneum` используется как proxy для `перитонеальная стенка / лаваж`, а `brain` временно дублирует `spinal_coord` | vocab для wall/lavage, tissue-specific CA |
| Zymosan | `peritoneum` proxy для `перитонеальный экссудат` | `peritoneum`, `spinal_coord`, `ganglia`, `brain` | `scenario_id`, `time_grid_h`, marker-oriented `trafficking` (`k_int_max=0.28`, `k_rec=0.12`) | текущий delayed-like gaussian MVP профиль | что exudate аппроксимируется `peritoneum`, а `brain` временно дублирует `spinal_coord` | отдельная tissue vocabulary, `zymosan_like` runtime-ветка, tissue-specific CA |
| CYP cystitis | `bladder` | `bladder`, `spinal_coord`, `ganglia`, `brain` | `scenario_id`, `cyp_cystitis_profile` (опц.), `tissue_overrides.<tissue>.formalin_profile` для фаз `gaussian_sum`, `time_grid_h`, `trafficking`, shared `antagonist_pk` | дефолтный H(t) по тканям в реестре, если фазы в YAML опущены; поддерживается только `gaussian_sum` | верхний `cyp_cystitis_profile.phase1/2` задаёт одинаковый merge 1-й/2-й гауссианы для **всех** тканей — органоспецифичные пики в `tissue_overrides`; горизонт MVP 24 ч; PK `bladder` → peritoneum в XLSX | обобщение поля до `scenario_profile` для всех сценариев (бэклог п.1) |

## Какие классы параметров реально кодируются сейчас

### `encoded_in_yaml`

- идентификатор модели: `model_id`
- моделируемое соединение: `compound`
- ссылка на источник: `traceability`
- явные текстовые допущения: `assumptions`
- выбор сценария: `driver.driver_type=scenario` и `driver.scenario_id`
- сетка времени: `time_grid_h` либо `time_grid + time_unit`
- базовый набор параметров траффикинга:
  `k_int_max_per_h`, `k_rec_per_h`, `k_synth_per_h`, `ec50_g_nm`, `ec50_barr_nm`,
  `hill_n`, `constitutive_activity`
- tissue-aware overrides через `tissue_overrides.<tissue>.trafficking`
- список тканей, которые реально прогоняются в симуляции
- только для `formalin` и `capsaicin`: scenario-specific profile overrides на top-level и в `tissue_overrides`
- для `cyp_cystitis`: опциональный top-level `cyp_cystitis_profile` и `tissue_overrides.<tissue>.formalin_profile` (те же поля `phase1`/`phase2`, что у formalin `gaussian_sum`: `amplitude_nm`, `center_min`, `sigma_min`)
- `antagonist_pk.administration_lag_h` для сценариев, где введение XC7 отстоит от индукции модели; отрицательные значения кодируют pretreatment

### `taken_from_registry`

Эти параметры не дублируются в YAML, чтобы не расходиться с runtime-кодом:

- `H_base` по тканям для сценариев без explicit profile overrides
- форма `H(t)` для сценариев без explicit YAML override
- набор допустимых тканей для каждого `scenario_id`
- центры и ширины фаз, если они не переопределены в `formalin_profile` или `capsaicin_profile`
- все CNS/ганглионарные профили

Источник истины: `src/pkpd_xc7/simulation/scenario_registry.py`.

Текущий runtime: канонический CNS tissue id для сценариев это `spinal_coord`; legacy alias `spinal` нормализуется при загрузке. Tissue `brain` зарегистрирован как временный proxy-профиль, синхронизированный с `spinal_coord`.

### `recorded_as_assumption`

В production-конфиге эти решения фиксируются только текстом:

- какой из нескольких литературных/табличных вариантов выбран baseline
- как переводится неканонический параметр в существующий контракт
  (например, `t1/2` formalin -> `sigma_min`)
- какие tissue-specific величины схлопнуты в один общий блок `trafficking`
- какие ткани сводной таблицы аппроксимируются ближайшим runtime-ключом
  (`peritoneal exudate` -> `peritoneum`)

### `requires_schema_change`

Следующие классы параметров принципиально не выражаются текущим `ModelConfig`:

- произвольные scenario-specific overrides для всех сценариев, а не только formalin/capsaicin
- хранение альтернативных наборов source values в одном конфиге
- source-backed литературный brain-профиль, отличный от временного proxy `spinal_coord -> brain`
- канонические ключи тканей `peritoneal_wall`, `peritoneal_exudate`,
  `visceral_afferents`
- delayed-rise профиль `zymosan_like` как исполняемая runtime-форма, а не только тип
- табличный/узловой ввод `H(t)` вместо жёстко заданного registry profile

## Базовые значения `trafficking`, которые фиксируются в YAML

| Сценарий | `k_int_max_per_h` | `k_rec_per_h` | `k_synth_per_h` | `ec50_g_nm` | `ec50_barr_nm` | `hill_n` | `constitutive_activity` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Formalin | 2.5 | 0.5 | 0.05 | 50 | 1500 | 1.0 | 0.05 |
| Capsaicin | 2.5 | 0.5 | 0.05 | 50 | 1500 | 1.0 | 0.05 |
| Compound 48/80 | 2.5 | 0.5 | 0.05 | 50 | 1500 | 1.0 | 0.05 |
| Carrageenan | 2.5 | 0.5 | 0.05 | 50 | 1500 | 1.0 | 0.05 |
| Hot plate | 2.5 | 0.5 | 0.05 | 50 | 1500 | 1.0 | 0.05 |
| Acetic writhing | 2.5 | 0.5 | 0.05 | 50 | 1500 | 1.0 | 0.05 |
| Zymosan | 0.28 | 0.12 | 0.05 | 50 | 1500 | 1.0 | 0.05 |

## Backlog расширения схемы

Следующий change-set должен быть отдельным и явно versioned:

1. Ввести единый `ScenarioOverrides` / `scenario_profile` для всех сценариев (сейчас для `cyp_cystitis` частично закрыто отдельным полем `cyp_cystitis_profile` и переиспользованием `formalin_profile` в `tissue_overrides`).
2. Разделить `trafficking` на общий baseline и tissue-aware overrides.
3. Добавить канонический словарь tissue IDs и миграционные alias-правила.
4. Реализовать `zymosan_like` в runtime или ввести табличный ввод `H(t)`.
5. После расширения синхронно обновить `docs/yaml_configuration_guide.md`,
   `CHANGELOG.md` и тесты схемы.
