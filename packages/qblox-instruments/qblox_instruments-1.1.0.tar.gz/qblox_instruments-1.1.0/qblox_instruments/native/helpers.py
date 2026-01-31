# ----------------------------------------------------------------------------
# Description    : Native interface helpers
# Git repository : https://gitlab.com/qblox/packages/software/qblox_instruments.git
# Copyright (C) Qblox BV (2021)
# ----------------------------------------------------------------------------

import copy
import math
import re
from collections.abc import Iterable, Iterator
from typing import Any, Callable, Optional, Union

import fastjsonschema
import numpy as np
from qcodes import validators as vals

from qblox_instruments.ieee488_2 import Ieee488_2
from qblox_instruments.native.definitions import (
    ACQ_JSON_SCHEMA,
    MAX_PROGRAM_LENGTH,
    QCM_SEQUENCE_JSON_SCHEMA,
    QRM_SEQUENCE_JSON_SCHEMA,
    QTM_SEQUENCE_JSON_SCHEMA,
    WAVE_JSON_SCHEMA,
    ChannelType,
    get_allowed_channels,
)
from qblox_instruments.types import WaveformWeight


# -----------------------------------------------------------------------------
# TODO: Here, the number of outputs and inputs is again hardcoded, just like in
#  module.py. In the future it should all be moved to one common place.
class ChannelMapCache:
    def __init__(self, instrument: Any, slot: int) -> None:
        self._funcs = instrument
        self._slot = slot
        if self._funcs._is_qrm_type(slot):
            self._num_dac = 2
            self._num_adc = 2
            self._num_seq = 6
        elif self._funcs._is_qcm_type(slot):
            self._num_dac = 4
            self._num_adc = 0
            self._num_seq = 6
        elif self._funcs._is_qrc_type(slot):
            self._num_dac = 12
            self._num_adc = 4
            self._num_seq = 12
        elif self._funcs._is_qtm_type(slot):
            self._num_dac = 0
            self._num_adc = 0
            self._num_seq = 8
        else:
            self._num_dac = 0
            self._num_adc = 0
            self._num_seq = 6
        self._current = {
            ChannelType.AWG: [None] * self._num_seq,
            ChannelType.ACQ: [None] * self._num_seq,
        }
        self._writeback = {
            ChannelType.AWG: [None] * self._num_seq,
            ChannelType.ACQ: [None] * self._num_seq,
        }

    def _check_direction(self, direction: ChannelType) -> None:
        if direction not in [ChannelType.AWG, ChannelType.ACQ]:
            raise ValueError(f"Invalid direction: {direction!r}")

    def _check_seq(self, seq: int) -> None:
        if not isinstance(seq, int):
            raise TypeError(f"seq should be int but is {type(seq).__name__}")
        if seq < 0 or seq >= self._num_seq:
            raise ValueError(f"seq is out of range: {seq}, max seq is {self._num_seq}")

    def _check_dac(self, dac: int) -> None:
        if not isinstance(dac, int):
            raise TypeError(f"dac should be int but is {type(dac).__name__}")
        if dac < 0 or dac >= self._num_dac:
            raise ValueError(f"dac is out of range: {dac}")

    def _check_adc(self, adc: int) -> None:
        if not isinstance(adc, int):
            raise TypeError(f"adc should be int but is {type(adc).__name__}")
        if adc < 0 or adc >= self._num_adc:
            raise ValueError(f"adc is out of range: {adc}")

    def _check_channel(self, direction: ChannelType, channel: int) -> None:
        self._check_direction(direction)
        if direction == ChannelType.AWG:
            self._check_dac(channel)
        else:
            self._check_adc(channel)

    def _check_path(self, path: int) -> None:
        if not isinstance(path, int):
            raise TypeError(f"path should be int but is {type(path).__name__}")
        if path < 0 or path >= 2:
            raise ValueError(f"path is out of range: {path}")

    def _get_cache(self, direction: ChannelType, seq: int) -> Any:
        """
        Returns a writable reference to the writeback cache entry for the
        channel map data for the given signal direction and sequencer.
        """
        self._check_direction(direction)
        self._check_seq(seq)

        # If we already have this in our writeback cache, return that entry.
        if self._writeback[direction][seq] is not None:
            return self._writeback[direction][seq]

        # If we don't know the current state yet, fetch it from the device.
        if self._current[direction][seq] is None:
            # Fetch from the device.
            if direction == ChannelType.AWG:
                current = self._funcs._get_sequencer_channel_map(self._slot, seq)
            elif self._num_adc > 0:
                current = self._funcs._get_sequencer_acq_channel_map(self._slot, seq)
            else:
                current = [[], []]

            # Convert the inner JSON arrays to the sets they represent.
            # Otherwise the equality check between current and desired
            # can give false negatives.
            for i in range(len(current)):
                current[i] = set(current[i])

            # Update current state cache.
            self._current[direction][seq] = current

        # Make a writeback cache entry for the current state. We make a copy
        # so the caller can update it.
        self._writeback[direction][seq] = copy.deepcopy(self._current[direction][seq])

        return self._writeback[direction][seq]

    def _set_cache(self, direction: ChannelType, seq: int, state: list[set[int]]) -> None:
        """
        Overrides the writeback cache entry for the channel map data for
        the given signal direction and sequencer.
        """
        self._check_direction(direction)
        self._check_seq(seq)
        self._writeback[direction][seq] = state

    def _flush_cache(self, direction: ChannelType, seq: int) -> None:
        """
        Flushes any pending changes for the given direction and sequencer to
        the instrument.
        """
        self._check_direction(direction)
        self._check_seq(seq)

        writeback = self._writeback[direction][seq]

        # Return if there is no writeback cache entry.
        if writeback is None:
            return

        # Also return if there is a writeback cache entry but it matches the
        # current state already.
        if writeback == self._current[direction][seq]:
            return

        # Convert the sets to lists.
        writeback = list(map(list, writeback))

        # Write to the instrument.
        if direction == ChannelType.AWG:
            self._funcs._set_sequencer_channel_map(self._slot, seq, writeback)
        elif self._num_adc > 0:
            self._funcs._set_sequencer_acq_channel_map(self._slot, seq, writeback)
        else:
            raise RuntimeError(
                "attempting to set acquisition channel map on instrument with no ADCs"
            )

        # Copy from the writeback cache to the current state cache to reflect
        # the changes made.
        self._current[direction][seq] = copy.deepcopy(self._writeback[direction][seq])

        # Clear the writeback cache entry.
        self._writeback[direction][seq] = None

    def clear_path(self, direction: ChannelType, seq: int, path: int) -> None:
        """
        Clears all connections to the given path of the given sequencer in
        the given direction.
        """
        self._check_direction(direction)
        self._check_seq(seq)
        self._get_cache(direction, seq)[path].clear()

    def clear(self, direction: Optional[ChannelType] = None, seq: Optional[int] = None) -> None:
        """
        Clears all connections to the given sequencer (or all of them if
        None) in the given direction (or both if None).
        """
        if direction is None:
            self.clear(ChannelType.AWG, seq)
            self.clear(ChannelType.ACQ, seq)
            return
        if seq is None:
            for seq in range(self._num_seq):  # noqa: PLR1704
                self.clear(direction, seq)

        self._check_direction(direction)
        self._check_seq(seq)
        self._set_cache(direction, seq, [set(), set()])

    def connect(
        self,
        direction: ChannelType,
        seq: int,
        path: int,
        channel: int,
        resolve_conflicts: bool = True,
    ) -> None:
        """
        Updates the (cached) channel map to make the given connection. If
        this connection conflicts with an existing connection, behavior depends
        on resolve_conflicts: if set, the offending connection is first
        disconnected if possible; if cleared, a RuntimeError is raised.
        """
        self._check_channel(direction, channel)
        self._check_seq(seq)
        self._check_path(path)

        cache = self._get_cache(direction, seq)
        output = channel if (not self._funcs._is_rf_type(self._slot)) else channel // 2

        # Check whether the connection is allowed.
        allowed_channels = get_allowed_channels(
            self._funcs._is_qrc_type(self._slot), direction, seq
        )
        if (allowed_channels is not True) and (channel not in allowed_channels):
            direction_str = "DAC output" if direction == ChannelType.AWG else "ADC input"
            raise RuntimeError(
                f"Prohibited channel map connection: "
                f"{direction_str} {output} on sequencer {seq} cannot be connected"
            )

        # The I and Q path of a sequencer cannot both be tied to a DAC
        # simultaneously.
        if direction == ChannelType.AWG and channel in cache[1 - path]:
            if not resolve_conflicts:
                raise RuntimeError(
                    f"DAC output {output} "
                    f"is already connected to the other I/Q path of sequencer {seq}"
                )
            cache[1 - path].discard(channel)

        # An acquisition input can only be tied to one ADC at a time.
        if direction == ChannelType.ACQ and cache[path] and channel not in cache[path]:
            if not resolve_conflicts:
                raise RuntimeError(
                    f"acquisition path {path} ({'IQ'[path]}) is already connected to another input"
                )
            cache[path].clear()

        # Raise if the connection already exists.
        if not resolve_conflicts and channel in cache[path]:
            raise RuntimeError("connection already exists")

        cache[path].add(channel)

    def disconnect(self, direction: ChannelType, seq: int, path: int, channel: int) -> None:
        """Updates the (cached) channel map to disable the given connection."""
        self._check_channel(direction, channel)
        self._check_seq(seq)
        self._check_path(path)
        self._get_cache(direction, seq)[path].discard(channel)

    def is_connected(self, direction: ChannelType, seq: int, path: int, channel: int) -> bool:
        """
        Returns whether the given connection is currently enabled (in
        cache).
        """
        self._check_channel(direction, channel)
        self._check_seq(seq)
        self._check_path(path)
        return channel in self._get_cache(direction, seq)[path]

    def get_connected_channels(self, direction: ChannelType, seq: int, path: int) -> Iterator[int]:
        """
        Returns a list of the channels connected to the given
        direction/sequencer/path triple.
        """
        self._check_direction(direction)
        self._check_seq(seq)
        self._check_path(path)
        yield from self._get_cache(direction, seq)[path]

    def iter_connections(self) -> Iterator[tuple[int, str, str]]:
        """
        Iterates over all enabled connections between ADCs, DACs, and
        sequencers. The four components of each connection are:
         - the index of the sequencer for the connection;
         - the connection point of the sequencer being connected to, being
           one of `I`, `Q`, `acq_I`, or `acq_Q`;
         - the external connection, being either `adc#` or `dac#`, where
           `#` is the zero-based ADC or DAC index.
        """
        for seq in range(self._num_seq):
            for path, name in [(0, "I"), (1, "Q")]:
                for channel in self.get_connected_channels(ChannelType.AWG, seq, path):
                    yield seq, name, f"dac{channel}"
            if self._num_adc:
                for path, name in [(0, "acq_I"), (1, "acq_Q")]:
                    for channel in self.get_connected_channels(ChannelType.ACQ, seq, path):
                        yield seq, name, f"adc{channel}"

    def flush(self) -> None:
        """Flushes pending changes to the channel map to the instrument."""
        for seq in range(self._num_seq):
            self._flush_cache(ChannelType.AWG, seq)
        if self._num_adc:
            for seq in range(self._num_seq):
                self._flush_cache(ChannelType.ACQ, seq)

    def __enter__(self) -> "ChannelMapCache":
        """
        Allow usage as a context manager, such that the instrument will be
        updated when the context closes.
        """
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Optional[bool]:
        self.flush()


