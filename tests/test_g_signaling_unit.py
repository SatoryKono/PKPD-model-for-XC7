from __future__ import annotations

import numpy as np

from src.histamine_profiles import Tissue
from src.models.g_signaling import (
    constitutive_activity_fraction_for_tissue,
    default_g_signal_params_for_tissue,
    g_signal_percent,
)


def test_constitutive_activity_fraction_matches_reported_tissue_defaults() -> None:
    assert np.isclose(constitutive_activity_fraction_for_tissue(Tissue.SKIN), 0.05)
    assert np.isclose(constitutive_activity_fraction_for_tissue(Tissue.GANGLIA), 0.10)
    assert np.isclose(constitutive_activity_fraction_for_tissue(Tissue.CNS), 0.25)


def test_g_signal_percent_uses_model3_formula() -> None:
    params = default_g_signal_params_for_tissue(Tissue.SKIN, ec50_g_nm=50.0, hill_n=1.0)
    value = g_signal_percent(histamine_nm=50.0, r_surf=0.8, params=params)
    expected = (0.05 + (1.0 - 0.05) * (50.0 / (50.0 + 50.0))) * 0.8 * 100.0
    assert np.isclose(value, expected)


def test_g_signal_percent_vectorized_output_is_bounded_by_surface_fraction() -> None:
    params = default_g_signal_params_for_tissue(Tissue.SKIN, ec50_g_nm=50.0, hill_n=1.0)
    values = np.asarray(
        g_signal_percent(
            histamine_nm=np.array([0.0, 50.0, 500.0]),
            r_surf=np.array([1.0, 0.8, 0.6]),
            params=params,
        ),
        dtype=float,
    )
    assert values.shape == (3,)
    assert np.all(values >= 0.0)
    assert np.all(values <= np.array([100.0, 80.0, 60.0]) + 1e-12)
