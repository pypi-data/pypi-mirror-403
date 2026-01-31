# cli.py
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from pprint import pprint
from typing import Any, Dict, Optional, Sequence

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.pretty import Pretty

from rakam_eval_sdk.client import DeepEvalClient
from rakam_eval_sdk.decorators import eval_run
from rakam_eval_sdk.utils.decorator_utils import (
    find_decorated_functions,
    load_module_from_path,
)

load_dotenv()
app = typer.Typer(help="CLI tools for evaluation utilities")
console = Console()

# add root of the project to sys.path
PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
list_app = typer.Typer(help="List resources")
app.add_typer(list_app, name="list")
metrics_app = typer.Typer(help="Metrics utilities")
app.add_typer(metrics_app, name="metrics")


def extract_metric_names(config: Any) -> list[tuple[str, str | None]]:
    """
    Returns [(type, name)] from EvalConfig / SchemaEvalConfig
    """
    if not hasattr(config, "metrics"):
        return []

    results: list[tuple[str, str | None]] = []

    for metric in config.metrics or []:
        metric_type = getattr(metric, "type", None)
        metric_name = getattr(metric, "name", None)
        if metric_type:
            results.append((metric_type, metric_name))

    return results


@metrics_app.command("list")
def metrics(
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
) -> None:
    """
    List all metric types used by loaded eval configs.
    """
    files = directory.rglob("*.py") if recursive else directory.glob("*.py")
    TARGET_DECORATOR = eval_run.__name__

    all_metrics: set[tuple[str, str | None]] = set()
    found_any = False

    for file in sorted(files):
        functions = find_decorated_functions(file, TARGET_DECORATOR)
        if not functions:
            continue

        typer.echo(f"\n📄 {file}")

        try:
            module = load_module_from_path(file)
        except Exception as e:
            typer.echo(f"  ❌ Failed to import module: {e}")
            continue

        for fn_name in functions:
            try:
                func = getattr(module, fn_name)
                result = func()

                metrics = extract_metric_names(result)
                if not metrics:
                    continue

                found_any = True
                for metric_type, metric_name in metrics:
                    all_metrics.add((metric_type, metric_name))

                    if metric_name:
                        typer.echo(f"  • {metric_type} (alias: {metric_name})")
                    else:
                        typer.echo(f"  • {metric_type}")

            except Exception as e:
                typer.echo(f"  ❌ Failed to inspect {fn_name}: {e}")

    if not found_any:
        typer.echo("\nNo metrics found.")
        raise typer.Exit(code=0)

    typer.echo(f"\n✅ {len(all_metrics)} unique metrics found")


@list_app.command("evals")
def list_evals(
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
) -> None:
    """
    Find functions decorated with @track.
    """
    TARGET_DECORATOR = eval_run.__name__
    files = directory.rglob("*.py") if recursive else directory.glob("*.py")

    found = False

    for file in sorted(files):
        functions = find_decorated_functions(file, TARGET_DECORATOR)
        for fn in functions:
            found = True
            typer.echo(f"{file}:{fn}")

    if not found:
        typer.echo(f"No @{TARGET_DECORATOR} functions found.")


@list_app.command("runs")
def list_runs(
    limit: int = typer.Option(20, help="Max number of runs"),
    offset: int = typer.Option(0, help="Pagination offset"),
):
    """
    List evaluation runs (newest first).
    """
    client = DeepEvalClient()

    runs = client.list_evaluation_testcases(
        limit=limit,
        offset=offset,
        raise_exception=True,
    )

    if not runs:
        typer.echo("No evaluation runs found.")
        return

    typer.echo(f"[id] " f"{'tag':<20}" f"{'label':<20}" f"created_at")
    # pretty CLI output
    for run in runs:
        run_id = run.get("id")
        label = run.get("label") or "-"
        uid = run.get("tag") or "-"
        created_at = run.get("created_at")

        if created_at:
            try:
                created_at = datetime.fromisoformat(created_at).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            except ValueError:
                pass

        typer.echo(
            f"[{run_id}] " f"{uid:<20} " f"{label:<20} " f"{created_at}")


