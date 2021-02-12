import json
from pathlib import Path
import re
import sys

import click
import nbformat

__version__ = "1.1.1"

EXIT_CODES = {
    "clean": 0,
    "dirty": 1,
    # "invalid usage": 2, - this is handled by click
    "invalid_path": 3,
}


def echo(*args, **kwargs):
    kwargs["err"] = kwargs.get("err", True)
    return click.secho(*args, **kwargs)


def i_exec(cell, meta):
    statement = "non-null execution_count"
    unpinned = ("pin_output" not in cell["metadata"])

    def condition():
        return (cell["execution_count"] is not None) and unpinned

    def fix():
        cell["execution_count"] = None

    return statement, condition, fix


def i_output(cell, meta):
    statement = "output without 'pin_output'"
    unpinned = ("pin_output" not in cell["metadata"])

    def condition():
        return cell["outputs"] and unpinned

    def fix():
        cell["outputs"] = []

    return statement, condition, fix


def i_meta(cell, meta):
    statement = "non-whitelisted metadata"
    without_meta = {k: v for k, v in cell["metadata"].items() if k not in meta}
    with_meta = {k: v for k, v in cell["metadata"].items() if k in meta}

    def condition():
        return without_meta

    def fix():
        cell["metadata"] = with_meta

    return statement, condition, fix


def i_answer(cell, meta):
    statement = "de-commented show_answer"

    def condition():
        return any(re.match(" *show_answer", ln) for ln in cell["source"].split("\n"))

    def fix():
        new = cell["source"].split("\n")
        new = [re.sub(r"^ *show_answer", r"#show_answer", ln) for ln in new]
        cell["source"] = "\n".join(new)

    return statement, condition, fix


def process_cell(cell, meta):
    # Find issues
    issues = []
    for issue in [i_exec, i_output, i_meta, i_answer]:
        statement, condition, fix = issue(cell, meta)
        if condition():
            issues.append([statement, fix])

    # Print issues
    if issues:
        echo("These issues:", fg="red")
        echo("- " + "\n- ".join([issue[0] for issue in issues]), fg="yellow")
        echo("were fixed in this cell:", fg="red")
        echo(json.dumps(cell, indent=4))

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


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument("src", required=False, nargs=-1)
@click.option("-m", "--meta", multiple=True, default=["pin_output"],
              help="A regular expression that matches WHITELISTED metadata keys "
              )
@click.pass_context
def main(ctx: click.Context, src: str, meta: list):
    """
    Ensure that Jupyter notebooks given by SRC are clean,
    i.e. do not contain outputs, execution counts or blacklisted metadata keys.
    Only code-cells are checked.

    The exit code is 1 if any notebook is dirty, 0 otherwise.
    """

    # Collect files
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

    found_issues = False

    # Loop files
    for s in sorted(sources):
        echo("File: " + s, fg="magenta")
        try:
            nb = nbformat.read(s, as_version=4)

            # Process
            try:
                process_file(nb, meta)

            except DirtyNotebookError:
                nbformat.write(nb, s)
                found_issues = True
        except Exception:
            echo("File could not be read.", fg="red")
            found_issues = True

    # Exit
    if found_issues:
        exit_code = EXIT_CODES["dirty"]
    else:
        exit_code = EXIT_CODES["clean"]
    ctx.exit(exit_code)
