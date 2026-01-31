# ----------------------------------------------------------------------------
# Description    : Qblox Instruments test script
# Git repository : https://gitlab.com/qblox/packages/software/qblox_instruments.git
# Copyright (C) Qblox BV (2020)
# ----------------------------------------------------------------------------


# -- include -----------------------------------------------------------------

from dataclasses import replace
from datetime import datetime

import fastjsonschema

from qblox_instruments import (
    BuildInfo,
    ClusterType,
    DeviceInfo,
    InstrumentType,
    SequencerStates,
    SequencerStatus,
    SequencerStatuses,
    SequencerStatusFlags,
    SystemStatus,
    SystemStatuses,
    SystemStatusFlags,
    SystemStatusSlotFlags,
    __version__,
    get_build_info,
)

# -- functions ---------------------------------------------------------------


def test_build_info(cluster):
    """
    Tests BuildInfo object methods.
    """
    # Create device info from dummy
    build_info = DeviceInfo.from_idn(cluster._get_idn()).fw_build

    # Replace build timestamp for conversion to unix timestamp to work.
    # The dummy timestamps are before 1970 and so will fail.
    timestamp = datetime.strptime("01/01/2000-00:00:00", "%d/%m/%Y-%H:%M:%S")
    build_info = replace(build_info, build=timestamp)

    # Check build info contents
    assert build_info.version == (0, 0, 0)
    assert build_info.build == timestamp
    assert build_info.build_iso == timestamp.isoformat()
    assert build_info.build_unix == timestamp.timestamp()
    assert build_info.hash == int("0xDEADBEAF", 16)
    assert build_info.hash_str == "DEADBEAF".lower()
    assert build_info.dirty is False
    assert build_info.dirty_str == "0"

    # Check build info IDN string
    assert build_info.to_idn() == (
        f"Version={build_info.version_str} "
        f"Build={build_info.build_str} "
        f"Hash=0x{build_info.hash:08X} "
        f"Dirty={build_info.dirty_str}"
    )

    # Check build info dict
    build_info_dict = {
        "version": build_info.version,
        "build": build_info.build_unix,
        "hash": build_info.hash,
        "dirty": build_info.dirty,
    }
    assert build_info.to_dict() == build_info_dict
    assert build_info == BuildInfo.from_dict(build_info_dict)

    # Check build info tuple
    assert build_info.to_tuple() == (
        build_info.version,
        build_info.build_unix,
        build_info.hash,
        build_info.dirty,
    )


# ----------------------------------------------------------------------------
def test_device_info(cluster):
    """
    Tests DeviceInfo object methods.
    """
    # Create device info from dummy
    device_info = DeviceInfo.from_idn(cluster._get_idn())

    # Check device info contents
    assert device_info.manufacturer == "qblox"
    assert device_info.model == "cluster_mm"
    assert device_info.serial == "whatever"

    assert "fw" in device_info
    assert "kmod" in device_info
    assert "sw" in device_info
    assert "cfg_man" in device_info

    # Replace build timestamps for conversion to unix timestamp to work.
    # The dummy timestamps are before 1970 and so will fail.
    timestamp = datetime.strptime("01/01/2000-00:00:00", "%d/%m/%Y-%H:%M:%S")
    device_info.build = replace(
        device_info.build,
        firmware=replace(device_info.fw_build, build=timestamp),
        kernel_module=replace(device_info.kmod_build, build=timestamp),
        application=replace(device_info.sw_build, build=timestamp),
    )

    # Get build info objects
    fw_build_info = device_info.fw_build
    assert fw_build_info is not None
    kmod_build_info = device_info.kmod_build
    assert kmod_build_info is not None
    sw_build_info = device_info.sw_build
    assert sw_build_info is not None
    sw_compat_info = device_info.sw_compat
    assert sw_compat_info is not None
    cfg_man_build_info = device_info.cfg_man_build
    assert cfg_man_build_info is not None
    cfg_man_compat_info = device_info.cfg_man_compat
    assert cfg_man_compat_info is not None

    # Check device info IDN string
    assert device_info.to_idn() == (
        f"{device_info.manufacturer},{device_info.model},{device_info.serial}"
        f",{device_info.build.to_idn()}"
    )

    # Check device info IDN dict
    device_info_dict = {
        "manufacturer": device_info.manufacturer,
        "model": device_info.model,
        "ser": device_info.serial,
        "fw": fw_build_info.to_dict(),
        "kmod": kmod_build_info.to_dict(),
        "sw": sw_build_info.to_dict(),
        "sw_compat": sw_compat_info.to_dict(),
        "cfg_man": cfg_man_build_info.to_dict(),
        "cfg_man_compat": cfg_man_compat_info.to_dict(),
        "is_extended_instrument": False,
        "is_rf": False,
        "qtm_eom": False,
    }
    assert device_info.to_dict() == device_info_dict
    assert device_info == DeviceInfo.from_dict(device_info_dict)

    # Check device info IDN tuple
    assert device_info.to_tuple() == (
        device_info.manufacturer,
        device_info.model,
        device_info.name,
        device_info.serial,
        device_info.is_extended_instrument,
        device_info.is_rf,
        device_info.qtm_eom,
        device_info.build,
        None,
    )


