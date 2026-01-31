# ----------------------------------------------------------------------------
# Description    : IEEE488.2 interface
# Git repository : https://gitlab.com/qblox/packages/software/qblox_instruments.git
# Copyright (C) Qblox BV (2020)
# ----------------------------------------------------------------------------


# -- include -----------------------------------------------------------------

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING

from qblox_instruments.types import DebugLevel

if TYPE_CHECKING:
    from typing import Any, Callable

    from qblox_instruments.ieee488_2 import Transport
    from qblox_instruments.native import Cluster


# -- function ----------------------------------------------------------------


def gpib_error_check(  # noqa: ANN201
    minimal_check: bool | Callable[..., Any | None] = False,
):
    """
    Factory function for a decorator that catches and checks for errors on an IEEE488.2 call.

    Parameters
    ----------
    minimal_check
        If True, this decorator will always check for errors unless the debug
        level is ``DebugLevel.NO_CHECK``. By default False.

    Returns
    -------
    Callable
        The decorator.

    Raises
    ------
    RuntimeError
        An error was found in system error.

    """

    def decorator(func: Callable[..., Any | None]) -> Callable[..., Any | None]:
        @wraps(func)
        def wrapper(self: Ieee488_2 | Cluster, *args: Any, **kwargs: Any) -> Any | None:
            if self._debug in (DebugLevel.ERROR_CHECK, DebugLevel.VERSION_AND_ERROR_CHECK) or (
                self._debug == DebugLevel.MINIMAL_CHECK and minimal_check is True
            ):
                error = None
                try:
                    return func(self, *args, **kwargs)
                except OSError:
                    raise
                except Exception as err:
                    error = err
                finally:
                    self._check_error(error)

            else:
                return func(self, *args, **kwargs)

        return wrapper

    # if used without parentheses
    if callable(minimal_check):
        return decorator(minimal_check)
    # if used with parentheses
    return decorator


# -- class -------------------------------------------------------------------


