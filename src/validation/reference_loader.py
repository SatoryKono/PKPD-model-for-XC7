from __future__ import annotations

from pathlib import Path

import pandas as pd

MODEL_CSV_CANDIDATES: dict[str, tuple[str, ...]] = {
    "formalin": ("formalin_marker_points.csv", "formalin/marker_points.csv"),
    "compound48_80": (
        "compound48_80_marker_points.csv",
        "compound_48_80_marker_points.csv",
        "compound48_80/marker_points.csv",
    ),
    "capsaicin": ("capsaicin_marker_points.csv", "capsaicin/marker_points.csv"),
    "carrageenin": (
        "carrageenin_marker_points.csv",
        "carrageenan_marker_points.csv",
        "carrageenin/marker_points.csv",
    ),
    "hot_plate": ("hot_plate_marker_points.csv", "hot_plate/marker_points.csv"),
}


def _resolve_base_dir(base_dir: str | Path | None) -> Path:
    if base_dir is not None:
        return Path(base_dir)
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "report_v12_extracted"


def find_reference_csv(model_key: str, base_dir: str | Path | None = None) -> Path | None:
    base = _resolve_base_dir(base_dir)
    canonical_key = model_key.strip().lower().replace("-", "_").replace(" ", "_")
    candidates = MODEL_CSV_CANDIDATES.get(canonical_key, ())

    for relative_path in candidates:
        candidate = base / relative_path
        if candidate.exists():
            return candidate
    return None


def load_reference_marker_table(model_key: str, base_dir: str | Path | None = None) -> pd.DataFrame:
    path = find_reference_csv(model_key, base_dir=base_dir)
    if path is None:
        raise FileNotFoundError(
            f"Reference marker table for model={model_key!r} not found under { _resolve_base_dir(base_dir) }"
        )
    return pd.read_csv(path)
