from click.testing import CliRunner
from nbhooks import main
from pathlib import Path
import nbformat
import pytest


@pytest.fixture
def nb():
    nb = nbformat.v4.new_notebook()

    # Add non-code cells. They should have no effect on the test results.
    nb.cells.append(nbformat.v4.new_markdown_cell())
    nb.cells.append(nbformat.v4.new_raw_cell())

    return nb


@pytest.fixture
def runner():
    return CliRunner()


def test_no_sources(runner: CliRunner):
    result = runner.invoke(main)
    assert result.exit_code == 0


def test_clean(runner: CliRunner, nb):
    nb.cells.append(nbformat.v4.new_code_cell())
    with runner.isolated_filesystem():
        nbformat.write(nb, "test.ipynb", version=4)
        result = runner.invoke(main, ["test.ipynb"])
        assert result.exit_code == 0


def test_dirty_with_outputs(runner: CliRunner, nb):
    cell = nbformat.v4.new_code_cell()
    cell.outputs.append(
        nbformat.v4.new_output(output_type="execute_result", execution_count=1)
    )
    nb.cells.append(cell)
    with runner.isolated_filesystem():
        nbformat.write(nb, "test.ipynb", version=4)
        result = runner.invoke(main, ["test.ipynb"])
        assert result.exit_code == 1


def test_dirty_with_execution_count(runner: CliRunner, nb):
    cell = nbformat.v4.new_code_cell(execution_count=1)
    nb.cells.append(cell)
    with runner.isolated_filesystem():
        nbformat.write(nb, "test.ipynb", version=4)
        result = runner.invoke(main, ["test.ipynb"])
        assert result.exit_code == 1


def test_dirty_with_metadata(runner: CliRunner, nb):
    cell = nbformat.v4.new_code_cell(metadata={"dummy": True})
    nb.cells.append(cell)
    with runner.isolated_filesystem():
        nbformat.write(nb, "test.ipynb", version=4)

        result = runner.invoke(main, ["test.ipynb", "--meta", "dummy"])
        assert result.exit_code == 1

        result = runner.invoke(main, ["test.ipynb"])
        assert result.exit_code == 0

        result = runner.invoke(main, ["test.ipynb", "--meta", "xyz"])
        assert result.exit_code == 0


def test_empty_notebook(runner: CliRunner):
    nb = nbformat.v4.new_notebook()
    with runner.isolated_filesystem():
        nbformat.write(nb, "test.ipynb", version=4)
        result = runner.invoke(main, ["test.ipynb"])
        assert result.exit_code == 0


def test_invalid_source(runner: CliRunner):
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["test.ipynb"])
        assert result.exit_code == 3


def test_stdin(runner: CliRunner, nb):
    result = runner.invoke(main, ["-"], input=nbformat.writes(nb, version=4))
    assert result.exit_code == 0

    cell = nbformat.v4.new_code_cell(execution_count=1)
    nb.cells.append(cell)
    result = runner.invoke(main, ["-"], input=nbformat.writes(nb, version=4))
    assert result.exit_code == 1


def test_metadata_in_non_code_cells(runner: CliRunner, nb):
    metadata = {"dummy": True}
    for cell in nb.cells:
        cell["metadata"].update(metadata)

    result = runner.invoke(
        main, ["-", "--meta", "dummy"], input=nbformat.writes(nb, version=4)
    )
    assert result.exit_code == 0

    cell = nbformat.v4.new_code_cell(metadata=metadata)
    nb.cells.append(cell)
    result = runner.invoke(
        main, ["-", "--meta", "dummy"], input=nbformat.writes(nb, version=4)
    )
    assert result.exit_code == 1


def test_no_files_to_check(runner: CliRunner):
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["."])
        assert result.exit_code == 0


def test_ignore_invalid_files(runner: CliRunner, nb):
    with runner.isolated_filesystem():
        nbformat.write(nb, "test-1.ipynb", version=4)
        Path("test-2.ipynb").write_text("this is not a notebook")
        result = runner.invoke(main, ["."])
        assert result.exit_code == 0
        assert "1 file was ignored" in result.output


def test_recursive_search(runner: CliRunner, nb):
    with runner.isolated_filesystem():
        Path("subdir").mkdir()
        nbformat.write(nb, "test.ipynb", version=4)
        nbformat.write(nb, "subdir/test.ipynb", version=4)
        result = runner.invoke(main, ["."])
        assert result.exit_code == 0
        assert "2 files are clean" in result.output


def test_multiple_sources(runner: CliRunner, nb):
    with runner.isolated_filesystem():
        nbformat.write(nb, "test-1.ipynb", version=4)
        nbformat.write(nb, "test-2.ipynb", version=4)
        result = runner.invoke(main, ["test-1.ipynb", "test-2.ipynb"])
        assert result.exit_code == 0
        assert "2 files are clean" in result.output
