from src.validation.rounding_spec import RoundingSpec, rounding_spec_by_model


def test_rounding_spec_formalin_all_marker_metrics_are_1dp() -> None:
    spec = RoundingSpec.from_model("formalin")
    assert spec.decimals_for("H") == 1
    assert spec.decimals_for("R_surf") == 1
    assert spec.decimals_for("R_int") == 1
    assert spec.decimals_for("G") == 1
    assert spec.decimals_for("loss") == 1


def test_rounding_spec_hot_plate_mix() -> None:
    spec = RoundingSpec.from_model("hot_plate")
    assert spec.decimals_for("H") == 1
    assert spec.decimals_for("R_surf") == 2
    assert spec.decimals_for("R_int") == 2
    assert spec.decimals_for("G") == 2
    assert spec.decimals_for("loss") == 2


def test_rounding_spec_catalog_contains_expected_models() -> None:
    catalog = rounding_spec_by_model()
    assert set(catalog) == {"formalin", "compound48_80", "capsaicin", "carrageenin", "hot_plate"}