# ----------------------------------------------------------------------------
def test_get_build_info():
    """
    Tests get build info function and checks if the returned dictionary has the
    correct format. If not, the test fails.
    """
    # Build info
    build_info = get_build_info()

    # Check build info
    build_info_schema = {
        "title": "Build information container.",
        "description": "Contains build information.",
        "required": ["version", "build", "hash", "dirty"],
        "properties": {
            "version": {"description": "Version string", "type": "string"},
            "build": {"description": "Build date", "type": "string"},
            "hash": {"description": "Git hash", "type": "string"},
            "dirty": {"description": "Git dirty indication", "type": "boolean"},
        },
    }

    validate_build_info = fastjsonschema.compile(build_info_schema)
    validate_build_info(build_info.to_idn_dict())


# ----------------------------------------------------------------------------
def test_version():
    """
    Test if __version__ matches version in the build information else fail.
    """
    # Test version
    assert __version__ == get_build_info().version_str


# ----------------------------------------------------------------------------
def test_instrument_types():
    """
    Test instrument type string representations.
    """
    assert repr(InstrumentType.QCM) == "<InstrumentType.QCM>"
    assert str(InstrumentType.QCM) == "QCM"
    assert InstrumentType.QCM == "QCM"
    assert list({InstrumentType.QCM: ""}.keys()) == ["QCM"]

    assert repr(ClusterType.CLUSTER_QRM_RF) == "<ClusterType.CLUSTER_QRM_RF>"
    assert str(ClusterType.CLUSTER_QRM_RF) == "Cluster QRM-RF"
    assert ClusterType.CLUSTER_QRM_RF == "Cluster QRM-RF"
    assert list({ClusterType.CLUSTER_QRM_RF: ""}.keys()) == ["Cluster QRM-RF"]


# ----------------------------------------------------------------------------
def test_system_status():
    """
    Test system status string representations.
    """
    # Test system state string representations
    state = SystemStatus(SystemStatuses.OKAY, [], SystemStatusSlotFlags())
    assert repr(state) == (
        "SystemStatus(status=<SystemStatuses.OKAY>, flags=[], slot_flags=SystemStatusSlotFlags())"
    )
    assert str(state) == "Status: OKAY, Flags: NONE, Slot flags: NONE"

    state = SystemStatus(
        SystemStatuses.OKAY,
        [SystemStatusFlags.PLL_UNLOCKED],
        SystemStatusSlotFlags(
            {
                "slot1": [SystemStatusFlags.PLL_UNLOCKED],
                "slot20": [SystemStatusFlags.PLL_UNLOCKED],
            }
        ),
    )
    assert repr(state) == (
        "SystemStatus(status=<SystemStatuses.OKAY>, "
        "flags=[<SystemStatusFlags.PLL_UNLOCKED>], "
        "slot_flags=SystemStatusSlotFlags("
        "slot1=[<SystemStatusFlags.PLL_UNLOCKED>], "
        "slot20=[<SystemStatusFlags.PLL_UNLOCKED>]))"
    )
    assert str(state) == (
        "Status: OKAY, Flags: PLL_UNLOCKED, Slot flags: SLOT1_PLL_UNLOCKED, SLOT20_PLL_UNLOCKED"
    )

    assert SystemStatuses.OKAY == "OKAY"
    assert list({SystemStatuses.OKAY: True}.keys()) == ["OKAY"]

    assert SystemStatusFlags.PLL_UNLOCKED == "PLL_UNLOCKED"
    assert list({SystemStatusFlags.PLL_UNLOCKED: ""}.keys()) == ["PLL_UNLOCKED"]


