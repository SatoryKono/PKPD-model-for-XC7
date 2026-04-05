# Validation examples: marker tables vs simulation output

Ниже — примеры строк сравнения `expected` vs `actual` после применения `rounding_spec`.

## Example 1 — formalin (`H, R_surf, R_int, G, loss -> 1 decimal`)

- `rounding_spec`: `RoundingSpec.from_model("formalin")`
- `expected`: `time_h=1.0, H=12.3, R_surf=0.7, R_int=0.2, G=3.8, loss=0.1`
- `actual`: `time_h=1.0, H=12.26, R_surf=0.72, R_int=0.18, G=3.84, loss=0.14`
- `rounded actual`: `time_h=1.0, H=12.3, R_surf=0.7, R_int=0.2, G=3.8, loss=0.1`
- Result: match

## Example 2 — hot plate (`H -> 1 decimal; R_surf, R_int, G, loss -> 2 decimals`)

- `rounding_spec`: `RoundingSpec.from_model("hot_plate")`
- `expected`: `time_h=0.5, H=9.4, R_surf=0.63, R_int=0.28, G=1.19, loss=0.03`
- `actual`: `time_h=0.5, H=9.44, R_surf=0.634, R_int=0.281, G=1.194, loss=0.028`
- `rounded actual`: `time_h=0.5, H=9.4, R_surf=0.63, R_int=0.28, G=1.19, loss=0.03`
- Result: match

## Example 3 — tolerated diff for 1-decimal outputs (`abs_tol <= 0.1`)

- `rounding_spec`: `RoundingSpec.from_model("capsaicin")`
- `expected`: `H=8.1`
- `actual`: `H=8.2`
- `|expected-actual|=0.1` -> accepted for 1-decimal metrics by regression comparator policy.
