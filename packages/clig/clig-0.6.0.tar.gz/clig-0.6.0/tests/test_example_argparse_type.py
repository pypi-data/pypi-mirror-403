##############################################################################################################
# %%          Add `<root>/src` to sys.path
##############################################################################################################

import sys
from pathlib import Path

path = Path(__file__).parent
sys.path.insert(0, str((path).resolve()))
sys.path.insert(0, str((path / "../../src").resolve()))

##############################################################################################################
# %%          TESTS
##############################################################################################################

import clig
import argparse
import pathlib


def test_example_argparse_type_1():
    parser = argparse.ArgumentParser()
    parser.add_argument("count", type=int)
    parser.add_argument("distance", type=float)
    parser.add_argument("street", type=ascii)
    parser.add_argument("code_point", type=ord)
    parser.add_argument("datapath", type=pathlib.Path)

    passed_args = ["3", "45.6", "ã", "A", "C:/Users"]

    args = parser.parse_args(passed_args)

    class ASCII(str):
        def __new__(cls, value):
            return super().__new__(cls, ascii(value))

    class Ordinal(int):
        def __new__(cls, value):
            return super().__new__(cls, ord(value))

    def func(count: int, distance: float, street: ASCII, code_point: Ordinal, datapath: pathlib.Path):
        return locals()

    assert clig.run(func, passed_args) == {
        "count": args.count,
        "distance": args.distance,
        "street": args.street,
        "code_point": args.code_point,
        "datapath": args.datapath,
    }


def test_example_argparse_type_2():

    def hyphenated(string):
        return "-".join([word[:4] for word in string.casefold().split()])

    parser = argparse.ArgumentParser()
    _ = parser.add_argument("short_title", type=hyphenated)

    passed_args = ['"The Tale of Two Cities"']

    args = parser.parse_args(passed_args)
    assert args.short_title == '"the-tale-of-two-citi'

    class Hyphenated(str):
        def __new__(cls, value):
            return super().__new__(cls, hyphenated(value))

    def func(short_title: Hyphenated):
        return locals()

    assert clig.run(func, passed_args) == {"short_title": '"the-tale-of-two-citi'}
