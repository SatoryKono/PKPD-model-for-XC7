from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from pkpd_xc7.config.schemas import ModelConfig

SHARED_CONFIGS_FIELD = "shared_configs"


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ValueError(f"YAML config at '{path}' must be a mapping at the top level.")
    return payload


def _normalize_shared_paths(value: Any, *, path: Path) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return list(value)
    raise ValueError(
        f"Field '{SHARED_CONFIGS_FIELD}' in '{path}' must be a string path or a list of string paths."
    )


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for key, value in base.items():
        merged[key] = value
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_model_config_payload(path: Path | str, *, _seen: set[Path] | None = None) -> dict[str, Any]:
    resolved_path = Path(path).resolve()
    seen = set() if _seen is None else set(_seen)
    if resolved_path in seen:
        cycle = " -> ".join(str(item) for item in [*seen, resolved_path])
        raise ValueError(f"Cyclic shared config reference detected: {cycle}")
    seen.add(resolved_path)

    payload = _read_yaml_mapping(resolved_path)
    raw_shared = payload.pop(SHARED_CONFIGS_FIELD, None)
    shared_paths = _normalize_shared_paths(raw_shared, path=resolved_path)

    merged: dict[str, Any] = {}
    for shared_rel_path in shared_paths:
        shared_path = (resolved_path.parent / shared_rel_path).resolve()
        shared_payload = load_model_config_payload(shared_path, _seen=seen)
        merged = _deep_merge(merged, shared_payload)
    return _deep_merge(merged, payload)


def load_model_config(path: Path | str) -> ModelConfig:
    payload = load_model_config_payload(path)
    return ModelConfig.model_validate(payload)
