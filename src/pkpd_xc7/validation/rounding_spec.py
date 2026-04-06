from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RoundingSpec:
    """Specification for deterministic rounding in validation snapshots."""

    decimals: dict[str, int] = field(default_factory=dict)
    default_decimals: int = 2

    @classmethod
    def from_model(cls, model_key: str) -> RoundingSpec:
        """Create a rounding specification for a specific experimental model."""
        if model_key == "formalin":
            return cls(
                decimals={
                    "histamine_nm": 1,
                    "R_surf": 1,
                    "R_int": 1,
                    "G_signal": 1,
                    "G_signal_pct": 1,
                    "G_signal_ligand": 1,
                    "G_signal_ligand_pct": 1,
                    "G_signal_constitutive": 1,
                    "G_signal_constitutive_pct": 1,
                    "beta_arr_signal": 2,
                    "beta_arr_signal_pct": 2,
                    "internalization_drive": 2,
                    "k_int_eff_per_h": 2,
                    "loss": 1,
                }
            )
        if model_key == "hot_plate":
            return cls(
                decimals={
                    "histamine_nm": 1,
                    "R_surf": 2,
                    "R_int": 2,
                    "G_signal": 2,
                    "G_signal_pct": 2,
                    "G_signal_ligand": 2,
                    "G_signal_ligand_pct": 2,
                    "G_signal_constitutive": 2,
                    "G_signal_constitutive_pct": 2,
                    "beta_arr_signal": 2,
                    "beta_arr_signal_pct": 2,
                    "internalization_drive": 2,
                    "k_int_eff_per_h": 2,
                    "loss": 2,
                }
            )
        if model_key == "capsaicin":
            return cls(
                decimals={
                    "histamine_nm": 1,
                }
            )
        return cls()
