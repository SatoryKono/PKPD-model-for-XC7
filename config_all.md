# E:\g-drive\05_AI\github\PKPD-model-for-XC7\examples\configs\scenarios\acetic_writhing.yaml  acetic_writhing.yaml

```yaml
model_id: acetic_writhing_pkpd_v1
compound: xc7
loss_mode: mse

traceability:
  source_in_report: "Scenario matrix row: acetic writhing"
  source_reference: ""
  source_version: "2026-04-06"

assumptions:
  - "canonical scenario_id acetic_writhing is used directly"
  - "runtime tissue peritoneum is used as a proxy for peritoneal wall/lavage marker measurements"
  - "peritoneum, spinal_coord, and ganglia H(t) profiles are taken from scenario_registry as the source of truth"
  - "brain is included as a mandatory CNS tissue and currently uses a spinal_coord proxy profile until a source-backed brain profile is introduced"
  - "peritoneum h_base_nm is overridden to 50 nM so the marker-tissue H(t) peak matches the tabulated 550 nM range at 5-10 min"
  - "top-level trafficking acts as deterministic defaults before tissue_overrides are applied"

shared_configs:
  - ../shared/common.yaml

driver:
  driver_type: scenario
  scenario_id: acetic_writhing

tissue_overrides:
  peritoneum:
    trafficking:
      h_base_nm: 50.0

tissues:
  - peritoneum
  - spinal_coord
  - ganglia
  - brain
  
time_grid: [
  0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55,
  60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115,
  120, 125, 130, 135, 140, 145, 150, 155, 160, 165, 170, 175,
  180, 185, 190, 195, 200, 205, 210, 215, 220, 225, 230, 235,
  240 
]
time_unit: min
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\examples\configs\scenarios\capsaicin.yaml  capsaicin.yaml

```yaml
model_id: capsaicin_pkpd_v1
compound: xc7
loss_mode: mse

traceability:
  source_in_report: "Scenario matrix row: capsaicin"
  source_reference: ""
  source_version: "2026-04-06"

assumptions:
  - "canonical scenario_id capsaicin is used directly"
  - "skin, spinal_coord, and ganglia H(t) profiles are taken from scenario_registry as the source of truth"
  - "brain is included as a mandatory CNS tissue and currently uses a spinal_coord proxy profile until a source-backed brain profile is introduced"
  - "top-level trafficking acts as deterministic defaults before tissue_overrides are applied"
  - "skin h_base_nm is overridden to 50 nM so the marker-tissue H(t) peak matches the tabulated 227 nM at 15 min"

shared_configs:
  - ../shared/common.yaml

driver:
  driver_type: scenario
  scenario_id: capsaicin

tissue_overrides:
  skin:
    trafficking:
      h_base_nm: 50.0

tissues:
  - skin
  - spinal_coord
  - ganglia
  - brain
  
time_grid: [
  0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55,
  60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115,
  120, 125, 130, 135, 140, 145, 150, 155, 160, 165, 170, 175,
  180, 185, 190, 195, 200, 205, 210, 215, 220, 225, 230, 235,
  240
]
time_unit: min
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\examples\configs\scenarios\carrageenan.yaml  carrageenan.yaml

