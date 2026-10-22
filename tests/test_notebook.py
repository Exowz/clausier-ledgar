"""Structural checks for the Colab training notebook without running a kernel."""

import ast

import nbformat

from src.utils import PROJECT_ROOT

NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "train_colab.ipynb"
PARAMETERS = {
    "REPO_URL", "BRANCH", "CONFIGS", "DRIVE_DIR", "SMOKE_FIRST", "SKIP_DONE", "EXTRA_ARGS",
}


def load_notebook():
    """Read the notebook that Ewan will open in Colab."""
    return nbformat.read(NOTEBOOK_PATH, as_version=4)


def test_notebook_is_valid_clean_and_compilable():
    notebook = load_notebook()
    nbformat.validate(notebook)

    for index, cell in enumerate(notebook.cells):
        if cell.cell_type != "code":
            continue
        assert cell.execution_count is None, index
        assert cell.outputs == [], index
        source = "\n".join(
            line for line in cell.source.splitlines() if not line.lstrip().startswith(("!", "%"))
        )
        compile(source, f"train_colab.ipynb:cell{index}", "exec")


def test_parameters_cover_existing_model_configs():
    notebook = load_notebook()
    cells = [cell for cell in notebook.cells if "parameters" in cell.metadata.get("tags", [])]
    assert len(cells) == 1
    assignments = {
        target.id: node.value
        for node in ast.parse(cells[0].source).body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    assert PARAMETERS <= assignments.keys()
    configs = ast.literal_eval(assignments["CONFIGS"])
    assert configs == [
        "configs/legal_bert.yaml", "configs/bert_base.yaml", "configs/legal_bert_lora.yaml",
        "configs/lstm.yaml", "configs/lstm_glove.yaml", "configs/legal_bert_long.yaml",
        "configs/legal_bert_lora_long.yaml",
    ]
    assert all((PROJECT_ROOT / path).is_file() for path in configs)


def test_colab_install_excludes_pinned_torch():
    notebook = load_notebook()
    install_cells = [cell.source for cell in notebook.cells if "req-colab.txt" in cell.source]
    assert len(install_cells) == 1
    assert "grep -v '^torch==' requirements.txt" in install_cells[0]
    assert "pip install -q -r /tmp/req-colab.txt" in install_cells[0]
