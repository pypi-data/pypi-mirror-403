# ----------------------------------------------------------------------------
# Description    : IOChannelQSM QCoDeS interface
# Description    : Project wide constants
# Git repository : https://gitlab.com/qblox/packages/software/qblox_instruments.git
# Copyright (C) Qblox BV (2025)
# ----------------------------------------------------------------------------

from dataclasses import dataclass
from typing import Final, Literal, TypedDict

from qblox_instruments import InstrumentType

MIN_SAFE_VOLTAGE: Final[float] = -10.0
MAX_SAFE_VOLTAGE: Final[float] = +10.0


class QSMIOChannelConfig(TypedDict):
    """
    A type for a configuration dictionary of a IO channel of a QSM module.
    """

    channel: int
    coarse_voltage: float
    fine_voltage: float
    integration_time: float
    low_pass_filter_cutoff: int
    measure_mode: Literal[
        "automatic",
        "coarse",
        "fine_nanoampere",
        "fine_picoampere",
    ]
    slew_rate: int
    source_mode: Literal[
        "v_source",
        "i_source",
        "ground",
        "open",
    ]


@dataclass(frozen=True)
class ModuleConstants:
    """Constants for a specific module type."""

    NUM_MARKERS: int
    NUM_OUT_CHANNELS: int
    NUM_IN_CHANNELS: int
    NUM_SEQ: int
    NUM_DIO: int
    NUM_SM: int


MODULE_CONSTANTS: Final[dict[InstrumentType, ModuleConstants]] = {
    InstrumentType.QCM: ModuleConstants(
        NUM_MARKERS=4,
        NUM_OUT_CHANNELS=4,
        NUM_IN_CHANNELS=0,
        NUM_SEQ=6,
        NUM_DIO=0,
        NUM_SM=0,
    ),
    InstrumentType.QRM: ModuleConstants(
        NUM_MARKERS=4,
        NUM_OUT_CHANNELS=2,
        NUM_IN_CHANNELS=2,
        NUM_SEQ=6,
        NUM_DIO=0,
        NUM_SM=0,
    ),
    InstrumentType.QRC: ModuleConstants(
        NUM_MARKERS=1,
        NUM_OUT_CHANNELS=12,
        NUM_IN_CHANNELS=4,
        NUM_SEQ=12,
        NUM_DIO=0,
        NUM_SM=0,
    ),
    InstrumentType.QTM: ModuleConstants(
        NUM_MARKERS=4,
        NUM_OUT_CHANNELS=4,
        NUM_IN_CHANNELS=0,
        NUM_SEQ=8,
        NUM_DIO=8,
        NUM_SM=0,
    ),
    InstrumentType.QSM: ModuleConstants(
        NUM_MARKERS=0,
        NUM_OUT_CHANNELS=0,
        NUM_IN_CHANNELS=0,
        NUM_SEQ=0,
        NUM_DIO=0,
        NUM_SM=8,
    ),
    InstrumentType.QDM: ModuleConstants(
        NUM_MARKERS=4,  # Same as QCM (default)
        NUM_OUT_CHANNELS=4,
        NUM_IN_CHANNELS=0,
        NUM_SEQ=6,
        NUM_DIO=0,
        NUM_SM=0,
    ),
    InstrumentType.LINQ: ModuleConstants(
        NUM_MARKERS=4,  # Same as QCM (default)
        NUM_OUT_CHANNELS=4,
        NUM_IN_CHANNELS=0,
        NUM_SEQ=6,
        NUM_DIO=0,
        NUM_SM=0,
    ),
}
