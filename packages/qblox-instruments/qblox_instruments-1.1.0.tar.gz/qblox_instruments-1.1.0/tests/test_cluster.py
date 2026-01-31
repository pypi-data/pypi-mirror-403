# ----------------------------------------------------------------------------
# Description    : Cluster test script
# Git repository : https://gitlab.com/qblox/packages/software/qblox_instruments.git
# Copyright (C) Qblox BV (2020)
# ----------------------------------------------------------------------------


# -- include -----------------------------------------------------------------

import json
import re
import struct
from functools import partial
from unittest.mock import patch

import fastjsonschema
import numpy as np
import pytest

from qblox_instruments import (
    Cluster,
    ClusterType,
    InstrumentClass,
    InstrumentType,
    Module,
    Sequencer,
    SequencerStates,
    SequencerStatus,
    SequencerStatuses,
    SequencerStatusFlags,
)
from qblox_instruments.native.definitions import SystemStatusFlags
from qblox_instruments.native.helpers import validate_wave
from qblox_instruments.qcodes_drivers.io_channel_qsm import IOChannelQSM, QSMIOChannelConfig
from qblox_instruments.types import DebugLevel, FilterMode
from tests.helpers import instrument, qcm_qrx, qtm, sequencer
from tests.helpers.cluster_dummy_config import DUMMY_CFG, module

# -- fixtures ----------------------------------------------------------------


@pytest.fixture(name="cluster_module", scope="module")
def make_dummy_cluster_module():
    clstr = Cluster("cluster_module", dummy_cfg=DUMMY_CFG)
    yield clstr
    clstr.close()


@pytest.fixture(name="mock_qsm_config")
def make_dummy_qsmconfig():
    mock_qsm_config = QSMIOChannelConfig(
        channel=1,
        coarse_voltage=1.1,
        fine_voltage=2.2e-3,
        integration_time=3,
        low_pass_filter_cutoff=10000,
        measure_mode="automatic",
        slew_rate=500,
        source_mode="v_source",
    )
    yield mock_qsm_config


# -- helpers ----------------------------------------------------------------


def assert_safe_voltage_range_respected(io_channel: IOChannelQSM) -> None:
    with pytest.raises(
        ValueError,
        match=r"A voltage of \+5 V cannot be set because "
        r"it falls outside the safety range of -1.0 V to \+1.0 V",
    ):
        io_channel.coarse_voltage(5)
    with pytest.raises(
        ValueError,
        match=r"A voltage of \+5 V cannot be set because "
        r"it falls outside the safety range of -1.0 V to \+1.0 V",
    ):
        io_channel.set_voltage_wait(5)
    with pytest.raises(
        ValueError,
        match=r"A voltage of \+5 V cannot be set because "
        r"it falls outside the safety range of -1.0 V to \+1.0 V",
    ):
        io_channel.set_voltage_instant(5)


# -- functions ---------------------------------------------------------------


def test_invalid_connection():
    """
    Test invalid connection scenarios.
    """
    # Connecting to non-CMM module.
    with pytest.raises(
        ConnectionError, match=re.escape("Unsupported instrument type detected (QCM)")
    ):
        _ = Cluster("cluster", dummy_cfg={"0": ClusterType.CLUSTER_QCM})


# ----------------------------------------------------------------------------
def test_debug_level():
    cluster = Cluster("cluster", debug=DebugLevel.NO_CHECK, dummy_cfg={1: ClusterType.CLUSTER_QCM})
    cluster._transport._system_error = ["some error"]
    cluster.get_json_description()  # Should not raise error.
    cluster.close()

    cluster = Cluster(
        "cluster", debug=DebugLevel.ERROR_CHECK, dummy_cfg={1: ClusterType.CLUSTER_QCM}
    )
    cluster._transport._system_error = ["some error"]
    with pytest.raises(RuntimeError, match="some error"):
        cluster.get_json_description()
    cluster.close()


# ----------------------------------------------------------------------------
def test_debug_level_int_compatibility():
    cluster = Cluster("cluster", debug=2, dummy_cfg={1: ClusterType.CLUSTER_QCM})
    cluster._transport._system_error = ["some error"]
    cluster.get_json_description()  # Should not raise error.
    cluster.close()

    cluster = Cluster("cluster", debug=1, dummy_cfg={1: ClusterType.CLUSTER_QCM})
    cluster._transport._system_error = ["some error"]
    with pytest.raises(RuntimeError, match="some error"):
        cluster.get_json_description()
    cluster.close()


# ----------------------------------------------------------------------------
def test_type_specification(cluster):
    """
    Test type specification.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    assert cluster.instrument_class == InstrumentClass.CLUSTER
    assert cluster.instrument_type == InstrumentType.MM
    assert cluster.is_dummy is True

    mod = module(cluster, ClusterType.CLUSTER_QCM)
    assert mod.module_type == InstrumentType.QCM
    assert mod.is_qcm_type is True
    assert mod.is_qrm_type is False
    assert mod.is_qtm_type is False
    assert mod.is_qdm_type is False
    assert mod.is_linq_type is False
    assert mod.is_qrc_type is False
    assert mod.is_qsm_type is False
    assert mod.is_rf_type is False
    assert mod.is_dummy is True

    mod = module(cluster, ClusterType.CLUSTER_QRM)
    assert mod.module_type == InstrumentType.QRM
    assert mod.is_qcm_type is False
    assert mod.is_qrm_type is True
    assert mod.is_qtm_type is False
    assert mod.is_qdm_type is False
    assert mod.is_linq_type is False
    assert mod.is_qrc_type is False
    assert mod.is_qsm_type is False
    assert mod.is_rf_type is False

    mod = module(cluster, ClusterType.CLUSTER_QCM_RF)
    assert mod.module_type == InstrumentType.QCM
    assert mod.is_qcm_type is True
    assert mod.is_qrm_type is False
    assert mod.is_qtm_type is False
    assert mod.is_qdm_type is False
    assert mod.is_linq_type is False
    assert mod.is_qrc_type is False
    assert mod.is_qsm_type is False
    assert mod.is_rf_type is True

    mod = module(cluster, ClusterType.CLUSTER_QRM_RF)
    assert mod.module_type == InstrumentType.QRM
    assert mod.is_qcm_type is False
    assert mod.is_qrm_type is True
    assert mod.is_qtm_type is False
    assert mod.is_qdm_type is False
    assert mod.is_linq_type is False
    assert mod.is_qrc_type is False
    assert mod.is_qsm_type is False
    assert mod.is_rf_type is True

    mod = module(cluster, ClusterType.CLUSTER_QDM)
    assert mod.module_type == InstrumentType.QDM
    assert mod.is_qcm_type is False
    assert mod.is_qrm_type is False
    assert mod.is_qtm_type is False
    assert mod.is_qdm_type is True
    assert mod.is_linq_type is False
    assert mod.is_qrc_type is False
    assert mod.is_qsm_type is False
    assert mod.is_rf_type is False

    mod = module(cluster, ClusterType.CLUSTER_QTM)
    assert mod.module_type == InstrumentType.QTM
    assert mod.is_qcm_type is False
    assert mod.is_qrm_type is False
    assert mod.is_qtm_type is True
    assert mod.is_qdm_type is False
    assert mod.is_linq_type is False
    assert mod.is_qrc_type is False
    assert mod.is_qsm_type is False
    assert mod.is_rf_type is False

    mod = module(cluster, ClusterType.CLUSTER_QTM_EOM)
    assert mod.module_type == InstrumentType.QTM
    assert mod.is_qcm_type is False
    assert mod.is_qrm_type is False
    assert mod.is_qtm_type is True
    assert mod.is_qdm_type is False
    assert mod.is_linq_type is False
    assert mod.is_qrc_type is False
    assert mod.is_qsm_type is False
    assert mod.is_rf_type is False
    assert mod.is_eom_type is True

    mod = module(cluster, ClusterType.CLUSTER_LINQ)
    assert mod.module_type == InstrumentType.LINQ
    assert mod.is_qcm_type is False
    assert mod.is_qrm_type is False
    assert mod.is_qtm_type is False
    assert mod.is_qdm_type is False
    assert mod.is_linq_type is True
    assert mod.is_qrc_type is False
    assert mod.is_qsm_type is False
    assert mod.is_rf_type is False

    mod = module(cluster, ClusterType.CLUSTER_QRC)
    assert mod.module_type == InstrumentType.QRC
    assert mod.is_qcm_type is False
    assert mod.is_qrm_type is False
    assert mod.is_qtm_type is False
    assert mod.is_qdm_type is False
    assert mod.is_linq_type is False
    assert mod.is_qrc_type is True
    assert mod.is_qsm_type is False
    assert mod.is_rf_type is True

    mod = module(cluster, ClusterType.CLUSTER_QSM)
    assert mod.module_type == InstrumentType.QSM
    assert mod.is_qcm_type is False
    assert mod.is_qrm_type is False
    assert mod.is_qtm_type is False
    assert mod.is_qdm_type is False
    assert mod.is_linq_type is False
    assert mod.is_qrc_type is False
    assert mod.is_qsm_type is True
    assert mod.is_rf_type is False


# ----------------------------------------------------------------------------
def test_module_access(cluster):
    """
    Tests if modules can be accessed.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    assert len(cluster.modules) == 20
    for mod_idx, mod in enumerate(cluster.modules):
        assert mod.name == f"{cluster.name}_module{mod_idx + 1}"
        assert mod.name == cluster[f"module{mod_idx + 1}"].name