class Ieee488_2:  # noqa: N801
    """
    Class that implements the IEEE488.2 interface.
    """

    __slots__ = ["_debug", "_transport"]

    # ------------------------------------------------------------------------
    def __init__(self, transport: Transport, debug: DebugLevel = DebugLevel.MINIMAL_CHECK) -> None:
        """
        Creates IEEE488.2 interface object.

        Parameters
        ----------
        transport : Transport
            Transport class responsible for the lowest level of communication
            (e.g. ethernet).
        debug : DebugLevel
            Debug level. See :class:`~qblox_instruments.types.DebugLevel` for more
            information. By default None, which means that for a connection to a dummy
            cluster, `DebugLevel.ERROR_CHECK` will be used, and for a real cluster,
            `DebugLevel.MINIMAL_CHECK`.

        """
        self._transport = transport
        self._debug = debug

    # ------------------------------------------------------------------------
    def _write(self, cmd_str: str) -> None:
        """
        Write command to instrument.

        Parameters
        ----------
        cmd_str : str
            Command string.

        """
        self._transport.write(cmd_str)

    # ------------------------------------------------------------------------
    def _write_bin(self, cmd_str: str, bin_block: bytes) -> None:
        """
        Write command and binary data block to instrument.

        Parameters
        ----------
        cmd_str : str
            Command string.
        bin_block : bytes
            Binary data array to send.

        """
        self._bin_block_write(cmd_str + " ", bin_block)

    # ------------------------------------------------------------------------
    def _read(self, cmd_str: str) -> str:
        """
        Write command to instrument and read response. Using an empty command
        string will skip the write and only read.

        Parameters
        ----------
        cmd_str : str
            Command string.

        Returns
        -------
        str
            Command response string.

        """
        self._transport.write(cmd_str)
        return self._transport.readline().rstrip()  # Remove trailing white space, CR, LF

    # ------------------------------------------------------------------------
    def _read_bin(self, cmd_str: str, flush_line_end: bool = True) -> bytes:
        """
        Write command to instrument and read binary data block. Using an empty
        command string will skip the write and only read to allow reading
        concatenated binary blocks.

        Parameters
        ----------
        cmd_str : str
            Command string.
        flush_line_end : bool
            Flush end of line characters.

        Returns
        -------
        bytes
            Binary data array received.

        """
        if cmd_str != "":
            self._transport.write(cmd_str)
        return self._bin_block_read(flush_line_end)

    # ------------------------------------------------------------------------
    def _write_read_bin(self, cmd_str: str, bin_block: bytes, flush_line_end: bool = True) -> bytes:
        """
        Write command and binary data block to instrument and read binary data
        block. Using an empty command string will skip the write and only read
        to allow reading concatenated binary blocks.

        Parameters
        ----------
        cmd_str : str
            Command string.
        bin_block : bytes
            Binary data array to send.
        flush_line_end : bool
            Flush end of line characters.

        Returns
        -------
        bytes
            Binary data array received.

        """
        if cmd_str != "":
            self._write_bin(cmd_str, bin_block)
        return self._bin_block_read(flush_line_end)

    # ------------------------------------------------------------------------
    def _bin_block_write(self, cmd_str: str, bin_block: bytes) -> None:
        """
        Write IEEE488.2 binary data block to instrument.

        Parameters
        ----------
        cmd_str : str
            Command string.
        bin_block : bytes
            Binary data array to send.

        """
        header = cmd_str + Ieee488_2._build_header_string(len(bin_block))
        self._transport.write_binary(header.encode(), bin_block)
        self._transport.write("")  # Add a Line Terminator

    # ------------------------------------------------------------------------
    def _bin_block_read(self, flush_line_end: bool = True) -> bytes:
        """
        Read IEEE488.2 binary data block from instrument.

        Parameters
        ----------
        flush_line_end : bool
            Flush end of line characters.

        Returns
        -------
        bytes
            Binary data array received.

        Raises
        ------
        RunTimeError
            Header error.

        """
        header_a = self._transport.read_binary(2)  # Read '#N'
        header_a_str = header_a.decode()
        # character ',' is a valid delimiter and we need to discard it
        if header_a_str[0] == ",":
            # read again to get the digit part of '#N'
            digit = self._transport.read_binary(1)
            digit_str = digit.decode()
            header_a_str = header_a_str[1] + digit_str  # continue as before
        if header_a_str[0] != "#":
            s = f"Header error: received {header_a}"
            raise RuntimeError(s)

        digit_cnt = int(header_a_str[1])
        header_b = self._transport.read_binary(digit_cnt)

        byte_cnt = int(header_b.decode())
        bin_block = self._transport.read_binary(byte_cnt)
        if flush_line_end:
            self._flush_line_end()

        return bin_block

    # ------------------------------------------------------------------------
    @staticmethod
    def _build_header_string(byte_cnt: int) -> str:
        """
        Generate IEEE488.2 binary data block header.

        Parameters
        ----------
        byte_cnt : int
            Size of the binary data block in bytes.

        Returns
        -------
        str
            Header string.

        """
        byte_cnt_str = str(byte_cnt)
        digit_cnt_str = str(len(byte_cnt_str))
        bin_header_str = "#" + digit_cnt_str + byte_cnt_str

        return bin_header_str

    # ------------------------------------------------------------------------
    def _flush_line_end(self) -> None:
        """
        Flush end of line <CR><LF> characters.
        """
        self._transport.read_binary(2)  # Consume <CR><LF>

    # -------------------------------------------------------------------------
    def _check_error(self, err: Exception | None = None) -> None:
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

        """
        if err:
            raise err from err

    # ------------------------------------------------------------------------
    # IEEE488.2 constants
    # ------------------------------------------------------------------------
    # fmt: off
    # *ESR and *ESE bits
    _ESR_OPERATION_COMPLETE = 0x01
    _ESR_REQUEST_CONTROL = 0x02
    _ESR_QUERY_ERROR = 0x04
    _ESR_DEVICE_DEPENDENT_ERROR = 0x08
    _ESR_EXECUTION_ERROR = 0x10
    _ESR_COMMAND_ERROR = 0x20
    _ESR_USER_REQUEST = 0x40
    _ESR_POWER_ON = 0x80
    # fmt: on

    # ------------------------------------------------------------------------
    # IEEE488.2 commands
    # ------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    @gpib_error_check
    def _get_idn(self) -> str:
        """
        Get device identity.

        Parameters
        ----------
        None

        Returns
        -------
        str
            Concatenated list of strings separated by the semicolon character.
            The IDN consists of four strings.

        Raises
        ------
        Exception
            An error is reported in system error and debug <= 1.

        """
        return self._read("*IDN?")

    # -------------------------------------------------------------------------
    @gpib_error_check
    def _reset(self) -> None:
        """
        Reset device and clear all status and event registers.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Raises
        ------
        Exception
            An error is reported in system error and debug <= 1.

        """
        self._write("*RST")

    # -------------------------------------------------------------------------
    @gpib_error_check
    def clear(self) -> None:
        """
        Clear all status and event registers (see `SCPI <https://www.ivifoundation.org/downloads/SCPI/scpi-99.pdf>`_).

        Parameters
        ----------
        None

        Returns
        -------
        None

        Raises
        ------
        Exception
            Invalid input parameter type.
        Exception
            An error is reported in system error and debug <= 1.

        """
        self._write("*CLS")

    # -------------------------------------------------------------------------
    @gpib_error_check
    def get_status_byte(self) -> int:
        """
        Get status byte register. Register is only cleared when feeding registers are cleared.

        Parameters
        ----------
        None

        Returns
        -------
        int
            Status byte register.

        Raises
        ------
        Exception
            An error is reported in system error and debug <= 1.

        """
        return int(self._read("*STB?"))

    # -------------------------------------------------------------------------
    @gpib_error_check
    def set_service_request_enable(self, reg: int) -> None:
        """
        Set service request enable register.

        Parameters
        ----------
        reg : int
            Service request enable register.

        Returns
        -------
        None

        Raises
        ------
        Exception
            Invalid input parameter type.
        Exception
            An error is reported in system error and debug <= 1.

        """
        if not isinstance(reg, int):
            raise TypeError(
                f"Unexpected type for input argument reg, expected int but got {type(reg).__qualname__}."  # noqa: E501
            )

        self._write(f"*SRE {reg}")

    # -------------------------------------------------------------------------
    @gpib_error_check
    def get_service_request_enable(self) -> int:
        """
        Get service request enable register. The register is cleared after reading it.

        Parameters
        ----------
        None

        Returns
        -------
        int
            Service request enable register.

        Raises
        ------
        Exception
            An error is reported in system error and debug <= 1.

        """
        return int(self._read("*SRE?"))

    # -------------------------------------------------------------------------
    @gpib_error_check
    def set_standard_event_status_enable(self, reg: int) -> None:
        """
        Set standard event status enable register.

        Parameters
        ----------
        reg : int
            Standard event status enable register.

        Returns
        -------
        None

        Raises
        ------
        Exception
            Invalid input parameter type.
        Exception
            An error is reported in system error and debug <= 1.

        """
        if not isinstance(reg, int):
            raise TypeError(
                f"Unexpected type for input argument reg, expected int but got {type(reg).__qualname__}."  # noqa: E501
            )

        self._write(f"*ESE {reg}")

    # -------------------------------------------------------------------------
    @gpib_error_check
    def get_standard_event_status_enable(self) -> int:
        """
        Get standard event status enable register. The register is cleared after reading it.

        Parameters
        ----------
        None

        Returns
        -------
        int
            Standard event status enable register.

        Raises
        ------
        Exception
            An error is reported in system error and debug <= 1.
            All errors are read from system error and listed in the exception.

        """
        return int(self._read("*ESE?"))

    # -------------------------------------------------------------------------
    @gpib_error_check
    def get_standard_event_status(self) -> int:
        """
        Get standard event status register. The register is cleared after reading it.

        Parameters
        ----------
        None

        Returns
        -------
        int
            Standard event status register.

        Raises
        ------
        Exception
            An error is reported in system error and debug <= 1.

        """
        return int(self._read("*ESR?"))

    # -------------------------------------------------------------------------
    @gpib_error_check
    def set_operation_complete(self) -> None:
        """
        Set device in operation complete query active state.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Raises
        ------
        Exception
            An error is reported in system error and debug <= 1.

        """
        self._write("*OPC")

    # -------------------------------------------------------------------------
    @gpib_error_check
    def get_operation_complete(self) -> bool:
        """
        Get operation complete state.

        Parameters
        ----------
        None

        Returns
        -------
        bool
            Operation complete state (False = running, True = completed).

        Raises
        ------
        Exception
            An error is reported in system error and debug <= 1.

        """
        return bool(int(self._read("*OPC?")))

    # -------------------------------------------------------------------------
    @gpib_error_check
    def test(self) -> bool:
        """
        Run self-test.

        Parameters
        ----------
        None

        Returns
        -------
        bool
            Test result (False = failed, True = success).

        Raises
        ------
        Exception
            An error is reported in system error and debug <= 1.

        """
        return bool(int(self._read("*TST?")))

    # -------------------------------------------------------------------------
    @gpib_error_check
    def wait(self) -> None:
        """
        Wait until operations completed before continuing.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Raises
        ------
        Exception
            An error is reported in system error and debug <= 1.

        """
        self._write("*WAI")
