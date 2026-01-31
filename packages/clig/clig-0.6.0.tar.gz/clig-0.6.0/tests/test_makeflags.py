##############################################################################################################
# %%          Add `<root>/src` to sys.path
##############################################################################################################

import sys
from pathlib import Path

this_dir = Path(__file__).parent

sys.path.insert(0, str((this_dir).resolve()))
sys.path.insert(0, str((this_dir / "../src").resolve()))

##############################################################################################################
# %%          Tests
##############################################################################################################

import pytest
from resources import CapSys
from clig.clig import Arg, data, Command


def test_make_flag_on_argument_automatically():
    def main(foobar: Arg[str, data("-f")]):
        return locals()

    cmd = Command(main)
    cmd._add_parsers()
    assert cmd.arguments[0].option_strings == ["-f", "--foobar"]


def test_donot_make_flag_on_argument_automatically():
    def main(foobar: Arg[str, data("-f", "--foo")]):
        return locals()

    cmd = Command(main)
    cmd._add_parsers()
    assert cmd.arguments[0].option_strings == ["-f", "--foo"]


def test_force_make_flag_on_argument_automatically():
    def main(foobar: Arg[str, data("-f", "--foo", make_flag=True)]):
        return locals()

    cmd = Command(main)
    cmd._add_parsers()
    assert cmd.arguments[0].option_strings == ["-f", "--foo", "--foobar"]


def test_force_make_flag_on_argument_automatically_in_command():
    def main(foobar: Arg[str, data("-f", "--foo")]):
        return locals()

    cmd = Command(main, make_flags=True)
    cmd._add_parsers()
    assert cmd.arguments[0].option_strings == ["-f", "--foo", "--foobar"]


def test_force_donot_make_flag_on_argument():
    def main(foobar: Arg[str, data("-f", make_flag=False)]):
        return locals()

    cmd = Command(main)
    cmd._add_parsers()
    assert cmd.arguments[0].option_strings == ["-f"]


def test_force_donot_make_flag_in_command():
    def main(foobar: Arg[str, data("-f")]):
        return locals()

    cmd = Command(main, make_flags=False)
    cmd._add_parsers()
    assert cmd.arguments[0].option_strings == ["-f"]


def test_conflict_force_make_flags_true_on_argument():
    def main(foobar: Arg[str, data("-f", "--foo", make_flag=True)], bazham: Arg[str, data("-b")]):
        return locals()

    cmd = Command(main, make_flags=False)
    cmd._add_parsers()
    assert cmd.arguments[0].option_strings == ["-f", "--foo", "--foobar"]
    assert cmd.arguments[1].option_strings == ["-b"]


def test_conflict_force_make_flags_true_on_command():
    def main(foobar: Arg[str, data("-f", "--foo", make_flag=False)], bazham: Arg[str, data("-b", "--baz")]):
        return locals()

    cmd = Command(main, make_flags=True)
    cmd._add_parsers()
    assert cmd.arguments[0].option_strings == ["-f", "--foo"]
    assert cmd.arguments[1].option_strings == ["-b", "--baz", "--bazham"]


def test_force_make_flags_on_command_argument_not_annotated(capsys: CapSys):
    def main(foobar: str, bazham: int = 42):
        return locals()

    cmd = Command(main, make_flags=False)
    cmd._add_parsers()
    assert cmd.arguments[0].option_strings == []
    assert cmd.arguments[1].option_strings == []

    with pytest.raises(SystemExit) as e:
        cmd.run(["dio"])

    assert e.value.code == 2
    assert "the following arguments are required: bazham" in capsys.readouterr().err


def test_force_make_shorts_on_command():
    def main(foobar: str = "dio", bazham: int = 42):
        return locals()

    cmd = Command(main)
    cmd._add_parsers()
    assert cmd.arguments[0].option_strings == ["--foobar"]
    assert cmd.arguments[1].option_strings == ["--bazham"]

    cmd = Command(main, make_shorts=True)
    cmd._add_parsers()
    assert cmd.arguments[0].option_strings == ["-f", "--foobar"]
    assert cmd.arguments[1].option_strings == ["-b", "--bazham"]


def test_force_make_shorts_conflict(capsys: CapSys):
    def main(foo: str = "dio", foobar: int = 42):
        return locals()

    cmd = Command(main)
    cmd._add_parsers()
    assert cmd.arguments[0].option_strings == ["--foo"]
    assert cmd.arguments[1].option_strings == ["--foobar"]

    cmd = Command(main, make_shorts=True)
    cmd._add_parsers()
    assert cmd.arguments[0].option_strings == ["-f", "--foo"]
    assert cmd.arguments[1].option_strings == ["-F", "--foobar"]


def test_force_make_shorts_conflicting_on_command():
    def main(foobar: str = "dio", foo_ham: int = 42, foo_hat: int = 42):
        return locals()

    cmd = Command(main, make_shorts=True)
    cmd._add_parsers()
    assert cmd.arguments[0].option_strings == ["-f", "--foobar"]
    assert cmd.arguments[1].option_strings == ["-F", "--foo-ham"]
    assert cmd.arguments[2].option_strings == ["-fh", "--foo-hat"]

    def second(name: str = "name", namefile: str = "file", namefolder: str = "folder"):
        return locals()

    cmd = Command(second, make_shorts=True)
    cmd._add_parsers()
    assert cmd.arguments[0].option_strings == ["-n", "--name"]
    assert cmd.arguments[1].option_strings == ["-N", "--namefile"]
    assert cmd.arguments[2].option_strings == ["-na", "--namefolder"]

    def third(
        name: str = "name", name_file: str = "file", name_folder: str = "folder", name_files: str = "folder"
    ):
        return locals()

    cmd = Command(third, make_shorts=True)
    cmd._add_parsers()
    assert cmd.arguments[0].option_strings == ["-n", "--name"]
    assert cmd.arguments[1].option_strings == ["-N", "--name-file"]
    assert cmd.arguments[2].option_strings == ["-nf", "--name-folder"]
    assert cmd.arguments[3].option_strings == ["-na", "--name-files"]