# ----------------------------------------------------------------------------
def test_reset_cache_invalidation(cluster):
    """
    Tests if the call to reset also invalidates the caches on the qcodes
    parameters.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    instrument.test_reset_cache_invalidation(cluster)


# ----------------------------------------------------------------------------
def test_str(cluster):
    """
    Test string representation based on __str__.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    instrument.test_str(cluster, "Cluster", "cluster")


# ----------------------------------------------------------------------------
def test_get_scpi_commands(cluster):
    """
    Tests get SCPI commands function call. If no exceptions occur and the
    returned object matches the json schema the test passes.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    instrument.test_get_scpi_commands(cluster)


# ----------------------------------------------------------------------------
def test_get_idn(cluster):
    """
    Tests get IDN function call. If no exceptions occur and the returned
    object matches the json schema the test passes.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    instrument.test_get_idn(cluster)


# ----------------------------------------------------------------------------
def test_scpi_commands(cluster):
    """
    Tests remaining mandatory SCPI commands. If no exceptions occur the
    test passes.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    instrument.test_scpi_commands(cluster)


# ----------------------------------------------------------------------------
def test_get_temp(cluster):
    """
    Tests temperature readout function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    instrument.test_get_temp(cluster)


# ----------------------------------------------------------------------------
def test_identify(cluster):
    """
    Tests test identify function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    instrument.test_identify(cluster)


# ----------------------------------------------------------------------------
def test_led_brightness(cluster):
    """
    Tests LED brightness setting and getting function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    instrument.test_led_brightness(cluster)


# ----------------------------------------------------------------------------
def test_ref_src(cluster):
    """
    Tests reference source setting and getting function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    instrument.test_ref_src(cluster)


# ----------------------------------------------------------------------------
def test_module_present(cluster):
    """
    Tests module present function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    for slot_idx in range(1, 20):
        module = cluster.submodules[f"module{slot_idx}"]
        assert module.present() == (str(slot_idx) in DUMMY_CFG)


# ----------------------------------------------------------------------------
def test_sequencer_access(cluster):
    """
    Tests if sequencers can be accessed.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    for inst in cluster.modules:
        if inst.present():
            if inst.module_type in (InstrumentType.QRM, InstrumentType.QCM, InstrumentType.QRC):
                qcm_qrx.test_sequencer_access(inst)
            if inst.module_type == InstrumentType.QTM:
                qtm.test_io_channel_access(inst)
        elif not inst.present():
            with pytest.raises(KeyError):
                qcm_qrx.test_sequencer_access(inst)


# ----------------------------------------------------------------------------
def test_lo_freq(cluster, mocker):
    """
    Tests LO frequency setting and getting function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture
    mocker: test_fixture
        mocker from pytest-mocker

    """
    modules = [
        module(cluster, ClusterType.CLUSTER_QCM_RF),
        module(cluster, ClusterType.CLUSTER_QRM_RF),
    ]
    for inst in modules:
        qcm_qrx.test_lo_freq(inst)
        mocker.patch.object(inst, "_run_mixer_lo_calib")
        for seq in inst.sequencers:
            mocker.patch.object(seq, "sideband_cal")
        qcm_qrx.test_lo_mixer_cal(inst)

    modules = [
        module(cluster, ClusterType.CLUSTER_QCM),
        module(cluster, ClusterType.CLUSTER_QRM),
        module(cluster, ClusterType.CLUSTER_QTM),
        module(cluster, ClusterType.CLUSTER_QDM),
    ]
    for inst in modules:
        try:
            qcm_qrx.test_lo_freq(inst)
            raise AssertionError("LO parameters should not be available in baseband modules.")
        except KeyError:
            pass


# ----------------------------------------------------------------------------
def test_lo_enable(cluster):
    """
    Tests LO enable setting and getting function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    modules = [
        module(cluster, ClusterType.CLUSTER_QCM_RF),
        module(cluster, ClusterType.CLUSTER_QRM_RF),
    ]
    for inst in modules:
        qcm_qrx.test_lo_enable(inst)

    modules = [
        module(cluster, ClusterType.CLUSTER_QCM),
        module(cluster, ClusterType.CLUSTER_QRM),
    ]
    for inst in modules:
        with pytest.raises(KeyError):
            qcm_qrx.test_lo_enable(inst)


# ----------------------------------------------------------------------------
def test_toggle_all_lo(cluster):
    """
    Tests enable/disable all LO parameters.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    qcm_rf_modules = cluster.get_connected_modules(
        filter_fn=lambda m: m.is_qcm_type and m.is_rf_type
    ).values()
    qrm_rf_modules = cluster.get_connected_modules(
        filter_fn=lambda m: m.is_qrm_type and m.is_rf_type
    ).values()

    cluster.toggle_all_lo(True)
    for mod in qcm_rf_modules:
        assert mod.out0_lo_en() is True
        assert mod.out1_lo_en() is True
    for mod in qrm_rf_modules:
        assert mod.out0_in0_lo_en() is True

    cluster.toggle_all_lo(False)
    for mod in qcm_rf_modules:
        assert mod.out0_lo_en() is False
        assert mod.out1_lo_en() is False
    for mod in qrm_rf_modules:
        assert mod.out0_in0_lo_en() is False


# ----------------------------------------------------------------------------
def test_toggle_all_lo_unsupported_module(cluster):
    """
    Tests whether enable/disable all LO parameters fails on non QCM-RF or QRM-RF.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    qtm_module = cluster.get_connected_modules(filter_fn=lambda m: m.is_qtm_type)[11]

    with pytest.raises(AttributeError):
        qtm_module.toggle_all_lo(True)


# ----------------------------------------------------------------------------
def test_lo_pwr(cluster):
    """
    Tests LO power setting and getting function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    modules = [
        module(cluster, ClusterType.CLUSTER_QCM_RF),
        module(cluster, ClusterType.CLUSTER_QRM_RF),
    ]
    for inst in modules:
        qcm_qrx.test_lo_pwr(inst)


# ----------------------------------------------------------------------------
def test_in_amp_gain(cluster):
    """
    Tests input amplifier gain setting and getting function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    qcm_qrx.test_in_amp_gain(module(cluster, ClusterType.CLUSTER_QRM))

    modules = [
        module(cluster, ClusterType.CLUSTER_QCM),
        module(cluster, ClusterType.CLUSTER_QCM_RF),
        module(cluster, ClusterType.CLUSTER_QRM_RF),
    ]
    for inst in modules:
        try:
            qcm_qrx.test_in_amp_gain(inst)
            raise AssertionError(
                "Input amplifier parameters should only be available the baseband QRM."
            )
        except KeyError:
            pass


# ----------------------------------------------------------------------------
def test_out_amp_offset(cluster):
    """
    Tests output amplifier offset setting and getting function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    modules = [
        module(cluster, ClusterType.CLUSTER_QCM_RF),
        module(cluster, ClusterType.CLUSTER_QRM_RF),
    ]
    for inst, num_out in zip(modules, [2, 1]):
        qcm_qrx.test_out_amp_offset(inst, num_out)

    modules = [
        module(cluster, ClusterType.CLUSTER_QCM),
        module(cluster, ClusterType.CLUSTER_QRM),
    ]
    for inst, num_out in zip(modules, [4, 2]):
        try:
            qcm_qrx.test_out_amp_offset(inst, num_out)
            raise AssertionError(
                "Output amplifier offset parameters should only be available in RF modules."
            )
        except KeyError:
            pass


# ----------------------------------------------------------------------------
def test_out_dac_offset(cluster):
    """
    Tests output DAC offset setting and getting function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    modules = [
        module(cluster, ClusterType.CLUSTER_QCM),
        module(cluster, ClusterType.CLUSTER_QRM),
    ]
    for inst, num_dac, max_offs in zip(modules, [4, 2], [2.5, 0.5]):
        qcm_qrx.test_out_dac_offset(inst, num_dac, max_offs)

    modules = [
        module(cluster, ClusterType.CLUSTER_QCM_RF),
        module(cluster, ClusterType.CLUSTER_QRM_RF),
    ]
    for inst, num_dac, max_offs in zip(modules, [4, 2], [2.5, 0.5]):
        try:
            qcm_qrx.test_out_dac_offset(inst, num_dac, max_offs)
            raise AssertionError(
                "Output DAC offset parameters should only be available in baseband modules."
            )

        except KeyError:
            pass


# ----------------------------------------------------------------------------
def test_out_fir_coeffs(cluster):
    """
    Tests output FIR coefficients setting and getting function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    inst = module(cluster, ClusterType.CLUSTER_QCM)
    qcm_qrx.test_out_fir_coeffs(inst, 4)

    inst = module(cluster, ClusterType.CLUSTER_QCM_RF)
    try:
        qcm_qrx.test_out_fir_coeffs(inst, 4)
        raise AssertionError(
            "Output FIR coefficients parameters should only be available in baseband modules."
        )

    except KeyError:
        pass


# ----------------------------------------------------------------------------
def test_attenuation(cluster):
    """
    Tests attenuation setting and getting function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    modules = [
        module(cluster, ClusterType.CLUSTER_QCM_RF),
        module(cluster, ClusterType.CLUSTER_QRM_RF),
    ]
    for inst, num_att, max_att in zip(modules, [0, 1], [30, 30]):
        qcm_qrx.test_attenuation(inst, True, num_att, max_att)
    for inst, num_att, max_att in zip(modules, [2, 1], [60, 60]):
        qcm_qrx.test_attenuation(inst, False, num_att, max_att)

    modules = [
        module(cluster, ClusterType.CLUSTER_QCM),
        module(cluster, ClusterType.CLUSTER_QRM),
    ]
    for inst, num_att, max_att in zip(modules, [2, 1], [60, 60]):
        with pytest.raises(KeyError):
            qcm_qrx.test_attenuation(inst, False, num_att, max_att)

    for inst, num_att, max_att in zip([modules[1]], [1], [30]):
        with pytest.raises(KeyError):
            qcm_qrx.test_attenuation(inst, True, num_att, max_att)


