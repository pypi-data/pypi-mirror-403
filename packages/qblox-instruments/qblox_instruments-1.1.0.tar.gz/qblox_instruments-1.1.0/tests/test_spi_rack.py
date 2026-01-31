# ----------------------------------------------------------------------------
# Description    : SPI rack test script
# Git repository : https://gitlab.com/qblox/packages/software/qblox_instruments.git
# Copyright (C) Qblox BV (2021)
# ----------------------------------------------------------------------------


# -- include -----------------------------------------------------------------

import pytest
from qcodes.instrument import Instrument

from qblox_instruments import SpiRack
from qblox_instruments.native import DummySpiApi
from qblox_instruments.qcodes_drivers.spi_rack_modules import DummySpiModule

# -- fixtures ----------------------------------------------------------------


@pytest.fixture
def dummy_spi():
    spi = SpiRack("dummy_spi", "COM2", is_dummy=True)
    spi.add_spi_module(2, DummySpiModule)
    spi.add_spi_module(3, "dummy", "test_module")
    yield spi

    for instr_name in list(Instrument._all_instruments):
        try:
            inst = Instrument.find_instrument(instr_name)
            inst.close()
        except KeyError:
            pass


@pytest.fixture
def dummy_spi_with_d5a():
    spi = SpiRack("dummy_spi_with_d5a", "COM2", is_dummy=True)
    spi.add_spi_module(2, "D5a", "d5a_module", reset_voltages=True, is_dummy=True)
    yield spi

    for instr_name in list(Instrument._all_instruments):
        try:
            inst = Instrument.find_instrument(instr_name)
            inst.close()
        except KeyError:
            pass


@pytest.fixture
def dummy_spi_with_s4g():
    spi = SpiRack("dummy_spi_with_s4g", "COM2", is_dummy=True)
    spi.add_spi_module(2, "S4g", "s4g_module", reset_currents=True, is_dummy=True)
    yield spi

    for instr_name in list(Instrument._all_instruments):
        try:
            inst = Instrument.find_instrument(instr_name)
            inst.close()
        except KeyError:
            pass


# -- functions -----------------------------------------------------------------


def test_get_idn(dummy_spi):
    """
    Tests whether the get_idn correctly returns the idn. By comparing the
    values to what is defined in the dummy driver.
    """
    spi = dummy_spi
    idn = spi.get_idn()
    assert idn["manufacturer"] == "Qblox"
    assert idn["model"] == "SPI Rack"
    assert "device" in idn["firmware"]
    assert "driver" in idn["firmware"]
    assert "version" in idn["firmware"]["driver"]
    assert "build" in idn["firmware"]["driver"]
    assert "hash" in idn["firmware"]["driver"]
    assert "dirty" in idn["firmware"]["driver"]

    spi.close()


# ----------------------------------------------------------------------------
def test_battery(dummy_spi):
    """
    Test battery_voltages parameter. Test simply checks whether the driver
    returns the voltages defined in the dummy correctly. Implicitly, this
    test also tests whether the dummy driver can be instantiated successfully.
    And dummy modules can be added.
    """
    spi = dummy_spi

    batt = spi.battery_voltages()
    assert batt == DummySpiApi.BATTERY_LVLS

    spi.close()


# ----------------------------------------------------------------------------
def test_temperature(dummy_spi):
    """
    Tests if the temperature parameter returns a sensible value.
    """
    spi = dummy_spi

    temp = spi.temperature()
    assert temp == DummySpiApi.TEMPERATURE

    spi.add_spi_module(5, DummySpiModule)
    spi.add_spi_module(4, "dummy", "test_module_2")

    temp = spi.temperature()
    assert temp == DummySpiApi.TEMPERATURE

    spi.close()


# ----------------------------------------------------------------------------
def test_add_spi_module(dummy_spi):
    """
    "
    Tests adding an SPI module to the driver and setting/getting parameters
    on this module.
    """
    spi = dummy_spi
    spi.add_spi_module(5, DummySpiModule)
    spi.add_spi_module(6, "dummy", "test_module_2")

    spi.test_module_2.output(1.0)

    val = spi.test_module_2.output()
    assert val == 1.0

    spi.test_module_2.output(-1.0)

    val = spi.test_module_2.output()
    assert val == -1.0

    spi.close()


