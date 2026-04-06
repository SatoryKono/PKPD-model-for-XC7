# PKPD-model-for-XC7

Документация для разработчика и технического писателя: быстрый запуск, трассируемость и реестры допущений/рисков.

## Quickstart

> Ниже приведены команды для локального запуска. В репозитории сейчас нет lock-файла зависимостей, поэтому устанавливайте зависимости из вашего стандартного окружения проекта (например, `pip install -r requirements.txt`, если файл появится в вашей ветке).

### 1) Simulate

```bash
python -m src.cli.app simulate --config examples/configs/capsaicin.yaml --out runs/capsaicin_quickstart
```

Формалиновый тест:

```bash
python -m src.cli.app simulate --config examples/configs/formalin.yaml --out runs/formalin_quickstart
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

Ниже — полные рабочие примеры конфигов.

### Пример 1: `capsaicin.yaml`

```yaml
model_id: capsaicin_pkpd_v1
compound: capsaicin
loss_mode: huber
assumptions:
  - docx_profile_driven_histamine_model
  - capsaicin_monophasic_histamine_release
traceability:
  source_in_report: "DOCX v12, Модель 1: Динамика концентрации гистамина"
  source_reference: "ДИНАМИКА_ГИСТАМИНА_И_ФАРМАКОДИНАМИКА_H3-РЕЦЕПТОРОВ_v12.docx"
  source_version: "v12"
time_grid: [0, 30, 60, 120, 240]
time_unit: min
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
    title: Histamine concentration over time
    plot_type: line
    x: time
    y: histamine_concentration
    x_unit: min
    y_unit: nM
histamine_profile:
  profile_id: capsaicin
  tissue: skin
  h_base_nm: 50.0
  phase1:
    amplitude_nm: 150.0
    t0_h: 0.0
    tau_rise_h: 0.16666666666666666
    tau_fall_h: 0.6666666666666666
trafficking:
  k_int_max: 2.5
  k_rec: 0.5
  k_synth: 0.05
  ec50_barr_nm: 1500.0
  hill_n: 1.0
  ec50_g_nm: 50.0
plot_proxy:
  g_signal_ec50_nm: 50.0
scenario_assumptions:
  clip_state_explicit: false
```

### Пример 2: `compound48_80.yaml`

```yaml
model_id: compound48_80_pkpd_v2
compound: compound48_80
loss_mode: mse
assumptions:
  - docx_profile_driven_histamine_model
  - compound48_80_biphasic_histamine_release
traceability:
  source_in_report: "DOCX v12, Модель 1: Динамика концентрации гистамина"
  source_reference: "ДИНАМИКА_ГИСТАМИНА_И_ФАРМАКОДИНАМИКА_H3-РЕЦЕПТОРОВ_v12.docx"
  source_version: "v12"
time_grid: [0, 0.5, 1.0, 2.0, 4.0, 8.0]
time_unit: h
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
    title: Histamine concentration over time
    plot_type: log_line
    x: time
    y: histamine_concentration
    x_unit: h
    y_unit: nM
histamine_profile:
  profile_id: compound48_80
  tissue: skin
  h_base_nm: 50.0
  phase1:
    amplitude_nm: 1500.0
    t0_h: 0.0
    tau_rise_h: 0.08333333333333333
    tau_fall_h: 0.3333333333333333
  phase2:
    amplitude_nm: 250.0
    t0_h: 1.0
    tau_rise_h: 0.6666666666666666
    tau_fall_h: 2.0
trafficking:
  k_int_max: 2.5
  k_rec: 0.5
  k_synth: 0.05
  ec50_barr_nm: 1500.0
  hill_n: 1.0
  ec50_g_nm: 50.0
plot_proxy:
  g_signal_ec50_nm: 50.0
```

### Пример 3: `formalin.yaml`

```yaml
model_id: formalin_histamine_skin_v1
compound: formalin
loss_mode: huber
assumptions:
  - docx_profile_driven_histamine_model
  - formalin_biphasic_histamine_release
  - phase_shape_ratios_scaled_from_reported_t_half
traceability:
  source_in_report: "DOCX v12, Модель 1: Формалиновый тест"
  source_reference: "ДИНАМИКА_ГИСТАМИНА_И_ФАРМАКОДИНАМИКА_H3-РЕЦЕПТОРОВ_v12.docx"
  source_version: "v12"
time_grid: [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
time_unit: min
tissues:
  - name: plasma
    volume: 2.5
    volume_unit: L
    partition_coeff: 1.0
  - name: skin
    volume: 1.2
    volume_unit: L
    partition_coeff: 3.6
plots: []
histamine_profile:
  profile_id: formalin
  tissue: skin
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
- `profile_id` — теперь задаётся явно в `histamine_profile.profile_id` для profile-driven Model 1.
- Если конфиг использует legacy Bateman-вход, явный `profile_id` можно не задавать; в этом случае трассируемость обеспечивается через `model_id` + `traceability.source_in_report`.
