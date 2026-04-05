from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml
from pandas.testing import assert_frame_equal

from src import api
from src.config.schemas import ModelConfig


def _noncanonical_payload() -> dict:
    return {
        "model_id": "canonical_test_model",
        "compound": "histamine",
        "loss_mode": "mse",
        "assumptions": ["unit_equivalence"],
        "traceability": {
            "source_in_report": "Unit conversion benchmark",
            "source_reference": "tests",
            "source_version": "1",
        },
        "time_grid": [0.0, 30.0, 60.0, 90.0, 120.0],
        "time_unit": "min",
        "initial_concentration": 0.1,
        "concentration_unit": "uM",
        "kinetics": {
            "k_abs": 0.02,
            "k_elim": 0.005,
            "rate_unit": "1/min",
        },
        "tissues": [
            {
                "name": "plasma",
                "volume": 1.0,
                "volume_unit": "L",
                "partition_coeff": 1.0,
            }
        ],
        "plots": [],
    }


def _canonical_config() -> ModelConfig:
    return ModelConfig.model_validate(
        {
            "model_id": "canonical_test_model",
            "compound": "histamine",
            "loss_mode": "mse",
            "assumptions": ["unit_equivalence"],
            "traceability": {
                "source_in_report": "Unit conversion benchmark",
                "source_reference": "tests",
                "source_version": "1",
            },
            "time_grid": [0.0, 0.5, 1.0, 1.5, 2.0],
            "time_unit": "h",
            "initial_concentration": 100.0,
            "concentration_unit": "nM",
            "kinetics": {
                "k_abs": 1.2,
                "k_elim": 0.3,
                "rate_unit": "1/h",
            },
            "tissues": [
                {
                    "name": "plasma",
                    "volume": 1.0,
                    "volume_unit": "L",
                    "partition_coeff": 1.0,
                }
            ],
            "plots": [],
        }
    )


def test_simulate_path_and_model_config_are_equivalent_across_units(tmp_path: Path) -> None:
    config_path = tmp_path / "noncanonical.yaml"
    config_path.write_text(yaml.safe_dump(_noncanonical_payload(), sort_keys=False), encoding="utf-8")

    out_from_path = tmp_path / "run_from_path"
    out_from_model = tmp_path / "run_from_model"

    api.simulate(config_path, out_from_path)
    api.simulate(_canonical_config(), out_from_model)

    simulation_from_path = pd.read_csv(out_from_path / "simulation.csv")
    simulation_from_model = pd.read_csv(out_from_model / "simulation.csv")
    assert_frame_equal(simulation_from_path, simulation_from_model)

    metadata = json.loads((out_from_model / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["canonical_units"] is True
    assert metadata["canonical_unit_tags"] == {
        "time": "h",
        "concentration": "nM",
        "rate": "1/h",
    }