```yaml
model_id: carrageenan_pkpd_v1
compound: xc7
loss_mode: mse

traceability:
  source_in_report: "Scenario matrix row: carrageenan"
  source_reference: ""
  source_version: "2026-04-06"

assumptions:
  - "canonical scenario_id carrageenan is used directly"
  - "muscle is used as the marker tissue because the source table points to m. gastrocnemius"
  - "early and late muscle phases are taken from scenario_registry as the source of truth"
  - "brain is included as a mandatory CNS tissue and currently uses a spinal_coord proxy profile until a source-backed brain profile is introduced"
  - "top-level trafficking acts as deterministic defaults before tissue_overrides are applied"

shared_configs:
  - ../shared/common.yaml

driver:
  driver_type: scenario
  scenario_id: carrageenan

tissues:
  - muscle
  - spinal_coord
  - ganglia
  - brain
  
time_grid: [
  0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55,
  60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115,
  120, 125, 130, 135, 140, 145, 150, 155, 160, 165, 170, 175,
  180, 185, 190, 195, 200, 205, 210, 215, 220, 225, 230, 235,
  240, 245, 250, 255, 260, 265, 270, 275, 280, 285, 290, 295,
  300, 305, 310, 315, 320, 325, 330, 335, 340, 345, 350, 355,
  360, 365, 370, 375, 380, 385, 390, 395, 400, 405, 410, 415,
  420, 425, 430, 435, 440, 445, 450, 455, 460, 465, 470, 475,
  480, 485, 490, 495, 500, 505, 510, 515, 520, 525, 530, 535,
  540, 545, 550, 555, 560, 565, 570, 575, 580, 585, 590, 595,
  600, 605, 610, 615, 620, 625, 630, 635, 640, 645, 650, 655,
  660, 665, 670, 675, 680, 685, 690, 695, 700, 705, 710, 715,
  720 
]
time_unit: min
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\examples\configs\scenarios\compound_48_80.yaml  compound_48_80.yaml

```yaml
model_id: compound_48_80_pkpd_v1
compound: xc7
loss_mode: mse

traceability:
  source_in_report: "Scenario matrix row: compound 48/80"
  source_reference: ""
  source_version: "2026-04-06"

assumptions:
  - "canonical scenario_id compound_48_80 is used directly"
  - "skin two-phase profile and CNS profiles are taken from scenario_registry as the source of truth"
  - "brain is included as a mandatory CNS tissue and currently uses a spinal_coord proxy profile until a source-backed brain profile is introduced"
  - "top-level trafficking acts as deterministic defaults before tissue_overrides are applied"
  - "legacy file examples/configs/compound48_80.yaml is retained only as a compatibility example"

shared_configs:
  - ../shared/common.yaml

driver:
  driver_type: scenario
  scenario_id: compound_48_80

tissues:
  - skin
  - spinal_coord
  - ganglia
  - brain
    
time_grid: [
  0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55,
  60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115,
  120, 125, 130, 135, 140, 145, 150, 155, 160, 165, 170, 175,
  180, 185, 190, 195, 200, 205, 210, 215, 220, 225, 230, 235,
  240, 245, 250, 255, 260, 265, 270, 275, 280, 285, 290, 295,
  300, 305, 310, 315, 320, 325, 330, 335, 340, 345, 350, 355,
  360, 365, 370, 375, 380, 385, 390, 395, 400, 405, 410, 415,
  420, 425, 430, 435, 440, 445, 450, 455, 460, 465, 470, 475,
  480, 485, 490, 495, 500, 505, 510, 515, 520, 525, 530, 535,
  540, 545, 550, 555, 560, 565, 570, 575, 580, 585, 590, 595,
  600, 605, 610, 615, 620, 625, 630, 635, 640, 645, 650, 655,
  660, 665, 670, 675, 680, 685, 690, 695, 700, 705, 710, 715,
  720 
]
time_unit: min
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\examples\configs\scenarios\formalin.yaml  formalin.yaml

