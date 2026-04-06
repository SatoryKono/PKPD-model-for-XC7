from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from pkpd_xc7.config.loader import load_model_config, load_model_config_payload
from pkpd_xc7.config.schemas import ModelConfig, ScenarioDriver

SCENARIO_CONFIG_CASES = [
    ("formalin", "rat", ["skin", "spinal_coord", "ganglia", "brain"]),
    ("capsaicin", "rat", ["skin", "spinal_coord", "ganglia", "brain"]),
    ("compound_48_80", "mouse", ["skin", "spinal_coord", "ganglia", "brain"]),
    ("carrageenan", "rat", ["muscle", "spinal_coord", "ganglia", "brain"]),
    ("hot_plate", "mouse", ["skin", "spinal_coord", "ganglia", "brain"]),
    ("acetic_writhing", "mouse", ["peritoneum", "spinal_coord", "ganglia", "brain"]),
    ("zymosan", "mouse", ["peritoneum", "spinal_coord", "ganglia", "brain"]),
]


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def scenario_examples_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "examples" / "configs" / "scenarios"


def _scenario_payload(**kwargs: object) -> dict:
    base: dict[str, object] = {
        "model_id": "m",
        "compound": "c",
        "traceability": {"source_in_report": "src"},
        "assumptions": ["a"],
        "driver": {"driver_type": "scenario", "scenario_id": "formalin"},
        "tissues": ["skin"],
        "time_grid_h": [0.0, 1.0],
    }
    base.update(kwargs)
    return base


def test_scenario_config_from_fixture(fixtures_dir: Path) -> None:
    path = fixtures_dir / "phase1_minimal_scenario.yaml"
    cfg = load_model_config(path)
    assert cfg.driver.driver_type == "scenario"
    h = cfg.config_sha256()
    assert len(h) == 64


def test_a002_empty_source_in_report() -> None:
    p = _scenario_payload()
    p["traceability"] = {"source_in_report": ""}
    with pytest.raises(ValidationError):
        ModelConfig.model_validate(p)


def test_assumptions_empty_item() -> None:
    p = _scenario_payload(assumptions=["ok", "  "])
    with pytest.raises(ValueError):
        ModelConfig.model_validate(p)


def test_time_grid_not_monotonic() -> None:
    p = _scenario_payload(time_grid_h=[1.0, 0.0])
    with pytest.raises(ValueError):
        ModelConfig.model_validate(p)


def test_time_grid_minutes_normalized_to_hours() -> None:
    p = _scenario_payload()
    p.pop("time_grid_h")
    p["time_grid"] = [0, 15, 30]
    p["time_unit"] = "min"
    cfg = ModelConfig.model_validate(p)
    assert cfg.time_grid_h == [0.0, 0.25, 0.5]


def test_time_grid_hours_normalized_without_change() -> None:
    p = _scenario_payload()
    p.pop("time_grid_h")
    p["time_grid"] = [0.0, 1.0, 2.0]
    p["time_unit"] = "h"
    cfg = ModelConfig.model_validate(p)
    assert cfg.time_grid_h == [0.0, 1.0, 2.0]


def test_time_grid_unsupported_unit() -> None:
    p = _scenario_payload()
    p.pop("time_grid_h")
    p["time_grid"] = [0, 15, 30]
    p["time_unit"] = "sec"
    with pytest.raises(ValidationError):
        ModelConfig.model_validate(p)


def test_assumptions_empty_list() -> None:
    p = _scenario_payload(assumptions=[])
    with pytest.raises(ValidationError):
        ModelConfig.model_validate(p)


def test_driver_union_invalid_tag() -> None:
    p = _scenario_payload()
    p["driver"] = {"driver_type": "composite", "scenario_id": "x"}
    with pytest.raises(ValidationError):
        ModelConfig.model_validate(p)


def test_scenario_id_alias_is_normalized() -> None:
    p = _scenario_payload(driver={"driver_type": "scenario", "scenario_id": "compound48_80"})
    cfg = ModelConfig.model_validate(p)
    assert isinstance(cfg.driver, ScenarioDriver)
    assert cfg.driver.scenario_id == "compound_48_80"


def test_species_alias_mice_is_normalized_to_mouse() -> None:
    cfg = ModelConfig.model_validate(_scenario_payload(species="mice"))
    assert cfg.species == "mouse"


def test_unknown_scenario_id_rejected() -> None:
    p = _scenario_payload(driver={"driver_type": "scenario", "scenario_id": "unknown"})
    with pytest.raises(ValidationError, match="Unsupported scenario_id='unknown'"):
        ModelConfig.model_validate(p)


def test_tissue_overrides_are_optional_for_backward_compatibility() -> None:
    cfg = ModelConfig.model_validate(_scenario_payload())
    assert cfg.tissue_overrides == {}


def test_tissue_aliases_are_normalized_to_canonical_ids() -> None:
    cfg = ModelConfig.model_validate(
        _scenario_payload(
            tissues=["skin", "spinal"],
            tissue_overrides={"spinal": {"trafficking": {"ec50_g_nm": 25.0}}},
        )
    )
    assert cfg.tissues == ["skin", "spinal_coord"]
    assert "spinal_coord" in cfg.tissue_overrides


def test_brain_is_allowed_as_canonical_tissue_and_override_key() -> None:
    cfg = ModelConfig.model_validate(
        _scenario_payload(
            tissues=["brain", "spinal_coord"],
            tissue_overrides={"brain": {"trafficking": {"ec50_g_nm": 25.0}}},
        )
    )
    assert cfg.tissues == ["brain", "spinal_coord"]
    assert "brain" in cfg.tissue_overrides


