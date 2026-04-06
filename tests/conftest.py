from __future__ import annotations

import sys
from pathlib import Path

# Корень репозитория в sys.path — дубликат к [tool.pytest.ini_options] pythonpath,
# нужен при запуске pytest без установки пакета (python -m pytest из корня).
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