```yaml
# Уникальный идентификатор конфигурации/запуска.
model_id: formalin_pkpd_v1
# Исследуемое соединение.
compound: xc7
# Режим функции потерь для сопутствующих fit/report путей.
loss_mode: mse

# Блок трассируемости источника параметров.
traceability:
  # Откуда в отчёте взят этот сценарий.
  source_in_report: "Scenario matrix row: formalin"
  # Внешняя ссылка или DOI, если есть.
  source_reference: ""
  # Версия источника/сводной таблицы.
  source_version: "2026-04-06"

# Явно зафиксированные модельные допущения.
assumptions:
  - "canonical scenario_id formalin is used directly"
  - "shared/common trafficking and top-level formalin_profile act as deterministic defaults before tissue_overrides, including tissue-specific profile_shape, are applied"
  - "brain is included as a mandatory CNS tissue and currently uses a spinal_coord proxy profile until a source-backed brain profile is introduced"
  - "formalin skin phase-1 half-life of 9 min is approximated as gaussian sigma_min=7.6"
  - "phase-2 skin peak is encoded via formalin_profile amplitude override to reach 400 nM on a 50 nM baseline"
  - "spinal_coord and ganglia phase centers are fixed at 30/120 min and 15/60 min respectively because the source table specifies peaks and t1/2 but not phase timing"

shared_configs:
  - ../shared/common.yaml

# Какой драйвер гистамина используется в симуляции.
driver:
  # Тип драйвера: сценарный профиль из реестра.
  driver_type: scenario
  # Канонический идентификатор сценария.
  scenario_id: formalin

# Базовый histamine-профиль formalin, используемый до тканевых override.
formalin_profile:
  # Параметры ранней фазы.
  phase1:
    # Амплитуда фазы над базальным уровнем, нМ.
    amplitude_nm: 990.0
    # Ширина гауссианы фазы, минут.
    sigma_min: 7.6
  # Параметры поздней фазы.
  phase2:
    # Амплитуда фазы над базальным уровнем, нМ.
    amplitude_nm: 390.0

# Переопределения параметров для конкретных тканей.
tissue_overrides:
  skin:
    # Тканеспецифичный histamine-профиль для кожи.
    formalin_profile:
      # Форма профиля H(t) для кожи.
      profile_shape: gaussian_sum
      phase1:
        # Амплитуда ранней фазы над базой, нМ.
        amplitude_nm: 990.0
        # Время центра ранней фазы, минут.
        center_min: 5.0
        # Ширина ранней фазы, минут.
        sigma_min: 7.6
      phase2:
        # Амплитуда поздней фазы над базой, нМ.
        amplitude_nm: 390.0
        # Время центра поздней фазы, минут.
        center_min: 40.0
        # Ширина поздней фазы, минут.
        sigma_min: 25.0
  spinal_coord:
    # Тканеспецифичный histamine-профиль для спинного мозга.
    formalin_profile:
      # Форма профиля H(t) для спинного мозга.
      profile_shape: gaussian_sum
      phase1:
        # Амплитуда ранней фазы над базой, нМ.
        amplitude_nm: 0.246
        # Время центра ранней фазы, минут.
        center_min: 30.0
        # Ширина ранней фазы, минут.
        sigma_min: 73.9
      phase2:
        # Амплитуда поздней фазы над базой, нМ.
        amplitude_nm: 7.883
        # Время центра поздней фазы, минут.
        center_min: 120.0
        # Ширина поздней фазы, минут.
        sigma_min: 73.9
  ganglia:
    # Тканеспецифичный histamine-профиль для симпатических ганглиев.
    formalin_profile:
      # Форма профиля H(t) для симпатических ганглиев.
      profile_shape: gaussian_sum
      phase1:
        # Амплитуда ранней фазы над базой, нМ.
        amplitude_nm: 3.426
        # Время центра ранней фазы, минут.
        center_min: 15.0
        # Ширина ранней фазы, минут.
        sigma_min: 23.8
      phase2:
        # Амплитуда поздней фазы над базой, нМ.
        amplitude_nm: 9.428
        # Время центра поздней фазы, минут.
        center_min: 60.0
        # Ширина поздней фазы, минут.
        sigma_min: 23.8
  brain:
    # Тканеспецифичный histamine-профиль для головного мозга.
    formalin_profile:
      # Форма профиля H(t) для головного мозга.
      profile_shape: gaussian_sum
      phase1:
        # Амплитуда ранней фазы над базой, нМ.
        amplitude_nm: 0.246
        # Время центра ранней фазы, минут.
        center_min: 30.0
        # Ширина ранней фазы, минут.
        sigma_min: 73.9
      phase2:
        # Амплитуда поздней фазы над базой, нМ.
        amplitude_nm: 7.883
        # Время центра поздней фазы, минут.
        center_min: 120.0
        # Ширина поздней фазы, минут.
        sigma_min: 73.9
        
# Список тканей, по которым будет рассчитана модель.
tissues:
  - skin
  - spinal_coord
  - ganglia
  - brain
  
# Временная сетка расчёта.
time_grid: [
  0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55,
  60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115,
  120, 125, 130, 135, 140, 145, 150, 155, 160, 165, 170, 175,
  180, 185, 190, 195, 200, 205, 210, 215, 220, 225, 230, 235,
  240, 245, 250, 255, 260, 265, 270, 275, 280, 285, 290, 295,
  300, 305, 310, 315, 320, 325, 330, 335, 340, 345, 350, 355,
  360, 365, 370, 375, 380, 385, 390, 395, 400, 405, 410, 415,
  420, 425, 430, 435, 440, 445, 450, 455, 460, 465, 470, 475,
  480, 485, 490, 495, 500, 505, 510, 515, 520, 525, 530, 535,
  540, 545, 550, 555, 560, 565, 570, 575, 580, 585, 590, 595,
  600, 605, 610, 615, 620, 625, 630, 635, 640, 645, 650, 655,
  660, 665, 670, 675, 680, 685, 690, 695, 700, 705, 710, 715,
  720
]
# Единица времени для time_grid.
time_unit: min
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\examples\configs\scenarios\hot_plate.yaml  hot_plate.yaml

```yaml
model_id: hot_plate_pkpd_v1
compound: xc7
loss_mode: mse

