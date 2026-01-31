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
from clig import Arg, data


def test_star_args():
    def foo(name: str, age: int, height: float, *others: str):
        return locals()

    assert clig.run(foo, "jack 32 1.86 badger BAR spam".split()) == {
        "name": "jack",
        "age": 32,
        "height": 1.86,
        "others": ("badger", "BAR", "spam"),
    }


def test_star_args_with_Arg_and_data():
    def foo(aaa: int, bbb: int, ccc: int, ddd: int, eee: Arg[int, data(nargs="?", default=777)], *fff):
        return locals()

    assert clig.run(foo, "1 2 3 4 5".split()) == {"aaa": 1, "bbb": 2, "ccc": 3, "ddd": 4, "eee": 5, "fff": ()}
    assert clig.run(foo, "1 2 3 4".split()) == {"aaa": 1, "bbb": 2, "ccc": 3, "ddd": 4, "eee": 777, "fff": ()}
    assert clig.run(foo, "1 2 3 4 5 6 7 8 9".split()) == {
        "aaa": 1,
        "bbb": 2,
        "ccc": 3,
        "ddd": 4,
        "eee": 5,
        "fff": ("6", "7", "8", "9"),
    }


def test_star_args_typed_with_Arg_and_data():
    def foo(aaa: int, bbb: int, ccc: int, ddd: int, eee: Arg[int, data(nargs="?", default=777)], *fff: int):
        return locals()

    assert clig.run(foo, "1 2 3 4 5".split()) == {"aaa": 1, "bbb": 2, "ccc": 3, "ddd": 4, "eee": 5, "fff": ()}
    assert clig.run(foo, "1 2 3 4".split()) == {"aaa": 1, "bbb": 2, "ccc": 3, "ddd": 4, "eee": 777, "fff": ()}
    assert clig.run(foo, "1 2 3 4 5 6 7 8 9".split()) == {
        "aaa": 1,
        "bbb": 2,
        "ccc": 3,
        "ddd": 4,
        "eee": 5,
        "fff": (6, 7, 8, 9),
    }


def test_star_kwargs_with_Arg_and_data():
    def foo(aaa: int, bbb: int, **fff):
        return locals()

    assert clig.run(foo, "1 2".split()) == {"aaa": 1, "bbb": 2, "fff": {}}
    assert clig.run(foo, "1 2 --numbers 3 4 5 6 --letters  a b c --name jack".split()) == {
        "aaa": 1,
        "bbb": 2,
        "fff": {"numbers": ["3", "4", "5", "6"], "letters": ["a", "b", "c"], "name": "jack"},
    }


def test_star_kwargs_typed_with_Arg_and_data():
    def foo(aaa: int, bbb: int, **fff: int):
        return locals()

    assert clig.run(foo, "1 2".split()) == {"aaa": 1, "bbb": 2, "fff": {}}
    assert clig.run(foo, "1 2 --numbers 3 4 5 6 --ages 32 45 67 --position 7".split()) == {
        "aaa": 1,
        "bbb": 2,
        "fff": {"numbers": [3, 4, 5, 6], "ages": [32, 45, 67], "position": 7},
    }
