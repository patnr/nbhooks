from abc import ABC, abstractmethod
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


#######################
#  Individual issues  #
#######################
class Issue(ABC):
    """Detect, state, and fix issue for one cell in a notebook."""
    def __init__(self, cell, whitelist):
        self.cell = cell
        self.whitelist = whitelist

    @property
    @abstractmethod
    def statement(self):
        pass

    @abstractmethod
    def condition(self):
        pass

    @abstractmethod
    def fix(self):
        pass


class HasExeCount(Issue):

    def statement(self):
        return "non-null execution_count"

    def condition(self):
        unpinned = "pin_output" not in self.cell["metadata"]
        return (self.cell["execution_count"] is not None) and unpinned

    def fix(self):
        self.cell["execution_count"] = None


class HasOutput(Issue):

    def statement(self):
        return "output without 'pin_output'"

    def condition(self):
        unpinned = "pin_output" not in self.cell["metadata"]
        return self.cell["outputs"] and unpinned

    def fix(self):
        self.cell["outputs"] = []


class HasMeta(Issue):

    def statement(self):
        return "non-whitelisted metadata"

    def condition(self):
        return [k for k in self.cell["metadata"] if k not in self.whitelist]

    def fix(self):
        self.cell["metadata"] = {
            k: v for k, v in self.cell["metadata"].items()
            if k in self.whitelist
        }


class AnswerUncommented(Issue):

    def statement(self):
        return "un-commented show_answer"

    def condition(self):
        return any(re.match(" *show_answer", ln)
                   for ln in self.cell["source"].split("\n"))

    def fix(self):
        new = self.cell["source"].split("\n")
        new = [re.sub(r"^ *show_answer", r"#show_answer", ln) for ln in new]
        self.cell["source"] = "\n".join(new)


##########
#  Main  #
##########
def echo(*args, **kwargs):
    kwargs["err"] = kwargs.get("err", True)
    return click.secho(*args, **kwargs)


class DirtyNotebookError(Exception):
    pass


def process_cell(cell, whitelist):
    # Find issues
    issues = []
    for cls in Issue.__subclasses__():
        x = cls(cell, whitelist)  # type: ignore
        if x.condition():
            issues.append(x)

    # Print
    messgs = [x.statement() for x in issues]
    if issues:
        echo("These issues:",            fg="red")  # noqa
        echo("- " + "\n- ".join(messgs), fg="yellow")
        echo("were fixed in this cell:", fg="red")
        echo(json.dumps(cell, indent=4))

    # Fix issues
    for x in issues:
        x.fix()

    # Report
    return bool(issues)


def process_file(nb, whitelist):

    had_issues = False
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            had_issues |= process_cell(cell, whitelist)

    if had_issues:
        raise DirtyNotebookError("Notebook had issues.")


###########
#  Click  #
###########
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
        except Exception:
            echo("File could not be read.", fg="red")
            found_issues = True
        else:
            # Process
            try:
                process_file(nb, meta)

            except DirtyNotebookError:
                nbformat.write(nb, s)
                found_issues = True

    # Exit
    if found_issues:
        exit_code = EXIT_CODES["dirty"]
    else:
        exit_code = EXIT_CODES["clean"]
    ctx.exit(exit_code)
