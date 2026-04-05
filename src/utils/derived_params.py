from __future__ import annotations


def ec50_barr_from_bias_factor(*, ec50_g_nm: float, bias_factor: float) -> float:
    """Convert bias-factor to β-arrestin EC50 using EC50_barr = EC50_G / bias_factor."""

    if ec50_g_nm <= 0:
        raise ValueError("ec50_g_nm must be > 0")
    if bias_factor <= 0:
        raise ValueError("bias_factor must be > 0")
    return ec50_g_nm / bias_factor


_TIME_TO_HOURS = {
    "h": 1.0,
    "hr": 1.0,
    "hour": 1.0,
    "min": 1.0 / 60.0,
    "s": 1.0 / 3600.0,
}


def time_to_hours(value: float, unit: str) -> float:
    unit_norm = unit.strip().lower()
    if unit_norm not in _TIME_TO_HOURS:
        raise ValueError(f"Unsupported time unit '{unit}'. Supported: {sorted(_TIME_TO_HOURS)}")
    return float(value) * _TIME_TO_HOURS[unit_norm]


_CONC_TO_NM = {
    "nm": 1.0,
    "um": 1e3,
    "mm": 1e6,
    "m": 1e9,
}


def concentration_to_nm(value: float, unit: str) -> float:
    unit_norm = unit.strip().lower().replace("μ", "u")
    if unit_norm not in _CONC_TO_NM:
        raise ValueError(f"Unsupported concentration unit '{unit}'. Supported: {sorted(_CONC_TO_NM)}")
    return float(value) * _CONC_TO_NM[unit_norm]


__all__ = ["ec50_barr_from_bias_factor", "time_to_hours", "concentration_to_nm"]