# ----------------------------------------------------------------------------
def test_sequencer_status():
    """
    Test sequencer status string representations.
    """
    # Test sequencer state string representations
    status = SequencerStatus(SequencerStatuses.OKAY, SequencerStates.IDLE, [], [], [], [])
    assert repr(status) == (
        "SequencerStatus(status=<SequencerStatuses.OKAY>, "
        "state=<SequencerStates.IDLE>, "
        "info_flags=[], "
        "warn_flags=[], "
        "err_flags=[], "
        "log=[])"
    )
    assert str(status) == (
        "Status: OKAY, State: IDLE, Info Flags: NONE, Warning Flags: NONE, Error Flags: NONE, "
        "Log: []"
    )

    status = SequencerStatus(
        SequencerStatuses.WARNING,
        SequencerStates.Q1_STOPPED,
        [],
        [SequencerStatusFlags.TRIGGER_NETWORK_MISSED_INTERNAL_TRIGGER],
        [],
        ["missed_tgr_addr:_7"],
    )
    assert repr(status) == (
        "SequencerStatus(status=<SequencerStatuses.WARNING>, "
        "state=<SequencerStates.Q1_STOPPED>, "
        "info_flags=[], "
        "warn_flags=[<SequencerStatusFlags.TRIGGER_NETWORK_MISSED_INTERNAL_TRIGGER>], "
        "err_flags=[], "
        "log=['missed_tgr_addr:_7'])"
    )

    assert str(status) == (
        "Status: WARNING, State: Q1_STOPPED, "
        "Info Flags: NONE, "
        "Warning Flags: TRIGGER_NETWORK_MISSED_INTERNAL_TRIGGER, "
        "Error Flags: NONE, "
        "Log: ['missed_tgr_addr:_7']"
    )

    status = SequencerStatus(
        SequencerStatuses.OKAY,
        SequencerStates.Q1_STOPPED,
        [
            SequencerStatusFlags.ACQ_SCOPE_DONE_PATH_0,
            SequencerStatusFlags.ACQ_SCOPE_DONE_PATH_1,
        ],
        [],
        [],
        [],
    )
    assert repr(status) == (
        "SequencerStatus(status=<SequencerStatuses.OKAY>, "
        "state=<SequencerStates.Q1_STOPPED>, "
        "info_flags=[<SequencerStatusFlags.ACQ_SCOPE_DONE_PATH_0>, "
        "<SequencerStatusFlags.ACQ_SCOPE_DONE_PATH_1>], "
        "warn_flags=[], "
        "err_flags=[], "
        "log=[])"
    )

    assert str(status) == (
        "Status: OKAY, "
        "State: Q1_STOPPED, "
        "Info Flags: ACQ_SCOPE_DONE_PATH_0, ACQ_SCOPE_DONE_PATH_1, "
        "Warning Flags: NONE, "
        "Error Flags: NONE, "
        "Log: []"
    )

    status = SequencerStatus(
        SequencerStatuses.ERROR,
        SequencerStates.Q1_STOPPED,
        [],
        [],
        [SequencerStatusFlags.SEQUENCE_PROCESSOR_Q1_ILLEGAL_INSTRUCTION],
        [],
    )
    assert repr(status) == (
        "SequencerStatus(status=<SequencerStatuses.ERROR>, "
        "state=<SequencerStates.Q1_STOPPED>, "
        "info_flags=[], "
        "warn_flags=[], "
        "err_flags=[<SequencerStatusFlags.SEQUENCE_PROCESSOR_Q1_ILLEGAL_INSTRUCTION>], "
        "log=[])"
    )

    assert str(status) == (
        "Status: ERROR, "
        "State: Q1_STOPPED, "
        "Info Flags: NONE, "
        "Warning Flags: NONE, "
        "Error Flags: SEQUENCE_PROCESSOR_Q1_ILLEGAL_INSTRUCTION, "
        "Log: []"
    )


