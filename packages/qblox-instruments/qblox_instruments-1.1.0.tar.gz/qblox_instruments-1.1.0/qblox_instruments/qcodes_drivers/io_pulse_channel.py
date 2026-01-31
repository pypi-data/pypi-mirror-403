# ----------------------------------------------------------------------------
# Description    : IOPulseChannel QCoDeS interface
# Git repository : https://gitlab.com/qblox/packages/software/qblox_instruments.git
# Copyright (C) Qblox BV (2024)
# ----------------------------------------------------------------------------


from typing import Union

from qcodes import Instrument, InstrumentChannel
from qcodes import validators as vals

from qblox_instruments.qcodes_drivers.component import Component
from qblox_instruments.qcodes_drivers.registration_mixin import ParentAttributeRegistrationMixin


class IOPulseChannel(Component, ParentAttributeRegistrationMixin):
    """
    Represents a single IO Pulse channel. It combines all channel specific
    parameters and functions into a single QCoDes InstrumentChannel.
    """

    def __init__(
        self,
        parent: Union[Instrument, InstrumentChannel],
        name: str,
        io_pulse_channel_idx: int,
    ) -> None:
        """
        Creates a IO Pulse channel class and adds all relevant parameters for the
        IO channel.

        Parameters
        ----------
        parent : Union[Instrument, InstrumentChannel]
            The QCoDeS class to which this IO channel belongs.
        name : str
            Name of this IO channel channel
        io_pulse_channel_idx : int
            The index of this IO channel in the parent instrument, representing
            which IO channel is controlled by this class.

        """
        # Initialize instrument channel
        super().__init__(parent, name)

        # Store IO channel index
        self._io_pulse_channel_idx = io_pulse_channel_idx

        # Add required parent attributes for the QCoDeS parameters to function
        self._register_all_required_attrs(self._get_required_parent_attr_names())

        # Add parameters
        # -- Channel map
        # -- TBD

        # IOPulseChannel (QTM-Pulse-only)
        self.add_parameter(
            "output_normalized_amplitude",
            label="Normalized output amplitude of the pulse",
            docstring="""Normalized output amplitude of the pulse. It should
                        range from 0.0 to 1.0 in steps of 1/65535""",
            unit="V",
            vals=vals.Numbers(),
            set_parser=float,
            get_parser=float,
            set_cmd=self._set_output_normalized_amplitude,
            get_cmd=self._get_output_normalized_amplitude,
        )

        self.add_parameter(
            "output_offset",
            label="DC output offset.",
            docstring="DC output offset. It should range from -3.0 to +3.0",
            unit="V",
            vals=vals.Numbers(),
            set_parser=float,
            get_parser=float,
            set_cmd=self._set_io_pulse_output_offset,
            get_cmd=self._get_io_pulse_output_offset,
        )

        self.add_parameter(
            "pulse_width",
            label="Output pulse duration. Configuration must be a dict"
            "containing coarse and fine keywords. Coarse range from 1..128 in unit of ns."
            "Fine range from 1..1000 ps",
            docstring="....",
            unit="ns/ps",
            vals=vals.Dict(),
            set_cmd=self._set_io_pulse_width_config,
            get_cmd=self._get_io_pulse_width_config,
        )

    @property
    def io_pulse_channel_idx(self) -> int:
        """
        Get IO Pulse channel index.

        Returns
        -------
        int
            IO Pulse Channel index

        """
        return self._io_pulse_channel_idx

    def _get_bind_index(self) -> int:
        """
        Return the IOPulseChannel index to bind to parent methods.

        Returns
        -------
        int
            The IOPulseChannel index for this sequencer.

        """
        return self._io_pulse_channel_idx

    @staticmethod
    def _get_required_parent_attr_names() -> list[str]:
        # IOPulseChannel attributes
        return [
            "_set_output_normalized_amplitude",
            "_get_output_normalized_amplitude",
            "_set_io_pulse_output_offset",
            "_get_io_pulse_output_offset",
            "_set_io_pulse_width_config",
            "_get_io_pulse_width_config",
        ]
