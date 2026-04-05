from __future__ import annotations

from pathlib import Path

import typer

from src import api

app = typer.Typer(help="PKPD model CLI")


@app.command()
def simulate(
    config: Path = typer.Option(..., exists=True, file_okay=True, dir_okay=False),
    out: Path = typer.Option(..., file_okay=False, dir_okay=True),
) -> None:
    """Run one simulation from a config file."""

    try:
        artifacts = api.simulate(config=config, out=out)
        typer.echo(f"simulation complete: {artifacts.simulation_csv}")
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"simulate failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@app.command()
def batch(
    configs_dir: Path = typer.Option(..., exists=True, file_okay=False, dir_okay=True),
    out_root: Path = typer.Option(Path("runs/batch"), file_okay=False, dir_okay=True),
) -> None:
    """Run simulation for each config in a directory."""

    try:
        artifacts = api.run_batch(configs_dir=configs_dir, out_root=out_root)
        typer.echo(f"batch complete: {len(artifacts)} run(s)")
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"batch failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@app.command()
def plot(
    run_dir: Path = typer.Option(..., exists=True, file_okay=False, dir_okay=True),
) -> None:
    """Create a PNG plot from run output."""

    try:
        import matplotlib.pyplot as plt
        import pandas as pd

        simulation_csv = run_dir / "simulation.csv"
        if not simulation_csv.exists():
            raise ValueError(f"simulation.csv not found in run-dir: {run_dir}")

        frame = pd.read_csv(simulation_csv)
        output_path = run_dir / "simulation.png"

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(frame["time_h"], frame["R_surf"], label="R_surf")
        ax.plot(frame["time_h"], frame["R_int"], label="R_int")
        ax.set_xlabel("time_h")
        ax.set_ylabel("state")
        ax.legend()
        fig.tight_layout()
        fig.savefig(output_path)
        plt.close(fig)

        typer.echo(f"plot saved: {output_path}")
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"plot failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@app.command()
def export(
    run_dir: Path = typer.Option(..., exists=True, file_okay=False, dir_okay=True),
    format: str = typer.Option(..., "--format", help="csv|tsv|xlsx"),
) -> None:
    """Export run output into csv/tsv/xlsx."""

    try:
        out_path = api.export(run_dir=run_dir, fmt=format)
        typer.echo(f"export complete: {out_path}")
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"export failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@app.command()
def validate(
    run_dir: Path = typer.Option(..., exists=True, file_okay=False, dir_okay=True),
    reference: Path = typer.Option(..., exists=True, file_okay=True, dir_okay=False),
) -> None:
    """Validate run output against a reference table."""

    ok, message = api.validate(run_dir=run_dir, reference=reference)
    if ok:
        typer.echo(message)
        return

    typer.echo(f"validate failed: {message}", err=True)
    raise typer.Exit(code=1)


@app.command()
def fit() -> None:
    """Reserved: optimization is not part of the supported pipeline."""

    typer.secho(
        "Подбор least_squares не входит в поддерживаемый пайплайн. "
        "Используйте parameter_resolution: fixed_params_only (по умолчанию) и поля "
        "trafficking / formalin_profile / plot_proxy в ModelConfig. "
        "См. CHANGELOG.md и docs/traceability.md.",
        err=True,
    )
    raise typer.Exit(code=2)


@app.command("fit-legacy")
def fit_legacy() -> None:
    """Legacy hook: программный вызов ``fit_histamine_to_markers`` помечен DeprecationWarning."""

    typer.secho(
        "Используйте программный API ``src.fitting.histamine_fit.fit_histamine_to_markers`` "
        "(DeprecationWarning). CLI-команда для фита не поддерживается. См. CHANGELOG.md.",
        err=True,
    )
    raise typer.Exit(code=2)


def main() -> None:
    """Run the Typer CLI application."""

    app()


if __name__ == "__main__":
    main()