# ----------------------------------------------------------------------------
def test_scope_acquisition_control(cluster):
    """
    Tests scope acquisition control function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    modules = [
        module(cluster, ClusterType.CLUSTER_QRM),
        module(cluster, ClusterType.CLUSTER_QRM_RF),
        module(cluster, ClusterType.CLUSTER_QRC),
    ]
    for inst in modules:
        qcm_qrx.test_scope_acquisition_control(inst)

    modules = [
        module(cluster, ClusterType.CLUSTER_QCM),
        module(cluster, ClusterType.CLUSTER_QCM_RF),
    ]
    for inst in modules:
        try:
            qcm_qrx.test_scope_acquisition_control(inst)
            raise AssertionError(
                "Acquisition functionality should only be supported by QRM modules."
            )
        except Exception:
            pass


# ----------------------------------------------------------------------------
def test_channelmap(cluster):
    """
    Tests channel map setting and getting function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    for inst, num_outputs, num_inputs, is_rf in [
        (module(cluster, ClusterType.CLUSTER_QCM), 4, 0, False),
        (module(cluster, ClusterType.CLUSTER_QRM), 2, 2, False),
        (module(cluster, ClusterType.CLUSTER_QCM_RF), 2, 0, True),
        (module(cluster, ClusterType.CLUSTER_QRM_RF), 1, 1, True),
    ]:
        sequencer.test_channelmap(inst, num_outputs, num_inputs, is_rf)


# ----------------------------------------------------------------------------
def test_waveform_weight_handling(cluster):
    """
    Tests waveform and weight handling (e.g. adding, deleting) function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    modules = [
        # module(cluster, ClusterType.CLUSTER_QCM),
        module(cluster, ClusterType.CLUSTER_QRM),
        # module(cluster, ClusterType.CLUSTER_QCM_RF),
        module(cluster, ClusterType.CLUSTER_QRM_RF),
    ]
    for inst in modules:
        for seq in inst.sequencers:
            sequencer.test_waveform_weight_handling(seq, "waveform")

    modules = [
        module(cluster, ClusterType.CLUSTER_QRM),
        module(cluster, ClusterType.CLUSTER_QRM_RF),
    ]
    for inst in modules:
        for seq in inst.sequencers:
            sequencer.test_waveform_weight_handling(seq, "weight")

    modules = [
        module(cluster, ClusterType.CLUSTER_QCM),
        module(cluster, ClusterType.CLUSTER_QCM_RF),
    ]
    for inst in modules:
        for seq in inst.sequencers:
            with pytest.raises(AttributeError):
                sequencer.test_waveform_weight_handling(seq, "weight")

    # Test private methods
    waveform_length = 100
    waveforms = {
        "sawtooth": {
            "data": np.array([(1.0 / waveform_length) * i for i in range(0, waveform_length)]),
            "index": 2,
        }
    }
    sequence = {
        "waveforms": waveforms,
        "weights": waveforms,
        "acquisitions": {},
        "program": "stop",
    }
    mod = module(cluster, ClusterType.CLUSTER_QRM)
    mod.sequencer0.sequence(sequence)
    slot = mod.slot_idx

    for key in ["waveform", "weight"]:
        prefix = "awg" if key == "waveform" else "acq"
        get_wave_weight_data = getattr(cluster, f"_get_{prefix}_{key}_data")
        get_wave_weight_index = getattr(cluster, f"_get_{prefix}_{key}_index")
        get_wave_weight_length = getattr(cluster, f"_get_{prefix}_{key}_length")
        get_wave_weight_name = getattr(cluster, f"_get_{prefix}_{key}_name")
        get_num_wave_weights = getattr(cluster, f"_get_{prefix}_num_{key}s")

        waveform_name = "sawtooth"
        index = get_wave_weight_index(slot, 0, waveform_name)
        length = get_wave_weight_length(slot, 0, waveform_name)
        name = get_wave_weight_name(slot, 0, waveforms[waveform_name]["index"])
        num = get_num_wave_weights(slot, 0)
        data = get_wave_weight_data(slot, 0, waveform_name, 0, waveform_length)

        assert index == waveforms[waveform_name]["index"]
        assert length == waveform_length
        assert name == waveform_name
        assert num == len(waveforms)
        for sample0, sample1 in zip(waveforms[waveform_name]["data"], data):
            assert struct.unpack("f", struct.pack("f", sample0))[0] == sample1


# ----------------------------------------------------------------------------
def test_invalid_waveform_weight():
    valid_waveforms = {
        "one": {
            "data": np.linspace(-1, 1, 10),
            "index": 0,
        },
        "two": {
            "data": [0.1, -0.2, 0.3, 0.5],
            "index": 1,
        },
        "three": {
            "data": [0.1, -0.2, 0.3, 0.5],
        },
        "four": {
            "data": (0.1, -0.2, 0.3, 0.5),
        },
        "five": {
            "data": [-1, 0, 1],
        },
    }
    for wave_data in valid_waveforms.values():
        validate_wave(wave_data)
    invalid_waveforms = {
        "one": {
            "index": 0,
        },
        "two": {},
        "three": {
            "foo": 1,
        },
        "four": {
            "data": "foo",
        },
    }
    for wave_data in invalid_waveforms.values():
        with pytest.raises(
            (TypeError, KeyError, fastjsonschema.exceptions.JsonSchemaValueException)
        ):
            validate_wave(wave_data)


# ----------------------------------------------------------------------------
def test_acquisition_handling(cluster):
    """
    Tests waveform handling (e.g. adding, deleting) function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    modules = [
        module(cluster, ClusterType.CLUSTER_QRM),
        module(cluster, ClusterType.CLUSTER_QRM_RF),
    ]
    for inst in modules:
        for seq in inst.sequencers:
            sequencer.test_acquisition_handling(seq)

    modules = [
        module(cluster, ClusterType.CLUSTER_QCM),
        module(cluster, ClusterType.CLUSTER_QCM_RF),
    ]
    for inst in modules:
        for seq in inst.sequencers:
            with pytest.raises(AttributeError):
                sequencer.test_acquisition_handling(seq)

    # Test private methods
    sample_width = 12
    max_sample_value = 2 ** (sample_width - 1) - 1
    size = 2**14
    scope_acq0 = struct.unpack(
        "i" * size,
        struct.pack("i" * size, *[int(max_sample_value / size) * i for i in range(0, size)]),
    )
    scope_acq1 = struct.unpack(
        "i" * size,
        struct.pack(
            "i" * size,
            *[max_sample_value - int(max_sample_value / size) * i for i in range(0, size)],
        ),
    )

    acquisitions = {"acq1": {"num_bins": 20, "index": 1}}
    sequence = {
        "waveforms": {},
        "weights": {},
        "acquisitions": acquisitions,
        "program": "stop",
    }
    mod = module(cluster, ClusterType.CLUSTER_QRM)
    slot = mod.slot_idx
    cluster.delete_dummy_binned_acquisition_data(slot)
    mod.sequencer0.sequence(sequence)
    mod.sequencer0.start_sequencer()

    acq_name = "acq1"
    index = cluster._get_acq_acquisition_index(slot, 0, acq_name)
    num_bins = cluster._get_acq_acquisition_num_bins(slot, 0, acq_name)
    name = cluster._get_acq_acquisition_name(slot, 0, acquisitions[acq_name]["index"])
    num_acq = cluster._get_acq_num_acquisitions(slot, 0)
    data = cluster._get_acq_acquisition_data(slot, 0, acq_name)

    assert index == acquisitions[acq_name]["index"]
    assert num_bins == 0
    assert name == acq_name
    assert num_acq == len(acquisitions)

    for sample0, sample1 in zip(scope_acq0, data["scope"]["path0"]["data"]):
        assert sample0 / max_sample_value == sample1
    for sample0, sample1 in zip(scope_acq1, data["scope"]["path1"]["data"]):
        assert sample0 / max_sample_value == sample1
    assert len(data["bins"]["integration"]["path0"]) == acquisitions[acq_name]["num_bins"]
    assert len(data["bins"]["integration"]["path1"]) == acquisitions[acq_name]["num_bins"]
    assert len(data["bins"]["threshold"]) == acquisitions[acq_name]["num_bins"]
    assert len(data["bins"]["avg_cnt"]) == acquisitions[acq_name]["num_bins"]


# ----------------------------------------------------------------------------
@pytest.mark.parametrize("as_numpy, exp_type", [(True, np.ndarray), (False, list)])
def test_get_acquisitions_as_numpy(cluster, as_numpy, exp_type):
    acquisitions = {"acq1": {"num_bins": 20, "index": 1}}
    sequence = {
        "waveforms": {},
        "weights": {},
        "acquisitions": acquisitions,
        "program": "stop",
    }
    mod = module(cluster, ClusterType.CLUSTER_QRM)
    slot = mod.slot_idx
    cluster.delete_dummy_binned_acquisition_data(slot)
    mod.sequencer0.sequence(sequence)
    mod.sequencer0.start_sequencer()

    acq = cluster.get_acquisitions(slot, 0, as_numpy=as_numpy)
    acq_data = acq["acq1"]["acquisition"]

    assert isinstance(acq_data["scope"]["path0"]["data"], exp_type)
    assert isinstance(acq_data["scope"]["path1"]["data"], exp_type)
    assert isinstance(acq_data["bins"]["integration"]["path0"], exp_type)
    assert isinstance(acq_data["bins"]["integration"]["path1"], exp_type)
    assert isinstance(acq_data["bins"]["threshold"], exp_type)
    assert isinstance(acq_data["bins"]["avg_cnt"], exp_type)


