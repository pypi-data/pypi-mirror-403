# ----------------------------------------------------------------------------
# Description    : SCPI interface
# Git repository : https://gitlab.com/qblox/packages/software/qblox_instruments.git
# Copyright (C) Qblox BV (2025)
# ----------------------------------------------------------------------------

# -- include ------------------------------------------------------------------

import sys
from typing import ClassVar, Optional

from qblox_instruments.build import BuildInfo
from qblox_instruments.ieee488_2 import Ieee488_2

# -- class --------------------------------------------------------------------


class Scpi(Ieee488_2):
    COMPATIBLE_BUILDS: ClassVar[list[BuildInfo]]
    """Compatible builds for this SCPI layer."""

    # ------------------------------------------------------------------------
    # SCPI constants
    # ------------------------------------------------------------------------

    # STATus:OPERation bits
    _STAT_OPER_CALIBRATING = 0x0001
    """ The instrument is currently performing a calibration """
    _STAT_OPER_SETTLING = 0x0002
    """
    The instrument is waiting for signals it controls
    to stabilize enough to begin measurements
    """
    _STAT_OPER_RANGING = 0x0004
    """ The instrument is currently changing its range """
    _STAT_OPER_SWEEPING = 0x0008
    """ A sweep is in progress """
    _STAT_OPER_MEASURING = 0x0010
    """ The instrument is actively measuring """
    _STAT_OPER_WAIT_TRIG = 0x0020
    """ The instrument is in a “wait for trigger” state of the trigger model """
    _STAT_OPER_WAIT_ARM = 0x0040
    """ The instrument is in a “wait for arm” state of the trigger model """
    _STAT_OPER_CORRECTING = 0x0080
    """ The instrument is currently performing a correction """
    _STAT_OPER_INST_SUMMARY = 0x2000
    """ One of n multiple logical instruments is reporting OPERational status """
    _STAT_OPER_PROG_RUNNING = 0x4000
    """ A user-defined program is currently in the run state """

    # STATus:QUEStionable bits
    _STAT_QUES_VOLTAGE = 0x0001
    _STAT_QUES_CURRENT = 0x0002
    _STAT_QUES_TIME = 0x0004
    _STAT_QUES_POWER = 0x0008
    _STAT_QUES_TEMPERATURE = 0x0010
    _STAT_QUES_FREQUENCY = 0x0020
    _STAT_QUES_PHASE = 0x0040
    _STAT_QUES_MODULATION = 0x0080
    _STAT_QUES_CALIBRATION = 0x0100
    _STAT_QUES_INST_SUMMARY = 0x2000
    _STAT_QUES_COMMAND_WARNING = 0x4000

    # -------------------------------------------------------------------------
    def get_system_error(self) -> str:
        """
        Get system error from queue (see `SCPI <https://www.ivifoundation.org/downloads/SCPI/scpi-99.pdf>`_).

        Parameters
        ----------
        None

        Returns
        -------
        str
            System error description string.

        """
        return self._read("SYSTem:ERRor:NEXT?")

    # -------------------------------------------------------------------------
    def get_num_system_error(self) -> int:
        """
        Get number of system errors (see `SCPI <https://www.ivifoundation.org/downloads/SCPI/scpi-99.pdf>`_).

        Parameters
        ----------
        None

        Returns
        -------
        int
            Current number of system errors.

        """
        return int(self._read("SYSTem:ERRor:COUNt?"))

    # -------------------------------------------------------------------------
    def check_error_queue(self, err: Optional[Exception] = None) -> None:
        """
        Check system error for errors. Empties and prints the complete error
        queue.

        Parameters
        ----------
        err : Optional[Exception]
            Exception to reraise.

        Raises
        ------
        Exception
            An exception was passed as input argument.
        RuntimeError
            An error was found in system error.

        """
        errors = [str(err)] if err is not None else []
        while self.get_num_system_error() > 0:
            errors.append(",".join(self.get_system_error().split(",")[1:]))

        if len(errors) > 0:
            err_type = type(err) if err is not None else RuntimeError
            raise err_type("\n".join(errors)).with_traceback(sys.exc_info()[2]) from err

    # -------------------------------------------------------------------------
    def clear_error_queue(self) -> None:
        """
        Empty and the complete error queue.

        Parameters
        ----------
        None

        """
        # Clear SCPI error queue.
        while self.get_num_system_error() > 0:
            _ = self.get_system_error()

    # -------------------------------------------------------------------------
    def _check_error(self, err: Optional[Exception] = None) -> None:
        self.check_error_queue(err)