# -----------------------------------------------------------------------------
class MultiplesNumbers(vals.Numbers):
    """
    A validator that checks if a value is a number multiple of a
    fixed divisor. This class extends validators.Numbers such that the
    value is also checked for being number between an optional
    min_value and max_value. Furthermore this validator checks that
    the value is a multiple of a fixed divisor.
    (i.e. value % divisor == 0)
    The class is based on validators.Multiples.

    Args:
        divisor: the value need the be a multiple of this divisor
        max_value: value must be <= max_value
        min_value: value must be >= min_value
    """

    def __init__(self, divisor: vals.validators.numbertypes = 1, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if divisor <= 0:
            raise TypeError("divisor must be a positive")
        self._divisor = divisor
        self._valid_values = (divisor,)

    def validate(self, value: vals.validators.numbertypes, context: str = "") -> None:
        """
        Validates if the value is a integer multiple of divisor else raises
        error.

        Args:
            value: A number.
            context: Context for validation.

        Raises
        ------
            ValueError: If not a multiple of a divisor.

        """
        super().validate(value=value, context=context)

        quotient = value / self._divisor
        closest_integer = round(quotient)

        if not math.isclose(quotient, closest_integer, rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError(f"{value!r} is not a multiple of {self._divisor!r}; {context}")

    def __repr__(self) -> str:
        return super().__repr__()[:-1] + f", Multiples of {self._divisor}>"

    is_numeric = True

    @property
    def divisor(self) -> int:
        return self._divisor


# -----------------------------------------------------------------------------
class Ieee488_2Connection:  # noqa: N801
    """
    Connection class to only expose public read/read_bin/write/write_bin methods.
    """

    def __init__(self, interface: Ieee488_2) -> None:
        self._interface = interface

    def read(self, cmd_str: str) -> str:
        return self._interface._read(cmd_str)

    def read_bin(self, cmd_str: str, flush_line_end: bool = True) -> bytes:
        return self._interface._read_bin(cmd_str, flush_line_end)

    def write(self, cmd_str: str) -> None:
        self._interface._write(cmd_str)

    def write_bin(self, cmd_str: str, bin_block: bytes) -> None:
        self._interface._write_bin(cmd_str, bin_block)

    def flush_line_end(self) -> None:
        self._interface._flush_line_end()


# -- helper functions --------------------------------------------------------


def check_sequencer_index(sequencer: int) -> None:
    """
    Check if sequencer index is within range. We just check if the index is a
    positive integer here, because sending a negative number breaks the
    underlying SCPI command. The upperbound is checked by the instrument.

    Parameters
    ----------
    sequencer : int
        Sequencer index.

    Raises
    ------
    ValueError
        Sequencer index is out-of-range (i.e. < 1).

    """
    if sequencer < 0:
        raise ValueError(f"Sequencer index is out-of-range ({sequencer})")


# ---------------------------------------------------------------------
def check_io_channel_index(io_channel: int) -> None:
    """
    Check if I/O channel index is within range. We just check if the
    index is a positive integer here, because sending a negative number
    breaks the underlying SCPI command. The upperbound is checked by the
    instrument.

    Parameters
    ----------
    io_channel : int
        I/O channel index.

    Raises
    ------
    ValueError
        I/O channel index is out-of-range (i.e. < 1).

    """
    if io_channel < 0:
        raise ValueError(f"I/O channel index is out-of-range ({io_channel})")


# ---------------------------------------------------------------------
def check_program_length(program: str) -> None:
    """
    Checks if the program length is above the limit.
    If it is,a Runtime error is raised.

    Parameters
    ----------
    program : str
        Sequence program to be updated to the device

    Raises
    ------
    RuntimeError
        Too large program string.

    """
    if len(program.encode("utf-8")) > MAX_PROGRAM_LENGTH:
        raise RuntimeError(
            f"Program length too large, expected something below {MAX_PROGRAM_LENGTH} bytes "
            f"but got {len(program.encode('utf-8'))} bytes."
        )


# ----------------------------------------------------------------------------
def check_is_valid_type(is_type: bool) -> None:
    """
    Check if module type is valid. If not throw a NotImplemented exception.
    This helper function can be used to catch execution of QXM functionality
    that is not implemented.

    Parameters
    ----------
    is_type : bool
        Is module type.

    Raises
    ------
    NotImplementedError
        Functionality not available on this module.

    """
    if not is_type:
        raise NotImplementedError("This functionality not available on this module.")


# ----------------------------------------------------------------------------
def create_read_bin(
    read_bin_func: Callable[[str, bool], bytes], cmd: str
) -> Callable[[Optional[int], Optional[int], Optional[str]], bytes]:
    """
    Create binary read function that can provide a binary read with a
    preconfigured command. This is useful for functions like
    `_get_awg_waveforms`, that need a specific binary read command to kick
    off a stream of binary blocks.

    Parameters
    ----------
    read_bin_func : Callable[[str, bool], bytes]
        SCPI layer binary read method.
    cmd : str
        Unformatted command string.

    Returns
    -------
    Callable[[Optional[int], Optional[str]], bytes]
        Binary read function with preconfigured command that takes the
        optional sequencer index and optional name string as arguments.

    """

    def read_bin(
        self_,
        slot: Optional[int] = None,
        sequencer: Optional[int] = None,
        name: Optional[str] = None,
    ) -> bytes:
        if slot is None:
            slot = ""
        if sequencer is None:
            sequencer = ""
        if name is None:
            new_cmd = cmd.format(slot, sequencer)
        else:
            new_cmd = cmd.format(slot, sequencer, name)
        return read_bin_func(self_, new_cmd, False)

    return read_bin


# ----------------------------------------------------------------------------
def validate_nested_dict_element(key: Any, keys: Any, nested_dict: Any) -> None:
    """
    Whenever traversing through a nested dictionary to set one of its elements,
    make sure the key valid.

    Parameters
    ----------
    key : Union[list[str], str]
        Key to access
    keys : Union[list[str], str]
        Configuration key to access, or hierarchical list thereof
    nested_dict : Any
        Nested dictionary which is being traversed.

    Raises
    ------
    KeyError

    """
    if (
        isinstance(nested_dict, list)
        and (not isinstance(key, int) or key < 0 or key >= len(nested_dict))
    ) or (isinstance(nested_dict, dict) and (not isinstance(key, str) or key not in nested_dict)):
        raise KeyError(f"Invalid path: {keys}, failed at {key}", key)


# --------------------------------------------------------------------------
def set_generic_json_config_val(
    get_func: Callable[[], dict],
    set_func: Callable[[dict], None],
    keys: Any,
    val: Any,
    is_sequencer: bool = False,
) -> None:
    """
    Generic code used by setters and getters of different configurations
    that are provided in a JSON format.

    Parameters
    ----------
    get_func : Callable[[], dict]
        Configuration getter function
    set_func : Callable[[dict], None]
        Configuration setter function
    keys : Union[list[str], str]
        Configuration key to access, or hierarchical list thereof
    val : Any
        Value to set parameter to.
    is_sequencer : bool
        Whether this is called by the sequencer config setter.

    """
    # Normalize keys argument.
    if not isinstance(keys, str) and isinstance(keys, Iterable):
        keys = tuple(keys)
    else:
        keys = [keys]

    # Get configuration.
    cfg = get_func()

    # Walk to the right "directory" in the hierarchy.
    d = cfg
    for key in keys[:-1]:
        validate_nested_dict_element(key, keys, d)
        # Handle sequencer config case.
        if is_sequencer and key in ("acq", "awg"):
            d = d[key][0]
        else:
            d = d[key]

    key = keys[-1]
    validate_nested_dict_element(key, keys, d)

    # The sequencer config needs different checks, or it breaks.
    if is_sequencer:
        json_types = (int, float, str, bool)
    else:
        json_types = (int, float, str, bool, list, dict)

    # Make sure val has the right JSON type; try casting it if not.
    cur_val = d[keys[-1]]
    for typ in json_types:
        if isinstance(cur_val, typ):
            try:
                val = typ(val)
            except (ValueError, TypeError) as e:
                raise TypeError(f"Invalid type: {typ.__name__}: {e}", typ.__name__) from e
            break
    else:
        # Probably a dict or array! Can't set those directly.
        raise KeyError(f"Incomplete path: {keys}")

    # Set the new value.
    if isinstance(d[keys[-1]], bool):
        d[keys[-1]] = val == 1
    else:
        d[keys[-1]] = val
    set_func(cfg)


# --------------------------------------------------------------------------
def get_generic_json_config_val(
    get_func: Callable[[], dict], keys: Any, is_sequencer: bool = False
) -> Any:
    """
    Get value of specific scope acquisition parameter.

    Parameters
    ----------
    get_func : Callable[[], dict]
        Configuration getter function
    keys : Union[list[str], str]
        Configuration key to access, or hierarchical list thereof
    is_sequencer : bool
        Whether this is called by the sequencer config getter.

    Returns
    -------
    Any
        Parameter value.

    """
    # Normalize keys argument.
    if not isinstance(keys, str) and isinstance(keys, Iterable):
        keys = tuple(keys)
    else:
        keys = [keys]

    d = get_func()
    for key in keys:
        validate_nested_dict_element(key, keys, d)
        # Handle sequencer config case.
        if is_sequencer and key in ("acq", "awg"):
            d = d[key][0]
        else:
            d = d[key]
    return d


# --------------------------------------------------------------------------
def parse_sequencer_status(
    full_status_str: str,
) -> tuple[str, str, Union[str, list], Union[str, list], Union[str, list], Union[str, list]]:
    """
    Helper function to parse the output of sequencer status cmd.

    Parameters
    ----------
    full_status_str : str
        Full string from command response.

    Returns
    -------
    status : str
        Status parsed string
    state : str
        State parsed string
    info_flag_list : str | list
        List of info flags
    warn_flag_list : str | list
        List of warning flags
    err_flag_list : str | list
        List of error flags
    log : str | list
        Extra log parsed from the cmd

    """
    full_status_list = re.sub(" |-", "_", full_status_str).split(";")

    # STATUS;STATE;INFO_FLAGS;WARN_FLAGS;ERR_FLAGS;LOG
    status = full_status_list[0]  # They are always present
    state = full_status_list[1]  # They are always present

    info_flag_list = full_status_list[2].split(",")[:-1] if full_status_list[2] else []
    warn_flag_list = full_status_list[3].split(",")[:-1] if full_status_list[3] else []
    err_flag_list = full_status_list[4].split(",")[:-1] if full_status_list[4] else []
    log = full_status_list[5] if full_status_list[5] else []

    return status, state, info_flag_list, warn_flag_list, err_flag_list, log


# --------------------------------------------------------------------------
validate_qcm_sequence = fastjsonschema.compile(QCM_SEQUENCE_JSON_SCHEMA)
validate_qrm_sequence = fastjsonschema.compile(QRM_SEQUENCE_JSON_SCHEMA)
validate_qtm_sequence = fastjsonschema.compile(QTM_SEQUENCE_JSON_SCHEMA)
validate_acq = fastjsonschema.compile(ACQ_JSON_SCHEMA)
_validate_wave_json = fastjsonschema.compile(WAVE_JSON_SCHEMA)


def validate_wave(wave_data: WaveformWeight) -> None:
    # The json validator intentionally does not check the type of "data",
    # because json is too strict.
    _validate_wave_json(wave_data)
    if (ndim := np.ndim(wave_data["data"])) != 1:
        raise TypeError(
            "Expected waveform to be a one-dimensional array, but got type "
            f"'{type(wave_data['data']).__name__}' and dimension {ndim}"
        )
    sample = next(iter(wave_data["data"]))
    if not isinstance(sample, (int, float)):
        raise TypeError(
            f"Expected waveform elements of type 'int | float' but got '{type(sample).__name__}'"
        )
