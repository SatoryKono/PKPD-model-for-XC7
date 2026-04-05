# Changelog

## [0.2.0] — 2026-04-06

### Non-breaking

- **ModelConfig** (optional sections, defaults preserve prior behaviour):
  - `parameter_resolution` (default `fixed_params_only`).
  - `trafficking`: optional H3R trafficking parameters; omitted block keeps previous built-in defaults.
  - `plot_proxy.g_signal_ec50_nm`: optional override for G_signal plots; if omitted, G proxy uses `trafficking.ec50_g_nm`.
  - `formalin_profile`: whitelist overrides for fixed formalin histamine parameters (`resolve_formalin_params`).
- **Metadata**: `metadata.json` and sidecar `meta.yaml` include `parameter_source` (`defaults` | `overrides`) and `optimization_applied` (bool).
- **Legacy fit**: `FitSpec.loss_mode` is passed to `scipy.optimize.least_squares(loss=...)` for `mse` / `huber` / `mae`; `nll` raises with a clear error.
- **I/O**: CSV/JSON/YAML writes for runs, exports, and legacy fit reports use temp-then-`os.replace`.
- **Validation**: `api.validate` uses `numpy.allclose` for floating-point columns.
- **Solver**: public `SolvedIvpResult` replaces reliance on SciPy private `OdeResult`.

### Breaking (migration)

- **CLI**: new `fit` / `fit-legacy` commands exit with code 2 and migration text; interactive optimization is not supported on the CLI.
- **Deprecation**: `fit_histamine_to_markers` emits `DeprecationWarning`; use fixed parameters via config.

### Tests / CI

- Regression marker test compares **pipeline output** vs reference CSV (no longer self-referential).
- CI runs `test_api_canonical_units`, `test_api_simulation_refactor`, `test_model_params_integration`, `test_formalin_params_resolve`.
- `pytest-regtest` added to optional `dev` extras.
