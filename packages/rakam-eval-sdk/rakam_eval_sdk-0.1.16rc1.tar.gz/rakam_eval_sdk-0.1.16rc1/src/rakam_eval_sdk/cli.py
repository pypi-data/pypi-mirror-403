# cli.py
from pathlib import Path

import typer

from rakam_eval_sdk.utils.decorator_utils import find_decorated_functions, load_module_from_path
from rakam_eval_sdk.decorators import eval_run
app = typer.Typer(help="CLI tools for evaluation utilities")


@app.command()
def find_eval_run_by_name(
    directory: Path = typer.Argument(
        Path("./eval"),
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="Directory to scan (default: ./eval)",
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive",
        "-r",
        help="Recursively search for Python files",
    ),
):
    """
    Find functions decorated with @track.
    """
    TARGET_DECORATOR = eval_run.__name__
    files = (
        directory.rglob("*.py")
        if recursive
        else directory.glob("*.py")
    )

    found = False

    for file in sorted(files):
        functions = find_decorated_functions(file, TARGET_DECORATOR)
        for fn in functions:
            found = True
            typer.echo(f"{file}:{fn}")

    if not found:
        typer.echo(f"No @{TARGET_DECORATOR} functions found.")


@app.command("run")
def run_eval_runs(
    directory: Path = typer.Argument(
        Path("./eval"),
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="Directory to scan (default: ./eval)",
    ),
    recursive: bool = typer.Option(
        False,
        "-r",
        "--recursive",
        help="Recursively search for Python files",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Only list functions without executing them",
    ),
):
    """
    Find and execute all functions decorated with @eval_run.
    """
    files = (
        directory.rglob("*.py")
        if recursive
        else directory.glob("*.py")
    )
    TARGET_DECORATOR = eval_run.__name__

    executed_any = False

    for file in sorted(files):
        functions = find_decorated_functions(file, TARGET_DECORATOR)
        if not functions:
            continue

        typer.echo(f"\n📄 {file}")

        module = None
        if not dry_run:
            try:
                module = load_module_from_path(file)
            except Exception as e:
                typer.echo(f"  ❌ Failed to import module: {e}")
                continue

        for fn_name in functions:
            typer.echo(f"  ▶ {fn_name}")

            if dry_run:
                continue

            try:
                func = getattr(module, fn_name)
                func()  # <-- actual execution
                executed_any = True
            except Exception as e:
                typer.echo(f"    ❌ Execution failed: {e}")

    if not executed_any and not dry_run:
        typer.echo("\nNo @eval_run functions executed.")


def main():
    app()


if __name__ == "__main__":
    main()
