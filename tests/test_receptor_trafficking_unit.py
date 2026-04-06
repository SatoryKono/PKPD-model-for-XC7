from __future__ import annotations

import numpy as np
import pytest

from pkpd_xc7.models.h3_signaling import g_signaling_fraction
from pkpd_xc7.models.receptor_trafficking import (
    TraffickingCoreParams,
    k_int_eff,
    receptor_trafficking_rhs,
    steady_state_ic,
)


@pytest.fixture
def default_params() -> TraffickingCoreParams:
    return TraffickingCoreParams(
        k_int_max_per_h=3.0,
        k_rec_per_h=0.5,
        k_synth_per_h=0.05,
        ec50_barr_nm=1500.0,
        ec50_internalization_nm=1500.0,
        hill_n=1.0,
        ec50_g_nm=50.0,
        constitutive_activity=0.0,
    )


def test_k_int_eff_zero_histamine_is_zero(default_params: TraffickingCoreParams) -> None:
    assert k_int_eff(0.0, default_params) == pytest.approx(0.0)


def test_k_int_eff_approaches_k_int_max(default_params: TraffickingCoreParams) -> None:
    value = k_int_eff(1e12, default_params)
    assert np.isclose(value, default_params.k_int_max_per_h, rtol=0.0, atol=1e-6)


def test_steady_state_ic_is_bounded_and_mass_conserved(default_params: TraffickingCoreParams) -> None:
    r_surf0, r_int0 = steady_state_ic(50.0, default_params)
    assert 0.0 <= r_surf0 <= 1.0
    assert 0.0 <= r_int0 <= 1.0
    assert abs((r_surf0 + r_int0) - 1.0) < 1e-6


def test_rhs_at_steady_state_returns_zero_vector(default_params: TraffickingCoreParams) -> None:
    h_base_nm = 50.0
    y0 = steady_state_ic(h_base_nm, default_params)
    dydt = receptor_trafficking_rhs(t_h=0.0, y=y0, histamine_nm=h_base_nm, params=default_params)
    assert np.allclose(dydt, np.zeros(2), atol=1e-10)


def test_rhs_clipping_mode_is_explicit_and_logged(default_params: TraffickingCoreParams) -> None:
    assumptions: list[str] = []
    dydt = receptor_trafficking_rhs(
        t_h=0.0,
        y=(1.2, -0.2),
        histamine_nm=10.0,
        params=default_params,
        clip_state_explicit=True,
        assumptions=assumptions,
    )
    assert dydt.shape == (2,)
    assert any("Scenario assumption" in text for text in assumptions)


def test_g_signaling_formula() -> None:
    params = TraffickingCoreParams(
        k_int_max_per_h=3.0,
        k_rec_per_h=0.5,
        k_synth_per_h=0.05,
        ec50_barr_nm=1500.0,
        ec50_internalization_nm=1500.0,
        hill_n=1.0,
        ec50_g_nm=50.0,
        constitutive_activity=0.0,
    )
    assert g_signaling_fraction(0.0, 1.0, params) == pytest.approx(0.0)
    assert np.isclose(g_signaling_fraction(50.0, 0.8, params), 0.4)
