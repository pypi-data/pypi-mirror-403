# ----------------------------------------------------------------------------
# Description    : Configuration manager test script
# Git repository : https://gitlab.com/qblox/packages/software/qblox_instruments.git
# Copyright (C) Qblox BV (2020)
# ----------------------------------------------------------------------------
import sys
from io import StringIO
from unittest.mock import Mock

import pytest

from qblox_instruments import Cluster, ConfigurationManager
from qblox_instruments.build import DeviceInfo
from qblox_instruments.cfg_man.probe import ConnectionInfo
from qblox_instruments.cfg_man.update_file import _is_qblox_os
from qblox_instruments.types import ClusterType, TypeHandle
from tests.helpers.cluster_dummy_config import DUMMY_CFG


@pytest.fixture(name="stdout")
def make_stdout():
    new_stdout = StringIO()
    sys.stdout = new_stdout
    yield new_stdout
    sys.stdout = sys.__stdout__


@pytest.fixture(name="cfg_man")
def make_cfg_man(mocker):
    mocker.patch("qblox_instruments.cfg_man.main.ScpiConnection")
    with ConfigurationManager(
        ConnectionInfo(
            "0.0.0.0",
            "scpi",
            ("0.0.0.0", 5026),
            "0",
            "0.0.0.0/24",
            "0.0.0.0",
            Mock(),
            {c.name.lower() for c in ClusterType if c != ClusterType._CLUSTER_MM},
        )
    ) as cfg_man:
        yield cfg_man


@pytest.fixture
def dummy_cluster_json_descr():
    dummy_cluster = Cluster("test", None, dummy_cfg=DUMMY_CFG)
    descr = dummy_cluster.get_json_description()
    yield descr
    dummy_cluster.close()


def test_help(stdout):
    """
    Test getting help using commandline interface.

    Parameters
    ----------
    stdout
        StringIO connected to sys.stdout

    """
    try:
        ConfigurationManager.cmd_line("")
        raise AssertionError("Should have failed.")
    except RuntimeError:
        pass


def test_version(stdout):
    """
    Test getting the configuration manager version using commandline interface.

    Parameters
    ----------
    stdout
        StringIO connected to sys.stdout

    """
    ConfigurationManager.cmd_line(["-V"])


def test_cfg_man_qblox_os_migration_all_qblox_os(cfg_man, dummy_cluster_json_descr):
    descr = dummy_cluster_json_descr
    # Pretend all modules are on qblox-os
    qblox_os_slots = []
    pulsar_os_slots = []
    excluded_slots = set()
    for slot, mod_info in descr["modules"].items():
        qblox_os_slots.append(int(slot))
        mod_info["sw"]["version"] = [1, 0, 0]

    device = DeviceInfo.from_dict(descr)

    with pytest.raises(
        ValueError,
        match="Migration update requires at least one Pulsar OS module to migrate. All modules are "
        "running qblox-os.",
    ):
        cfg_man._check_qblox_os_migration_compat(
            qblox_os_slots, pulsar_os_slots, excluded_slots, device
        )


@pytest.mark.parametrize("version", [[0, 13, 0], [1, 1, 1]])
def test_qrc_qsm_always_qblox_os(dummy_cluster_json_descr, version):
    descr = dummy_cluster_json_descr

    for slot, mod_info in descr["modules"].items():
        if DUMMY_CFG[slot] in (ClusterType.CLUSTER_QRC, ClusterType.CLUSTER_QSM):
            mod_info["sw"]["version"] = version

    device = DeviceInfo.from_dict(descr)
    for slot, mod_info in device.modules.items():
        if DUMMY_CFG[slot] in (ClusterType.CLUSTER_QRC, ClusterType.CLUSTER_QSM):
            assert _is_qblox_os(mod_info.sw_build.version, TypeHandle(mod_info.model))


def test_cfg_man_qblox_os_migration_mix_pulsar_and_qrc_qsm(cfg_man, dummy_cluster_json_descr):
    descr = dummy_cluster_json_descr
    # Pretend all modules are on pulsar-os (except QRC/QSM)
    qblox_os_slots = []
    pulsar_os_slots = []
    excluded_slots = set()
    for slot, mod_info in descr["modules"].items():
        if DUMMY_CFG[slot] in (ClusterType.CLUSTER_QRC, ClusterType.CLUSTER_QSM):
            qblox_os_slots.append(int(slot))
            mod_info["sw"]["version"] = [0, 13, 0]
        else:
            pulsar_os_slots.append(int(slot))
            mod_info["sw"]["version"] = [0, 12, 1]

    device = DeviceInfo.from_dict(descr)

    cfg_man._check_qblox_os_migration_compat(
        qblox_os_slots, pulsar_os_slots, excluded_slots, device
    )
    assert excluded_slots == set(qblox_os_slots)


def test_cfg_man_qblox_os_migration_mix_pulsar_and_qblox(cfg_man, dummy_cluster_json_descr):
    descr = dummy_cluster_json_descr
    qblox_os_slots = []
    pulsar_os_slots = []
    excluded_slots = set()
    for slot, mod_info in descr["modules"].items():
        # Just make half the slots qblox-os, half Pulsar OS
        if int(slot) % 2:
            qblox_os_slots.append(int(slot))
            mod_info["sw"]["version"] = [1, 0, 0]
        else:
            pulsar_os_slots.append(int(slot))
            mod_info["sw"]["version"] = [0, 12, 1]

    device = DeviceInfo.from_dict(descr)

    cfg_man._check_qblox_os_migration_compat(
        qblox_os_slots, pulsar_os_slots, excluded_slots, device
    )
    assert excluded_slots == set(qblox_os_slots)


def test_cfg_man_qblox_os_migration_pulsar_013(cfg_man, dummy_cluster_json_descr):
    descr = dummy_cluster_json_descr
    qblox_os_slots = []
    pulsar_os_slots = []
    excluded_slots = set()
    for slot, mod_info in descr["modules"].items():
        # Just make half the slots qblox-os, half Pulsar OS
        if int(slot) % 2:
            qblox_os_slots.append(int(slot))
            mod_info["sw"]["version"] = [1, 0, 0]
        else:
            pulsar_os_slots.append(int(slot))
            mod_info["sw"]["version"] = [0, 13, 0]

    device = DeviceInfo.from_dict(descr)

    slot_string = ", ".join(f"slot {slot}" for slot in pulsar_os_slots)

    with pytest.raises(
        ValueError,
        match=f"Cannot migrate modules running version 0.13. Modules in {slot_string} are running "
        "version 0.13. Please downgrade these modules to version 0.12.1 first before attempting to "
        "migrate.",
    ):
        cfg_man._check_qblox_os_migration_compat(
            qblox_os_slots, pulsar_os_slots, excluded_slots, device
        )