# ----------------------------------------------------------------------------
def test_set_dacs_zero(dummy_spi):
    """
    Tests the set_dacs_zero function by first setting values, then calling
    :meth:`set_dacs_zero` and then checking whether it is zero.
    """
    spi = dummy_spi

    spi.test_module.output(1.0)
    val = spi.test_module.output()
    assert val == 1.0

    spi.set_dacs_zero()

    val = spi.test_module.output()
    assert val == 0.0

    spi.test_module.output(-1.213)
    spi.set_dacs_zero()

    val = spi.test_module.output()
    assert val == 0.0

    spi.close()


# -- D5a tests -----------------------------------------------------------------
def test_d5a_voltage_set(dummy_spi_with_d5a):
    """
    Tests if the "voltage" qcodes parameter functions correctly.
    """
    spi = dummy_spi_with_d5a
    assert spi.d5a_module.dac4.voltage() == 0.0
    spi.d5a_module.dac4.voltage(1.0)
    assert spi.d5a_module.dac4.voltage() == 1.0


# ----------------------------------------------------------------------------
def test_d5a_span(dummy_spi_with_d5a):
    """
    Tests if the "span" qcodes parameter functions correctly.
    """
    spi = dummy_spi_with_d5a
    spi.d5a_module.dac4.span("range_4V_bi")
    assert spi.d5a_module.dac4.span() == "range_4V_bi"

    spi.d5a_module.dac4.span("range_4V_uni")
    assert spi.d5a_module.dac4.span() == "range_4V_uni"


# ----------------------------------------------------------------------------
def test_d5a_stepsize(dummy_spi_with_d5a):
    """
    Tests if the "stepsize" qcodes parameter functions correctly.
    """
    spi = dummy_spi_with_d5a
    assert pytest.approx(spi.d5a_module.dac12.stepsize()) == 3.0517578125e-05


# ----------------------------------------------------------------------------
def test_d5a_dac_channel(dummy_spi_with_d5a):
    """
    Tests if the "dac_channel" qcodes parameter functions correctly.
    """
    spi = dummy_spi_with_d5a
    assert spi.d5a_module.dac12.dac_channel() == 12


# ----------------------------------------------------------------------------
def test_d5a_set_dacs_zero(dummy_spi_with_d5a):
    """
    Tests if the `set_dacs_zero` function functions correctly.
    """
    spi = dummy_spi_with_d5a

    spi.d5a_module.dac4.voltage(3.0)
    assert spi.d5a_module.dac4.voltage() == 3.0
    spi.d5a_module.set_dacs_zero()
    assert spi.d5a_module.dac4.voltage() == 0.0


# -- S4g tests -----------------------------------------------------------------
def test_s4g_current_set(dummy_spi_with_s4g):
    """
    Tests if the "current" qcodes parameter functions correctly.
    """
    spi = dummy_spi_with_s4g
    assert spi.s4g_module.dac3.current() == 0.0
    spi.s4g_module.dac3.current(1.0e-3)
    assert spi.s4g_module.dac3.current() == 1.0e-3


# ----------------------------------------------------------------------------
def test_s4g_span(dummy_spi_with_s4g):
    """
    Tests if the "span" qcodes parameter functions correctly.
    """
    spi = dummy_spi_with_s4g
    spi.s4g_module.dac2.span("range_min_bi")
    assert spi.s4g_module.dac2.span() == "range_min_bi"

    spi.s4g_module.dac1.span("range_max_bi")
    assert spi.s4g_module.dac1.span() == "range_max_bi"


# ----------------------------------------------------------------------------
def test_s4g_stepsize(dummy_spi_with_s4g):
    """
    Tests if the "stepsize" qcodes parameter functions correctly.
    """
    spi = dummy_spi_with_s4g
    assert pytest.approx(spi.s4g_module.dac1.stepsize()) == 3.814697265625e-07


# ----------------------------------------------------------------------------
def test_s4g_dac_channel(dummy_spi_with_s4g):
    """
    Tests if the "dac_channel" qcodes parameter functions correctly.
    """
    spi = dummy_spi_with_s4g
    assert spi.s4g_module.dac1.dac_channel() == 1


# ----------------------------------------------------------------------------
def test_s4g_set_dacs_zero(dummy_spi_with_s4g):
    """
    Tests if the `set_dacs_zero` function functions correctly.
    """
    spi = dummy_spi_with_s4g

    spi.s4g_module.dac0.current(3.0e-3)
    assert spi.s4g_module.dac0.current() == 3.0e-3
    spi.s4g_module.set_dacs_zero()
    assert spi.s4g_module.dac0.current() == 0.0