# ----------------------------------------------------------------------------
def test_sequencer_status_types():
    """
    Test sequencer status types string representations.
    """
    assert SequencerStatuses.OKAY == "OKAY"
    assert SequencerStatuses.WARNING == "WARNING"
    assert SequencerStatuses.ERROR == "ERROR"

    assert list({SequencerStatuses.OKAY: ""}.keys()) == ["OKAY"]
    assert list({SequencerStatuses.WARNING: ""}.keys()) == ["WARNING"]
    assert list({SequencerStatuses.ERROR: ""}.keys()) == ["ERROR"]

    assert SequencerStates.IDLE == "IDLE"
    assert SequencerStates.ARMED == "ARMED"
    assert SequencerStates.RUNNING == "RUNNING"
    assert SequencerStates.Q1_STOPPED == "Q1_STOPPED"
    assert SequencerStates.STOPPED == "STOPPED"

    assert list({SequencerStates.IDLE: ""}.keys()) == ["IDLE"]
    assert list({SequencerStates.ARMED: ""}.keys()) == ["ARMED"]
    assert list({SequencerStates.RUNNING: ""}.keys()) == ["RUNNING"]
    assert list({SequencerStates.Q1_STOPPED: ""}.keys()) == ["Q1_STOPPED"]
    assert list({SequencerStates.STOPPED: ""}.keys()) == ["STOPPED"]


