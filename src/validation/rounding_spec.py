from __future__ import annotations

from dataclasses import dataclass, field


DEFAULT_METRICS = ("H", "R_surf", "R_int", "G", "loss")


@dataclass(frozen=True)
class RoundingSpec:
    """Precision rules for marker-table comparison."""

    decimals_by_metric: dict[str, int] = field(default_factory=dict)

    def decimals_for(self, metric: str) -> int:
        """Return decimals for metric, falling back to metric-agnostic '*' or 2."""
        if metric in self.decimals_by_metric:
            return self.decimals_by_metric[metric]
        if "*" in self.decimals_by_metric:
            return self.decimals_by_metric["*"]
        return 2

    @classmethod
    def from_model(cls, model_key: str) -> "RoundingSpec":
        """Construct rounding rules derived from report marker-table precision."""
        key = model_key.strip().lower().replace("-", "_").replace(" ", "_")

        one_decimal_models = {
            "formalin",
            "compound",
            "compound48_80",
            "compound_48_80",
            "capsaicin",
            "carrageenin",
            "carrageenan",
        }

        if key in one_decimal_models:
            return cls({metric: 1 for metric in DEFAULT_METRICS})

        if key in {"hot_plate", "hotplate"}:
            spec = {metric: 2 for metric in DEFAULT_METRICS}
            spec["H"] = 1
            return cls(spec)

        return cls({"*": 2})


def rounding_spec_by_model() -> dict[str, RoundingSpec]:
    """Known model->spec mapping expected by validation tests."""
    return {
        "formalin": RoundingSpec.from_model("formalin"),
        "compound48_80": RoundingSpec.from_model("compound48_80"),
        "capsaicin": RoundingSpec.from_model("capsaicin"),
        "carrageenin": RoundingSpec.from_model("carrageenin"),
        "hot_plate": RoundingSpec.from_model("hot_plate"),
    }
