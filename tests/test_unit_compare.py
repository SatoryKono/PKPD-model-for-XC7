import pandas as pd

from src.validation.compare import apply_rounding_spec, compare_marker_tables
from src.validation.rounding_spec import RoundingSpec


def test_apply_rounding_spec_rounds_numeric_columns_by_metric() -> None:
    spec = RoundingSpec({"H": 1, "R_surf": 2, "*": 3})
    df = pd.DataFrame({"H": [12.34], "R_surf": [0.678], "comment": ["ok"]})

    out = apply_rounding_spec(df, spec)

    assert out.at[0, "H"] == 12.3
    assert out.at[0, "R_surf"] == 0.68
    assert out.at[0, "comment"] == "ok"


def test_compare_marker_tables_accepts_1dp_abs_tolerance_policy() -> None:
    spec = RoundingSpec({"H": 1, "*": 2})
    expected = pd.DataFrame({"H": [8.1], "G": [1.23]})
    actual = pd.DataFrame({"H": [8.2], "G": [1.23]})

    diffs = compare_marker_tables(expected, actual, spec, abs_tol_1dp=0.1)
    assert diffs == []


def test_compare_marker_tables_detects_mismatch_outside_policy() -> None:
    spec = RoundingSpec({"H": 1, "*": 2})
    expected = pd.DataFrame({"H": [8.1], "G": [1.23]})
    actual = pd.DataFrame({"H": [8.31], "G": [1.23]})

    diffs = compare_marker_tables(expected, actual, spec, abs_tol_1dp=0.1)

    assert len(diffs) == 1
    assert diffs[0].column == "H"
