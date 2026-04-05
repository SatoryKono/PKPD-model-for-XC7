"""Atomic file writes (temp then replace)."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd


def write_text_atomic(path: str | Path, text: str, *, encoding: str = "utf-8") -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(text, encoding=encoding)
    os.replace(tmp, target)
    return target


def dataframe_to_csv_atomic(
    frame: pd.DataFrame,
    path: str | Path,
    *,
    index: bool = False,
    encoding: str = "utf-8",
    sep: str = ",",
) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    frame.to_csv(tmp, index=index, encoding=encoding, sep=sep)
    os.replace(tmp, target)
    return target


__all__ = ["dataframe_to_csv_atomic", "write_text_atomic"]