@app.command()
def show(
    id: Optional[int] = typer.Option(
        None,
        "--id",
        help="Run ID",
    ),
    tag: Optional[str] = typer.Option(
        None,
        "--tag",
        help="Run tag",
    ),
    raw: bool = typer.Option(
        False,
        "--raw",
        help="Print raw JSON instead of formatted output",
    ),
):
    """
    Show a single evaluation testcase by ID or tag.
    """
    if not id and not tag:
        raise typer.BadParameter("You must provide either --id or --uid")

    if id and tag:
        raise typer.BadParameter("Provide only one of --id or --uid")

    client = DeepEvalClient()

    if id:
        result = client.get_evaluation_testcase_by_id(id)
        identifier = f"id={id}"
    else:
        result = client.get_evaluation_testcase_by_tag(tag)
        identifier = f"tag={tag}"

    if not result:
        console.print(
            Panel(
                f"No response received for {identifier}",
                title="Error",
                style="red",
            )
        )
        raise typer.Exit(code=1)

    if isinstance(result, dict) and result.get("error"):
        console.print(
            Panel(
                result["error"],
                title="Error",
                style="red",
            )
        )
        raise typer.Exit(code=1)

    if raw:
        console.print(Pretty(result))
        raise typer.Exit()

    console.print(
        Panel.fit(
            Pretty(result),
            title="Evaluation TestCase",
            subtitle=identifier,
        )
    )


def validate_eval_result(result: Any, fn_name: str) -> str:
    eval_config = getattr(result, "__eval_config__", None)

    if not isinstance(eval_config, str):
        expected = "EvalConfig or SchemaEvalConfig"
        actual = type(result).__name__

        typer.echo(
            f"    ❌ Invalid return type from `{fn_name}`\n"
            f"       Expected: {expected}\n"
            f"       Got: {actual}"
        )
        return ""

    return eval_config


@app.command()
def run(
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
    save_runs: bool = typer.Option(
        False,
        "--save-runs",
        help="Save each evaluation run result to a JSON file",
    ),
    output_dir: Path = typer.Option(
        Path("./eval_runs"),
        "--output-dir",
        help="Directory where run results are saved",
    ),
) -> None:
    """
    Find and execute all functions decorated with @eval_run.
    """
    files = directory.rglob("*.py") if recursive else directory.glob("*.py")
    TARGET_DECORATOR = eval_run.__name__

    executed_any = False

    if save_runs and not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

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
                result = func()

                eval_type = validate_eval_result(result, fn_name)
                if not eval_type:
                    continue

                client = DeepEvalClient()

                if eval_type == "text_eval":
                    resp = client.text_eval(config=result)
                else:
                    resp = client.schema_eval(config=result)

                typer.echo(f"{resp}")
                executed_any = True
                typer.echo(f"    ✅ Returned {type(result).__name__}")

                if save_runs:
                    run_id = (
                        resp["id"]
                        if resp is not None and "id" in resp
                        else uuid.uuid4().hex[:8]
                    )

                    output_path = output_dir / f"run_{fn_name}_{run_id}.json"

                    def to_json_safe(obj: Any) -> Any:
                        if hasattr(obj, "model_dump"):
                            return obj.model_dump()
                        if hasattr(obj, "dict"):
                            return obj.dict()
                        return obj

                    with output_path.open("w", encoding="utf-8") as f:
                        json.dump(
                            to_json_safe(resp),
                            f,
                            indent=2,
                            ensure_ascii=False,
                        )

                    typer.echo(f"    💾 Saved run → {output_path}")

            except Exception as e:
                typer.echo(f"    ❌ Execution failed: {e}")

    if not executed_any and not dry_run:
        typer.echo("\nNo @eval_run functions executed.")


def _print_and_save(
    resp: dict,
    pretty: bool,
    out: Path | None,
    overwrite: bool,
) -> None:
    if pretty:
        typer.echo(typer.style("📊 Result:", bold=True))
        pprint(resp)
    else:
        typer.echo(resp)

    if out is None:
        return

    if out.exists() and not overwrite:
        typer.echo(
            f"❌ File already exists: {out} (use --overwrite to replace)")
        raise typer.Exit(code=1)

    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", encoding="utf-8") as f:
        json.dump(resp, f, indent=2, ensure_ascii=False)

    typer.echo(f"💾 Result saved to {out}")


@app.command()
def compare(
    tag: list[str] = typer.Option(
        [],
        "--tag",
        help="Tag identifying a reference testcase",
    ),
    run: list[int] = typer.Option(
        [],
        "--run",
        help="Run ID identifying an evaluation testcase",
    ),
    pretty: bool = typer.Option(
        True,
        "--pretty/--raw",
        help="Pretty-print the response",
    ),
    raise_exception: bool = typer.Option(
        False,
        "--raise",
        help="Raise HTTP exceptions instead of swallowing them",
    ),
    out: Path | None = typer.Option(
        None,
        "-o",
        "--out",
        help="Optional file path to save the result as JSON",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite output file if it already exists",
    ),
) -> None:
    """
    Compare two evaluation testcases using runs and/or labels.
    """

    targets = []

    for r in run:
        targets.append(("run", r))

    for l in tag:
        targets.append(("label", l))

    if len(targets) != 2:
        typer.echo(
            "❌ Provide exactly two targets using --run and/or --label"
        )
        raise typer.Exit(code=1)

    client = DeepEvalClient()

    (type_a, value_a), (type_b, value_b) = targets

    typer.echo(
        f"🔍 Comparing {type_a} '{value_a}' ↔ {type_b} '{value_b}'"
    )

    kwargs = {"raise_exception": raise_exception}

    if type_a == "run":
        kwargs["testcase_a_id"] = value_a
    else:
        kwargs["testcase_a_tag"] = value_a

    if type_b == "run":
        kwargs["testcase_b_id"] = value_b
    else:
        kwargs["testcase_b_tag"] = value_b

    try:
        resp = client.compare_testcases(**kwargs)
    except Exception as e:
        typer.echo(f"❌ Request failed: {e}")
        raise typer.Exit(code=1)

    if not resp:
        typer.echo("⚠️ No response received")
        raise typer.Exit(code=1)

    _print_and_save(resp, pretty, out, overwrite)


