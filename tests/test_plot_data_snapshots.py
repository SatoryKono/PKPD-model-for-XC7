from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.pipelines.artifact_generator import generate_unified_artifacts


def _write_simulation_csv(path: Path) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "time_h": [0.0, 1.0, 2.0],
            "R_surf": [1.0, 0.8, 0.6],
            "R_int": [0.0, 0.2, 0.4],
            "histamine_nm": [0.0, 100.0, 200.0],
        }
    )
    frame.to_csv(path, index=False)
    return frame


def test_unified_generator_creates_required_plots_and_snapshots(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    source = _write_simulation_csv(run_dir / "simulation.csv")

    artifacts = generate_unified_artifacts(run_dir)

    assert artifacts.plots["histamine"].exists()
    assert artifacts.plots["receptors"].exists()
    assert artifacts.plots["gsignaling"].exists()

    hist = pd.read_csv(artifacts.plot_snapshots["histamine"])
    rec = pd.read_csv(artifacts.plot_snapshots["receptors"])
    gsig = pd.read_csv(artifacts.plot_snapshots["gsignaling"])

    assert hist.to_dict(orient="list") == {
        "time_h": [0.0, 1.0, 2.0],
        "histamine_nm": [0.0, 100.0, 200.0],
    }
    assert rec.to_dict(orient="list") == {
        "time_h": [0.0, 1.0, 2.0],
        "R_surf": [1.0, 0.8, 0.6],
        "R_int": [0.0, 0.2, 0.4],
    }

    expected_default_g = (source["R_surf"] * source["histamine_nm"]) / (100.0 + source["histamine_nm"])
    assert gsig.columns.tolist() == ["time_h", "G_signal"]
    assert gsig["G_signal"].round(12).tolist() == expected_default_g.round(12).tolist()


def test_snapshot_data_uses_configurable_ec50_when_provided(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    source = _write_simulation_csv(run_dir / "simulation.csv")

    artifacts = generate_unified_artifacts(run_dir, config_meta={"ec50_nm": 50.0})
    gsig = pd.read_csv(artifacts.plot_snapshots["gsignaling"])

    expected_custom_g = (source["R_surf"] * source["histamine_nm"]) / (50.0 + source["histamine_nm"])
    assert gsig["G_signal"].round(12).tolist() == expected_custom_g.round(12).tolist()
