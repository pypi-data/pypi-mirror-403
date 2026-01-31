# ----------------------------------------------------------------------------
# Description    : IOChannelQSM QCoDeS interface
# Git repository : https://gitlab.com/qblox/packages/software/qblox_instruments.git
# Copyright (C) Qblox BV (2025)
# ----------------------------------------------------------------------------
"""IOChannelQSM QCoDeS interface."""

import warnings
from functools import partial
from typing import Any, Optional, Union, get_type_hints

from qcodes import Instrument, InstrumentChannel
from qcodes import validators as vals

from qblox_instruments.constants import MAX_SAFE_VOLTAGE, MIN_SAFE_VOLTAGE, QSMIOChannelConfig
from qblox_instruments.native.helpers import MultiplesNumbers
from qblox_instruments.qcodes_drivers.component import Component
from qblox_instruments.qcodes_drivers.registration_mixin import ParentAttributeRegistrationMixin
from qblox_instruments.types import FilterMode


class IOChannelQSM(Component, ParentAttributeRegistrationMixin):
    """
    QSM channel representation for the Source Measurement Unit.

    Combines all channel specific parameters and functions
    into a single QCoDes InstrumentChannel.
    """

    def __init__(
        self,
        parent: Union[Instrument, InstrumentChannel],
        name: str,
        io_channel_idx: int,
    ) -> None:
        """
        Creates an IO channel class and adds all relevant parameters for the channel.

        Parameters
        ----------
        parent : Union[Instrument, InstrumentChannel]
            The QCoDeS class to which this IO channel belongs.
        name : str
            Name of this IO channel
        io_channel_idx : int
            The index of this IO channel in the parent instrument, representing
            which IO channel is controlled by this class.

        """
        # Initialize instrument channel
        super().__init__(parent, name)

        # Store SM channel index
        self._io_channel_idx = io_channel_idx

        # Add required parent attributes for the QCoDeS parameters to function
        self._register_all_required_attrs(self._get_required_parent_attr_names())

        # Add parameters

        self.add_parameter(
            "source_mode",
            label="Output sourcing behavior for the given channel",
            docstring="Sets/gets the output sourcing behavior for a specified channel.",
            unit="",
            vals=vals.Enum("v_source", "i_source", "ground", "open"),
            set_cmd=partial(
                self._set_io_channel_config_val,
                "source_mode",
            ),
            get_cmd=partial(
                self._get_io_channel_config_val,
                ["source_mode"],
            ),
        )

        self.add_parameter(
            "measure_mode",
            label="Measurement precision for the given channel",
            docstring="Sets/gets the measurement precision for a specified channel.",
            unit="",
            vals=vals.Enum("automatic", "coarse", "fine_nanoampere", "fine_picoampere"),
            set_cmd=partial(
                self._set_io_channel_config_val,
                "measure_mode",
            ),
            get_cmd=partial(
                self._get_io_channel_config_val,
                ["measure_mode"],
            ),
        )

        self.add_parameter(
            "slew_rate",
            label="Slew rate for output adjustment for the given channel",
            docstring="Sets/gets the slew rate for output adjustment for the specified channel.",
            unit="V/s",
            vals=vals.Numbers(),
            set_cmd=partial(
                self._set_io_channel_config_val,
                "slew_rate",
            ),
            get_cmd=partial(
                self._get_io_channel_config_val,
                ["slew_rate"],
            ),
        )

        self.add_parameter(
            "integration_time",
            label="Integration time for the given channel",
            docstring="Sets/gets the integration time for the specified channel.",
            unit="s",
            vals=MultiplesNumbers(100e-06, min_value=100e-06, max_value=10),
            set_cmd=partial(
                self._set_io_channel_config_val,
                "integration_time",
            ),
            get_cmd=partial(
                self._get_io_channel_config_val,
                ["integration_time"],
            ),
        )

        self.add_parameter(
            "coarse_voltage",
            label="Coarse voltage for the given channel",
            docstring="Sets/gets the coarse voltage for the specified channel.",
            unit="V",
            vals=vals.Numbers(min_value=MIN_SAFE_VOLTAGE, max_value=MAX_SAFE_VOLTAGE),
            set_cmd=self._set_coarse_voltage,
            get_cmd=partial(
                self._get_io_channel_config_val,
                ["coarse_voltage"],
            ),
        )

        self.add_parameter(
            "fine_voltage",
            label="Fine voltage for the given channel",
            docstring="Sets/gets the fine voltage for the specified channel.",
            unit="V",
            vals=vals.Numbers(0, 0.0025),
            set_cmd=self._set_fine_voltage,
            get_cmd=partial(
                self._get_io_channel_config_val,
                ["fine_voltage"],
            ),
        )

        self.add_parameter(
            "low_pass_filter_cutoff",
            label="Output low-pass filter mode for the given channel",
            docstring="Sets/gets the output low-pass filter mode for a specified channel.",
            unit="Hz",
            vals=vals.Enum(*FilterMode),
            set_cmd=partial(
                self._set_io_channel_config_val,
                "low_pass_filter_cutoff",
            ),
            get_cmd=partial(
                self._get_io_channel_config_val,
                ["low_pass_filter_cutoff"],
            ),
            set_parser=FilterMode,
            get_parser=FilterMode,
        )

        # Set the default safe voltage range
        self._safe_voltage_range: tuple[float, float] = (MIN_SAFE_VOLTAGE, MAX_SAFE_VOLTAGE)

    @property
    def io_channel_idx(self) -> int:
        """
        Get IO channel index.

        Returns
        -------
        int
            IOChannelQSM index

        """
        return self._io_channel_idx

    def _get_bind_index(self) -> int:
        """
        Return the IOChannel index to bind to parent methods.

        Returns
        -------
        int
            The IOChannel index for this sequencer.

        """
        return self._io_channel_idx

    @staticmethod
    def _get_required_parent_attr_names() -> list[str]:
        """
        Return list of parent attribute names that are required for the QCoDeS
        parameters to function, so that they can be registered to this object
        using the _register method.

        Returns
        -------
        list
            List of parent attribute names to register.

        """
        # IOChannelQSM attributes
        attr_names = [
            "_set_io_channel_config",
            "_get_io_channel_config",
            "_set_io_channel_config_val",
            "_get_io_channel_config_val",
            "_measure_current",
            "_measure_voltage",
            "_set_io_output_config",
            "_set_voltage_instant",
            "_set_voltage_wait",
            "reset_io_channel_output",
        ]
        return attr_names

    def measure_current(self) -> float:
        """
        Returns the current measured for a specified channel.

        Returns
        -------
        float
            The measured current for the specified channel in amperes.

        """
        return self._measure_current()

    def measure_voltage(self) -> float:
        """
        Returns the voltage measured for a specified channel.

        Returns
        -------
        float
            The measured voltage for the specified channel in volts.

        Raises
        ------
        ValueError
            If the io channel number is not 0 or 4.

        """
        if self._io_channel_idx not in (0, 4):
            raise ValueError(
                f"measure_voltage is only implemented for io channels 0 and 4 on module "
                f"'{self.parent.name}'"
            )

        return self._measure_voltage()

    def _validate_voltage(self, voltage: float, *, source_mode: Optional[str] = None) -> None:
        """
        Ensure that the given voltage falls within safety limits.

        Parameters
        ----------
        voltage : float
            The voltage to test against the safety limits.
        source_mode : str
            The source mode being set together with the given voltage.
            This is used when an entire configuration is being passed to the IO channel,
            and thus the current QCoDeS parameter does not reflect the new state.

        Raises
        ------
        ValueError
            If the given voltage is out of the safe voltage range.

        """
        # We use the cache because source_mode() causes "Invalid path" here.
        current_source_mode = source_mode or self.source_mode.cache()
        if current_source_mode not in (None, "v_source"):
            warnings.warn(
                'Voltages cannot be set unless `source_mode` is set to "v_source"',
                stacklevel=2,
            )

        min_v, max_v = self._safe_voltage_range
        if not min_v <= voltage <= max_v:
            raise ValueError(
                f"A voltage of {voltage:+} V cannot be set because it falls outside the safety "
                f"range of {min_v:+} V to {max_v:+} V"
            )

    def _set_coarse_voltage(self, voltage: float) -> None:
        """
        Set the coarse voltage for the current channel.

        Parameters
        ----------
        voltage : float
            The coarse voltage to set.

        """
        self._validate_voltage(voltage)
        self._set_io_channel_config_val("coarse_voltage", voltage)

    def _set_fine_voltage(self, voltage: float) -> None:
        """
        Set the fine voltage for the current channel.

        Parameters
        ----------
        voltage : float
            The fine voltage to set.

        """
        self._validate_voltage(voltage)
        self._set_io_channel_config_val("fine_voltage", voltage)

    def set_safe_voltage_range(self, min_voltage: float, max_voltage: float) -> None:
        """
        Set the safe voltage range for the current channel.

        Parameters
        ----------
        min_voltage : float
            The desired minimum voltage in volts.
        max_voltage : float
            The desired maximum voltage in volts.

        """
        if min_voltage > max_voltage:
            raise ValueError("The minimum voltage must be lower than the maximum voltage")
        if min_voltage < MIN_SAFE_VOLTAGE or max_voltage > MAX_SAFE_VOLTAGE:
            raise ValueError(
                f"The safe voltage range limits must be between "
                f"{MIN_SAFE_VOLTAGE:+} V and {MAX_SAFE_VOLTAGE:+} V"
            )
        self._safe_voltage_range = (min_voltage, max_voltage)

    def set_voltage_wait(self, voltage: float) -> None:
        """
        Sets the voltage for a specified channel and blocks execution
        until the voltage stabilizes at the requested value.

        Parameters
        ----------
        voltage : float
            The voltage to set.

        """
        self._validate_voltage(voltage)
        self._set_voltage_wait(voltage)

    def set_voltage_instant(self, voltage: float) -> None:
        """
        Sets the voltage for a specified channel immediately,
        bypassing ramping constraints.

        Returns
        -------
        None

        """
        self._validate_voltage(voltage)
        self._set_voltage_instant(voltage)

    def set_io_channel_config(self, config: dict[str, Any]) -> None:
        """
        Set configuration parameters for the given I/O channel.

        Parameters
        ----------
        config : dict[str, Any]
            A JSON object with instrument-specific content.

        """
        self._set_io_channel_config(config)

    def get_io_channel_config(self) -> dict[str, Any]:
        """
        Get configuration parameters for the given I/O channel.

        Returns
        -------
        dict[str, Any]
            A JSON object with instrument-specific content.

        """
        return self._get_io_channel_config()

    def _validate_config(self, config: QSMIOChannelConfig) -> None:
        """
        Validate the configuration dictionary for the IO channel.

        Parameters
        ----------
        config : QSMIOChannelConfig
            Configuration dictionary to validate.

        Raises
        ------
        RuntimeError
            If the configuration contains invalid parameters or values.

        """
        # Fetch the source_mode separately to use in voltage validation.
        config_source_mode = config.get("source_mode")

        for param_name, param_value in config.items():
            # 'Channel' is part of the config but needs not to be validated
            if param_name == "channel":
                continue

            try:
                vals = self.parameters[param_name]
            except KeyError:
                raise RuntimeError(
                    f"Configuration validation failed: Parameter '{param_name}' "
                    f"is not a valid QSM IO channel parameter. "
                    f"Expected one of: {list(get_type_hints(QSMIOChannelConfig).keys())}. "
                    f"Please verify your configuration dictionary contains "
                    f"only supported parameters."
                )
            vals.validate(param_value)

            # Enforce voltage check if the config contains a voltage parameter
            if "voltage" in param_name and param_value:  # not 0.0 or None
                self._validate_voltage(param_value, source_mode=config_source_mode)
