from pathlib import Path
from typing import TypedDict, Literal
import os
import json


Data = TypedDict("Data", {"text/plain": list[str]})


class Output(TypedDict):
    name: str
    output_type: Literal["stream", "execute_result"]
    text: list[str]
    data: Data


class MetaData(TypedDict):
    tags: list[str]


class Cell(TypedDict):
    cell_type: Literal["markdown", "code"]
    source: list[str]
    metadata: MetaData
    outputs: list[Output]


class Notebook(TypedDict):
    cells: list[Cell]


THISDIR: Path = Path(__file__).parent

os.chdir(THISDIR)


def end_snippet(previous_was_snippet: bool):
    return "```\n" if previous_was_snippet else ""


def format_markdown_cell(cell: Cell, previous_was_snippet: bool):
    out = end_snippet(previous_was_snippet) + "".join(cell["source"])
    return out + ("\n" if not out.endswith("\n") else "")


def format_python_file_cell(cell: Cell, previous_was_snippet: bool):
    return end_snippet(previous_was_snippet) + "```python\n" + "".join(cell["source"][1:]) + "\n```\n"


def get_outputs(cell: Cell):
    lines = []
    for o in cell["outputs"]:
        if o["output_type"] == "stream":
            lines.append("".join(o["text"]))
        if o["output_type"] == "execute_result":
            lines.append("".join(o["data"]["text/plain"]))
    out = "".join(lines)
    if "Traceback " in out:
        out = cell["outputs"][-1]["text"][-1]

    return out.strip() + "\n" if out else ""


def format_shell_cell(cell: Cell, previous_was_snippet: bool):
    return (
        end_snippet(previous_was_snippet)
        + "```\n>"
        + cell["source"][0].lstrip("!")
        + "\n\n"
        + get_outputs(cell)
        + "```\n"
    )


def format_python_snippet_cell(cell: Cell, previous_was_snippet: bool):
    lines: list[str] = []
    for line in cell["source"]:
        lines.append(f"... {line}" if (line.startswith(" ") or len(line.strip()) == 0) else f">>> {line}")
    lines = [line for line in lines if ">>> pass" not in line]
    content = ("" if previous_was_snippet else "```python\n") + "".join(lines)
    return content.strip() + "\n" + get_outputs(cell)


def convert_notebook(notebook_name: str):
    with open(Path(f"{notebook_name}.ipynb").resolve(), "r", encoding="utf-8") as fd:
        nb: Notebook = json.load(fd)

    lines: list[str] = []
    previous_was_snippet: bool = False
    for cell in nb["cells"]:
        if cell["metadata"] and "to_hide" in cell["metadata"]["tags"]:
            continue
        if cell["cell_type"] == "markdown":
            lines.append(format_markdown_cell(cell, previous_was_snippet))
            previous_was_snippet = False
        if cell["cell_type"] == "code" and len(cell["source"]) > 0:
            if cell["source"][0].startswith("!"):
                lines.append(format_shell_cell(cell, previous_was_snippet))
                previous_was_snippet = False
            elif cell["source"][0].startswith("%%"):
                lines.append(format_python_file_cell(cell, previous_was_snippet))
                previous_was_snippet = False
            else:
                lines.append(format_python_snippet_cell(cell, previous_was_snippet))
                previous_was_snippet = True

    with open(Path(f"{notebook_name}.md").resolve(), "w", encoding="utf-8") as fd:
        fd.write("".join(lines))

    print(f"{notebook_name} converted")


def replace_note_sections_in_markdown_for_myst(notebook_name: str):
    file = f"{notebook_name}.md"

    """Put the correct "Note" section inside the markdown docs (for MyST with sphinx)"""
    in_Note = False
    note_section = []
    note_sections_list: list[str] = []
    for line in open(file, "r", encoding="utf-8"):
        if line.startswith("**Note:**"):
            in_Note = True
            note_section.append(line)
            continue
        if in_Note:
            if line.strip():
                note_section.append(line)
            else:
                in_Note = False
                note_sections_list.append("".join(note_section))
                note_section = []
    with open(file, "r", encoding="utf-8") as fd:
        text = fd.read()
    for note in note_sections_list:
        note_snippet = note.replace("**Note:**", "```{note}", 1) + "```"
        new_snippet = "\n".join([line.lstrip() for line in note_snippet.split("\n")])
        text = text.replace(note, new_snippet)
    with open(file, "w", encoding="utf-8") as fd:
        fd.write(text)


def extract_block(text: str, start_marker: str, end_marker: str | None = None) -> str:
    i1 = text.find(start_marker)
    if i1 == -1:
        raise ValueError("Not on string")

    if end_marker is None:
        i2 = -1
    else:
        i2 = text.find(end_marker, i1 + len(start_marker))
        if i2 == -1:
            raise ValueError("Not on string")

    return text[i1:i2]  # include start marker, exclude end marker


def generate_readme(*files: str, excerpt: list[tuple[str, str | None]], readme: str = "../../../README.md"):
    readme_file = Path(readme).resolve()
    with open(readme_file, "r", encoding="utf-8") as fd:
        finaltext = extract_block(fd.read(), "#", excerpt[0][0])
    for i, file in enumerate(files):
        filepath = Path(f"{file}.md").resolve()
        with open(filepath, "r", encoding="utf-8") as fd:
            text = fd.read()
        text = extract_block(text, excerpt[i][0], excerpt[i][1])
        # text = text.replace("](./", "](./docs/sphinx/source/notebooks/")
        text = text.replace(
            "](./", "](https://github.com/diogo-rossi/clig/tree/main/docs/sphinx/source/notebooks/"
        )
        finaltext += text

    with open(readme_file, "w", encoding="utf-8") as fd:
        fd.write(finaltext)


convert_notebook("notebooks/userguide")
generate_readme("notebooks/userguide", excerpt=[("# User guide", None)])
replace_note_sections_in_markdown_for_myst("notebooks/userguide")
convert_notebook("notebooks/advancedfeatures")
replace_note_sections_in_markdown_for_myst("notebooks/advancedfeatures")
