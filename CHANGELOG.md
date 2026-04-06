# Changelog

## [Unreleased]

### Non-breaking

- **XC7 competitive antagonism on internalization**: `internalization_drive`, `k_int_eff`, `steady_state_ic`, `receptor_trafficking_rhs`, and exported `beta_arr_signal` / `internalization_drive` / `k_int_eff_per_h` now account for tissue XC7 concentration through a competitive shift `H_eff = H / (1 + C / Kb_arr)`. New optional trafficking fields `kb_arr_nm` and `kb_g_nm` are accepted by the YAML schema and exported via resolved trafficking metadata; when omitted they deterministically fall back to the matching pathway EC50 values.
- **Canonical CNS tissue ids**: scenario configs now use `spinal_coord` as the canonical CNS tissue id; legacy YAML alias `spinal` is normalized during config loading for backward compatibility. A temporary `brain` runtime profile is now registered as an explicit proxy of `spinal_coord`, and `examples/configs/shared/common.yaml` includes shared overrides for `muscle`, `spinal_coord`, `brain`, and `ganglia`.
- **Tissue-specific scenario parameters**: `ModelConfig` now accepts optional `tissue_overrides` with per-tissue `trafficking` and formalin-only `formalin_profile` overrides. Resolution order is deterministic: registry defaults -> top-level config defaults -> `tissue_overrides[<tissue>]`.
- **Resolved trafficking metadata**: `meta.yaml` now writes `default_trafficking_params` plus `trafficking_params_by_tissue`, so plotting and post-run analysis can reproduce the exact per-tissue pharmacology used by the simulation. Legacy loaders still accept older runs that only contain `trafficking_params`.
- **Docs contract sync**: `docs/yaml_configuration_guide.md` now matches the current `ModelConfig`/CLI contract, including required `driver`, string-based `tissues`, supported `time_grid_h` vs `time_grid` + `time_unit`, and removal of stale legacy fields from examples.
- **Canonical scenario ids in artifacts**: documentation now explicitly states that scenario aliases are normalized before export, so `driver_id` in `simulation.csv` and `meta.yaml` is written with the canonical registry id such as `compound_48_80`.
- **Validation examples sync**: `docs/validation_examples.md` now documents the actual phase-8 API (`RoundingSpec` + `apply_rounding_spec`) and no longer claims an unsupported tolerance-based comparator policy.
- **Phase 7 visualization**: added `pkpd_xc7.io.loaders` with `SimulationRun` / `load_simulation_run`, plus `pkpd_xc7.viz` time-axis and plotting helpers that render figures strictly from `simulation.csv` and `meta.yaml`.
- **Reproducible plotting contract**: documentation plot scripts now accept `--run-dir`, read `trafficking_params` from exported `meta.yaml`, and no longer duplicate ODE math or hard-code pharmacology constants inside the plotting path.
- **Visualization contract**: plotting now resolves `ec50_g_nm`, `ec50_barr_nm`, `hill_n`, and `constitutive_activity` per tissue from `meta.yaml -> trafficking_params_by_tissue`, while still accepting legacy single-mapping runs for backward compatibility.
- **Phase 8 validation**: added `pkpd_xc7.validation` module (`RoundingSpec`, `apply_rounding_spec`) for deterministic regression testing. Column names in snapshots aligned with export contract (`histamine_nm`, `G_signal`, etc.). Restored `test_snapshots_timeseries.py` in CI.
- **Phase 6 scenario registry**: scenario-driven `H(t)` now resolves through a deterministic registry with canonical `scenario_id`, tissue-level `h_base_nm`, and runtime shapes `pulse` / `gaussian_sum` stored in hours and nM.
- **Scenario shape precedence**: runtime resolves scenario form in this order: `formalin_profile.profile_shape` -> `driver.profile_shape` -> registry default. `driver.profile_shape` is optional, and legacy aliases such as `compound48_80` are normalized to canonical ids like `compound_48_80`.
- **Formalin overrides**: `formalin_profile` remains a formalin-only override block; its YAML fields stay in minutes (`*_min`) and are deterministically converted to hours before the mathematical `H(t)` functions are evaluated.
- **Phase 3 fixes**: `receptor_trafficking_rhs` again supports optional explicit state-clipping traceability, removing the runtime `NameError` that blocked IVP execution and runner tests.
- **G signaling contract**: `run_experiment` now uses `pkpd_xc7.models.h3_signaling` as the single source of truth for `G_signal` / `G_signal_pct`, including Hill activation and `constitutive_activity`; the config schema version is unchanged because the YAML contract did not change.
- **Phase 4 export contract**: `simulation.csv` layout is centralized in `pkpd_xc7.io.layout` with `simulation_schema_version = 1.0.0`, and CLI now writes a sidecar `meta.yaml` with column order, row count, config hash, driver metadata, and solver settings.
- **Regression snapshots**: updated the phase-1 runner snapshot to reflect real phase-3 ODE output instead of the former zero-valued stub trajectory.
- **Phase 2 core**: added `pkpd_xc7.models.receptor_trafficking` with `TraffickingCoreParams`, `k_int_eff`, analytic `steady_state_ic`, and explicit mass-balance assumption `k_deg == k_synth`.
- **G signaling**: added `pkpd_xc7.models.h3_signaling` with model-space fractions in `[0, 1]`; report-space percentages stay in post-processing via `G_signal_pct = 100 * G_signal`.
- **Solver contract**: added deterministic `pkpd_xc7.solvers.solve_ivp_wrapper` with explicit `method` (`LSODA` / `BDF` / `Radau`), `rtol`, `atol`, `max_step`, and metadata snapshot helpers.
- **Config bridge**: `ModelConfig` now exposes optional `trafficking` parameters, and `simulation.model_mapping` provides a stable mapper from Pydantic config to the lightweight ODE core container.
- **Tests**: added phase-2 unit tests for steady state, clipping, G signaling, solver determinism, marker extraction, and stiff smoke coverage.

### Breaking (migration)

- **PK baseline histamine contract**: PK runs no longer fall back to an implicit `h_base_nm=50.0`. Every PK tissue must now resolve `trafficking.h_base_nm` explicitly from the top-level `trafficking` block or from `tissue_overrides[<tissue>].trafficking.h_base_nm`. This makes PK runtime and exported `meta.yaml -> trafficking_params_by_tissue[*].h_base_nm` share the same traceable source of truth.

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
