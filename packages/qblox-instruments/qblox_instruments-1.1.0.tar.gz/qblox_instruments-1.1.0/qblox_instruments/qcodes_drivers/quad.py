# ----------------------------------------------------------------------------
# Description    : Quad QCoDeS interface
# Git repository : https://gitlab.com/qblox/packages/software/qblox_instruments.git
# Copyright (C) Qblox BV (2020)
# ----------------------------------------------------------------------------

from functools import partial
from typing import Final, Union

from qcodes import Instrument, InstrumentChannel
from qcodes import validators as vals

from qblox_instruments.qcodes_drivers.component import Component
from qblox_instruments.qcodes_drivers.registration_mixin import ParentAttributeRegistrationMixin


class Quad(Component, ParentAttributeRegistrationMixin):
    """
    Represents a single quad. It combines all quad specific
    parameters and functions into a single QCoDes InstrumentChannel.
    """

    DISPLAY_TO_INTERNAL_CHANNEL_COMBINE_MAP: Final[dict[bool, str]] = {
        True: "fan-out",
        False: "independent",
    }

    def __init__(
        self,
        parent: Union[Instrument, InstrumentChannel],
        name: str,
        quad_idx: int,
    ) -> None:
        """
        Creates a quad class and adds all relevant parameters for the
        quad.

        Parameters
        ----------
        parent : Union[Instrument, InstrumentChannel]
            The QCoDeS class to which this quad belongs.
        name : str
            Name of this quad channel
        quad_idx : int
            The index of this quad in the parent instrument, representing
            which quad is controlled by this class.

        """
        # Initialize instrument channel
        super().__init__(parent, name)

        # Store quad index
        self._quad_idx = quad_idx

        # Add required parent attributes for the QCoDeS parameters to function
        self._register_all_required_attrs(self._get_required_parent_attr_names())

        # Add parameters
        # -- Channel map
        # -- TBD

        # Quad parameters (QTM-only)
        self.add_parameter(
            "timetag_oversampling",
            label="Timetag oversampling setting of all channels in the given quad",
            docstring="Sets/gets the timetag oversampling setting of all "
            "channels in the given quad ('disabled' = no oversampling, '2x' = "
            "events are sampled by the converter twice with a typical "
            "single-shot RMS of 15 ps, '4x' = events are sampled by the "
            "converter four times with a typical single-shot RMS of 10 ps)",
            unit="",
            vals=vals.Enum("disabled", "x2", "x4"),
            set_parser=str,
            get_parser=str,
            set_cmd=partial(
                self._set_quad_config_val,
                ["timetag_oversampling"],
            ),
            get_cmd=partial(
                self._get_quad_config_val,
                ["timetag_oversampling"],
            ),
        )

        self.add_parameter(
            "input_fan_out",
            label="Input fan-out status of both pairs in this channel",
            docstring="Sets/gets the input fan-out status of both pairs in this channel. "
            "If True, the input of the auxiliary channel is internally wired to the main "
            "I/O, otherwise the channels in each channel pair are fully independent.",
            unit="",
            vals=vals.Bool(),
            set_parser=bool,
            get_parser=bool,
            set_cmd=self._set_channel_combine,
            get_cmd=self._get_channel_combine,
        )

    @property
    def quad_idx(self) -> int:
        """
        Get quad index.

        Returns
        -------
        int
            Quad index

        """
        return self._quad_idx

    def _get_bind_index(self) -> int:
        """
        Return the quad index to bind to parent methods.

        Returns
        -------
        int
            The quad index for this sequencer.

        """
        return self._quad_idx

    @staticmethod
    def _get_required_parent_attr_names() -> list[str]:
        # IOChannelQTM attributes
        return [
            "_set_quad_config",
            "_get_quad_config",
            "_set_quad_config_val",
            "_get_quad_config_val",
        ]

    def _set_channel_combine(self, val: bool) -> None:
        """
        Custom setter for the channel_combine parameter of the object.
        Acts as a wrapper.
        Uses the DISPLAY_TO_INTERNAL_CHANNEL_COMBINE_MAP to match the available
        options of the user to the internally used equivalent.

        Parameters
        ----------
        val: str
            key of DISPLAY_TO_INTERNAL_CHANNEL_COMBINE_MAP

        """
        internal_val = self.DISPLAY_TO_INTERNAL_CHANNEL_COMBINE_MAP[val]
        self._set_quad_config_val(["channel_combine"], internal_val)

    def _get_channel_combine(self) -> bool:
        """
        Custom getter for the channel_combine parameter of the obnect.
        Acts as a wrapper.
        Uses the INTERNAL_TO_DISPLAY_MODE_MAP to match the
        internally used termsto the ones the user is familiar with.

        Returns
        -------
        mode: str

        """
        INTERNAL_TO_DISPLAY_MODE_MAP: Final[dict[str, bool]] = {
            v: k for k, v in self.DISPLAY_TO_INTERNAL_CHANNEL_COMBINE_MAP.items()
        }
        internal_val = self._get_quad_config_val(["channel_combine"])
        return INTERNAL_TO_DISPLAY_MODE_MAP[internal_val]
