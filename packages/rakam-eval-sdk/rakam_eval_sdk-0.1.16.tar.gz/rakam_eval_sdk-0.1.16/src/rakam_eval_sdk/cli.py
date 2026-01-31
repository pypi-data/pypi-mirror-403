# cli.py
import typer
from pathlib import Path

app = typer.Typer()


@app.command()
def read(file: Path):
    """Read a Python file"""
    if file.suffix != ".py":
        raise typer.BadParameter("Must be a .py file")
    typer.echo(file.read_text())


def main():
    app()
