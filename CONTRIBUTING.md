# Contributing

## Tests

Установка зависимостей для разработки:

```bash
python -m pip install -e ".[dev]"
```

Запуск всех тестов (настройки в `[tool.pytest.ini_options]` в `pyproject.toml`):

```bash
python -m pytest tests
```

Выборочно:

- без регрессии по внешнему отчёту: `python -m pytest tests -m "not regression_data"`
- без снапшотов regtest: `python -m pytest tests -m "not snapshot"`

Маркеры: `regression_data`, `snapshot`, `integration` (зарезервирован для части сценариев).

## Reproducibility tooling

Lockfile tool is currently **not fixed** (`uv` / `poetry` / `pip-tools` are candidates).

- Status: **[неполные данные]** — team decision required.
- Action item: choose one tool in engineering sync and update this section with exact commands for:
  - lockfile creation/update
  - CI verification step
  - local developer workflow

Until then, runtime reproducibility metadata is captured in `runs/<run_id>/metadata.json`, and artifact hashes are used as the deterministic acceptance signal.
