# ----------------------------------------------------------------------------
# Description    : QCM/QRM QCoDeS interface
# Git repository : https://gitlab.com/qblox/packages/software/qblox_instruments.git
# Copyright (C) Qblox BV (2020)
# ----------------------------------------------------------------------------


# -- include -----------------------------------------------------------------

import math
import warnings
from collections.abc import Iterable, Sequence
from functools import partial
from typing import Any, Callable, Optional, Union, overload

from qcodes import Instrument, InstrumentChannel, Parameter
from qcodes import validators as vals

from qblox_instruments import InstrumentType
from qblox_instruments.constants import MODULE_CONSTANTS, ModuleConstants
from qblox_instruments.native.helpers import MultiplesNumbers
from qblox_instruments.qcodes_drivers.io_channel_qsm import IOChannelQSM
from qblox_instruments.qcodes_drivers.io_channel_qtm import IOChannelQTM
from qblox_instruments.qcodes_drivers.io_pulse_channel import IOPulseChannel
from qblox_instruments.qcodes_drivers.quad import Quad
from qblox_instruments.qcodes_drivers.registration_mixin import ParentAttributeRegistrationMixin
from qblox_instruments.qcodes_drivers.sequencer import Sequencer
from qblox_instruments.types import FrequencyParameter


# -- class -------------------------------------------------------------------
class Module(InstrumentChannel, ParentAttributeRegistrationMixin):
    """
    Represents a QCM/QRM/QTM/QSM module. It combines all module specific
    parameters and functions into a single QCoDes InstrumentChannel.
    """

    # ------------------------------------------------------------------------
    def __init__(
        self,
        parent: Instrument,
        name: str,
        slot_idx: int,
    ) -> None:
        """
        Creates a QCM/QRM/QTM/QSM module class and adds all relevant parameters for
        the module.

        Parameters
        ----------
        parent : Instrument
            The QCoDeS class to which this module belongs.
        name : str
            Name of this module channel
        slot_idx : int
            The index of this module in the parent instrument, representing
            which module is controlled by this class.

        """
        # Initialize instrument channel
        super().__init__(parent, name)

        # Store sequencer index
        self._slot_idx = slot_idx

        # Register common attributes required for all modules (even empty slots)
        self._register("_get_modules_present")
        self._register("_get_modules_connected")

        # Scope acquisition attributes
        # Note that although these methods are not used in QCM/... modules,
        # they are still present on the cluster level. They are also marked as
        # internal, so this should not be a problem.
        for operation in ["set", "get"]:
            self._register(f"_{operation}_acq_scope_config")
            self._register(f"_{operation}_acq_scope_config_val")

        # Add required parent attributes for the QCoDeS parameters to function
        try:
            self.parent._present_at_init(self.slot_idx)

        except KeyError:
            pass
        else:
            # Get module-specific constants
            module_constants = self._get_module_constants()
            NUM_MARKERS = module_constants.NUM_MARKERS
            NUM_OUT_CHANNELS = module_constants.NUM_OUT_CHANNELS
            NUM_IN_CHANNELS = module_constants.NUM_IN_CHANNELS
            NUM_SEQ = module_constants.NUM_SEQ
            NUM_DIO = module_constants.NUM_DIO
            NUM_SM = module_constants.NUM_SM

            # Register attributes based on module type
            if self.is_rf_type:
                for attr_name in Module._get_required_rf_attr_names():
                    self._register(attr_name)
            if self.is_qtm_type:
                for attr_name in Module._get_required_parent_qtm_attr_names():
                    self._register(attr_name)
            elif self.is_qsm_type:
                for attr_name in Module._get_required_parent_qsm_attr_names():
                    self._register(attr_name)
                self._register("_set_io_channel_config", new_name="set_io_channel_config")
                self._register("_get_io_channel_config", new_name="get_io_channel_config")
                self._register("_set_safe_voltage_range", new_name="set_safe_voltage_range")
            elif self.is_qcm_type or self.is_qrm_type or self.is_qrc_type:
                num_lo = 2 if self.is_rf_type else 0
                for attr_name in Module._get_required_parent_qrx_qcm_attr_names(
                    num_lo=num_lo,
                    num_in_channels=NUM_IN_CHANNELS,
                    num_out_channels=NUM_OUT_CHANNELS,
                    num_markers=NUM_MARKERS,
                ):
                    self._register(attr_name)

                if self.is_qrm_type:
                    for attr_name in Module._get_required_qrm_attr_names():
                        self._register(attr_name)
                elif self.is_qrc_type:
                    for attr_name in (
                        Module._get_required_qrc_attr_names()
                        + Module._get_required_parent_qrc_attr_names()
                    ):
                        self._register(attr_name)
                elif self.is_qcm_type:
                    for attr_name in Module._get_required_qcm_attr_names():
                        self._register(attr_name)

            if self.is_dummy and any([self.is_qrm_type, self.is_qtm_type, self.is_qrc_type]):
                for attr_name in Module._get_required_dummy_attr_names():
                    self._register(attr_name)

            # Add QCM/QRM/QTM/QDM/LINQ/QRC QCoDeS parameters
            if (
                self.is_qrm_type
                or self.is_qcm_type
                or self.is_qtm_type
                or self.is_qrc_type
                or self.is_qsm_type
            ):
                add_qcodes_params(
                    self,
                    num_seq=NUM_SEQ,
                    num_dio=NUM_DIO,
                    num_in_channels=NUM_IN_CHANNELS,
                    num_out_channels=NUM_OUT_CHANNELS,
                    num_markers=NUM_MARKERS,
                    num_sm=NUM_SM,
                )

        # Add module QCoDeS parameters
        self.add_parameter(
            "present",
            label="Module present status",
            docstring="Sets/gets module present status for slot {} in the Cluster.",
            unit="",
            vals=vals.Bool(),
            get_parser=bool,
            get_cmd=self._get_modules_present,
        )

        self.add_parameter(
            "connected",
            label="Module connected status",
            docstring="Gets module connected status for slot {} in the Cluster.",
            unit="",
            vals=vals.Bool(),
            get_parser=bool,
            get_cmd=self._get_modules_connected,
        )

    def _get_bind_index(self) -> int:
        """
        Return the module slot index to bind to parent methods.

        Returns
        -------
        int
            The slot index for this sequencer.

        """
        return self._slot_idx

    def _get_module_constants(self) -> ModuleConstants:
        """
        Get module-specific constants based on module type.

        Returns
        -------
        ModuleConstants
            Constants for the module type.

        """
        return MODULE_CONSTANTS[self.module_type]

    def snapshot_base(
        self,
        update: Optional[bool] = False,
        params_to_skip_update: Optional[Sequence[str]] = None,
    ) -> dict[Any, Any]:
        """
        Override the module snapshot method to prevent it from sending unnecessary commands
        to poll its `connected` and `present` statuses if they've already present in the cache
        (likely because the cluster's snapshot was requested).
        If the parameter is not present in the QCoDeS cache, then we bypass the respective
        getter function and instead use the more optimized methods on the parent cluster.

        See :meth:`InstrumentBase.snapshot_base` for the function signature.
        """
        if self.parameters["connected"].cache.get(get_if_invalid=False) is None:
            self.parameters["connected"].cache.set(
                self.slot_idx in self.parent._get_slots_with_module_connected()
            )
        if self.parameters["present"].cache.get(get_if_invalid=False) is None:
            self.parameters["present"].cache.set(
                self.slot_idx in self.parent._get_slots_with_module_present()
            )

        params_to_skip_update = set(params_to_skip_update or []) | {"connected", "present"}
        return super().snapshot_base(update, params_to_skip_update)  # type: ignore

    # ------------------------------------------------------------------------
    def __repr__(self) -> str:
        try:
            if self.is_rf_type and not self.is_qrc_type:
                suffix = "-RF"
            elif self.is_eom_type:
                suffix = "-Pulse"
            else:
                suffix = ""
            return f"<{self.module_type}{suffix}, {self.name}>"
        except KeyError:
            # A KeyError may happen if there is no physical module in this slot.
            return f"<{self.name}>"

    # ------------------------------------------------------------------------
    @property
    def slot_idx(self) -> int:
        """
        Get slot index.

        Returns
        -------
        int
            Slot index

        """
        return self._slot_idx

    # ------------------------------------------------------------------------
    @property
    def module_type(self) -> InstrumentType:
        """
        Get module type (e.g. QRM, QCM).

        Returns
        -------
        InstrumentType
            Module type

        Raises
        ------
        KeyError
            Module is not available.

        """
        return self.parent._module_type(self.slot_idx)

    # ------------------------------------------------------------------------
    @property
    def is_qcm_type(self) -> bool:
        """
        Return if module is of type QCM.

        Returns
        -------
        bool
            True if module is of type QCM.

        Raises
        ------
        KeyError
            Module is not available.

        """
        return self.parent._is_qcm_type(self.slot_idx)

    # ------------------------------------------------------------------------
    @property
    def is_qrm_type(self) -> bool:
        """
        Return if module is of type QRM.

        Returns
        -------
        bool:
            True if module is of type QRM.

        Raises
        ------
        KeyError
            Module is not available.

        """
        return self.parent._is_qrm_type(self.slot_idx)

    # ------------------------------------------------------------------------
    @property
    def is_qtm_type(self) -> bool:
        """
        Return if module is of type QTM.

        Returns
        -------
        bool:
            True if module is of type QTM.

        Raises
        ------
        KeyError
            Module is not available.

        """
        return self.parent._is_qtm_type(self.slot_idx)

    # ------------------------------------------------------------------------
    @property
    def is_qdm_type(self) -> bool:
        """
        Return if module is of type QDM.

        Returns
        -------
        bool:
            True if module is of type QDM.

        Raises
        ------
        KeyError
            Module is not available.

        """
        return self.parent._is_qdm_type(self.slot_idx)

    # ------------------------------------------------------------------------
    @property
    def is_eom_type(self) -> bool:
        """
        Return if module is of type EOM.

        Returns
        -------
        bool:
            True if module is of type EOM.

        Raises
        ------
        KeyError
            Module is not available.

        """
        return self.parent._is_eom_type(self.slot_idx)

    # ------------------------------------------------------------------------
    @property
    def is_linq_type(self) -> bool:
        """
        Return if module is of type LINQ.

        Returns
        -------
        bool:
            True if module is of type LINQ.

        Raises
        ------
        KeyError
            Module is not available.

        """
        return self.parent._is_linq_type(self.slot_idx)

    # ------------------------------------------------------------------------
    @property
    def is_qrc_type(self) -> bool:
        """
        Return if module is of type QRC.

        Returns
        -------
        bool:
            True if module is of type QRC.

        Raises
        ------
        KeyError
            Module is not available.

        """
        return self.parent._is_qrc_type(self.slot_idx)

    # ------------------------------------------------------------------------
    @property
    def is_qsm_type(self) -> bool:
        """
        Return if module is of type QSM.

        Returns
        -------
        bool:
            True if module is of type QSM.

        Raises
        ------
        KeyError
            Module is not available.

        """
        return self.parent._is_qsm_type(self.slot_idx)

    # ------------------------------------------------------------------------
    @property
    def is_rf_type(self) -> bool:
        """
        Return if module is of type QCM-RF or QRM-RF.

        Returns
        -------
        bool:
            True if module is of type QCM-RF or QRM-RF.

        Raises
        ------
        KeyError
            Module is not available.

        """
        return self.parent._is_rf_type(self.slot_idx)

    # ------------------------------------------------------------------------
    @property
    def sequencers(self) -> list:
        """
        Get list of sequencers submodules.

        Returns
        -------
        list
            List of sequencer submodules.

        """
        sequencers_list = [
            submodule for submodule in self.submodules.values() if "sequencer" in str(submodule)
        ]
        return sequencers_list

    # ------------------------------------------------------------------------
    @property
    def io_channels(self) -> list:
        """
        Get list of digital I/O channels.

        Returns
        -------
        list
            List of digital I/O channels.

        """
        io_channels_list = [
            submodule for submodule in self.submodules.values() if "io_channel" in str(submodule)
        ]
        return io_channels_list

    # ------------------------------------------------------------------------
    @property
    def io_pulse_channels(self) -> list:
        """
        Get list of digital I/O Pulse channels.

        Returns
        -------
        list
            List of digital I/O Pulse channels.

        """
        io_pulse_channels_list = [
            submodule
            for submodule in self.submodules.values()
            if "io_pulse_channel" in str(submodule)
        ]
        return io_pulse_channels_list

    # ------------------------------------------------------------------------
    @property
    def quads(self) -> list:
        """
        Get list of digital I/O quads.

        Returns
        -------
        list
            List of digital I/O quads.

        """
        quads_list = [
            submodule for submodule in self.submodules.values() if "quad" in str(submodule)
        ]
        return quads_list

    # ------------------------------------------------------------------------
    @property
    def is_dummy(self) -> bool:
        """
        Return True if the parent instrument is configured as dummy.

        Returns
        -------
        bool
            Whether the parent is a dummy instrument.

        """
        return self.parent.is_dummy

    # ------------------------------------------------------------------------
    @staticmethod
    def _get_required_parent_qrx_qcm_attr_names(
        num_lo: int,
        num_in_channels: int,
        num_out_channels: int,
        num_markers: int,
    ) -> list:
        """
        Return list of parent attributes names that are common to QCM/QRM/QRC,
        so that they can be registered to this object using the _register method.

        Returns
        -------
        list
            List of parent attribute names to register.

        """
        attr_names = [
            # Channel map attributes
            "disconnect_outputs",
            "disconnect_inputs",
            "_iter_connections",
        ]

        # LO attributes
        for operation in ["set", "get"]:
            for idx in range(0, num_lo):
                attr_names += [
                    f"_{operation}_lo_freq_{idx}",
                    f"_{operation}_lo_pwr_{idx}",
                    f"_{operation}_lo_enable_{idx}",
                ]
        attr_names.append("_run_mixer_lo_calib")

        # Input attributes
        for operation in ["set", "get"]:
            for idx in range(0, num_in_channels):
                attr_names += [
                    f"_{operation}_in_amp_gain_{idx}",
                    f"_{operation}_in_offset_{idx}",
                ]
            for idx in range(0, num_in_channels // 2):
                attr_names.append(f"_{operation}_in_att_{idx}")

        # Output attributes
        for operation in ["set", "get"]:
            for idx in range(0, num_out_channels):
                attr_names += [
                    f"_{operation}_out_amp_offset_{idx}",
                    f"_{operation}_dac_offset_{idx}",
                ]
            for idx in range(0, num_out_channels // 2):
                attr_names += [
                    f"_{operation}_out_att_{idx}",
                    f"_{operation}_max_out_att_{idx}",
                ]

        # Marker attributes
        for operation in ["set", "get"]:
            for idx in range(0, num_markers):
                attr_names.append(f"_{operation}_mrk_inv_en_{idx}")

        # Pre-distortion config (common to all QCM/QRM/QRC)
        for operation in ["set", "get"]:
            attr_names.append(f"_{operation}_pre_distortion_config_val")
        attr_names.append("_get_output_latency")

        # Sequencer program attributes
        attr_names += [
            "get_assembler_status",
            "get_assembler_log",
        ]

        # Common sequencer attributes (waveforms, sequencer control, etc.)
        attr_names += Sequencer._get_required_parent_attr_names()

        return attr_names

    @staticmethod
    def _get_required_qrm_attr_names() -> list:
        """
        Return list of parent attributes names that are QRM-specific,
        so that they can be registered to this object using the _register method.

        Returns
        -------
        list
            List of parent attribute names to register.

        """
        attr_names = []

        # Acquisition and weight attributes
        attr_names += Sequencer._get_acquisition_parent_attr_names()
        return attr_names

    @staticmethod
    def _get_required_qrc_attr_names() -> list:
        """
        Return list of parent attributes names that are QRC-specific,
        so that they can be registered to this object using the _register method.

        Returns
        -------
        list
            List of parent attribute names to register.

        """
        attr_names = []

        # Acquisition and weight attributes
        attr_names += Sequencer._get_acquisition_parent_attr_names()
        return attr_names

    @staticmethod
    def _get_required_qcm_attr_names() -> list:
        """
        Return list of parent attributes names that are QCM-specific,
        so that they can be registered to this object using the _register method.

        Returns
        -------
        list
            List of parent attribute names to register.

        """
        return []

    @staticmethod
    def _get_required_dummy_attr_names() -> list:
        """
        Return list of parent attributes names that are dummy-specific,
        so that they can be registered to this object using the _register method.

        Returns
        -------
        list
            List of parent attribute names to register.

        """
        return Sequencer._get_dummy_parent_attr_names()

    @staticmethod
    def _get_required_parent_qrc_attr_names() -> list:
        attr_names = [
            "_set_out_ch_comb_en",
            "_set_out_mix_dds",
            "_set_out_out_sel",
            "_get_out_mix_dds",
            "_get_out_out_sel",
            "_set_out_nyquist_filter",
            "_get_out_nyquist_filter",
            "_set_out_mixer_filter_bank",
            "_get_out_mixer_filter_bank",
            "_print_out_gpio_configuration",
            "_set_in_amp_iso_fw",
            "_set_in_ch_splt_en",
            "_set_in_dsa_1",
            "_set_in_dsa_2",
            "_set_in_mix_dds",
            "_set_in_mix_x2",
            "_set_in_nyq_sel",
            "_get_in_amp_iso_fw",
            "_get_in_ch_splt_en",
            "_get_in_dsa_1",
            "_get_in_dsa_2",
            "_get_in_mix_dds",
            "_get_in_mix_x2",
            "_get_in_nyq_sel",
            "_set_in_nyquist_filter",
            "_get_in_nyquist_filter",
            "_print_in_gpio_configuration",
            "_set_out_lo_frequency",
            "_set_out_lo_power",
            "_get_out_lo_power",
            "_init_out_lo",
            "_soft_sync_all_out_lo",
            "_power_down_out_lo_output",
            "_power_down_out_lo",
            "_set_out_att",
            "_get_out_att",
            "_set_in_att",
            "_get_in_att",
            "_set_in_dsa1",
            "_set_in_dsa2",
            "_get_max_out_att",
            "_get_max_in_att",
            "_set_out_freq",
            "_get_out_freq",
            "_set_output_mode",
            "_get_output_mode",
            "_set_input_mode",
            "_get_input_mode",
            "_set_mixer_settings_freq_dac",
            "_set_mixer_settings_coarse_delay_dac",
            "_get_mixer_settings_freq_adc",
            "_reset_duc_phase_dac",
            "_set_nyquist_zone",
            "_set_inv_sync_filter",
            "_set_dac_current",
            "_set_decoder_mode",
            "_set_out_mixer_mode",
            "_set_in_freq",
            "_get_in_freq",
            "_set_out_amp_ctrl",
            "_set_out_bpf_all_ctrl",
            "_set_out_bpf_switch_a_ctrl",
            "_set_out_bpf_switch_b_ctrl",
            "_set_out_hpf_ctrl",
            "_set_out_lpf_ctrl",
            "_set_out_pwr_ctrl",
            "_get_out_amp_ctrl",
            "_get_out_bpf_all_ctrl",
            "_get_out_bpf_switch_a_ctrl",
            "_get_out_bpf_switch_b_ctrl",
            "_get_out_hpf_ctrl",
            "_get_out_lpf_ctrl",
            "_get_out_pwr_ctrl",
        ]

        return attr_names

    @staticmethod
    def _get_required_rf_attr_names() -> list:
        """
        Return list of parent attributes names that are RF-specific,
        so that they can be registered to this object using the _register method.

        Returns
        -------
        list
            List of parent attribute names to register.

        """
        return [
            "toggle_all_lo",
        ]

    # ------------------------------------------------------------------------
    @staticmethod
    def _get_required_parent_qtm_attr_names() -> list:
        """
        Return list of parent attributes names that are required for the
        QCoDeS parameters to function for a QTM, so that they can be registered to this
        object using the _register method.

        Returns
        -------
        list
            List of parent attribute names to register.

        """
        attr_names = [
            # Channel map attributes
            "_iter_connections",
            # Sequencer program attributes
            "get_assembler_status",
            "get_assembler_log",
            "disconnect_inputs",
            "disconnect_outputs",
            "scope_trigger_arm",
            "get_scope_data",
        ]

        # Sequencer attributes
        attr_names += Sequencer._get_required_parent_attr_names()
        attr_names += [
            attr for attr in Sequencer._get_acquisition_parent_attr_names() if "weight" not in attr
        ]
        attr_names += IOChannelQTM._get_required_parent_attr_names()
        attr_names += IOPulseChannel._get_required_parent_attr_names()
        attr_names += Quad._get_required_parent_attr_names()

        return attr_names

    # ------------------------------------------------------------------------
    @staticmethod
    def _get_required_parent_qsm_attr_names() -> list:
        """
        Return list of parent attributes names that are required for the
        QCoDeS parameters to function for a QSM, so that they can be registered to this
        object using the _register method.

        Returns
        -------
        list
            List of parent attribute names to register.

        """
        attr_names = [
            "request_rampdown",
            "clear_rampdown",
            "_measure_current",
        ]

        # Sequencer attributes
        attr_names += IOChannelQSM._get_required_parent_attr_names()

        return attr_names

    def _invalidate_qcodes_parameter_cache(self, sequencer: Optional[int] = None) -> None:
        """
        Marks the cache of all QCoDeS parameters in the module, including in
        any sequencers the module might have, as invalid. Optionally,
        a sequencer can be specified. This will invalidate the cache of that
        sequencer only instead of all parameters.

        Parameters
        ----------
        sequencer : Optional[int]
            Sequencer index of sequencer for which to invalidate the QCoDeS
            parameters.

        """
        invalidate_qcodes_parameter_cache(self, sequencer)

    # ------------------------------------------------------------------------
    def print_readable_snapshot(self, update: bool = False, max_chars: int = 80) -> None:
        """
        Introduce additional spacing in the readable version of the snapshot.
        """
        print()
        super().print_readable_snapshot(update=update, max_chars=max_chars)

    # ------------------------------------------------------------------------
    @overload
    def measure_current(self, io_channels: int) -> float: ...
    @overload
    def measure_current(self, io_channels: Iterable[int]) -> list[float]: ...
    def measure_current(self, io_channels: Union[int, Iterable[int]]) -> Union[float, list[float]]:
        """
        Measures the current of the specified IO channel(s).

        Parameters
        ----------
        io_channels : Union[int, Iterable[int]]
            The index (or indices) of the IO channel(s) to measure.

        Returns
        -------
        Union[float, list[float]]
            The measured current in Amperes.
            Returns a single `float` if `io_channels` is an `int`.
            Returns a `list[float]` if `io_channels` is an iterable.

        """
        return self._measure_current(io_channels)

    # ------------------------------------------------------------------------
    def __getitem__(self, key: str) -> Union[InstrumentChannel, Parameter, Callable[..., Any]]:
        """
        Get sequencer or parameter using string based lookup.

        Parameters
        ----------
        key : str
            Sequencer, parameter or function to retrieve.

        Returns
        -------
        Union[InstrumentChannel, Parameter, Callable[..., Any]]
            Sequencer, parameter or function.

        Raises
        ------
        KeyError
            Sequencer, parameter or function does not exist.

        """
        return get_item(self, key)


# -- functions ---------------------------------------------------------------


def add_qcodes_params(
    parent: Union[Instrument, Module],
    num_seq: int,
    num_dio: int,
    num_in_channels: int,
    num_out_channels: int,
    num_markers: int,
    num_sm: int,
) -> None:
    """
    Add all QCoDeS parameters for a single QCM/QRM module.

    Parameters
    ----------
    parent : Union[Instrument, Module]
        Parent object to which the parameters need to be added.
    num_seq : int
        Number of sequencers to add as submodules.
    num_dio: int
        Number of DIO units. Applies to QTM.
    num_in_channels:
        Number of input channels. Does not apply to QTM since its channels are in/out.
    num_out_channels: int
        Number of output channels. Does not apply to QTM since its channels are in/out.
    num_markers: int
        Number of markers.
    num_sm: int
        Number of QSM channels. Applies to QSM.

    """
    if parent.is_rf_type:
        num_out = num_out_channels // 2
        num_in = num_in_channels // 2
    else:
        num_out = num_out_channels
        num_in = num_in_channels

    # -- LO frequencies (RF-modules only) ------------------------------------
    if parent.is_rf_type:
        if parent.is_qrm_type:
            parent.add_parameter(
                "out0_in0_lo_freq_cal_type_default",
                label="Default automatic mixer calibration setting",
                docstring="Sets/gets the Default automatic mixer"
                "calibration while setting local oscillator"
                "frequency for output and input 0.",
                unit="Hz",
                vals=vals.Enum("off", "lo only", "lo and sidebands"),
                set_cmd=None,
                get_cmd=None,
                initial_value="off",
            )

            out0_in0_lo_freq = Parameter(
                "_out0_in0_lo_freq",
                label="Local oscillator frequency",
                docstring="Sets/gets the local oscillator frequency for output 0 and input 0.",
                unit="Hz",
                vals=vals.Numbers(2e9, 18e9),
                set_parser=int,
                get_parser=int,
                set_cmd=parent._set_lo_freq_1,
                get_cmd=parent._get_lo_freq_1,
            )

            parent.add_parameter(
                "out0_in0_lo_freq",
                parameter_class=FrequencyParameter,
                source=out0_in0_lo_freq,
                calibration_function=partial(_calibrate_lo, parent, 1),
            )

            parent.out0_in0_lo_cal = partial(parent._run_mixer_lo_calib, 1)
        elif parent.is_qcm_type:
            parent.add_parameter(
                "out0_lo_freq_cal_type_default",
                label="Default automatic mixer calibration setting",
                docstring="Sets/gets the Default automatic mixer"
                "calibration while setting local oscillator"
                "frequency for output 0.",
                unit="Hz",
                vals=vals.Enum("off", "lo only", "lo and sidebands"),
                set_cmd=None,
                get_cmd=None,
                initial_value="off",
            )

            out0_lo_freq = Parameter(
                "_out0_lo_freq",
                label="Output 0 local oscillator frequency",
                docstring="Sets/gets the local oscillator frequency for output 0.",
                unit="Hz",
                vals=vals.Numbers(2e9, 18e9),
                set_parser=int,
                get_parser=int,
                set_cmd=parent._set_lo_freq_0,
                get_cmd=parent._get_lo_freq_0,
            )

            parent.add_parameter(
                "out0_lo_freq",
                parameter_class=FrequencyParameter,
                source=out0_lo_freq,
                calibration_function=partial(_calibrate_lo, parent, 0),
            )

            parent.out0_lo_cal = partial(parent._run_mixer_lo_calib, 0)

            parent.add_parameter(
                "out1_lo_freq_cal_type_default",
                label="Default automatic mixer calibration setting",
                docstring="Sets/gets the Default automatic mixer"
                "calibration while setting local oscillator"
                "frequency for output 1.",
                unit="Hz",
                vals=vals.Enum("off", "lo only", "lo and sidebands"),
                set_cmd=None,
                get_cmd=None,
                initial_value="off",
            )

            out1_lo_freq = Parameter(
                "out1_lo_freq",
                label="Output 1 local oscillator frequency",
                docstring="Sets/gets the local oscillator frequency for output 1.",
                unit="Hz",
                vals=vals.Numbers(2e9, 18e9),
                set_parser=int,
                get_parser=int,
                set_cmd=parent._set_lo_freq_1,
                get_cmd=parent._get_lo_freq_1,
            )

            parent.add_parameter(
                "out1_lo_freq",
                parameter_class=FrequencyParameter,
                source=out1_lo_freq,
                calibration_function=partial(_calibrate_lo, parent, 1),
            )

            parent.out1_lo_cal = partial(parent._run_mixer_lo_calib, 1)
        elif parent.is_qrc_type:

            def make_qrc_out_att_setter(ch: int, value: float) -> None:
                max_att = parent._get_max_out_att(ch)
                if value > max_att:
                    raise ValueError(
                        f"Output {ch} attenuation value {value} dB exceeds "
                        f"maximum allowed {max_att} dB"
                    )
                parent._set_out_att(ch, value)

            def make_qrc_in_att_setter(ch: int, value: float) -> None:
                max_att = parent._get_max_in_att(ch)
                if value > max_att:
                    raise ValueError(
                        f"Input {ch} attenuation value {value} dB exceeds "
                        "maximum allowed {max_att} dB"
                    )
                parent._set_in_att(ch, value)

            def qrc_set_lo_freq_settings(
                freq: Union[float, int], channel_id: int, only_out: bool
            ) -> None:
                def set_freq(freq, freq_fun) -> None:
                    if not math.isclose(freq % 10**6, 0, abs_tol=1e-9):
                        raise ValueError(
                            f"Error setting QRC frequency setting for channel '{channel_id}'. "
                            f"Frequency '{freq}' is not multiple of 1e6 Hz."
                        )
                    freq_fun(channel_id, round(freq * 1e-6))

                set_freq(freq, parent._set_out_freq)
                if not only_out:
                    set_freq(freq, parent._set_in_freq)

            def qrc_set_freq_settings(
                settings: Union[float, int], channel_id: int, only_out: bool
            ) -> None:
                warnings.warn(
                    f"module.out{channel_id}_in{channel_id}_freq is deprecated, use "
                    f"module.out{channel_id}_in{channel_id}_lo_freq instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                return qrc_set_lo_freq_settings(settings, channel_id, only_out)

            def qrc_get_lo_freq_settings(channel_id: int, only_out: bool) -> float:
                # NOTE, for the QRC, _get_out_freq and _get_in_freq return a
                # dictionary with format `{"frequency": <MHz value>}`
                out_freq = parent._get_out_freq(channel_id)["frequency"] * 10**6
                if not only_out:
                    in_freq = parent._get_in_freq(channel_id)["frequency"] * 10**6
                    if out_freq != in_freq:
                        raise RuntimeError(
                            f"Error while retrieving QRC frequency. "
                            f"Module '{parent}' channel '{channel_id}' has "
                            f"{out_freq} Hz output frequency and {in_freq} Hz "
                            f"input frequency, which is not allowed."
                        )
                return out_freq

            def qrc_get_freq_settings(channel_id: int, only_out: bool) -> None:
                warnings.warn(
                    f"module.out{channel_id}_in{channel_id}_freq is deprecated, use "
                    f"module.out{channel_id}_in{channel_id}_lo_freq instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                return qrc_get_lo_freq_settings(channel_id, only_out)

            # For QRC the output mixer for which frequency needs to be set is shared by
            # input 0 and output 0, and
            # input 1 and output 1;
            # the rest of the frequency settings only control output frequencies.
            for channel_id in range(0, 2):
                parent.add_parameter(
                    f"out{channel_id}_in{channel_id}_freq",
                    label=f"Output {channel_id} and input{channel_id} frequency",
                    docstring=(f"Sets/gets output {channel_id} and input {channel_id} frequency."),
                    unit="Hz",
                    vals=MultiplesNumbers(
                        100 * 10**6, min_value=500 * 10**6, max_value=10_100 * 10**6
                    ),
                    set_cmd=partial(qrc_set_freq_settings, channel_id=channel_id, only_out=False),
                    get_cmd=partial(qrc_get_freq_settings, channel_id=channel_id, only_out=False),
                )
                parent.add_parameter(
                    f"out{channel_id}_in{channel_id}_lo_freq",
                    label=f"Output {channel_id} and input{channel_id} frequency settings",
                    docstring=(
                        f"Sets/gets output {channel_id} and input {channel_id} frequency settings."
                    ),
                    unit="Hz",
                    vals=MultiplesNumbers(
                        100 * 10**6, min_value=500 * 10**6, max_value=10_100 * 10**6
                    ),
                    set_cmd=partial(
                        qrc_set_lo_freq_settings, channel_id=channel_id, only_out=False
                    ),
                    get_cmd=partial(
                        qrc_get_lo_freq_settings, channel_id=channel_id, only_out=False
                    ),
                )
            for channel_id in range(2, num_out):
                parent.add_parameter(
                    f"out{channel_id}_freq",
                    label=f"Output {channel_id} frequency",
                    docstring=(f"Sets/gets output {channel_id} frequency."),
                    unit="Hz",
                    vals=MultiplesNumbers(
                        100 * 10**6, min_value=500 * 10**6, max_value=10_100 * 10**6
                    ),
                    set_cmd=partial(qrc_set_freq_settings, channel_id=channel_id, only_out=True),
                    get_cmd=partial(qrc_get_freq_settings, channel_id=channel_id, only_out=True),
                )
                parent.add_parameter(
                    f"out{channel_id}_lo_freq",
                    label=f"Output {channel_id} frequency settings",
                    docstring=(f"Sets/gets output {channel_id} frequency settings."),
                    unit="Hz",
                    vals=MultiplesNumbers(
                        100 * 10**6, min_value=500 * 10**6, max_value=10_100 * 10**6
                    ),
                    set_cmd=partial(qrc_set_lo_freq_settings, channel_id=channel_id, only_out=True),
                    get_cmd=partial(qrc_get_lo_freq_settings, channel_id=channel_id, only_out=True),
                )

    # -- LO enables (RF-modules only) ----------------------------------------
    if parent.is_rf_type:
        if parent.is_qrm_type:
            parent.add_parameter(
                "out0_in0_lo_en",
                label="Local oscillator enable",
                docstring="Sets/gets the local oscillator enable for output 0 and input 0.",
                vals=vals.Bool(),
                set_parser=bool,
                get_parser=bool,
                set_cmd=parent._set_lo_enable_1,
                get_cmd=parent._get_lo_enable_1,
            )
        elif parent.is_qcm_type:
            for i, set_lo_enable, get_lo_enable in zip(
                range(num_out),
                [f"_set_lo_enable_{n}" for n in range(num_out)],
                [f"_get_lo_enable_{n}" for n in range(num_out)],
            ):
                parent.add_parameter(
                    f"out{i}_lo_en",
                    label=f"Output {i} local oscillator enable",
                    docstring="Sets/gets the local oscillator enable for output {i}.",
                    vals=vals.Bool(),
                    set_parser=bool,
                    get_parser=bool,
                    set_cmd=getattr(parent, set_lo_enable),
                    get_cmd=getattr(parent, get_lo_enable),
                )

    # -- Attenuation settings (RF-modules only) ------------------------------
    if parent.is_rf_type:
        if parent.is_qrm_type:
            parent.add_parameter(
                "in0_att",
                label="Input 0 attenuation",
                docstring=(
                    "Sets/gets input attenuation in a range of 0dB to 30dB with a resolution "
                    "of 2dB per step."
                ),
                unit="dB",
                vals=vals.Multiples(2, min_value=0, max_value=30),
                set_parser=int,
                get_parser=int,
                set_cmd=parent._set_in_att_0,
                get_cmd=parent._get_in_att_0,
            )

        if parent.is_qcm_type or parent.is_qrm_type:
            for x in range(0, num_out):
                max_att = getattr(parent, f"_get_max_out_att_{x}")()
                parent.add_parameter(
                    f"out{x}_att",
                    label=f"Output {x} attenuation",
                    docstring="Sets/gets output attenuation in a range of 0 dB to "
                    f"{max_att} dB with a resolution of 2dB per step.",
                    unit="dB",
                    vals=vals.Multiples(
                        2,
                        min_value=0,
                        max_value=max_att,
                    ),
                    set_parser=int,
                    get_parser=int,
                    set_cmd=getattr(parent, f"_set_out_att_{x}"),
                    get_cmd=getattr(parent, f"_get_out_att_{x}"),
                )
        elif parent.is_qrc_type:
            for channel in range(0, num_out):
                parent.add_parameter(
                    f"out{channel}_att",
                    label=f"Output {channel} attenuation",
                    docstring=(
                        f"Sets/gets output attenuation in steps of 0.5 dB, "
                        f"minimum is 0 dB, default maximum is "
                        f"{parent._get_max_out_att(channel)} dB. "
                        "Note that the max attenuation is configurable for "
                        "the QRC module."
                    ),
                    unit="dB",
                    vals=MultiplesNumbers(
                        0.5,
                        min_value=0,
                    ),
                    set_parser=float,
                    get_parser=float,
                    set_cmd=partial(make_qrc_out_att_setter, channel),
                    get_cmd=partial(parent._get_out_att, channel),
                )
            for channel in range(0, num_in):
                parent.add_parameter(
                    f"in{channel}_att",
                    label=f"Input {channel} attenuation",
                    docstring=("Sets/gets input attenuation in steps of 0.5 dB from 0 dB."),
                    unit="dB",
                    vals=MultiplesNumbers(
                        0.5,
                        min_value=0,
                    ),
                    set_parser=float,
                    get_parser=float,
                    set_cmd=partial(make_qrc_in_att_setter, channel),
                    get_cmd=partial(parent._get_in_att, channel),
                )

    # -- Input gain (AWG baseband modules only) ------------------------------
    if not parent.is_rf_type:
        for i, set_in_amp_gain, get_in_amp_gain in zip(
            range(num_in),
            [f"_set_in_amp_gain_{n}" for n in range(num_in)],
            [f"_get_in_amp_gain_{n}" for n in range(num_in)],
        ):
            parent.add_parameter(
                f"in{i}_gain",
                label=f"Input {i} gain",
                docstring=(
                    f"Sets/gets input {i} gain in a range of -6dB to 26dB with a resolution "
                    f"of 1dB per step."
                ),
                unit="dB",
                vals=vals.Numbers(-6, 26),
                set_parser=int,
                get_parser=int,
                set_cmd=getattr(parent, set_in_amp_gain),
                get_cmd=getattr(parent, get_in_amp_gain),
            )

    # -- Input offset (AWG modules only) ------------------------------
    if parent.is_qrm_type:
        for i, set_in_offset, get_in_offset in zip(
            range(num_in_channels),
            [f"_set_in_offset_{n}" for n in range(num_in_channels)],
            [f"_get_in_offset_{n}" for n in range(num_in_channels)],
        ):
            if parent.is_rf_type:
                parent.add_parameter(
                    f"in{i // 2}_offset_path{i % 2}",
                    label=f"Input 0 offset for path {i}",
                    docstring="Sets/gets input 0 offset for path 0 in a range of -0.09V to 0.09V",
                    unit="V",
                    vals=vals.Numbers(-0.09, 0.09),
                    set_parser=float,
                    get_parser=float,
                    set_cmd=getattr(parent, set_in_offset),
                    get_cmd=getattr(parent, get_in_offset),
                )
            else:
                parent.add_parameter(
                    f"in{i}_offset",
                    label=f"Input {i} offset",
                    docstring=f"Sets/gets input {i} offset in a range of -0.09V to 0.09V",
                    unit="V",
                    vals=vals.Numbers(-0.09, 0.09),
                    set_parser=float,
                    get_parser=float,
                    set_cmd=getattr(parent, set_in_offset),
                    get_cmd=getattr(parent, get_in_offset),
                )

    # -- Output offsets (All modules) ----------------------------------------
    if parent.is_rf_type and not parent.is_qrc_type:
        for i, set_out_amp_offset, get_out_amp_offset in zip(
            range(num_out_channels),
            [f"_set_out_amp_offset_{n}" for n in range(num_out_channels)],
            [f"_get_out_amp_offset_{n}" for n in range(num_out_channels)],
        ):
            out = i // 2
            path = i % 2
            parent.add_parameter(
                f"out{out}_offset_path{path}",
                label=f"Output {out} offset for path {path}",
                docstring=f"Sets/gets output 0 offset for path {path}.",
                unit="mV",
                vals=vals.Numbers(-84.0, 73.0),
                set_parser=float,
                get_parser=float,
                set_cmd=getattr(parent, set_out_amp_offset),
                get_cmd=getattr(parent, get_out_amp_offset),
            )

    elif parent.is_qrm_type or parent.is_qcm_type:
        for i, set_dac_offset, get_dac_offset in zip(
            range(num_out_channels),
            [f"_set_dac_offset_{n}" for n in range(num_out_channels)],
            [f"_get_dac_offset_{n}" for n in range(num_out_channels)],
        ):
            parent.add_parameter(
                f"out{i}_offset",
                label=f"Output {i} offset",
                docstring=f"Sets/gets output {i} offset",
                unit="V",
                vals=(vals.Numbers(-2.5, 2.5) if parent.is_qcm_type else vals.Numbers(-0.5, 0.5)),
                set_parser=float,
                get_parser=float,
                set_cmd=getattr(parent, set_dac_offset),
                get_cmd=getattr(parent, get_dac_offset),
            )

    # -- Scope acquisition settings (QRM modules only) -----------------------
    if parent.is_qrm_type or parent.is_qrc_type:
        for x in range(0, num_in_channels):
            parent.add_parameter(
                f"scope_acq_trigger_mode_path{x}",
                label=f"Scope acquisition trigger mode for input path {x}",
                docstring=(
                    f"Sets/gets scope acquisition trigger mode for input path {x} "
                    f"('sequencer' = triggered by sequencer, 'level' = triggered by input level)."
                ),
                unit="",
                vals=vals.Bool(),
                val_mapping={"level": True, "sequencer": False},
                set_parser=bool,
                get_parser=bool,
                set_cmd=partial(parent._set_acq_scope_config_val, ["trig", "mode_path", x]),
                get_cmd=partial(parent._get_acq_scope_config_val, ["trig", "mode_path", x]),
            )

            parent.add_parameter(
                f"scope_acq_trigger_level_path{x}",
                label=f"Scope acquisition trigger level for input path {x}",
                docstring=(
                    f"Sets/gets scope acquisition trigger level when using input level "
                    f"trigger mode for input path {x}."
                ),
                unit="",
                vals=vals.Numbers(-1.0, 1.0),
                set_parser=float,
                get_parser=float,
                set_cmd=partial(parent._set_acq_scope_config_val, ["trig", "lvl_path", x]),
                get_cmd=partial(parent._get_acq_scope_config_val, ["trig", "lvl_path", x]),
            )

            parent.add_parameter(
                f"scope_acq_avg_mode_en_path{x}",
                label=f"Scope acquisition averaging mode enable for input path {x}",
                docstring=f"Sets/gets scope acquisition averaging mode enable for input path {x}.",
                unit="",
                vals=vals.Bool(),
                set_parser=bool,
                get_parser=bool,
                set_cmd=partial(parent._set_acq_scope_config_val, ["avg_en_path", x]),
                get_cmd=partial(parent._get_acq_scope_config_val, ["avg_en_path", x]),
            )

        def get_scope_sequencer() -> Union[int, list[int]]:
            sel_path = parent._get_acq_scope_config_val("sel_path")[:num_in_channels]
            if any(sel_path[0] != v for v in sel_path):
                sel_path_i = sel_path[0::2]
                sel_path_q = sel_path[1::2]
                if sel_path_i != sel_path_q:
                    raise ValueError(f"Module '{parent}' has invalid sel_path '{sel_path}'.")
                return sel_path_i
            else:
                return sel_path[0]

        def set_scope_sequencer(seq: Union[int, list[int]]) -> None:
            if isinstance(seq, int):
                for channel in range(num_in_channels):
                    parent._set_acq_scope_config_val(["sel_path", channel], seq)
            else:
                parent._set_acq_scope_config_val(
                    ["sel_path"],
                    [x for x in seq for _ in range(2)],
                )

        num_scope_iq_pairs = 2 if parent.is_qrc_type else 1
        num_readout_seq = 8 if parent.is_qrc_type else num_seq
        parent.add_parameter(
            name="scope_acq_sequencer_select",
            label="Scope acquisition sequencer select",
            docstring="Sets/gets sequencer that specifies which "
            "sequencer triggers the scope acquisition when using "
            "sequencer trigger mode. It is a sequencer id, "
            "or a list of sequencer ids for each scope IQ pair.",
            unit="",
            vals=vals.MultiType(
                vals.Numbers(0, num_readout_seq - 1),
                vals.Sequence(
                    elt_validator=vals.Numbers(0, num_readout_seq - 1), length=num_scope_iq_pairs
                ),
            ),
            get_cmd=get_scope_sequencer,
            set_cmd=set_scope_sequencer,
        )

    # -- Marker settings (All modules, only 2 markers for RF modules) --------
    if parent.is_qcm_type or parent.is_qrm_type:
        num_markers_inv_en = 2 if parent.is_rf_type else num_markers
        for x in range(num_markers_inv_en):
            parent.add_parameter(
                f"marker{x}_inv_en",
                label=f"Output {x} marker invert enable",
                docstring=f"Sets/gets output {x} marker invert enable",
                unit="",
                vals=vals.Bool(),
                set_parser=bool,
                get_parser=bool,
                set_cmd=getattr(parent, f"_set_mrk_inv_en_{x}"),
                get_cmd=getattr(parent, f"_get_mrk_inv_en_{x}"),
            )

    # -- Pre-distortion configuration settings
    # Only QCMs and QRMs have predistortions for now
    if parent.is_qcm_type or parent.is_qrm_type or parent.is_qrc_type:
        _add_rtp_qcodes_params(parent, num_out=num_out, num_markers=num_markers)

    # Add sequencers
    if parent.is_qcm_type or parent.is_qrm_type or parent.is_qtm_type or parent.is_qrc_type:
        for seq_idx in range(0, num_seq):
            seq = Sequencer(parent, f"sequencer{seq_idx}", seq_idx)
            parent.add_submodule(f"sequencer{seq_idx}", seq)

    if num_sm != 0 and num_dio != 0:
        # "io_channel" is used for both QTM io channels and QSM io channels.
        raise ValueError(
            f"Module '{parent}' has both QTM and QSM io channels, which is not allowed."
        )

    # Add sm-related components
    for sm_idx in range(0, num_sm):
        io_channel = IOChannelQSM(parent, f"io_channel{sm_idx}", sm_idx)
        parent.add_submodule(f"io_channel{sm_idx}", io_channel)
    # Add dio-related components
    for dio_idx in range(0, num_dio):
        io_channel = IOChannelQTM(parent, f"io_channel{dio_idx}", dio_idx)
        parent.add_submodule(f"io_channel{dio_idx}", io_channel)
    for quad_idx in range(0, math.ceil(num_dio / 4)):
        quad = Quad(parent, f"quad{quad_idx}", quad_idx)
        parent.add_submodule(f"quad{quad_idx}", quad)

    # Add QTM-Pulse components
    if parent.is_eom_type:
        # For now QTM pulse only have 1 output
        io_pulse_channel = IOPulseChannel(parent, "io_pulse_channel0", 0)
        parent.add_submodule("io_pulse_channel", io_pulse_channel)


# ----------------------------------------------------------------------------
def invalidate_qcodes_parameter_cache(
    parent: Union[Instrument, Module],
    sequencer: Optional[int] = None,
    quad: Optional[int] = None,
    io_channel: Optional[int] = None,
    io_pulse_channel: Optional[int] = None,
) -> None:
    """
    Marks the cache of all QCoDeS parameters in the module as invalid,
    including in any sequencer submodules the module might have. Optionally,
    a sequencer can be specified. This will invalidate the cache of that
    sequencer only instead of all parameters.

    Parameters
    ----------
    parent : Union[Instrument, Module]
        The parent module object for which to invalidate the QCoDeS parameters.
    sequencer : Optional[int]
        The sequencer index for which to invalidate the QCoDeS parameters.
    quad : Optional[int]
        The quad index for which to invalidate the QCoDeS parameters.
    io_channel : Optional[int]
        The IO channel index for which to invalidate the QCoDeS parameters.
    io_pulse_channel : Optional[int]
        The IO pulse channel index for which to invalidate the QCoDeS parameters.

    """
    # Invalidate module parameters
    if sequencer is None:
        for param in parent.parameters.values():
            param.cache.invalidate()
        sequencer_list = parent.sequencers
    else:
        sequencer_list = [parent.sequencers[sequencer]]

    quad_list = parent.quads if quad is None else [parent.quads[quad]]

    io_channel_list = parent.io_channels if io_channel is None else [parent.io_channels[io_channel]]

    if io_pulse_channel is None:
        io_pulse_channel_list = parent.io_pulse_channels
    else:
        io_pulse_channel_list = [parent.io_pulse_channels[io_pulse_channel]]

    # Invalidate sequencer parameters
    for seq in sequencer_list:
        seq._invalidate_qcodes_parameter_cache()
    for q in quad_list:
        q._invalidate_qcodes_parameter_cache()
    for io_ch in io_channel_list:
        io_ch._invalidate_qcodes_parameter_cache()
    for io_pulse_ch in io_pulse_channel_list:
        io_pulse_ch._invalidate_qcodes_parameter_cache()


# ----------------------------------------------------------------------------
def get_item(
    parent: Union[Instrument, Module], key: str
) -> Union[InstrumentChannel, Parameter, Callable[[Any], Any]]:
    """
    Get submodule or parameter using string based lookup.

    Parameters
    ----------
    parent : Union[Instrument, Module]
        Parent module object to search.
    key : str
        submodule, parameter or function to retrieve.

    Returns
    -------
    Union[InstrumentChannel, Parameter, Callable[[Any], Any]]
        Submodule, parameter or function.

    Raises
    ------
    KeyError
        Submodule, parameter or function does not exist.

    """
    # Check for submodule
    try:
        return parent.submodules[key]
    except KeyError:
        try:
            return parent.parameters[key]
        except KeyError:
            return parent.functions[key]


# ----------------------------------------------------------------------------
def _add_rtp_qcodes_params(parent: Union[Instrument, Module], num_out, num_markers) -> None:
    NUM_IIR = 4

    if not parent.is_qcm_type and not parent.is_qrm_type and not parent.is_qrc_type:
        raise TypeError("RTP parameters can only be declared for QRC, QRM and QCM modules.")
    predistortion_val_mapping_filter = {
        "bypassed": "disabled",
        "delay_comp": "enabled",
    }
    predist_mapping_docstring = (
        "If 'bypassed', the filter is disabled.\n"
        "If 'delay_comp', the filter is bypassed, but the output is delayed as if it were applied."
    )

    def add_distortion_parameters(output) -> None:
        parent.add_parameter(
            f"out{output}_fir_coeffs",
            label=f"Coefficients for the FIR filter for output {output}",
            docstring=f"Sets/gets the coefficients for the FIR filter for output {output}",
            unit="",
            vals=vals.Sequence(elt_validator=vals.Numbers(-2, 1.99), length=32),
            set_cmd=partial(
                parent._set_pre_distortion_config_val,
                [f"out{output}", "FIR", "stage0"],
            ),
            get_cmd=partial(
                parent._get_pre_distortion_config_val,
                [f"out{output}", "FIR", "stage0"],
            ),
        )
        for i in range(NUM_IIR):
            parent.add_parameter(
                f"out{output}_exp{i}_time_constant",
                label=f"Time constant of the exponential overshoot filter {i} for output {output}",
                docstring=(
                    f"Sets/gets the time constant of the exponential overshoot filter {i} "
                    f"for output {output}"
                ),
                unit="",
                vals=vals.Numbers(6, float("inf")),
                set_parser=float,
                get_parser=float,
                set_cmd=partial(
                    parent._set_pre_distortion_config_val,
                    [f"out{output}", "IIR", f"stage{i}", "tau"],
                ),
                get_cmd=partial(
                    parent._get_pre_distortion_config_val,
                    [f"out{output}", "IIR", f"stage{i}", "tau"],
                ),
            )
            parent.add_parameter(
                f"out{output}_exp{i}_amplitude",
                label=f"Amplitude of the exponential overshoot filter {i} for output {output}",
                docstring=(
                    f"Sets/gets the amplitude of the exponential overshoot filter {i} "
                    f"for output {output}"
                ),
                unit="",
                vals=vals.Numbers(-1, 1),
                set_parser=float,
                get_parser=float,
                set_cmd=partial(
                    parent._set_pre_distortion_config_val,
                    [f"out{output}", "IIR", f"stage{i}", "amp"],
                ),
                get_cmd=partial(
                    parent._get_pre_distortion_config_val,
                    [f"out{output}", "IIR", f"stage{i}", "amp"],
                ),
            )

    def add_output_parameters(output) -> None:
        parent.add_parameter(
            f"out{output}_latency",
            label=f"Gets the latency in output path {output}",
            docstring=(
                f"Gets the latency in output path {output}.\n"
                "The output path can change depending on the filter configuration of the output."
            ),
            unit="s",
            set_cmd=False,
            get_cmd=partial(
                parent._get_output_latency,
                2 * output if parent.is_rf_type else output,
            ),
        )
        if parent.is_rf_type:
            parent.add_parameter(
                f"out{output}_fir_config",
                label=f"Configuration of FIR filter for output {output}",
                docstring=(
                    f"Sets/gets the configuration of FIR filter for output {output}."
                    f"\n{predist_mapping_docstring}"
                ),
                unit="",
                val_mapping=predistortion_val_mapping_filter,
                set_cmd=partial(
                    lambda output, val: parent.parent._set_pre_distortion_config(
                        parent.slot_idx,
                        {
                            f"out{2 * output}": {"state": {"stage5": val}},
                            f"out{2 * output + 1}": {"state": {"stage5": val}},
                        },
                    ),
                    output,
                ),
                get_cmd=partial(
                    parent._get_pre_distortion_config_val,
                    [f"out{output}", "state", "stage5"],
                ),
            )
            for i in range(NUM_IIR):
                parent.add_parameter(
                    f"out{output}_exp{i}_config",
                    label=f"Configuration of exponential overshoot filter {i} for output {output}",
                    docstring=(
                        f"Sets/gets configuration of exponential overshoot filter {i} "
                        f"for output {output}.\n{predist_mapping_docstring}"
                    ),
                    unit="",
                    val_mapping=predistortion_val_mapping_filter,
                    set_cmd=partial(
                        lambda output,
                        val,
                        stage_idx=i + 1: parent.parent._set_pre_distortion_config(
                            parent.slot_idx,
                            {
                                f"out{2 * output}": {"state": {f"stage{stage_idx}": val}},
                                f"out{2 * output + 1}": {"state": {f"stage{stage_idx}": val}},
                            },
                        ),
                        output,
                    ),
                    get_cmd=partial(
                        parent._get_pre_distortion_config_val,
                        [f"out{2 * output}", "state", f"stage{i + 1}"],
                    ),
                )
        else:
            parent.add_parameter(
                f"out{output}_fir_config",
                label=f"Configuration of FIR filter for output {output}",
                docstring=(
                    f"Sets/gets the configuration of FIR filter for output {output}.\n"
                    f"{predist_mapping_docstring}"
                ),
                unit="",
                val_mapping=predistortion_val_mapping_filter,
                set_cmd=partial(
                    parent._set_pre_distortion_config_val,
                    [f"out{output}", "state", "stage5"],
                ),
                get_cmd=partial(
                    parent._get_pre_distortion_config_val,
                    [f"out{output}", "state", "stage5"],
                ),
            )
            for i in range(NUM_IIR):
                parent.add_parameter(
                    f"out{output}_exp{i}_config",
                    label=f"Configuration of exponential overshoot filter {i} for output {output}",
                    docstring=(
                        f"Sets/gets configuration of exponential overshoot filter {i} "
                        f"for output {output}.\n{predist_mapping_docstring}"
                    ),
                    unit="",
                    val_mapping=predistortion_val_mapping_filter,
                    set_cmd=partial(
                        parent._set_pre_distortion_config_val,
                        [f"out{output}", "state", f"stage{i + 1}"],
                    ),
                    get_cmd=partial(
                        parent._get_pre_distortion_config_val,
                        [f"out{output}", "state", f"stage{i + 1}"],
                    ),
                )

    def add_marker_parameters(x) -> None:
        parent.add_parameter(
            f"marker{x}_fir_config",
            label=f"Delay compensation config for the FIR filter on marker {x}",
            docstring=(
                f"Delay compensation config for the FIR filter on marker {x}. If 'bypassed', "
                f"the marker is not delayed. If 'enabled', the marker is delayed."
            ),
            unit="",
            val_mapping=predistortion_val_mapping_marker,
            set_cmd=partial(
                parent._set_pre_distortion_config_val,
                [f"out{x}", "markers", "state", "stage5"],
            ),
            get_cmd=partial(
                parent._get_pre_distortion_config_val,
                [f"out{x}", "markers", "state", "stage5"],
            ),
        )
        for i in range(NUM_IIR):
            parent.add_parameter(
                f"marker{x}_exp{i}_config",
                label=(
                    f"Delay compensation config for the exponential overshoot filter {i} "
                    f"on marker {x}"
                ),
                docstring=(
                    f"Delay compensation config for the exponential overshoot filter {i} "
                    f"on marker {x}. If 'bypassed', the marker is not delayed. If 'enabled', "
                    f"the marker is delayed."
                ),
                unit="",
                val_mapping=predistortion_val_mapping_marker,
                set_cmd=partial(
                    parent._set_pre_distortion_config_val,
                    [f"out{x}", "markers", "state", f"stage{i + 1}"],
                ),
                get_cmd=partial(
                    parent._get_pre_distortion_config_val,
                    [f"out{x}", "markers", "state", f"stage{i + 1}"],
                ),
            )

    if not parent.is_rf_type:
        if parent.is_qcm_type:
            predist_mapping_docstring += "\nIf 'enabled', the filter is enabled."
            predistortion_val_mapping_filter["enabled"] = "enabled"
            predistortion_val_mapping_filter["delay_comp"] = "comp_delay"

        for output in range(num_out):
            add_output_parameters(output)
            if parent.is_qcm_type:
                add_distortion_parameters(output)
    else:
        for output in range(num_out):
            add_output_parameters(output)

    predistortion_val_mapping_marker = {
        "bypassed": "disabled",
        "delay_comp": "enabled",
    }

    for x in range(num_markers):
        add_marker_parameters(x)


# ----------------------------------------------------------------------------
def _calibrate_lo(
    parent: Union[Instrument, Module],
    output: int,
    cal_type: Optional[str] = None,
) -> None:
    """
    Calibrate the mixer according to the calibration type.

    Parameters
    ----------
    parent : Union[Instrument, Module]
        Parent module object to search.
    output : str
        Output of the module.
    cal_type : Optional[str]
        Automatic mixer calibration to perform after
        setting the frequency. Can be one of
        'off', 'lo only' or 'lo and sidebands'.

    Raises
    ------
    ValueError
        cal_type is not one of
        'off', 'lo only' or 'lo and sidebands'.

    """
    if cal_type is None:
        if parent.is_qrm_type:
            cal_type = parent.out0_in0_lo_freq_cal_type_default()
        else:
            cal_type = parent.parameters[f"out{output}_lo_freq_cal_type_default"]()
    if cal_type == "lo only":
        parent._run_mixer_lo_calib(output)
        return
    elif cal_type == "lo and sidebands":
        if parent.is_qrm_type:
            connected_sequencers = [
                sequencer
                for sequencer in parent.sequencers
                if sequencer.parameters["connect_out0"]() == "IQ"
            ]
        else:
            connected_sequencers = [
                sequencer
                for sequencer in parent.sequencers
                if (
                    sequencer.parameters[f"connect_out{output}"]() == "IQ"
                    and sequencer.parameters[f"connect_out{(output + 1) % 2}"]() == "off"
                )
            ]
        parent._run_mixer_lo_calib(output)
        for sequencer in connected_sequencers:
            sequencer.sideband_cal()
        return
    if cal_type != "off":
        raise ValueError("cal_type must be one of 'off', 'lo only' or 'lo and sidebands'.")
