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


def test_optmetavarmodifier1():
    def myfun(aba: str = "hello", gue: str = "world"):
        return locals()

    cmd = clig.Command(myfun, optmetavarmodifier=lambda s: f"<{s.lower()}>")
    cmd._add_parsers()
    assert cmd.arguments[0].metavar == "<aba>"
    assert cmd.arguments[1].metavar == "<gue>"


def test_optmetavarmodifier2():
    def myfun(path_prefix: str = "users", user_age: int = 0):
        return locals()

    cmd = clig.Command(myfun, optmetavarmodifier=lambda s: f"{s.replace("_","-")}")
    cmd._add_parsers()
    assert cmd.arguments[0].metavar == "path-prefix"
    assert cmd.arguments[1].metavar == "user-age"

    cmd = clig.Command(myfun, optmetavarmodifier=lambda s: f"{s.upper()}")
    cmd._add_parsers()
    assert cmd.arguments[0].metavar == "PATH_PREFIX"
    assert cmd.arguments[1].metavar == "USER_AGE"

    cmd = clig.Command(myfun, optmetavarmodifier=lambda s: f"<{s.replace('_','-')}>")
    cmd._add_parsers()
    assert cmd.arguments[0].metavar == "<path-prefix>"
    assert cmd.arguments[1].metavar == "<user-age>"


def test_posmetavarmodifier():
    def myfun(my_arg_test):
        return locals()

    cmd = clig.Command(myfun, posmetavarmodifier=lambda s: f"{s.capitalize()}")
    cmd._add_parsers()
    assert cmd.arguments[0].metavar == "My_arg_test"

    cmd = clig.Command(myfun, posmetavarmodifier=lambda s: f"{s.replace("_","--").capitalize()}")
    cmd._add_parsers()
    assert cmd.arguments[0].metavar == "My--arg--test"


def test_metavarmodifier_example1():
    def myfun(bar, foo=None):
        return locals()

    cmd = clig.Command(myfun, posmetavarmodifier="XXX", optmetavarmodifier="YYY")
    cmd._add_parsers()
    assert cmd.arguments[0].metavar == "XXX"
    assert cmd.arguments[1].metavar == "YYY"


def test_metavarmodifier_example2():
    def prog(
        x: Arg[str, data("-x", make_flag=False, nargs=2, metavar=None)], foo: tuple[str, str] | None = None
    ):
        return locals()

    cmd = clig.Command(prog, prog="PROG", optmetavarmodifier=("bar", "baz"))
    cmd._add_parsers()
    assert cmd.arguments[0].metavar == None
    assert cmd.arguments[1].metavar == ("bar", "baz")

    assert cmd.arguments[0].option_strings == ["-x"]
    assert cmd.arguments[1].option_strings == ["--foo"]
