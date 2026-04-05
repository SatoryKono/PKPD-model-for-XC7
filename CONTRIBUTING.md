# Contributing

## Reproducibility tooling

Lockfile tool is currently **not fixed** (`uv` / `poetry` / `pip-tools` are candidates).

- Status: **[неполные данные]** — team decision required.
- Action item: choose one tool in engineering sync and update this section with exact commands for:
  - lockfile creation/update
  - CI verification step
  - local developer workflow

Until then, runtime reproducibility metadata is captured in `runs/<run_id>/metadata.json`, and artifact hashes are used as the deterministic acceptance signal.
