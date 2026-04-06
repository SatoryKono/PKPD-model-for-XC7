from __future__ import annotations

from pathlib import Path

import typer

from pkpd_xc7.config.loader import load_model_config
from pkpd_xc7.io.export import export_simulation_run
from pkpd_xc7.simulation.runner import run_experiment

app = typer.Typer(help="PKPD Model for XC7 CLI")


@app.command()
def version() -> None:
    """Print package version (second command keeps Typer multi-command mode for simulate)."""
    import importlib.metadata
    try:
        ver = importlib.metadata.version("pkpd-model-xc7")
    except importlib.metadata.PackageNotFoundError:
        ver = "unknown"
    typer.echo(f"pkpd-model-xc7 v{ver}")


@app.command()
def simulate(
    config: Path = typer.Option(
        ...,
        "--config",
        "-c",
        help="Путь к YAML конфигурации",
        exists=True,
        dir_okay=False,
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        "-o",
        help="Директория для сохранения результатов",
    ),
) -> None:
    typer.echo(f"Загрузка конфигурации: {config}")
    model_config = load_model_config(config)

    df = run_experiment(model_config)
    artifacts = export_simulation_run(df, model_config, out)

    typer.echo(f"Симуляция успешно завершена. Результаты сохранены в {artifacts.simulation_csv}")
    typer.echo(f"Meta YAML: {artifacts.meta_yaml}")
    typer.echo(f"Config SHA256: {model_config.config_sha256()}")
    typer.echo(f"Schema Version: {model_config.schema_version}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()