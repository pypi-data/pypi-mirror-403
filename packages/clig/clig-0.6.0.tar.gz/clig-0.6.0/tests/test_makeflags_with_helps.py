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

import argparse
import pytest
from resources import CapSys
from clig.clig import Arg, data, Command


def test_make_short_with_helps():
    def main(hostname: str = "me"):
        return locals()

    cmd = Command(main, make_shorts=True)
    cmd._add_parsers()
    assert cmd.arguments[0].option_strings == ["-H", "--hostname"]


def test_make_short_with_custom_helps():
    def main(hostname: str = "me"):
        return locals()

    cmd = Command(main, make_shorts=True, help_flags=["-?", "--help"])
    cmd._add_parsers()
    assert cmd.arguments[0].option_strings == ["-h", "--hostname"]
    assert cmd.parser is not None
    assert cmd.parser._actions[0].option_strings == ["-?", "--help"]
