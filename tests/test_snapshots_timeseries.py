import numpy as np
import pandas as pd
import pytest

pytest.importorskip("pytest_regtest", reason="optional dependency for snapshot tests")

from src.validation.compare import apply_rounding_spec
from src.validation.rounding_spec import RoundingSpec


def test_timeseries_snapshot_after_rounding(regtest) -> None:  # type: ignore[no-untyped-def]
    times = np.linspace(0.0, 2.0, 5)
    raw = pd.DataFrame(
        {
            "time_h": times,
            "H": 10.0 * np.exp(-0.3 * times),
            "R_surf": 0.63 + 0.01 * np.sin(times),
            "R_int": 0.22 + 0.01 * np.cos(times),
            "G": 1.2 + 0.1 * np.exp(-times),
            "loss": 0.03 + 0.01 * times,
        }
    )

    rounded = apply_rounding_spec(raw, RoundingSpec.from_model("hot_plate"))
    regtest.write(rounded.to_csv(index=False))
