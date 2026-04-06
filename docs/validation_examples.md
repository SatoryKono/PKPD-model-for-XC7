# Validation examples: snapshot rounding

Ниже показано фактическое поведение `pkpd_xc7.validation` в фазе 8.

Текущий API:

- `RoundingSpec.from_model(model_key)` задаёт число знаков после запятой по колонкам.
- `apply_rounding_spec(df, spec)` округляет все числовые колонки DataFrame.
- Модуль не выполняет отдельное tolerance-based сравнение; регрессионный снимок сравнивает уже округлённый канонический CSV.

## Example 1 — formalin (`histamine_nm, R_surf, R_int, G_signal, G_signal_pct, loss -> 1 decimal`)

- `rounding_spec`: `RoundingSpec.from_model("formalin")`
- `raw`: `time_h=1.0, histamine_nm=12.26, R_surf=0.72, R_int=0.18, G_signal=3.84, G_signal_pct=384.44, loss=0.14`
- `rounded`: `time_h=1.0, histamine_nm=12.3, R_surf=0.7, R_int=0.2, G_signal=3.8, G_signal_pct=384.4, loss=0.1`

## Example 2 — hot plate (`histamine_nm -> 1 decimal; R_surf, R_int, G_signal, G_signal_pct, loss -> 2 decimals`)

- `rounding_spec`: `RoundingSpec.from_model("hot_plate")`
- `raw`: `time_h=0.5, histamine_nm=9.44, R_surf=0.634, R_int=0.281, G_signal=1.194, G_signal_pct=119.44, loss=0.028`
- `rounded`: `time_h=0.5, histamine_nm=9.4, R_surf=0.63, R_int=0.28, G_signal=1.19, G_signal_pct=119.44, loss=0.03`

## Example 3 — default rounding for unspecified numeric columns

- `rounding_spec`: `RoundingSpec.from_model("capsaicin")`
- Для `capsaicin` явно задано только `histamine_nm -> 1 decimal`.
- Остальные числовые колонки, не перечисленные в `spec.decimals`, округляются по `default_decimals=2`.
- Пример: `time_h=0.3333` становится `0.33`, а `histamine_nm=8.24` становится `8.2`.
