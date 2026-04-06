# Диаграмма параметров formalin

**Поддерживаемый путь:** `ModelConfig.histamine_profile.profile_id=formalin`. Базовые параметры formalin теперь **детерминированно выводятся** из summary-величин (`H_base`, `peak I`, `peak II`, `t1/2`) через `derive_formalin_params_from_summary`. `ModelConfig.formalin_profile` остаётся как legacy whitelist-override поверх уже выведенных параметров. **Оптимизация (least_squares) в рабочем пайплайне не используется.**

```mermaid
flowchart LR
    summarySpec["Formalin summary by tissue<br/>H_base, peak I, peak II, t1/2"]
    derivation["derive_formalin_params_from_summary<br/>fixed shape ratios + phase II peak matching"]
    runtimeProfile["default_formalin_params<br/>HistamineProfileParams(profile_type=bi)"]
    histamineProfile["ModelConfig.histamine_profile<br/>profile_id=formalin"]
    legacyOverrides["ModelConfig.formalin_profile<br/>legacy optional override"]
    resolver["resolve_formalin_params<br/>deterministic merge + validation"]
    modelEval["formalin_histamine(t, params)<br/>H(t)=h_base+pulse1+pulse2"]

    summarySpec --> derivation
    derivation --> runtimeProfile
    runtimeProfile --> resolver
    histamineProfile --> modelEval
    legacyOverrides --> resolver
    resolver --> modelEval
```
