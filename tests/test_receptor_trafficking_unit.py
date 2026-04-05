from __future__ import annotations

import numpy as np

from src.models.receptor_trafficking import (
    DEFAULT_PARAMS,
    k_int_eff,
    receptor_trafficking_rhs,
    steady_state_ic,
)


def test_k_int_eff_zero_histamine_is_zero() -> None:
    assert k_int_eff(0.0) == 0.0


def test_k_int_eff_approaches_k_int_max_for_large_histamine() -> None:
    value = k_int_eff(1e12)
    assert np.isclose(value, DEFAULT_PARAMS.k_int_max, rtol=0.0, atol=1e-6)


def test_steady_state_ic_is_bounded_and_mass_conserved() -> None:
    r_surf0, r_int0 = steady_state_ic(50.0)
    assert 0.0 <= r_surf0 <= 1.0
    assert 0.0 <= r_int0 <= 1.0
    assert abs((r_surf0 + r_int0) - 1.0) < 1e-6


def test_rhs_at_steady_state_returns_zero_vector() -> None:
    h_base_nm = 50.0
    y0 = steady_state_ic(h_base_nm)
    dydt = receptor_trafficking_rhs(t_h=0.0, y=y0, histamine_nm=h_base_nm)
    assert np.allclose(dydt, np.zeros(2), atol=1e-10)


def test_rhs_clipping_mode_is_explicit_and_logged() -> None:
    assumptions: list[str] = []
    dydt = receptor_trafficking_rhs(
        t_h=0.0,
        y=(1.2, -0.2),
        histamine_nm=10.0,
        clip_state_explicit=True,
        assumptions=assumptions,
    )
    assert dydt.shape == (2,)
    assert any("Scenario assumption" in text for text in assumptions)