# ----------------------------------------------------------------------------
def test_program_handling(cluster, tmpdir):
    """
    Tests program handling function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture
    tmpdir
        Temporary directory

    """
    modules = [
        module(cluster, ClusterType.CLUSTER_QCM),
        module(cluster, ClusterType.CLUSTER_QRM),
        module(cluster, ClusterType.CLUSTER_QCM_RF),
        module(cluster, ClusterType.CLUSTER_QRM_RF),
    ]
    for inst in modules:
        for seq in inst.sequencers:
            sequencer.test_program_handling(seq, tmpdir)


# ----------------------------------------------------------------------------
def test_sequencer_control(cluster, mocker):
    """
    Tests program handling function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture
    mocker: test_fixture
        mocker from pytest-mocker

    """
    modules = [
        module(cluster, ClusterType.CLUSTER_QCM_RF),
        module(cluster, ClusterType.CLUSTER_QRM_RF),
    ]
    for inst in modules:
        for seq in inst.sequencers:
            sequencer.test_sequencer_control(seq, inst.is_qrm_type)
            mocker.patch.object(seq, "sideband_cal")
            sequencer.test_sideband_calibration(seq, inst.is_qrm_type)

    modules = [
        module(cluster, ClusterType.CLUSTER_QCM),
        module(cluster, ClusterType.CLUSTER_QRM),
    ]
    for inst in modules:
        for seq in inst.sequencers:
            sequencer.test_sequencer_control(seq, inst.is_qrm_type)


# ----------------------------------------------------------------------------
def test_dummy_binned_acquisition(cluster):
    """
    Tests dummy binned acquisition data mocking.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    qrm_module = module(cluster, ClusterType.CLUSTER_QRM)
    qrm_rf_module = module(cluster, ClusterType.CLUSTER_QRM_RF)

    def _set_dummy_fun_on_cluster(mod0, seq0, mod1, seq1):
        set_dummy_fun0 = partial(
            cluster.set_dummy_binned_acquisition_data,
            sequencer=seq0,
            slot_idx=mod0.slot_idx,
        )
        set_dummy_fun1 = partial(
            cluster.set_dummy_binned_acquisition_data,
            sequencer=seq1,
            slot_idx=mod1.slot_idx,
        )
        return set_dummy_fun0, set_dummy_fun1

    def _set_dummy_fun_on_module(mod0, seq0, mod1, seq1):
        module0 = getattr(cluster, f"module{mod0.slot_idx}")
        set_dummy_fun0 = partial(module0.set_dummy_binned_acquisition_data, sequencer=seq0)
        module1 = getattr(cluster, f"module{mod1.slot_idx}")
        set_dummy_fun1 = partial(module1.set_dummy_binned_acquisition_data, sequencer=seq1)
        return set_dummy_fun0, set_dummy_fun1

    def _set_dummy_fun_on_sequencer(mod0, seq0, mod1, seq1):
        module0 = getattr(cluster, f"module{mod0.slot_idx}")
        sequencer0 = getattr(module0, f"sequencer{seq0}")
        set_dummy_fun0 = sequencer0.set_dummy_binned_acquisition_data
        module1 = getattr(cluster, f"module{mod1.slot_idx}")
        sequencer1 = getattr(module1, f"sequencer{seq1}")
        set_dummy_fun1 = sequencer1.set_dummy_binned_acquisition_data
        return set_dummy_fun0, set_dummy_fun1

    for mod0, seq0, mod1, seq1 in [
        (qrm_module, 2, qrm_rf_module, 3),
        (qrm_module, 3, qrm_rf_module, 2),
    ]:
        # Testing multiple ways of setting the dummy data.
        set_dummy_fun0, set_dummy_fun1 = _set_dummy_fun_on_cluster(mod0, seq0, mod1, seq1)
        sequencer.test_dummy_binned_acquisition(
            seq0, seq1, mod0, mod1, set_dummy_fun0, set_dummy_fun1
        )

        set_dummy_fun0, set_dummy_fun1 = _set_dummy_fun_on_module(mod0, seq0, mod1, seq1)
        sequencer.test_dummy_binned_acquisition(
            seq0, seq1, mod0, mod1, set_dummy_fun0, set_dummy_fun1
        )

        set_dummy_fun0, set_dummy_fun1 = _set_dummy_fun_on_sequencer(mod0, seq0, mod1, seq1)
        sequencer.test_dummy_binned_acquisition(
            seq0, seq1, mod0, mod1, set_dummy_fun0, set_dummy_fun1
        )


# ----------------------------------------------------------------------------
def test_dummy_scope_acquisition(cluster):
    """
    Tests dummy scope acquisition data mocking.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    qrm_module = module(cluster, ClusterType.CLUSTER_QRM)
    qrm_rf_module = module(cluster, ClusterType.CLUSTER_QRM_RF)
    qrc_module = module(cluster, ClusterType.CLUSTER_QRC)

    def _set_dummy_fun_on_cluster(mod, _):
        set_dummy_fun = partial(
            cluster.set_dummy_scope_acquisition_data,
            slot_idx=mod.slot_idx,
            sequencer=None,
        )
        return set_dummy_fun

    def _set_dummy_fun_on_module(mod, _):
        module = getattr(cluster, f"module{mod.slot_idx}")
        set_dummy_fun = partial(module.set_dummy_scope_acquisition_data, sequencer=None)
        return set_dummy_fun

    def _set_dummy_fun_on_sequencer(mod, seq):
        module = getattr(cluster, f"module{mod.slot_idx}")
        sequencer = getattr(module, f"sequencer{seq}")
        set_dummy_fun = sequencer.set_dummy_scope_acquisition_data
        return set_dummy_fun

    for mod, seq, test_dataset_index in [
        (qrm_module, 0, 0),
        (qrm_rf_module, 1, 1),
        (qrc_module, 2, 2),
    ]:
        # Testing multiple ways of setting the dummy data.
        set_dummy_fun = _set_dummy_fun_on_cluster(mod, seq)
        sequencer.test_dummy_scope_acquisition(seq, mod, set_dummy_fun, test_dataset_index)

        set_dummy_fun = _set_dummy_fun_on_module(mod, seq)
        sequencer.test_dummy_scope_acquisition(seq, mod, set_dummy_fun, test_dataset_index)

        set_dummy_fun = _set_dummy_fun_on_sequencer(mod, seq)
        sequencer.test_dummy_scope_acquisition(seq, mod, set_dummy_fun, test_dataset_index)


# ----------------------------------------------------------------------------
def test_feedback(cluster):
    """
    Tests program handling function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    modules = [
        module(cluster, ClusterType.CLUSTER_QCM),
        module(cluster, ClusterType.CLUSTER_QRM),
        module(cluster, ClusterType.CLUSTER_QCM_RF),
        module(cluster, ClusterType.CLUSTER_QRM_RF),
    ]
    for inst in modules:
        for seq in inst.sequencers:
            sequencer.test_feedback_sequencer_param(seq, inst.is_qrm_type)


# ----------------------------------------------------------------------------
def test_get_connected_modules(cluster):
    """
    Tests get_connected_modules method call.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    modules = cluster.get_connected_modules()

    for idx, qxm in modules.items():
        assert qxm.slot_idx == idx
        assert str(qxm.slot_idx) in DUMMY_CFG


# ----------------------------------------------------------------------------
@pytest.mark.parametrize(
    "attr_name, dummy_slot_idx",
    [
        ("is_qcm_type", (1, 3, 4, 8, 20)),
        ("is_qrm_type", (15, 16)),
        ("is_rf_type", (4, 8, 16, 17, 20)),
        ("is_qtm_type", (11, 13)),
        ("is_eom_type", (13,)),
        ("is_qdm_type", (10,)),
        ("is_linq_type", (12,)),
        ("is_qrc_type", (17,)),
        ("is_qsm_type", (18,)),
    ],
)
def test_get_connected_modules_filter(cluster, attr_name, dummy_slot_idx):
    """
    Tests get_connected_modules method call.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture
    attr_name
        Name of Module boolean attribute
    dummy_slot_idx
        Occupied slot indices that for which the given attribute is True.

    """

    def filter_fn(mod):
        return getattr(mod, attr_name)

    modules = cluster.get_connected_modules(filter_fn=filter_fn)
    for idx, qxm in modules.items():
        assert getattr(qxm, attr_name)
        assert qxm.slot_idx == idx
        assert qxm.slot_idx in dummy_slot_idx

    # Assert that modules does not contain anything else
    assert len(modules) == len(dummy_slot_idx)


