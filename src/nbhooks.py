from functools import partial
from collections import Counter
from pathlib import Path
from typing import Iterator
import re
import sys

import click
import nbformat

__version__ = "1.1.1"

CLEAN = "clean"
DIRTY = "dirty"
IGNORED = "ignored"

EXIT_CODES = {
    "clean": 0,
    "dirty": 1,
    # "invalid usage": 2, - this is handled by click
    "invalid_path": 3,
}



def i_exec(cell):
    statement      = "non-null execution_count"
    def condition(): return cell["execution_count"] is not None
    def       fix(): cell["execution_count"] = None
    return statement, condition, fix
def i_output(cell):
    statement      = "output without 'pin_output'"
    def condition(): return cell["outputs"] and all("pin_output" not in ln for ln in cell["source"])
    def       fix(): cell["outputs"] = []
    return statement, condition, fix
def i_meta(cell):
    statement      = "output with metadata"
    def condition(): return cell["metadata"]
    def       fix(): cell["metadata"] = {}
    return statement, condition, fix
def i_answer(cell):
    statement      = "de-commented show_answer"
    def condition(): return any(re.match(" *show_answer", ln) for ln in cell["source"].split("\n"))
    def       fix():
        new = cell["source"].split("\n")
        new = [re.sub(r"^ *show_answer", r"#show_answer", ln) for ln in new]
        cell["source"] = "\n".join(new)
    return statement, condition, fix


import json
def process_cell(cell, meta):
    # Find issues
    issues = []
    for issue in [i_exec, i_output, i_meta, i_answer]:
        statement, condition, fix = issue(cell)
        if condition():
            issues.append([statement, fix])

    # Print issues
    if issues:
        hecho("\nThese issues:")
        echo("- "+"\n- ".join([issue[0] for issue in issues]),fg="yellow")
        hecho("are present in the below cell:")
        echo(json.dumps(cell,indent=4))

    # Fix issues
    for issue in issues:
        issue[1]()

    # Report
    return bool(issues)


class DirtyNotebookError(Exception):
    pass


def process_file(nb, meta):

    had_issues = False
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            had_issues |= process_cell(cell, meta)

    if had_issues:
        raise DirtyNotebookError("Notebook had issues.")






echo = partial(click.secho, err=True)
hecho = partial(click.secho, err=True, bold=True, fg="magenta")


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument("src", required=False, nargs=-1)
@click.option(
    "-m",
    "--meta",
    default="",
    help="A regular expression that matches blacklisted metadata keys "
    "(i.e. those which renders a notebook dirty).",
)
@click.option(
    "-q", "--quiet", is_flag=True, help="Do not emit non-error messages to stderr."
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Emit messages about clean and ignored files to stderr.",
)
@click.pass_context
def main(ctx: click.Context, src: str, meta: str, quiet: bool, verbose: bool):
    """
    Ensure that Jupyter notebooks given by SRC are clean,
    i.e. do not contain outputs, execution counts or blacklisted metadata keys.
    Only code-cells are checked.

    The exit code is 1 if any notebook is dirty, 0 otherwise.
    """
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
            echo("Invalid path: {}".format(s), fg="red")
            ctx.exit(EXIT_CODES["invalid_path"])

    report = []
    for s in sorted(sources):

        # Read files
        d = {"name": getattr(s, "name", s)}
        report.append(d)
        try:
            nb = nbformat.read(s, as_version=4)
        except Exception as e:
            d["status"] = IGNORED
            d["error"] = str(e)
            continue

        # Process
        try:
            hecho("Processing: "+s)
            hecho("***********************************************")
            process_file(nb, meta=meta)
            d["status"] = CLEAN
        except DirtyNotebookError as e:
            d["status"] = DIRTY
            d["error"] = str(e)
            nbformat.write(nb, s)

    # Exit
    if any(d["status"] == DIRTY for d in report):
        # echo(":(", bold=True, fg="red")
        exit_code = EXIT_CODES["dirty"]
    else:
        # echo(":)", bold=True, fg="green")
        exit_code = EXIT_CODES["clean"]
    ctx.exit(exit_code)