traceability:
  source_in_report: "Scenario matrix row: hot plate"
  source_reference: ""
  source_version: "2026-04-06"

assumptions:
  - "canonical scenario_id hot_plate is used directly"
  - "runtime registry is treated as the source of truth for skin, spinal_coord, and ganglia H(t)"
  - "brain is included as a mandatory CNS tissue and currently uses a spinal_coord proxy profile until a source-backed brain profile is introduced"
  - "skin h_base_nm is overridden to 50 nM so the marker-tissue H(t) peak matches the primary 262 nM text value at 1 min"
  - "top-level trafficking acts as deterministic defaults before tissue_overrides are applied"

shared_configs:
  - ../shared/common.yaml

driver:
  driver_type: scenario
  scenario_id: hot_plate

tissue_overrides:
  skin:
    trafficking:
      h_base_nm: 50.0

tissues:
  - skin
  - spinal_coord
  - ganglia
  - brain
  
time_grid: [
  0, 1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55,
  60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115,
  120, 125, 130, 135, 140, 145, 150, 155, 160, 165, 170, 175,
  180, 185, 190, 195, 200, 205, 210, 215, 220, 225, 230, 235,
  240, 245, 250, 255, 260, 265, 270, 275, 280, 285, 290, 295,
  300, 305, 310, 315, 320, 325, 330, 335, 340, 345, 350, 355,
  360, 365, 370, 375, 380, 385, 390, 395, 400, 405, 410, 415,
  420, 425, 430, 435, 440, 445, 450, 455, 460, 465, 470, 475,
  480, 485, 490, 495, 500, 505, 510, 515, 520, 525, 530, 535,
  540, 545, 550, 555, 560, 565, 570, 575, 580, 585, 590, 595,
  600, 605, 610, 615, 620, 625, 630, 635, 640, 645, 650, 655,
  660, 665, 670, 675, 680, 685, 690, 695, 700, 705, 710, 715,
  720 
]
time_unit: min
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\examples\configs\scenarios\zymosan.yaml  zymosan.yaml