# ----------------------------------------------------------------------------
def test_get_connected_modules_repr(cluster):
    """
    Tests get_connected_modules string representation.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    modules = cluster.get_connected_modules()
    for idx, type_ in DUMMY_CFG.items():
        module_type = type_.value.removeprefix("Cluster ")
        assert repr(modules[int(idx)]) == f"<{module_type}, cluster_module{idx}>"


# ----------------------------------------------------------------------------
def test_get_sequencer_status(cluster):
    """
    Tests sequencer status interface.

    Parameters
    ----------
    cluster
        cluster: test_fixture

    """
    modules = [
        module(cluster, ClusterType.CLUSTER_QCM),
        module(cluster, ClusterType.CLUSTER_QRM),
        module(cluster, ClusterType.CLUSTER_QCM_RF),
        module(cluster, ClusterType.CLUSTER_QRM_RF),
    ]
    for inst in modules:
        for seq in inst.sequencers:
            sequencer.test_get_sequencer_status(seq)


# ----------------------------------------------------------------------------
def test_dummy_cluster_propagates_start_stop_sequencer(cluster):
    """
    Verify that the dummy cluster properly starts and stops all armed sequencer when
    calling cluster.start_sequencer() or cluster.stop_sequencer().

    Parameters
    ----------
    cluster
        cluster: test_fixture

    """
    mod = module(cluster, ClusterType.CLUSTER_QCM)
    sequence = {
        "waveforms": {},
        "weights": {},
        "acquisitions": {},
        "program": "stop",
    }
    mod.sequencers[0].sequence(sequence)
    mod.sequencers[0].arm_sequencer()

    cluster.start_sequencer()

    assert mod.get_sequencer_status(0) == SequencerStatus(
        SequencerStatuses.OKAY,
        SequencerStates.STOPPED,
        [SequencerStatusFlags.ACQ_BINNING_DONE],
        [],
        [],
        [],
    )

    mod.sequencers[2].sequence(sequence)
    mod.sequencers[2].arm_sequencer()

    cluster.stop_sequencer()

    assert mod.get_sequencer_status(2) == SequencerStatus(
        SequencerStatuses.OKAY,
        SequencerStates.STOPPED,
        [SequencerStatusFlags.ACQ_BINNING_DONE],
        [],
        [],
        [],
    )


# ----------------------------------------------------------------------------
def test_qtm_io_channels(cluster, mocker):
    """
    Tests if QTM IO channels can be accessed.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture
    mocker: test_fixture
        mocker from pytest-mocker

    """
    mod = module(cluster, ClusterType.CLUSTER_QTM)

    assert len(mod.io_channels) == 8
    for idx, io_channel in enumerate(mod.io_channels):
        assert io_channel.name == f"{mod.name}_io_channel{idx}"
        assert io_channel.name == mod[f"io_channel{idx}"].name


# ----------------------------------------------------------------------------
@pytest.mark.parametrize(
    "channel_no, method_name, set_value",
    [
        # Parametrize the test with different channel numbers, setting methods, and their
        # corresponding values
        (0, "analog_threshold", 0.5),
        (1, "binned_acq_time_source", "second"),
        (2, "binned_acq_time_ref", "epoch"),
        (3, "binned_acq_on_invalid_time_delta", "discard"),
        (4, "binned_acq_count_source", "low-latency"),
        (5, "binned_acq_on_invalid_count", "error"),
        (6, "binned_acq_on_invalid_threshold", "record_0"),
        (7, "binned_acq_threshold_source", "thresh1"),
        (0, "forward_trigger_en", True),
        (1, "forward_trigger_mode", "sampled-high"),
        (2, "forward_trigger_address", 12),
        (3, "scope_trigger_mode", "external"),
        (4, "scope_trigger_level", "rising"),
        (5, "scope_mode", "timetags-windowed"),
        (6, "thresholded_acq_trigger_en", True),
        (7, "thresholded_acq_trigger_address_low", 3),
        (0, "thresholded_acq_trigger_address_mid", 6),
        (1, "thresholded_acq_trigger_address_high", 9),
        (2, "thresholded_acq_trigger_address_invalid", 12),
        (3, "truth_table_en", False),
    ],
)
def test_qtm_channel_settings(cluster, mocker, channel_no, method_name, set_value):
    """
    Tests QTM channel settings using parametrization.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture
    mocker: test_fixture
        mocker from pytest-mocker
    channel_no : int
        The specific channel number to test
    method_name : str
        The name of the channel setting method
    set_value : Any
        The value to set for the corresponding channel setting

    """
    mod = module(cluster, ClusterType.CLUSTER_QTM)

    write_binary_mock = mocker.patch.object(
        cluster._transport, "write_binary", wraps=cluster._transport.write_binary
    )

    # Dynamically get the channel object (e.g., mod.io_channel1, mod.io_channel7)
    channel_obj = getattr(mod, f"io_channel{channel_no}")

    # Dynamically get and call the setter method (e.g., channel_obj.source_mode("open"))
    setter_method = getattr(channel_obj, method_name)
    setter_method(set_value)

    default_io_channel_settings = {
        "out_mode": "low",
        "in_threshold_primary": 0.0,
        "binned_acq_time_source": "first",
        "binned_acq_time_ref": "start",
        "binned_acq_on_invalid_time_delta": "error",
        "binned_acq_count_source": "timetags",
        "binned_acq_on_invalid_count": "error",
        "binned_acq_threshold_source": "thresh0",
        "binned_acq_on_invalid_threshold": "error",
        "in_trigger_en": False,
        "in_trigger_mode": "sequencer",
        "in_trigger_address": 1,
        "scope_trigger_mode": "sequencer",
        "scope_trigger_level": "any",
        "scope_mode": "scope",
        "thresholded_acq_trigger_en": False,
        "thresholded_acq_trigger_address_low": 0,
        "thresholded_acq_trigger_address_mid": 0,
        "thresholded_acq_trigger_address_high": 0,
        "thresholded_acq_trigger_address_invalid": 0,
        "thresholded_acq_lut_en": False,
        "thresholded_acq_lut_data": {},
    }
    aliases = {
        "analog_threshold": "in_threshold_primary",
        "forward_trigger_en": "in_trigger_en",
        "forward_trigger_mode": "in_trigger_mode",
        "forward_trigger_address": "in_trigger_address",
        "truth_table_en": "thresholded_acq_lut_en",
    }

    # Construct the full expected call
    command_prefix = f"SLOT11:IO:CHANnel{channel_no}:CONFig"
    expected_payload = default_io_channel_settings
    expected_payload[aliases.get(method_name, method_name)] = set_value
    expected_json_str = json.dumps(expected_payload)
    expected_header = cluster._build_header_string(len(expected_json_str))
    expected_call1 = f"{command_prefix} {expected_header}".encode()
    expected_call2 = expected_json_str.encode()

    write_binary_mock.assert_called_once_with(expected_call1, expected_call2)
    write_binary_mock.reset_mock()

    # Dynamically get and call the getter method
    getter_method = getattr(channel_obj, method_name)
    assert getter_method() == set_value

    write_binary_mock.assert_not_called()


# ----------------------------------------------------------------------------
def test_qtm_pulse_api(cluster):
    """
    Tests if the correct attributes were added to QTM if it's EOM board.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    for inst in cluster.modules:
        if inst.present() and inst.module_type == InstrumentType.QTM:
            # Fake it as QTM Pulse
            inst._is_eom_type = True
            qtm.test_pulse_access(inst)


# ----------------------------------------------------------------------------
def test_qrc_attenuation(cluster, mocker):
    """
    Tests QRC attenuation setting and getting function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture
    mocker: test_fixture
        mocker from pytest-mocker

    """
    mod = module(cluster, ClusterType.CLUSTER_QRC)
    mocker.patch.object(cluster._transport, "write", wraps=cluster._transport.write)

    mod.out0_att(4.0)
    cluster._transport.write.assert_any_call("SLOT17:AFE:OUT:ATT:SET? 0,4.0")
    cluster._transport.write.reset_mock()
    assert mod.out0_att() == 4.0
    cluster._transport.write.assert_any_call("SLOT17:AFE:OUT:ATT:GET? 0")
    cluster._transport.write.reset_mock()

    mod.out1_att(4.5)
    cluster._transport.write.assert_any_call("SLOT17:AFE:OUT:ATT:SET? 1,4.5")
    cluster._transport.write.reset_mock()
    assert mod.out1_att() == 4.5
    cluster._transport.write.assert_any_call("SLOT17:AFE:OUT:ATT:GET? 1")
    cluster._transport.write.reset_mock()

    mod.out2_att(5.0)
    cluster._transport.write.assert_any_call("SLOT17:AFE:OUT:ATT:SET? 2,5.0")
    cluster._transport.write.reset_mock()
    assert mod.out2_att() == 5.0
    cluster._transport.write.assert_any_call("SLOT17:AFE:OUT:ATT:GET? 2")
    cluster._transport.write.reset_mock()

    mod.out3_att(5.5)
    cluster._transport.write.assert_any_call("SLOT17:AFE:OUT:ATT:SET? 3,5.5")
    cluster._transport.write.reset_mock()
    assert mod.out3_att() == 5.5
    cluster._transport.write.assert_any_call("SLOT17:AFE:OUT:ATT:GET? 3")
    cluster._transport.write.reset_mock()

    mod.out4_att(6.0)
    cluster._transport.write.assert_any_call("SLOT17:AFE:OUT:ATT:SET? 4,6.0")
    cluster._transport.write.reset_mock()
    assert mod.out4_att() == 6.0
    cluster._transport.write.assert_any_call("SLOT17:AFE:OUT:ATT:GET? 4")
    cluster._transport.write.reset_mock()

    mod.out5_att(6.5)
    cluster._transport.write.assert_any_call("SLOT17:AFE:OUT:ATT:SET? 5,6.5")
    cluster._transport.write.reset_mock()
    assert mod.out5_att() == 6.5
    cluster._transport.write.assert_any_call("SLOT17:AFE:OUT:ATT:GET? 5")
    cluster._transport.write.reset_mock()