# ----------------------------------------------------------------------------
def test_device_info_from_describe(cluster):
    """
    Test the full pipeline from `*DESCribe?` to DeviceInfo by verifying every
    module in the dummy configuration.
    """
    description = cluster.get_json_description()
    device_info = DeviceInfo.from_dict(description)

    assert device_info.manufacturer == "qblox"
    assert device_info.model == "cluster_mm"
    assert device_info.name == "cluster-mm"
    assert device_info.serial == "00019_2426_027"
    assert device_info.is_extended_instrument is False
    assert device_info.is_rf is False
    assert device_info.qtm_eom is False
    assert device_info.fw_build is not None
    assert device_info.kmod_build is not None
    assert device_info.sw_build is not None
    assert device_info.cfg_man_build is not None
    assert device_info.mac_address is not None

    assert device_info.sw_build.version == (0, 0, 0)
    assert device_info.sw_build.dirty is True
    assert device_info.sw_build.hash == 0x51D8517D

    assert device_info.kmod_build.version == (0, 0, 0)
    assert device_info.kmod_build.dirty is True
    assert device_info.kmod_build.hash == 0x51D8517D

    assert device_info.cfg_man_build.version == (0, 0, 0)
    assert device_info.cfg_man_build.dirty is True
    assert device_info.cfg_man_build.hash == 0x51D8517D

    assert device_info.fw_build.version == (0, 0, 0)
    assert device_info.fw_build.dirty is False
    assert device_info.fw_build.hash == 0x98F2499F

    # Expectations: (model, name, is_rf, qtm_eom, is_extended, has_fw_build)
    expected_modules = {
        "1": ("cluster_qcm", "cluster-qcm", False, False, False, True),
        "3": ("cluster_qcm", "cluster-qcm", False, False, False, True),
        "4": ("cluster_qcm", "cluster-qcm", True, False, False, True),
        "8": ("cluster_qcm", "cluster-qcm", True, False, False, True),
        "10": ("cluster_qdm", "cluster-qdm", False, False, True, False),
        "11": ("cluster_qtm", "cluster-qtm", False, False, False, True),
        "12": ("cluster_linq", "cluster-linq", False, False, True, False),
        "13": ("cluster_qtm", "cluster-qtm", False, True, False, True),
        "15": ("cluster_qrm", "cluster-qrm", False, False, False, True),
        "16": ("cluster_qrm", "cluster-qrm", True, False, False, True),
        "17": ("cluster_qrc", "cluster-qrc", True, False, False, True),
        "18": ("cluster_qsm", "cluster-qsm", False, False, False, True),
        "20": ("cluster_qcm", "cluster-qcm", True, False, False, True),
    }

    for slot, (
        exp_model,
        exp_name,
        exp_rf,
        exp_qtm_eom,
        exp_ext,
        exp_has_fw,
    ) in expected_modules.items():
        assert slot in device_info.modules, f"Slot {slot} missing"
        mod = device_info.modules[slot]

        assert mod.manufacturer == "qblox", f"Slot {slot} manufacturer mismatch"
        assert mod.model == exp_model, f"Slot {slot} model mismatch"
        assert mod.serial == "00019_2426_027", f"Slot {slot} serial mismatch"
        assert mod.name == exp_name, f"Slot {slot} name mismatch"
        assert mod.is_rf is exp_rf, f"Slot {slot} is_rf mismatch"
        assert mod.qtm_eom is exp_qtm_eom, f"Slot {slot} qtm_eom mismatch"
        assert mod.is_extended_instrument is exp_ext, f"Slot {slot} is_extended mismatch"

        assert mod.sw_build is not None, f"Slot {slot} missing sw build"
        assert mod.sw_compat is not None, f"Slot {slot} missing sw compat"

        if exp_has_fw:
            assert mod.fw_build is not None, f"Slot {slot} missing fw build"
            assert mod.kmod_build is not None, f"Slot {slot} missing kmod build"
            assert mod.cfg_man_build is not None, f"Slot {slot} missing cfg_man build"
            assert mod.cfg_man_compat is not None, f"Slot {slot} missing cfg_man compat"

            assert mod.sw_build.version == (0, 0, 0), f"Slot {slot} wrong sw version"
            assert mod.sw_build.hash == 0x51D8517D, f"Slot {slot} wrong sw hash"
            assert mod.sw_build.dirty is True, f"Slot {slot} wrong sw dirty"

            assert mod.kmod_build.version == (0, 0, 0), f"Slot {slot} wrong kmod version"
            assert mod.kmod_build.hash == 0x51D8517D, f"Slot {slot} wrong kmod hash"
            assert mod.kmod_build.dirty is True, f"Slot {slot} wrong kmod dirty"

            assert mod.cfg_man_build.version == (0, 0, 0), f"Slot {slot} wrong cfg_man version"
            assert mod.cfg_man_build.hash == 0x51D8517D, f"Slot {slot} wrong cfg_man hash"
            assert mod.cfg_man_build.dirty is True, f"Slot {slot} wrong cfg_man dirty"

            assert mod.fw_build.version == (0, 0, 0), f"Slot {slot} wrong fw version"
            assert mod.fw_build.hash == 0x98F2499F, f"Slot {slot} wrong fw hash"
            assert mod.fw_build.dirty is False, f"Slot {slot} wrong fw dirty"
        else:
            assert mod.fw_build is None, f"Slot {slot} should not have fw build"
            assert mod.kmod_build is None, f"Slot {slot} should not have kmod build"
            assert mod.cfg_man_build is None, f"Slot {slot} should not have cfg_man build"

    generated_dict = device_info.to_dict()
    assert generated_dict["model"] == "cluster_mm"
    assert generated_dict["modules"]["1"]["model"] == "cluster_qcm"
    assert "fw" not in generated_dict["modules"]["10"]

    idn_str = device_info.to_idn()
    assert idn_str.startswith("qblox,cluster_mm,00019_2426_027,")
    assert "fwVersion=0.0.0" in idn_str

    # Check module IDN generation
    mod1_idn = device_info.modules["1"].to_idn()
    assert mod1_idn.startswith("qblox,cluster_qcm,00019_2426_027,")

    tup = device_info.to_tuple()
    assert tup[0] == "qblox"
    assert tup[1] == "cluster_mm"
    assert tup[4] is False
    assert isinstance(tup[8], tuple)
    assert "1" in tup[8]
