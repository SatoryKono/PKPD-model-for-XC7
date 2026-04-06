from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

import numpy as np

from src.config.schemas import LossMode


@dataclass(frozen=True)
class ParameterSpec:
    """Specification for one fitted parameter."""

    name: str
    init: float
    lower: float
    upper: float

    def validate(self) -> None:
        if not self.name:
            raise ValueError("Parameter name must be non-empty")
        if not np.isfinite(self.init):
            raise ValueError(f"Parameter '{self.name}' init must be finite")
        if not np.isfinite(self.lower) or not np.isfinite(self.upper):
            raise ValueError(f"Parameter '{self.name}' bounds must be finite")
        if self.lower > self.upper:
            raise ValueError(f"Parameter '{self.name}' lower bound cannot exceed upper bound")
        if not (self.lower <= self.init <= self.upper):
            raise ValueError(f"Parameter '{self.name}' init must be inside bounds")


def scipy_least_squares_loss(mode: LossMode) -> str:
    """Map config ``LossMode`` to SciPy ``least_squares`` ``loss`` names."""

    if mode == LossMode.MSE:
        return "linear"
    if mode == LossMode.HUBER:
        return "huber"
    if mode == LossMode.MAE:
        return "soft_l1"
    raise ValueError(
        "LossMode.nll is not supported for scipy.optimize.least_squares; use a dedicated likelihood fitter."
    )


@dataclass(frozen=True)
class FitSpec:
    """Deterministic least-squares fit configuration."""

    parameters: tuple[ParameterSpec, ...]
    fixed_params: Mapping[str, float] = field(default_factory=dict)
    objective_definition: str = "marker_residuals: model(t_i)-observed(t_i)"
    loss_mode: LossMode = LossMode.MSE
    seed: int = 2026
    method: str = "trf"
    ftol: float = 1e-10
    xtol: float = 1e-10
    gtol: float = 1e-10
    max_nfev: int = 5000

    def validate(self) -> None:
        if not self.parameters:
            raise ValueError("FitSpec.parameters must be non-empty")

        names: set[str] = set()
        for spec in self.parameters:
            spec.validate()
            if spec.name in names:
                raise ValueError(f"Duplicate parameter '{spec.name}' in FitSpec")
            names.add(spec.name)

        if self.method not in {"trf", "dogbox", "lm"}:
            raise ValueError("method must be one of {'trf', 'dogbox', 'lm'}")
        if self.method == "lm" and any((p.lower != -np.inf or p.upper != np.inf) for p in self.parameters):
            raise ValueError("method='lm' does not support finite bounds")
        if self.loss_mode == LossMode.NLL:
            raise ValueError("FitSpec.loss_mode='nll' is not supported for scipy least_squares legacy fit")

    @property
    def init_guess(self) -> np.ndarray:
        return np.array([p.init for p in self.parameters], dtype=float)

    @property
    def bounds(self) -> tuple[np.ndarray, np.ndarray]:
        low = np.array([p.lower for p in self.parameters], dtype=float)
        high = np.array([p.upper for p in self.parameters], dtype=float)
        return low, high

    @property
    def parameter_names(self) -> tuple[str, ...]:
        return tuple(p.name for p in self.parameters)

    def validate_identifiability(self, independent_constraints_count: int) -> None:
        """Check simple identifiability proxy: parameters <= independent constraints."""

        n_params = len(self.parameters)
        if n_params > independent_constraints_count:
            raise ValueError(
                "[неполные данные] Число параметров больше числа независимых ограничений; "
                "уточните FitSpec (сократите параметры или добавьте маркерные ограничения)."
            )


def fit_spec_to_dict(spec: FitSpec) -> dict[str, Any]:
    """Return a JSON-serializable structure for reporting."""

    low, high = spec.bounds
    return {
        "fitted_parameter_names": list(spec.parameter_names),
        "fixed_params": dict(spec.fixed_params),
        "bounds": {
            "lower": low.tolist(),
            "upper": high.tolist(),
        },
        "init_guess": spec.init_guess.tolist(),
        "objective_definition": spec.objective_definition,
        "loss_mode": spec.loss_mode.value,
        "seed": spec.seed,
        "scipy_least_squares": {
            "method": spec.method,
            "loss": scipy_least_squares_loss(spec.loss_mode),
            "ftol": spec.ftol,
            "xtol": spec.xtol,
            "gtol": spec.gtol,
            "max_nfev": spec.max_nfev,
        },
    }