# ----------------------------------------------------------------------------
def test_qrc_lo_frequency(cluster, mocker):
    """
    Tests QRC lo frequency setting and getting function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture
    mocker: test_fixture
        mocker from pytest-mocker

    """
    mod = module(cluster, ClusterType.CLUSTER_QRC)

    mocker.patch.object(cluster._transport, "write", wraps=cluster._transport.write)

    mod.out0_in0_lo_freq(2_000_000_000)
    cluster._transport.write.assert_any_call("SLOT17:AFE:OUT:FREQ:SET? 0,2000")
    cluster._transport.write.assert_any_call("SLOT17:AFE:IN:FREQ:SET? 0,2000")
    cluster._transport.write.reset_mock()
    assert mod.out0_in0_lo_freq() == 2_000_000_000

    mod.out1_in1_lo_freq(3_000_000_000)
    cluster._transport.write.assert_any_call("SLOT17:AFE:OUT:FREQ:SET? 1,3000")
    cluster._transport.write.assert_any_call("SLOT17:AFE:IN:FREQ:SET? 1,3000")
    cluster._transport.write.reset_mock()
    assert mod.out1_in1_lo_freq() == 3_000_000_000

    mod.out2_lo_freq(4_000_000_000)
    cluster._transport.write.assert_any_call("SLOT17:AFE:OUT:FREQ:SET? 2,4000")
    cluster._transport.write.reset_mock()
    assert mod.out2_lo_freq() == 4_000_000_000

    mod.out3_lo_freq(5_000_000_000)
    cluster._transport.write.assert_any_call("SLOT17:AFE:OUT:FREQ:SET? 3,5000")
    cluster._transport.write.reset_mock()
    assert mod.out3_lo_freq() == 5_000_000_000

    mod.out4_lo_freq(6_000_000_000)
    cluster._transport.write.assert_any_call("SLOT17:AFE:OUT:FREQ:SET? 4,6000")
    cluster._transport.write.reset_mock()
    assert mod.out4_lo_freq() == 6_000_000_000

    mod.out5_lo_freq(7_000_000_000)
    cluster._transport.write.assert_any_call("SLOT17:AFE:OUT:FREQ:SET? 5,7000")
    cluster._transport.write.reset_mock()
    assert mod.out5_lo_freq() == 7_000_000_000


# ----------------------------------------------------------------------------
def test_qrc_frequency(cluster, mocker):
    """
    Tests QRC frequency setting and getting function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture
    mocker: test_fixture
        mocker from pytest-mocker

    """
    mod = module(cluster, ClusterType.CLUSTER_QRC)

    mocker.patch.object(cluster._transport, "write", wraps=cluster._transport.write)

    mod.out0_in0_freq(2_000_000_000)
    cluster._transport.write.assert_any_call("SLOT17:AFE:OUT:FREQ:SET? 0,2000")
    cluster._transport.write.assert_any_call("SLOT17:AFE:IN:FREQ:SET? 0,2000")
    cluster._transport.write.reset_mock()
    assert mod.out0_in0_freq() == 2_000_000_000

    mod.out1_in1_freq(3_000_000_000)
    cluster._transport.write.assert_any_call("SLOT17:AFE:OUT:FREQ:SET? 1,3000")
    cluster._transport.write.assert_any_call("SLOT17:AFE:IN:FREQ:SET? 1,3000")
    cluster._transport.write.reset_mock()
    assert mod.out1_in1_freq() == 3_000_000_000

    mod.out2_freq(4_000_000_000)
    cluster._transport.write.assert_any_call("SLOT17:AFE:OUT:FREQ:SET? 2,4000")
    cluster._transport.write.reset_mock()
    assert mod.out2_freq() == 4_000_000_000

    mod.out3_freq(5_000_000_000)
    cluster._transport.write.assert_any_call("SLOT17:AFE:OUT:FREQ:SET? 3,5000")
    cluster._transport.write.reset_mock()
    assert mod.out3_freq() == 5_000_000_000

    mod.out4_freq(6_000_000_000)
    cluster._transport.write.assert_any_call("SLOT17:AFE:OUT:FREQ:SET? 4,6000")
    cluster._transport.write.reset_mock()
    assert mod.out4_freq() == 6_000_000_000

    mod.out5_freq(7_000_000_000)
    cluster._transport.write.assert_any_call("SLOT17:AFE:OUT:FREQ:SET? 5,7000")
    cluster._transport.write.reset_mock()
    assert mod.out5_freq() == 7_000_000_000


# ----------------------------------------------------------------------------
def test_qrc_scope_acq_settings_all_paths(cluster, mocker):
    """
    Tests QRC scope acquisition setting and getting.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture
    mocker: test_fixture
        mocker from pytest-mocker

    """
    mod = module(cluster, ClusterType.CLUSTER_QRC)

    path = 0
    for path in range(4):
        getattr(mod, f"scope_acq_trigger_mode_path{path}")("sequencer")
        assert getattr(mod, f"scope_acq_trigger_mode_path{path}")() == "sequencer"

        getattr(mod, f"scope_acq_trigger_level_path{path}")(True)
        assert getattr(mod, f"scope_acq_trigger_level_path{path}")()

        getattr(mod, f"scope_acq_avg_mode_en_path{path}")(True)
        assert getattr(mod, f"scope_acq_avg_mode_en_path{path}")()


# ----------------------------------------------------------------------------
def test_qsm_io_channels(cluster, mocker):
    """
    Tests if QSM IO channels can be accessed.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture
    mocker: test_fixture
        mocker from pytest-mocker

    """
    mod = module(cluster, ClusterType.CLUSTER_QSM)

    assert len(mod.io_channels) == 8
    for idx, io_channel in enumerate(mod.io_channels):
        assert io_channel.name == f"{mod.name}_io_channel{idx}"
        assert io_channel.name == mod[f"io_channel{idx}"].name


# ----------------------------------------------------------------------------
@pytest.mark.parametrize(
    "channel_no, method_name, set_value",
    [
        # Parametrize the test with different channel numbers, setting methods, and their
        # corresponding values
        (0, "source_mode", "open"),
        (1, "measure_mode", "coarse"),
        (2, "slew_rate", 0.01),
        (3, "integration_time", 0.01),
        (4, "coarse_voltage", 0.1),
        (5, "fine_voltage", 0.001),
        (6, "source_mode", "ground"),
        (7, "measure_mode", "automatic"),
        (0, "low_pass_filter_cutoff", FilterMode.FREQ_250_KHZ),
        (1, "low_pass_filter_cutoff", 10),
    ],
)
def test_qsm_channel_settings(cluster, mocker, channel_no, method_name, set_value):
    """
    Tests QSM channel settings using parametrization.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture
    mocker: test_fixture
        mocker from pytest-mocker
    channel_no : int
        The specific channel number to test
    method_name : str
        The name of the channel setting method
    set_value : Any
        The value to set for the corresponding channel setting

    """
    mod = module(cluster, ClusterType.CLUSTER_QSM)

    write_binary_mock = mocker.patch.object(
        cluster._transport, "write_binary", wraps=cluster._transport.write_binary
    )

    # Dynamically get the channel object (e.g., mod.io_channel1, mod.io_channel7)
    channel_obj = getattr(mod, f"io_channel{channel_no}")
    channel_obj.source_mode("v_source")
    write_binary_mock.reset_mock()

    # Dynamically get and call the setter method (e.g., channel_obj.source_mode("open"))
    setter_method = getattr(channel_obj, method_name)
    setter_method(set_value)

    # Construct the full expected call
    command_prefix = f"SLOT18:IO:CHANnel{channel_no}:CONFig"
    expected_payload = channel_obj._get_io_channel_config() | {method_name: set_value}
    expected_json_str = json.dumps(expected_payload)
    expected_header = cluster._build_header_string(len(expected_json_str))
    expected_call1 = f"{command_prefix} {expected_header}".encode()
    expected_call2 = expected_json_str.encode()

    write_binary_mock.assert_called_once_with(expected_call1, expected_call2)
    write_binary_mock.reset_mock()

    # Dynamically get and call the getter method
    getter_method = getattr(channel_obj, method_name)
    assert getter_method() == set_value

    write_binary_mock.assert_not_called()


# ----------------------------------------------------------------------------
def test_qsm_measure_current(cluster, mocker):
    mod = module(cluster, ClusterType.CLUSTER_QSM)

    # This ignores empty line terminators sent by _bin_block_write to preserve
    # the dummy transport's output buffer state.
    original_write = cluster._transport.write

    def smart_write(cmd_str: str):
        if cmd_str == "":
            return None
        return original_write(cmd_str)

    mocker.patch.object(cluster._transport, "write", side_effect=smart_write)
    mock_bin_write = mocker.patch.object(
        cluster._transport, "write_binary", wraps=cluster._transport.write_binary
    )

    def assert_binary_call(expected_payload: bytes):
        """
        Constructs the expected SCPI command with binary header and asserts call.
        """
        # Encode full block (Header + Data) using transport utility
        full_block = cluster._transport._encode_bin(expected_payload, False)

        # Slice off the data to isolate just the header bytes (e.g. b'#13')
        header_only = full_block[: -len(expected_payload)]

        # Construct the full command: Command String + Header
        expected_cmd_arg = b"SLOT18:IO:CHANnels:MEASurement:CURRent? " + header_only

        mock_bin_write.assert_any_call(expected_cmd_arg, expected_payload)
        mock_bin_write.reset_mock()

    # Test IOChannelQSM interface
    assert mod.io_channel7.measure_current() == 0.1
    assert_binary_call(b"[7]")

    # Test Module interface
    # Format: (input_channels, expected_return_value, expected_sent_payload)
    test_cases = [
        # Case 1: Single Integer -> Returns single Float
        (7, 0.1, b"[7]"),
        # Case 2: Single Item List -> Returns List with 1 item
        ([0], [0.1], b"[0]"),
        # Case 3: Multi-Channel List -> Returns List with N items
        ([0, 1], [0.1, 0.1], b"[0, 1]"),
        # Case 4: Tuple (Iterable) -> Returns List
        ((2, 3, 4), [0.1, 0.1, 0.1], b"[2, 3, 4]"),
        # Case 5: Range -> Returns List
        (range(0, 4), [0.1, 0.1, 0.1, 0.1], b"[0, 1, 2, 3]"),
    ]

    for channels, expected_ret, expected_payload in test_cases:
        result = mod.measure_current(channels)
        assert result == expected_ret
        assert_binary_call(expected_payload)


