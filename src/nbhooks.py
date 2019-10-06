from functools import partial
from collections import Counter
from pathlib import Path
from typing import Iterator
import re
import sys

import click
import nbformat

__version__ = "1.0.0"

CLEAN = "clean"
DIRTY = "dirty"
IGNORED = "ignored"

EXIT_CODES = {
    "clean": 0,
    "dirty": 1,
    # "invalid usage": 2, - this is handled by click
    "invalid_path": 3,
}


class DirtyNotebookError(Exception):
    pass


def iter_code_cells(notebook: dict) -> Iterator[dict]:
    yield from (
        cell for cell in notebook.get("cells", []) if cell.get("cell_type") == "code"
    )


def cell_has_execution_count(cell: dict) -> bool:
    return cell.get("execution_count") is not None


def cell_has_outputs(cell: dict) -> bool:
    return bool(cell.get("outputs", []))


def cell_has_metadata_key(cell: dict, regex: str) -> bool:
    pattern = re.compile(regex)
    return any(pattern.match(key) for key in cell.get("metadata", {}))


def check_notebook_is_clean(nb: dict, meta: str = "") -> None:
    for cell in iter_code_cells(nb):
        if cell_has_outputs(cell):
            raise DirtyNotebookError("Notebook contains outputs")
        elif cell_has_execution_count(cell):
            raise DirtyNotebookError("Notebook contains execution counts")
        elif meta and cell_has_metadata_key(cell, meta):
            raise DirtyNotebookError("Notebook contains blacklisted cell metadata")


err = partial(click.secho, fg="red", err=True)
out = partial(click.secho, err=True)


@click.command()
@click.argument("src", required=False, nargs=-1)
@click.option("-m", "--meta", default="")
@click.option("-q", "--quiet", is_flag=True)
@click.option("-v", "--verbose", is_flag=True)
@click.pass_context
def main(ctx: click.Context, src: str, meta: str, quiet: bool, verbose: bool):
    sources = set()
    for s in src:
        p = Path(s)
        if s == "-":
            sources.add(sys.stdin)
        elif p.is_file():
            sources.add(s)
        elif p.is_dir():
            sources.update(map(str, p.glob("**/*.ipynb")))
        else:
            out("Invalid path: {}".format(s), fg="red")
            ctx.exit(EXIT_CODES["invalid_path"])

    report = []
    for s in sorted(sources):
        if not quiet:
            out(".", nl=False)

        d = {"name": getattr(s, "name", s)}
        report.append(d)
        try:
            nb = nbformat.read(s, as_version=4)
        except Exception as e:
            d["status"] = IGNORED
            d["error"] = str(e)
            continue

        try:
            check_notebook_is_clean(nb, meta=meta)
            d["status"] = CLEAN
        except DirtyNotebookError as e:
            d["status"] = DIRTY
            d["error"] = str(e)

    if not quiet:
        out("\n")

    out(format_report(report, quiet=quiet, verbose=verbose))

    if any(d["status"] == DIRTY for d in report):
        exit_code = EXIT_CODES["dirty"]
        color = "red"
    else:
        exit_code = EXIT_CODES["clean"]
        color = "green"

    out(":)", bold=True, fg=color)
    ctx.exit(exit_code)


def format_report(report: list, quiet: bool = False, verbose: bool = False) -> str:
    lines = []
    counts = Counter(d["status"] for d in report)
    colors = {DIRTY: "red", CLEAN: "green", IGNORED: "yellow"}

    if quiet:
        verbose = False

    for d in report:
        if not verbose and d["status"] != DIRTY:
            continue
        lines.append(
            "{}{}".format(
                click.style(d["status"].ljust(8), fg=colors[d["status"]]), d["name"]
            )
        )
        if d["status"] == DIRTY:
            lines.append("{}{}".format("".ljust(8), click.style(d["error"], bold=True)))

    if lines:
        lines.append("")

    if not quiet and not report:
        lines.append("No files were checked")

    if not quiet:
        messages = []
        if counts.get(DIRTY):
            messages.append(
                "{} {} dirty".format(
                    counts[DIRTY], "file is" if counts[DIRTY] == 1 else "files are"
                )
            )
        if counts.get(CLEAN):
            messages.append(
                "{} {} clean".format(
                    counts[CLEAN], "file is" if counts[CLEAN] == 1 else "files are"
                )
            )
        if counts.get(IGNORED):
            messages.append(
                "{} {} ignored".format(
                    counts[IGNORED],
                    "file was" if counts[IGNORED] == 1 else "files were",
                )
            )
        lines.append(click.style(", ".join(messages), bold=True))

    return "\n".join(lines)
