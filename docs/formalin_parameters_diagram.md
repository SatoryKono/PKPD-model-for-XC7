# Диаграмма параметров formalin

**Поддерживаемый путь:** фиксированные параметры из `default_formalin_params` и опциональные whitelist-override из `ModelConfig.formalin_profile` через `resolve_formalin_params` / `resolve_formalin_params_from_model_config`. **Оптимизация (least_squares) в рабочем пайплайне не используется.** Исторический пример `runs/example_fit/fitted_params.json` и программный legacy-вызов `fit_histamine_to_markers` помечены как deprecated (см. `CHANGELOG.md`).

```mermaid
flowchart LR
    defaultFormalin["default_formalin_params<br/>profile_type=bi<br/>tissue=skin<br/>h_base_nm=50.0"]
    phase1Defaults["phase1 defaults<br/>amplitude_nm=950.0<br/>t0_h=0.0<br/>tau_rise_h=0.03<br/>tau_fall_h=0.12"]
    phase2Defaults["phase2 defaults<br/>amplitude_nm=400.0<br/>t0_h=20/60 h (0.3333)<br/>tau_rise_h=0.15<br/>tau_fall_h=0.80"]
    modelEval["formalin_histamine(t, params)<br/>H(t)=h_base+pulse1+pulse2"]

    configOverrides["ModelConfig.formalin_profile<br/>(optional whitelist)"]
    resolver["resolve_formalin_params<br/>deterministic merge + validation"]

    defaultFormalin --> phase1Defaults
    defaultFormalin --> phase2Defaults
    defaultFormalin --> resolver
    configOverrides --> resolver
    resolver --> modelEval
    phase1Defaults --> modelEval
    phase2Defaults --> modelEval
```