# ----------------------------------------------------------------------------
def test_qsm_measure_voltage(cluster, mocker):
    """
    Tests QSM measure current function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture
    mocker: test_fixture
        mocker from pytest-mocker

    """
    mod = module(cluster, ClusterType.CLUSTER_QSM)
    mocker.patch.object(cluster._transport, "write", wraps=cluster._transport.write)

    assert mod.io_channel0.measure_voltage() == 0.2
    cluster._transport.write.assert_any_call("SLOT18:IO:CHANnel0:MEASurement:VOLTage?")
    cluster._transport.write.reset_mock()


# ----------------------------------------------------------------------------
@pytest.mark.parametrize(
    "channel_no, expects_error_on_call",  # Renamed parameters for clarity
    [
        (0, False),  # Channel 0 should succeed
        (4, False),  # Channel 4 should succeed
        (1, True),  # Channel 1 should raise ValueError
        (2, True),  # Channel 2 should raise ValueError
        (3, True),  # Channel 3 should raise ValueError
        (5, True),  # Channel 5 should raise ValueError
        (6, True),  # Channel 6 should raise ValueError
        (7, True),  # Channel 7 should raise ValueError
    ],
)
def test_qsm_measure_voltage_availability(cluster, mocker, channel_no, expects_error_on_call):
    """
    Tests QSM measure_voltage method behavior on specific channels.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture
    mocker: test_fixture
        mocker from pytest-mocker
    channel_no : int
        The index of the IO channel to test.
    expects_error_on_call : bool
        True if calling 'measure_voltage' is expected to raise a ValueError, False otherwise.

    """
    mod = module(cluster, ClusterType.CLUSTER_QSM)

    # Dynamically get the specific IO channel object
    io_channel_obj = getattr(mod, f"io_channel{channel_no}")

    if expects_error_on_call:
        # If an error is expected, use pytest.raises to check for it
        with pytest.raises(ValueError):
            io_channel_obj.measure_voltage()
    else:
        assert io_channel_obj.measure_voltage() == 0.2


# ----------------------------------------------------------------------------
def test_qsm_outputs_to_zero(cluster, mocker):
    """
    Tests QSM outputs to zero current function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture
    mocker: test_fixture
        mocker from pytest-mocker

    """
    mod = module(cluster, ClusterType.CLUSTER_QSM)
    mocker.patch.object(cluster._transport, "write", wraps=cluster._transport.write)

    mod.reset_io_channel_output()
    cluster._transport.write.assert_any_call("SLOT18:IO:CHANnel:OUT:ZERO")
    cluster._transport.write.reset_mock()

    mod.io_channel7.reset_io_channel_output()
    cluster._transport.write.assert_any_call("SLOT18:IO:CHANnel7:OUT:ZERO")
    cluster._transport.write.reset_mock()


# ----------------------------------------------------------------------------
def test_qsm_voltage_wait(cluster, mocker):
    """
    Tests QSM voltage wait function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture
    mocker: test_fixture
        mocker from pytest-mocker

    """
    mod = module(cluster, ClusterType.CLUSTER_QSM)
    mocker.patch.object(cluster._transport, "write", wraps=cluster._transport.write)

    mod.io_channel7.source_mode("v_source")
    mod.io_channel7.set_voltage_wait(0.1)
    cluster._transport.write.assert_any_call("SLOT18:IO:CHANnel7:VOLTage:WAIT 0.1")
    cluster._transport.write.reset_mock()


# ----------------------------------------------------------------------------
def test_qsm_voltage_instant(cluster, mocker):
    """
    Tests QSM instant function calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture
    mocker: test_fixture
        mocker from pytest-mocker

    """
    mod = module(cluster, ClusterType.CLUSTER_QSM)
    mocker.patch.object(cluster._transport, "write", wraps=cluster._transport.write)

    mod.io_channel7.source_mode("v_source")
    mod.io_channel7.set_voltage_instant(0.1)
    cluster._transport.write.assert_any_call("SLOT18:IO:CHANnel7:VOLTage:INSTant 0.1")
    cluster._transport.write.reset_mock()


# -----------------------------------------------------------------------------
def test_set_qsm_multiple_io_channels_config(cluster, mock_qsm_config) -> None:
    """
    Tests user set QSM IO channels config.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture
    mock_qsm_config: test_fixture
        realistic user config

    """
    # Check if the key exist and value is in range.
    mod = module(cluster, ClusterType.CLUSTER_QSM)
    mod.set_io_channel_config(config=[mock_qsm_config])

    # Invalid keys
    false_config = {"channel": 0, "not": "working"}
    expected_error_message = (
        r"Configuration validation failed.*Parameter 'not'.*is not a valid QSM IO channel parameter"
    )

    with pytest.raises(RuntimeError, match=expected_error_message):
        mod.set_io_channel_config(config=[false_config])


# -----------------------------------------------------------------------------
def test_qsm_set_io_channel_config(cluster, mock_qsm_config) -> None:
    """
    Tests user set QSM config.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture
    mock_qsm_config: test_fixture
        realistic user config

    """
    mod = module(cluster, ClusterType.CLUSTER_QSM)
    io_channel = mod.io_channels[0]
    io_channel.set_io_channel_config(mock_qsm_config)
    expected_error_message = (
        r"Configuration validation failed.*Parameter 'not'.*is not a valid QSM IO channel parameter"
    )
    false_config = {"channel": 0, "not": "working"}

    with pytest.raises(RuntimeError, match=expected_error_message):
        io_channel.set_io_channel_config(false_config)


# -----------------------------------------------------------------------------
def test_request_and_clear_rampdown(cluster, mocker):
    write_mock = mocker.patch.object(cluster._transport, "write", wraps=cluster._transport.write)

    cluster.request_rampdown(18)
    cluster.clear_rampdown(18)
    write_mock.assert_any_call("SLOT18:IO:OUTput:OUT:RAMPdown")
    write_mock.assert_any_call("SLOT18:IO:OUTput:OUT:CLR")

    write_mock.reset_mock()

    mod = module(cluster, ClusterType.CLUSTER_QSM)
    mod.request_rampdown()
    mod.clear_rampdown()
    write_mock.assert_any_call("SLOT18:IO:OUTput:OUT:RAMPdown")
    write_mock.assert_any_call("SLOT18:IO:OUTput:OUT:CLR")


# ----------------------------------------------------------------------------
def test_update_sequence_add_parts(cluster, mocker):
    """
    Tests cumulative sequence update.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture
    mocker: test_fixture
        mocker from pytest-mocker

    """
    mod = module(cluster, ClusterType.CLUSTER_QRM)
    sequence = {
        "waveforms": {},
        "weights": {},
        "acquisitions": {},
        "program": "stop",
    }
    mod.sequencers[0].sequence(sequence)
    assert mod.sequencers[0].sequence.cache.valid is True
    assert mod.sequencers[0].sequence.cache() == sequence

    set_program_spy = mocker.spy(cluster, "_set_sequencer_program")
    delete_waveform_spy = mocker.spy(cluster, "_delete_waveform")
    add_waveforms_spy = mocker.spy(cluster, "_add_waveforms")
    delete_weight_spy = mocker.spy(cluster, "_delete_weight")
    add_weights_spy = mocker.spy(cluster, "_add_weights")
    delete_acquisition_spy = mocker.spy(cluster, "_delete_acquisition")
    add_acquisitions_spy = mocker.spy(cluster, "_add_acquisitions")

    mod.sequencers[0].update_sequence(
        waveforms={"wave0": {"index": 0, "data": [0.0, 0.1, 0.2, 0.3]}},
        weights={"weight0": {"index": 0, "data": [0.0, 0.1, 0.2, 0.3]}},
        erase_existing=False,
    )

    assert mod.sequencers[0].sequence.cache.valid is False
    set_program_spy.assert_not_called()
    delete_waveform_spy.assert_not_called()
    add_waveforms_spy.assert_called_once()
    delete_weight_spy.assert_not_called()
    add_weights_spy.assert_called_once()
    delete_acquisition_spy.assert_not_called()
    add_acquisitions_spy.assert_not_called()


