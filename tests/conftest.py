from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Remaining ignored tests still depend on removed `src/` subpackages or
# validation/reference modules that have not been migrated to `pkpd_xc7` yet.
collect_ignore = [
    "test_unit_rounding_spec.py",
    "test_unit_reference_loader.py",
    "test_solver_marker_interpolation.py",
    "test_unit_compare.py",
    "test_regression_marker_tables.py",
    "test_plot_data_snapshots.py",
    "test_model_params_integration.py",
]