# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "clig"
copyright = "2025, Diogo Rossi"
author = "Diogo Rossi"
release = "0.6.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

import os
import sys
import importlib
import inspect
from pathlib import Path
from typing import TypedDict, Literal
import git
import clig


class PyDomainInfo(TypedDict):
    module: str
    fullname: str


path = Path(__file__).parent
sys.path.insert(0, str((path).resolve()))
os.chdir(path)

git_repo = git.Repo(".", search_parent_directories=True)
code_url = f"https://github.com/diogo-rossi/clig/blob/main/"

import convert_notebook

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "myst_parser",
    "sphinx_copybutton",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.extlinks",
    "sphinxnotes.comboroles",
    "sphinx.ext.linkcode",
]

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_title = '<p style="text-align: center"><b>clig</b></p>'
html_static_path = ["_static"]
# conf.py
html_css_files = ["css/custom.css"]
html_logo = "logo.png"

myst_heading_anchors = 3


def linkcode_resolve(domain: Literal["py", "c", "cpp", "javascript"], info: PyDomainInfo):
    if domain != "py":
        print("---------------- here")
        return None
    if not info["module"]:
        print("---------------- there")
        return None

    mod = importlib.import_module(info["module"])
    if "." in info["fullname"]:
        objname, attrname = info["fullname"].split(".")
        obj = getattr(mod, objname)
        try:
            # object is a method of a class
            obj = getattr(obj, attrname)
        except AttributeError:
            # object is an attribute of a class
            print("---------------- other")
            return None
    else:
        obj = getattr(mod, info["fullname"])

    try:
        file = inspect.getsourcefile(obj)
        lines = inspect.getsourcelines(obj)
    except TypeError:
        # e.g. object is a typing.Union
        print("---------------- otherother")
        return None
    if file is None:
        print("---------------- otherotherother")
        return None
    file = Path(file).resolve().relative_to(git_repo.working_dir)
    # if file.parts[0] != "clig":
    # e.g. object is a typing.NewType
    # print(f"---------------- {file}")
    # return None
    start, end = lines[1], lines[1] + len(lines[0]) - 1

    # return "https://github.com/diogo-rossi/clig"  # f"{code_url}/{file}#L{start}-L{end}"
    return f"{code_url}/{file}#L{start}-L{end}"


def setup(app):
    app.add_css_file("custom.css")
