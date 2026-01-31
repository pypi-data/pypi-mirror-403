# ----------------------------------------------------------------------------
# Description    : check_error_queue decorator tests
# Git repository : https://gitlab.com/qblox/packages/software/qblox_instruments.git
# Copyright (C) Qblox BV (2025)
# ----------------------------------------------------------------------------

from unittest.mock import MagicMock

from qblox_instruments.scpi.error_check import scpi_error_check
from qblox_instruments.types import DebugLevel


class Example:
    def __init__(self, debug: DebugLevel) -> None:
        self._debug = debug

    def _check_error(self, err: str) -> None:
        # Implementation is not important
        pass

    @scpi_error_check
    def function_with_default_decorator(self, arg: int) -> None:
        # Implementation is not important
        pass

    @scpi_error_check(minimal_check=True)
    def function_with_minimal_check_true(self, arg: int) -> None:
        # Implementation is not important
        pass


def test_default_minimal():
    example = Example(DebugLevel.MINIMAL_CHECK)
    example._check_error = MagicMock()
    example.function_with_default_decorator(2)
    example._check_error.assert_not_called()


def test_default_all():
    example = Example(DebugLevel.ERROR_CHECK)
    example._check_error = MagicMock()
    example.function_with_default_decorator(2)
    example._check_error.assert_called_once()


def test_minimal_check_true():
    example = Example(DebugLevel.MINIMAL_CHECK)
    example._check_error = MagicMock()
    example.function_with_minimal_check_true(2)
    example._check_error.assert_called_once()