def test_tissue_overrides_unknown_tissue_rejected() -> None:
    p = _scenario_payload(
        tissues=["skin"],
        tissue_overrides={"spinaal": {"trafficking": {"ec50_g_nm": 25.0}}},
    )
    with pytest.raises(ValidationError, match="Unknown tissue_overrides keys"):
        ModelConfig.model_validate(p)


def test_pk_driver_requires_explicit_resolved_h_base_nm() -> None:
    payload = _scenario_payload(
        driver={"driver_type": "pk", "k_abs_per_h": 1.0, "k_elim_per_h": 0.5},
        tissues=["skin", "spinal_coord"],
    )
    with pytest.raises(ValidationError, match="PK driver requires explicit trafficking\\.h_base_nm"):
        ModelConfig.model_validate(payload)


def test_antagonist_pk_requires_resolved_species_and_tissue_mapping() -> None:
    payload = _scenario_payload(
        species=None,
        tissues=["skin", "brain"],
        antagonist_pk={
            "enabled": True,
            "source_xlsx": "pk.xlsx",
            "dose_mg_per_kg": 90.0,
            "tissue_map": {"skin": "skin"},
        },
    )
    with pytest.raises(ValidationError, match="requires species"):
        ModelConfig.model_validate(payload)


def test_antagonist_pk_normalizes_species_and_tissue_aliases() -> None:
    cfg = ModelConfig.model_validate(
        _scenario_payload(
            species="mice",
            tissues=["skin", "spinal"],
            antagonist_pk={
                "enabled": True,
                "source_xlsx": "pk.xlsx",
                "species": "rats",
                "dose_mg_per_kg": 90.0,
                "tissue_map": {
                    "skin": "skin",
                    "spinal": "spinal cord",
                },
            },
        )
    )
    assert cfg.species == "mouse"
    assert cfg.antagonist_pk is not None
    assert cfg.antagonist_pk.species == "rat"
    assert cfg.antagonist_pk.tissue_map["spinal_coord"] == "spinal cord"


def test_tissue_overrides_hash_is_deterministic_for_identical_payloads() -> None:
    payload = _scenario_payload(
        tissues=["skin", "spinal_coord"],
        tissue_overrides={
            "spinal_coord": {
                "trafficking": {"ec50_g_nm": 25.0, "constitutive_activity": 0.1},
                "formalin_profile": {"h_base_nm": 3.0},
            }
        },
    )
    cfg_a = ModelConfig.model_validate(payload)
    cfg_b = ModelConfig.model_validate(dict(payload))
    assert cfg_a.config_sha256() == cfg_b.config_sha256()


@pytest.mark.parametrize(("scenario_id", "expected_species", "expected_tissues"), SCENARIO_CONFIG_CASES)
def test_scenario_example_configs_validate(
    scenario_examples_dir: Path,
    scenario_id: str,
    expected_species: str,
    expected_tissues: list[str],
) -> None:
    path = scenario_examples_dir / f"{scenario_id}.yaml"
    cfg = load_model_config(path)

    assert isinstance(cfg.driver, ScenarioDriver)
    assert cfg.driver.scenario_id == scenario_id
    assert cfg.species == expected_species
    assert cfg.tissues == expected_tissues
    assert "brain" in cfg.tissue_overrides
    assert cfg.tissue_overrides["brain"].trafficking is not None
    assert len(cfg.config_sha256()) == 64


def test_shared_config_payload_merges_before_validation(scenario_examples_dir: Path) -> None:
    path = scenario_examples_dir / "formalin.yaml"

    payload = load_model_config_payload(path)
    cfg = load_model_config(path)

    assert payload["trafficking"]["k_int_max_per_h"] == pytest.approx(1.25)
    assert payload["trafficking"]["h_base_nm"] == pytest.approx(10.0)
    assert "profile_shape" not in payload["formalin_profile"]
    assert payload["tissue_overrides"]["skin"]["formalin_profile"]["profile_shape"] == "gaussian_sum"
    assert payload["tissue_overrides"]["spinal_coord"]["trafficking"]["k_int_max_per_h"] == pytest.approx(1.4)
    assert payload["tissue_overrides"]["spinal_coord"]["formalin_profile"]["profile_shape"] == "gaussian_sum"
    assert payload["tissue_overrides"]["brain"]["formalin_profile"]["profile_shape"] == "gaussian_sum"
    assert payload["tissue_overrides"]["brain"]["trafficking"]["k_int_max_per_h"] == pytest.approx(1.4)
    assert payload["tissue_overrides"]["ganglia"]["trafficking"]["k_int_max_per_h"] == pytest.approx(1.8)
    assert payload["tissue_overrides"]["ganglia"]["formalin_profile"]["profile_shape"] == "gaussian_sum"
    assert payload["tissue_overrides"]["spinal_coord"]["trafficking"]["h_base_nm"] == pytest.approx(2.0)
    assert cfg.tissue_overrides["ganglia"].trafficking is not None
    assert cfg.tissue_overrides["spinal_coord"].trafficking is not None
    assert cfg.tissue_overrides["spinal_coord"].trafficking.k_int_max_per_h == pytest.approx(1.4)
    assert cfg.tissue_overrides["ganglia"].trafficking.k_rec_per_h == pytest.approx(0.7)
    assert cfg.tissue_overrides["ganglia"].trafficking.k_int_max_per_h == pytest.approx(1.8)
    assert cfg.tissue_overrides["ganglia"].trafficking.h_base_nm == pytest.approx(10.0)