@app.command(hidden=True)
def compare_label_latest(
    label_a: str = typer.Argument(
        ...,
        help="First label (latest run will be used)",
    ),
    label_b: str = typer.Argument(
        ...,
        help="Second label (latest run will be used)",
    ),
    pretty: bool = typer.Option(
        True,
        "--pretty/--raw",
        help="Pretty-print the response",
    ),
    raise_exception: bool = typer.Option(
        False,
        "--raise",
        help="Raise HTTP exceptions instead of swallowing them",
    ),
    out: Path | None = typer.Option(
        None,
        "-o",
        "--out",
        help="Optional file path to save the result as JSON",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite output file if it already exists",
    ),
) -> None:
    """
    Compare the latest evaluation runs for two labels.
    """
    client = DeepEvalClient()

    typer.echo(f"🔍 Comparing latest runs: '{label_a}' ↔ '{label_b}'")

    try:
        resp = client.compare_latest_by_labels(
            label_a=label_a,
            label_b=label_b,
            raise_exception=raise_exception,
        )
    except Exception as e:
        typer.echo(f"❌ Request failed: {e}")
        raise typer.Exit(code=1)

    if not resp:
        typer.echo("⚠️ No response received")
        raise typer.Exit(code=1)

    _print_and_save(resp, pretty, out, overwrite)


@app.command(hidden=True)
def compare_last(
    label: str = typer.Argument(
        ...,
        help="Label whose last two runs will be compared",
    ),
    pretty: bool = typer.Option(
        True,
        "--pretty/--raw",
        help="Pretty-print the response",
    ),
    raise_exception: bool = typer.Option(
        False,
        "--raise",
        help="Raise HTTP exceptions instead of swallowing them",
    ),
    out: Path | None = typer.Option(
        None,
        "-o",
        "--out",
        help="Optional file path to save the result as JSON",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite output file if it already exists",
    ),
) -> None:
    """
    Compare the last two evaluation runs of a label.
    """
    client = DeepEvalClient()

    typer.echo(f"🔍 Comparing last two runs for label '{label}'")

    try:
        resp = client.compare_last_two_by_label(
            label=label,
            raise_exception=raise_exception,
        )
    except Exception as e:
        typer.echo(f"❌ Request failed: {e}")
        raise typer.Exit(code=1)

    if not resp:
        typer.echo("⚠️ No response received")
        raise typer.Exit(code=1)

    _print_and_save(resp, pretty, out, overwrite)


@app.command("tag")
def tag_command(
    run_id: Optional[int] = typer.Option(
        None,
        "--run",
        help="Evaluation run ID",
    ),
    tag: Optional[str] = typer.Option(
        None,
        "--tag",
        help="Tag to assign to the run",
    ),
    delete: Optional[str] = typer.Option(
        None,
        "--delete",
        help="Delete a tag",
    ),
):
    """
    Assign a tag to a run or delete a tag.
    """

    # --- validation ---
    if delete:
        if run_id or tag:
            typer.echo("❌ --delete cannot be used with --run or --tag")
            raise typer.Exit(code=1)
    else:
        if not run_id or not tag:
            typer.echo("❌ Use --run and --tag together, or --delete")
            raise typer.Exit(code=1)

    client = DeepEvalClient()

    # --- delete mode ---
    if delete:
        result = client.update_evaluation_testcase_tag(
            testcase_id=run_id,
            tag=delete,
            raise_exception=True,
        )
        typer.echo("🗑️ Tag deleted successfully")
        typer.echo(f"Tag: {delete}")
        return

    # --- assign/update mode ---
    result = client.update_evaluation_testcase_tag(
        testcase_id=run_id,
        tag=tag,
        raise_exception=True,
    )

    typer.echo("✅ Tag assigned successfully")
    typer.echo(f"Run ID: {run_id}")
    typer.echo(f"Tag: {result.get('tag')}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
