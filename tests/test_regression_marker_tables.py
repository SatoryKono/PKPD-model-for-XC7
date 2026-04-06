from pathlib import Path

import pytest

from src.validation.compare import compare_marker_tables
from src.validation.reference_loader import find_reference_csv, load_reference_marker_table
from src.validation.regression_harness import pipeline_marker_table_vs_reference
from src.validation.rounding_spec import RoundingSpec


REPORT_DIR = Path(__file__).resolve().parents[1] / "report_v12_extracted"

pytestmark = pytest.mark.regression_data


@pytest.mark.parametrize(
    ("model_key", "xfail_reason"),
    [
        ("formalin", None),
        ("compound48_80", None),
        ("capsaicin", None),
        ("carrageenin", None),
        ("hot_plate", None),
        ("acetic_writhing", "[неполные данные] model has no marker table"),
    ],
)
def test_marker_points_regression_against_report_reference(
    model_key: str,
    xfail_reason: str | None,
) -> None:
    if xfail_reason is not None:
        pytest.xfail(xfail_reason)

    if not REPORT_DIR.exists():
        pytest.xfail("[неполные данные] report_v12_extracted/ is not attached to repository")

    ref_path = find_reference_csv(model_key, base_dir=REPORT_DIR)
    if ref_path is None:
        pytest.xfail(f"[неполные данные] marker table is missing for model={model_key}")

    expected = load_reference_marker_table(model_key, base_dir=REPORT_DIR)

    actual = pipeline_marker_table_vs_reference(expected, model_key=model_key)

    diffs = compare_marker_tables(
        expected,
        actual,
        RoundingSpec.from_model(model_key),
        abs_tol_1dp=0.1,
    )

    assert diffs == []
