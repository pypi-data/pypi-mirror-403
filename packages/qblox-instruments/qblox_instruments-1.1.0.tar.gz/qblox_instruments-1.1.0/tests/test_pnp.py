# ----------------------------------------------------------------------------
# Description    : Plug and Play test script
# Git repository : https://gitlab.com/qblox/packages/software/qblox_instruments.git
# Copyright (C) Qblox BV (2020)
# ----------------------------------------------------------------------------


# -- include -----------------------------------------------------------------

import sys
from io import StringIO

import pytest

from qblox_instruments import PlugAndPlay

# -- fixtures ----------------------------------------------------------------


@pytest.fixture(name="stdout")
def make_stdout():
    new_stdout = StringIO()
    sys.stdout = new_stdout
    yield new_stdout
    sys.stdout = sys.__stdout__


@pytest.fixture(name="pnp")
def make_pnp():
    with PlugAndPlay() as pnp:
        yield pnp


# -- functions ---------------------------------------------------------------


def test_help(stdout):
    """
    Test getting help using commandline interface.

    Parameters
    ----------
    stdout
        StringIO connected to sys.stdout

    """
    try:
        PlugAndPlay.cmd_line("")
        raise AssertionError("Should have failed.")
    except RuntimeError:
        pass


# ----------------------------------------------------------------------------
def test_list(stdout):
    """
    Test listing the devices using commandline interface.

    Parameters
    ----------
    stdout
        StringIO connected to sys.stdout

    """
    PlugAndPlay.cmd_line(["list"])


# ----------------------------------------------------------------------------
def test_describe(pnp):
    """
    Test describing a module using it's serial number.

    Parameters
    ----------
    pnp
        PlugAndPlay object.

    """
    try:
        pnp.describe("test")
        raise AssertionError("Should have failed.")
    except TimeoutError:
        pass