```yaml
model_id: zymosan_pkpd_v1
compound: xc7
loss_mode: mse

traceability:
  source_in_report: "Scenario matrix row: zymosan"
  source_reference: ""
  source_version: "2026-04-06"

assumptions:
  - "canonical scenario_id zymosan is used directly"
  - "runtime tissue peritoneum is used as a proxy for peritoneal exudate marker measurements"
  - "zymosan uses the current gaussian_sum MVP approximation from scenario_registry until a dedicated delayed profile is implemented"
  - "brain is included as a mandatory CNS tissue and currently uses a spinal_coord proxy profile until a source-backed brain profile is introduced"
  - "peritoneum h_base_nm is overridden to 50 nM so the marker-tissue H(t) peak matches the primary tabulated 350 nM value"
  - "marker-oriented trafficking values k_int_max=0.28 and k_rec=0.12 act as deterministic defaults before tissue_overrides are applied"

shared_configs:
  - ../shared/common.yaml

driver:
  driver_type: scenario
  scenario_id: zymosan

trafficking:
  k_int_max_per_h: 0.28
  k_rec_per_h: 0.12

tissue_overrides:
  peritoneum:
    trafficking:
      h_base_nm: 50.0

tissues:
  - peritoneum
  - spinal_coord
  - ganglia
  - brain
  

time_grid: [
  0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55,
  60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115,
  120, 125, 130, 135, 140, 145, 150, 155, 160, 165, 170, 175,
  180, 185, 190, 195, 200, 205, 210, 215, 220, 225, 230, 235,
  240, 245, 250, 255, 260, 265, 270, 275, 280, 285, 290, 295,
  300, 305, 310, 315, 320, 325, 330, 335, 340, 345, 350, 355,
  360, 365, 370, 375, 380, 385, 390, 395, 400, 405, 410, 415,
  420, 425, 430, 435, 440, 445, 450, 455, 460, 465, 470, 475,
  480, 485, 490, 495, 500, 505, 510, 515, 520, 525, 530, 535,
  540, 545, 550, 555, 560, 565, 570, 575, 580, 585, 590, 595,
  600, 605, 610, 615, 620, 625, 630, 635, 640, 645, 650, 655,
  660, 665, 670, 675, 680, 685, 690, 695, 700, 705, 710, 715,
  720 
]
time_unit: min
```

# E:\g-drive\05_AI\github\PKPD-model-for-XC7\examples\configs\shared\common.yaml  common.yaml

