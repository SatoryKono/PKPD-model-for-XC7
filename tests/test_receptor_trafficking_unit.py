from __future__ import annotations

import numpy as np
import pytest

from pkpd_xc7.models.h3_signaling import agonist_g_signal_fraction, beta_arr_fraction, g_signaling_fraction
from pkpd_xc7.models.receptor_trafficking import (
    TraffickingCoreParams,
    internalization_drive,
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
        kb_arr_nm=150.0,
        hill_n=1.0,
        ec50_g_nm=50.0,
        kb_g_nm=50.0,
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
    xc7_nm = 75.0
    y0 = steady_state_ic(h_base_nm, default_params, xc7_nm=xc7_nm)
    dydt = receptor_trafficking_rhs(
        t_h=0.0,
        y=y0,
        histamine_nm=h_base_nm,
        params=default_params,
        xc7_nm=xc7_nm,
    )
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
        kb_arr_nm=150.0,
        hill_n=1.0,
        ec50_g_nm=50.0,
        kb_g_nm=50.0,
        constitutive_activity=0.0,
    )
    assert g_signaling_fraction(0.0, 1.0, params) == pytest.approx(0.0)
    assert np.isclose(g_signaling_fraction(50.0, 0.8, params), 0.4)


def test_g_no_antagonist(default_params: TraffickingCoreParams) -> None:
    histamine_nm = 50.0
    r_surf = 0.8
    legacy_agonist = agonist_g_signal_fraction(histamine_nm, r_surf, default_params)
    legacy_total = g_signaling_fraction(histamine_nm, r_surf, default_params)

    assert agonist_g_signal_fraction(histamine_nm, r_surf, default_params, xc7_nm=0.0) == pytest.approx(legacy_agonist)
    assert g_signaling_fraction(histamine_nm, r_surf, default_params, xc7_nm=0.0) == pytest.approx(legacy_total)


def test_g_full_block(default_params: TraffickingCoreParams) -> None:
    histamine_nm = 50.0
    r_surf = 1.0
    xc7_nm = 1e300

    agonist_fraction = agonist_g_signal_fraction(histamine_nm, r_surf, default_params, xc7_nm=xc7_nm)
    total_fraction = g_signaling_fraction(histamine_nm, r_surf, default_params, xc7_nm=xc7_nm)

    assert np.isfinite(agonist_fraction)
    assert np.isfinite(total_fraction)
    assert agonist_fraction == pytest.approx(0.0, abs=1e-12)
    assert total_fraction == pytest.approx(0.0, abs=1e-12)


def test_g_monotonic(default_params: TraffickingCoreParams) -> None:
    histamine_nm = 50.0
    r_surf = 0.9
    xc7_grid = (0.0, 10.0, 100.0, 1_000.0)

    agonist_values = [
        agonist_g_signal_fraction(histamine_nm, r_surf, default_params, xc7_nm=xc7_nm) for xc7_nm in xc7_grid
    ]
    total_values = [g_signaling_fraction(histamine_nm, r_surf, default_params, xc7_nm=xc7_nm) for xc7_nm in xc7_grid]

    assert agonist_values == sorted(agonist_values, reverse=True)
    assert total_values == sorted(total_values, reverse=True)


def test_g_vs_arr_bias() -> None:
    params = TraffickingCoreParams(
        k_int_max_per_h=3.0,
        k_rec_per_h=0.5,
        k_synth_per_h=0.05,
        ec50_barr_nm=50.0,
        ec50_internalization_nm=50.0,
        kb_arr_nm=10.0,
        hill_n=1.0,
        ec50_g_nm=50.0,
        kb_g_nm=1_000.0,
        constitutive_activity=0.0,
    )

    g_fraction = agonist_g_signal_fraction(50.0, 1.0, params, xc7_nm=100.0)
    beta_arr = beta_arr_fraction(50.0, params, xc7_nm=100.0)

    assert g_fraction > beta_arr


def test_xc7_zero_preserves_legacy_internalization(default_params: TraffickingCoreParams) -> None:
    histamine_nm = 50.0
    assert internalization_drive(histamine_nm, default_params) == pytest.approx(
        internalization_drive(histamine_nm, default_params, xc7_nm=0.0)
    )
    assert k_int_eff(histamine_nm, default_params) == pytest.approx(
        k_int_eff(histamine_nm, default_params, xc7_nm=0.0)
    )


def test_xc7_monotonically_reduces_internalization(default_params: TraffickingCoreParams) -> None:
    histamine_nm = 50.0
    values = [k_int_eff(histamine_nm, default_params, xc7_nm=xc7_nm) for xc7_nm in (0.0, 10.0, 100.0, 1_000.0)]
    assert values == sorted(values, reverse=True)


def test_negative_xc7_is_rejected(default_params: TraffickingCoreParams) -> None:
    with pytest.raises(ValueError, match="xc7_nm must be non-negative"):
        internalization_drive(50.0, default_params, xc7_nm=-1.0)