# ----------------------------------------------------------------------------
def test_update_sequence_replace_parts(cluster, mocker):
    """
    Tests replacement sequence update.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture
    mocker: test_fixture
        mocker from pytest-mocker

    """
    mod = module(cluster, ClusterType.CLUSTER_QRM)
    sequence = {
        "waveforms": {},
        "weights": {},
        "acquisitions": {},
        "program": "stop",
    }
    mod.sequencers[0].sequence(sequence)
    assert mod.sequencers[0].sequence.cache.valid is True
    assert mod.sequencers[0].sequence.cache() == sequence

    set_program_spy = mocker.spy(cluster, "_set_sequencer_program")
    delete_waveform_spy = mocker.spy(cluster, "_delete_waveform")
    add_waveforms_spy = mocker.spy(cluster, "_add_waveforms")
    delete_weight_spy = mocker.spy(cluster, "_delete_weight")
    add_weights_spy = mocker.spy(cluster, "_add_weights")
    delete_acquisition_spy = mocker.spy(cluster, "_delete_acquisition")
    add_acquisitions_spy = mocker.spy(cluster, "_add_acquisitions")

    mod.sequencers[0].update_sequence(
        program="play 0,0,100\nstop",
        acquisitions={"acq0": {"index": 0, "num_bins": 1}},
        erase_existing=True,
    )

    assert mod.sequencers[0].sequence.cache.valid is False
    set_program_spy.assert_called_once()
    delete_waveform_spy.assert_not_called()
    add_waveforms_spy.assert_not_called()
    delete_weight_spy.assert_not_called()
    add_weights_spy.assert_not_called()
    delete_acquisition_spy.assert_called_once()
    add_acquisitions_spy.assert_called_once()


# ----------------------------------------------------------------------------
@pytest.mark.parametrize("update", [True, False])
def test_snapshot_does_not_send_unnecessary_scpi_commands(cluster, mocker, update):
    """
    Tests snapshot feature not making unnecessary SCPI calls.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture
    mocker: test_fixture
        mocker from pytest-mocker
    update: bool
        Value of the `update` parameter passed to the snapshot method

    """
    get_mods_info_spy = mocker.spy(cluster._scpi, "_get_mods_info")
    get_modules_present_spy = mocker.spy(cluster._scpi, "_get_modules_present")

    cluster_snap = cluster.snapshot(update=update)

    # Check that `connected` and `present` are retrieved regardless of the `update` argument.
    for status_param in ("connected", "present"):
        assert all(
            isinstance(mod["parameters"][status_param]["value"], bool)
            for mod in cluster_snap["submodules"].values()
            if status_param in mod["parameters"]
        )
    # Check whether a sample argument is polled "live" depending on the `update` value.
    exp_param_value = 0.0 if update else None
    assert (
        cluster_snap["submodules"]["module1"]["parameters"]["out0_offset"]["value"]
        == exp_param_value
    )

    get_mods_info_spy.assert_called_once()
    get_modules_present_spy.assert_called_once()


# ----------------------------------------------------------------------------
def test_set_safe_voltage_range_validation(cluster):
    """
    Tests that setting a safe voltage range does not bypass the default range
    of MIN_SAFE_VOLTAGE to MAX_SAFE_VOLTAGE.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    cluster.set_safe_voltage_range(-5.0, 5.0)
    with pytest.raises(
        ValueError, match=r"The minimum voltage must be lower than the maximum voltage"
    ):
        cluster.set_safe_voltage_range(42, -1)
    with pytest.raises(
        ValueError, match=r"The safe voltage range limits must be between -10.0 V and \+10.0 V"
    ):
        cluster.set_safe_voltage_range(-9000, 9001)


# ----------------------------------------------------------------------------
def test_set_safe_voltage_range_at_cluster_and_module_level(cluster):
    """
    Tests that setting a safe voltage range across a whole cluster or module
    applies the limit to all the channels.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    mod = module(cluster, ClusterType.CLUSTER_QSM)

    for obj in (cluster, mod):
        obj.set_safe_voltage_range(-1.0, +1.0)

        for io_chan in mod.io_channels:
            # Prepare source_mode
            io_chan.source_mode("v_source")
            assert_safe_voltage_range_respected(io_chan)


# ----------------------------------------------------------------------------
def test_set_safe_voltage_range_at_channel_level(cluster):
    """
    Tests that setting a safe voltage range on a specific channel applies the limit
    only to that channel, leaving other channels at the default.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    mod = module(cluster, ClusterType.CLUSTER_QSM)

    # Prepare source_mode
    mod.io_channels[0].source_mode("v_source")
    # Change the voltage limit for channel 0 and try to set it outside range
    mod.io_channels[0].set_safe_voltage_range(-1.0, +1.0)
    assert_safe_voltage_range_respected(mod.io_channels[0])

    # Check that the limits haven't changed for the other channels
    for io_chan in mod.io_channels[1:]:
        # Prepare source_mode
        io_chan.source_mode("v_source")
        # Value within default range
        io_chan.coarse_voltage(5.0)
        io_chan.set_voltage_wait(5.0)
        io_chan.set_voltage_instant(5.0)
        # Value outside default range
        with pytest.raises(ValueError):
            io_chan.coarse_voltage(42)
        with pytest.raises(ValueError):
            io_chan.set_voltage_wait(42)
        with pytest.raises(ValueError):
            io_chan.set_voltage_instant(42)


# ----------------------------------------------------------------------------
def test_setting_voltage_in_wrong_source_mode_warns(cluster):
    """
    Tests that setting a safe voltage range on a specific channel applies the limit
    only to that channel, leaving other channels at the default.

    Parameters
    ----------
    cluster: test_fixture
        Dummy Cluster test fixture

    """
    mod = module(cluster, ClusterType.CLUSTER_QSM)

    # Set an non-voltage source mode
    mod.io_channels[0].source_mode("i_source")
    # Change the voltage limit for channel 0 and try to set it outside range
    with pytest.warns(
        UserWarning, match=r'Voltages cannot be set unless `source_mode` is set to "v_source"'
    ):
        mod.io_channels[0].set_voltage_instant(1.0)


# ----------------------------------------------------------------------------
def test_program_comments_are_trimmed_before_upload(mocker, cluster):
    spy = mocker.spy(cluster._scpi, "_set_sequencer_program")

    rx_prog = """
        wait_sync 4
        move    10, R0          # R0 ← number of shots

    loop:                       # start of acquisition loop
        wait     200            # dead-time before each acquire (ns)
        acquire  0,0,1024       # scope=0, bin=0, length=1024 samples
        loop     R0,@loop       # R0; if >0, jump back to @loop
        stop                    # when R0==0, halt sequencer
    """
    expected_program = (
        "wait_sync 4\nmove 10, R0\nloop:\nwait 200\nacquire 0,0,1024\nloop R0,@loop\nstop"
    )
    rx_sequence = {
        "waveforms": {},
        "weights": {},
        "acquisitions": {},
        "program": rx_prog,
    }

    sequencer = cluster.module15.sequencer0
    sequencer.sequence(rx_sequence)
    spy.assert_called_once()
    spy.assert_called_once_with(15, 0, expected_program)


# ----------------------------------------------------------------------------
@pytest.mark.xfail  # todo: look into after release. works locally, but not on ci/cd pipeline.
def test_non_ascii_character_in_program(cluster):
    rx_prog = "wait←sync"
    rx_sequence = {
        "waveforms": {},
        "weights": {},
        "acquisitions": {},
        "program": rx_prog,
    }

    module = Module(cluster, "module", 15)
    sequencer = Sequencer(module, name="sequencer", seq_idx=0)
    with pytest.raises(UnicodeEncodeError):
        sequencer.sequence(rx_sequence)


# ----------------------------------------------------------------------------
@pytest.mark.parametrize(
    "mock_state,expected_flags",
    [
        (
            "OKAY;UNKNOWN_FLAG_1,UNKNOWN_FLAG_2,PLL_UNLOCKED,",
            [
                SystemStatusFlags.UNKNOWN,
                SystemStatusFlags.UNKNOWN,
                SystemStatusFlags.PLL_UNLOCKED,
            ],
        ),
        (
            "OKAY;SLOT_1_UNKNOWN_SLOT_FLAG,SLOT_2_PLL_UNLOCKED,",
            [
                SystemStatusFlags.UNKNOWN,
                SystemStatusFlags.PLL_UNLOCKED,
            ],
        ),
        (
            "ERROR;UNKNOWN_SYS_FLAG,TEMPERATURE_OUT_OF_RANGE,SLOT_1_UNKNOWN_SLOT_FLAG,SLOT_3_HARDWARE_COMPONENT_FAILED,",
            [
                SystemStatusFlags.UNKNOWN,
                SystemStatusFlags.TEMPERATURE_OUT_OF_RANGE,
                SystemStatusFlags.UNKNOWN,
                SystemStatusFlags.HARDWARE_COMPONENT_FAILED,
            ],
        ),
        (
            "OKAY;PLL_UNLOCKED,TEMPERATURE_OUT_OF_RANGE,",
            [
                SystemStatusFlags.PLL_UNLOCKED,
                SystemStatusFlags.TEMPERATURE_OUT_OF_RANGE,
            ],
        ),
        ("OKAY;", []),
    ],
)
def test_unknown_flags_handled_correctly(cluster, mock_state: str, expected_flags: list) -> None:
    with patch(
        "qblox_instruments.scpi.layers.cluster_mm_1_0.Cluster._get_system_state",
        return_value=mock_state,
    ):
        result = cluster.get_system_status()

        all_flags = list(result.flags)
        for slot_flags in result.slot_flags:
            if slot_flags:
                all_flags.extend(slot_flags)

        assert all_flags == expected_flags


def test_connecting_to_cluster_with_unknown_module_type_fails_gracefully():
    with pytest.warns(UserWarning, match="Invalid instrument type: 'UNKNOWN_OR_UNSUPPORTED'"):
        cluster = Cluster(
            "cluster",
            dummy_cfg={
                "2": ClusterType.CLUSTER_QRM,
                "4": ClusterType.CLUSTER_QCM,
                "6": ClusterType.CLUSTER_QRM_RF,
                "8": ClusterType.CLUSTER_QCM_RF,
                "9": "UNKNOWN_OR_UNSUPPORTED",
            },
            debug=DebugLevel.NO_CHECK,
        )

    assert len(cluster.get_connected_modules()) == 4