```yaml
# Общие параметры trafficking, используемые как базовые defaults.
trafficking:
  # Максимальная скорость интернализации рецептора, 1/ч; эквивалентный t1/2 ≈ 0.55 ч (≈ 33.3 мин).
  k_int_max_per_h: 1.25
  # Скорость возврата рецептора на мембрану, 1/ч; эквивалентный t1/2 ≈ 1.39 ч (≈ 83.2 мин).
  k_rec_per_h: 0.5
  # Скорость синтеза/восстановления пула рецепторов, 1/ч; эквивалентный t1/2 ≈ 13.86 ч (≈ 831.8 мин).
  k_synth_per_h: 0.05
  # EC50 для beta-arrestin ветки, нМ.
  ec50_barr_nm: 500.0
  # Коэффициент Хилла для сигнальных веток.
  hill_n: 1.0
  # EC50 для G-белкового пути, нМ.
  ec50_g_nm: 20.0
  # Конститутивная активность H3R как доля от Emax (0.05 = 5%).
  constitutive_activity: 0.05
  # Базальная концентрация гистамина, нМ.
  h_base_nm: 10.0

# Тканеспецифичные переопределения общих параметров.
tissue_overrides:
  skin:
    # Параметры для кожи.
    trafficking:
      # Максимальная скорость интернализации рецептора, 1/ч; эквивалентный t1/2 ≈ 0.55 ч (≈ 33.3 мин).
      k_int_max_per_h: 1.25
      # Скорость возврата рецептора на мембрану, 1/ч; эквивалентный t1/2 ≈ 1.39 ч (≈ 83.2 мин).
      k_rec_per_h: 0.5
      # Скорость синтеза/восстановления пула рецепторов, 1/ч; эквивалентный t1/2 ≈ 13.86 ч (≈ 831.8 мин).
      k_synth_per_h: 0.05
      # EC50 для beta-arrestin ветки, нМ.
      ec50_barr_nm: 500.0
      # Коэффициент Хилла для сигнальных веток.
      hill_n: 1.0
      # EC50 для G-белкового пути, нМ.
      ec50_g_nm: 20.0
      # Конститутивная активность H3R как доля от Emax.
      constitutive_activity: 0.05
      # Базальная концентрация гистамина, нМ.
      h_base_nm: 10.0
  muscle:
    # Параметры для мышцы.
    trafficking:
      # Максимальная скорость интернализации рецептора, 1/ч; эквивалентный t1/2 ≈ 0.55 ч (≈ 33.3 мин).
      k_int_max_per_h: 1.25
      # Скорость возврата рецептора на мембрану, 1/ч; эквивалентный t1/2 ≈ 1.39 ч (≈ 83.2 мин).
      k_rec_per_h: 0.5
      # Скорость синтеза/восстановления пула рецепторов, 1/ч; эквивалентный t1/2 ≈ 13.86 ч (≈ 831.8 мин).
      k_synth_per_h: 0.05
      # EC50 для beta-arrestin ветки, нМ.
      ec50_barr_nm: 500.0
      # Коэффициент Хилла для сигнальных веток.
      hill_n: 1.0
      # EC50 для G-белкового пути, нМ.
      ec50_g_nm: 20.0
      # Конститутивная активность H3R как доля от Emax.
      constitutive_activity: 0.05
      # Базальная концентрация гистамина, нМ.
      h_base_nm: 10.0
  spinal_coord:
    # Параметры для спинного мозга.
    trafficking:
      # Максимальная скорость интернализации рецептора, 1/ч; повышена для спинного мозга.
      k_int_max_per_h: 1.4
      # Скорость возврата рецептора на мембрану, 1/ч; эквивалентный t1/2 ≈ 0.87 ч (≈ 52.0 мин).
      k_rec_per_h: 0.8
      # Скорость синтеза/восстановления пула рецепторов, 1/ч; эквивалентный t1/2 ≈ 13.86 ч (≈ 831.8 мин).
      k_synth_per_h: 0.05
      # EC50 для beta-arrestin ветки, нМ.
      ec50_barr_nm: 500.0
      # Коэффициент Хилла для сигнальных веток.
      hill_n: 1.0
      # EC50 для G-белкового пути, нМ.
      ec50_g_nm: 20.0
      # Конститутивная активность H3R как доля от Emax.
      constitutive_activity: 0.25
      # Базальная концентрация гистамина, нМ.
      h_base_nm: 2.0
  brain:
    # Параметры для головного мозга; временно синхронизированы с spinal_coord.
    trafficking:
      # Максимальная скорость интернализации рецептора, 1/ч; синхронизирована с spinal_coord.
      k_int_max_per_h: 1.4
      # Скорость возврата рецептора на мембрану, 1/ч; эквивалентный t1/2 ≈ 0.87 ч (≈ 52.0 мин).
      k_rec_per_h: 0.8
      # Скорость синтеза/восстановления пула рецепторов, 1/ч; эквивалентный t1/2 ≈ 13.86 ч (≈ 831.8 мин).
      k_synth_per_h: 0.05
      # EC50 для beta-arrestin ветки, нМ.
      ec50_barr_nm: 500.0
      # Коэффициент Хилла для сигнальных веток.
      hill_n: 1.0
      # EC50 для G-белкового пути, нМ.
      ec50_g_nm: 20.0
      # Конститутивная активность H3R как доля от Emax.
      constitutive_activity: 0.25
      # Базальная концентрация гистамина, нМ.
      h_base_nm: 2.0
  ganglia:
    # Параметры для симпатических ганглиев.
    trafficking:
      # Максимальная скорость интернализации рецептора, 1/ч; повышена для симпатических ганглиев.
      k_int_max_per_h: 1.8
      # Скорость возврата рецептора на мембрану, 1/ч; эквивалентный t1/2 ≈ 0.99 ч (≈ 59.4 мин).
      k_rec_per_h: 0.7
      # Скорость синтеза/восстановления пула рецепторов, 1/ч; эквивалентный t1/2 ≈ 13.86 ч (≈ 831.8 мин).
      k_synth_per_h: 0.05
      # EC50 для beta-arrestin ветки, нМ.
      ec50_barr_nm: 1500.0
      # Коэффициент Хилла для сигнальных веток.
      hill_n: 1.0
      # EC50 для G-белкового пути, нМ.
      ec50_g_nm: 20.0
      # Конститутивная активность H3R как доля от Emax.
      constitutive_activity: 0.10
      # Базальная концентрация гистамина, нМ.
      h_base_nm: 5.0
```
