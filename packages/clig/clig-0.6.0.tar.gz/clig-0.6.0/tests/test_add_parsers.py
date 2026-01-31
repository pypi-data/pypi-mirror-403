##############################################################################################################
# %%          Add `<root>/src` to sys.path
##############################################################################################################

import sys
from pathlib import Path

path = Path(__file__).parent
sys.path.insert(0, str((path).resolve()))
sys.path.insert(0, str((path / "../../src").resolve()))


import functions as fun
from clig import Command


def test_posWithType_kwWithType_kwBoolWithType_cligDocMultiline():
    cmd = Command(fun.ptc_kti_ktb_cligDocMutiline)
    cmd._add_parsers()
