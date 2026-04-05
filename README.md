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
