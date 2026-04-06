from __future__ import annotations

from pandas.testing import assert_frame_equal

from pkpd_xc7.config.schemas import ModelConfig
from pkpd_xc7.simulation.runner import run_experiment


def _noncanonical_payload() -> dict:
    return {
        "model_id": "canonical_test_model",
        "compound": "xc7",
        "loss_mode": "mse",
        "assumptions": ["unit_equivalence"],
        "traceability": {
            "source_in_report": "Unit conversion benchmark",
            "source_reference": "tests",
            "source_version": "1",
        },
        "time_grid": [0.0, 30.0, 60.0, 90.0, 120.0],
        "time_unit": "min",
        "driver": {"driver_type": "pk", "dose": 100.0, "k_abs_per_h": 1.2, "k_elim_per_h": 0.3},
        "trafficking": {"h_base_nm": 50.0},
        "tissues": ["brain"],
    }


def _canonical_config() -> ModelConfig:
    return ModelConfig.model_validate(
        {
            "model_id": "canonical_test_model",
            "compound": "xc7",
            "loss_mode": "mse",
            "assumptions": ["unit_equivalence"],
            "traceability": {
                "source_in_report": "Unit conversion benchmark",
                "source_reference": "tests",
                "source_version": "1",
            },
            "driver": {"driver_type": "pk", "dose": 100.0, "k_abs_per_h": 1.2, "k_elim_per_h": 0.3},
            "trafficking": {"h_base_nm": 50.0},
            "tissues": ["brain"],
            "time_grid_h": [0.0, 0.5, 1.0, 1.5, 2.0],
        }
    )


def test_model_config_normalizes_time_units_to_time_grid_h() -> None:
    normalized = ModelConfig.model_validate(_noncanonical_payload())
    canonical = _canonical_config()

    assert normalized.time_grid_h == canonical.time_grid_h


def test_run_experiment_is_equivalent_for_min_and_hour_inputs() -> None:
    normalized = ModelConfig.model_validate(_noncanonical_payload())
    canonical = _canonical_config()

    simulation_from_min = run_experiment(normalized)
    simulation_from_hours = run_experiment(canonical)

    assert_frame_equal(simulation_from_min, simulation_from_hours)
