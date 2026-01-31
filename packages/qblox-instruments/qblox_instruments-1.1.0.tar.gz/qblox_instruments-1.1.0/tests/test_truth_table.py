# ----------------------------------------------------------------------------
# Description    : TruthTable test script
# Git repository : https://gitlab.com/qblox/packages/software/qblox_instruments.git
# Copyright (C) Qblox BV (2025)
# ----------------------------------------------------------------------------

import warnings

import pytest

from qblox_instruments import TruthTable
from qblox_instruments.qcodes_drivers.truth_table import ChannelMeasurement, Condition


@pytest.mark.parametrize(
    "channel, measurement",
    [
        (0, "digital"),
        (5, "count"),
    ],
    ids=["digital", "count"],
)
def test_single_condition(channel, measurement):
    # Create a truth table object from a configuration
    config = [
        {
            "conditions": [{"channel": channel, "measurement": measurement, "level": "low"}],
            "trigger": 3,
        },
        {
            "conditions": [{"channel": channel, "measurement": measurement, "level": "mid"}],
            "trigger": 5,
        },
        {
            "conditions": [{"channel": channel, "measurement": measurement, "level": "high"}],
            "trigger": 7,
        },
    ]
    tt_from_config = TruthTable.from_config(config)

    # Create a truth table object manually
    tt_manual = TruthTable()
    tt_manual.add_conditions([Condition(ChannelMeasurement(channel, measurement), "low")], 3)
    tt_manual.add_conditions([Condition(ChannelMeasurement(channel, measurement), "mid")], 5)
    tt_manual.add_conditions([Condition(ChannelMeasurement(channel, measurement), "high")], 7)

    # Expected LUT
    expected_lut = {"src": [{"ch": channel, "cfg": measurement}], "lut": [3, 5, 7, 0]}

    assert tt_from_config.lut == expected_lut
    assert tt_manual.lut == expected_lut
    assert tt_from_config.lut == tt_manual.lut


@pytest.mark.parametrize(
    "config, expected_lut",
    [
        (
            # 2 conditions config
            [
                {
                    "conditions": [
                        {"channel": 0, "measurement": "count", "level": "low"},
                        {"channel": 1, "measurement": "digital", "level": "mid"},
                    ],
                    "trigger": 3,
                },
                {
                    "conditions": [
                        {"channel": 0, "measurement": "count", "level": "mid"},
                        {"channel": 1, "measurement": "digital", "level": "high"},
                    ],
                    "trigger": 5,
                },
                {
                    "conditions": [
                        {"channel": 0, "measurement": "count", "level": "high"},
                        {"channel": 1, "measurement": "digital", "level": "low"},
                    ],
                    "trigger": 7,
                },
            ],
            # 2 conditions expected LUT
            {
                "src": [{"ch": 0, "cfg": "count"}, {"ch": 1, "cfg": "digital"}],
                "lut": [0, 0, 7, 0, 3, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0],
            },
        ),
        (
            # 3 conditions config
            [
                {
                    "conditions": [
                        {"channel": 0, "measurement": "digital", "level": "low"},
                        {"channel": 1, "measurement": "count", "level": "mid"},
                        {"channel": 2, "measurement": "digital", "level": "high"},
                    ],
                    "trigger": 3,
                },
                {
                    "conditions": [
                        {"channel": 0, "measurement": "digital", "level": "mid"},
                        {"channel": 1, "measurement": "count", "level": "high"},
                        {"channel": 2, "measurement": "digital", "level": "low"},
                    ],
                    "trigger": 5,
                },
                {
                    "conditions": [
                        {"channel": 0, "measurement": "digital", "level": "high"},
                        {"channel": 1, "measurement": "count", "level": "low"},
                        {"channel": 2, "measurement": "digital", "level": "mid"},
                    ],
                    "trigger": 7,
                },
            ],
            # 3 conditions expected LUT
            {
                "src": [
                    {"ch": 0, "cfg": "digital"},
                    {"ch": 1, "cfg": "count"},
                    {"ch": 2, "cfg": "digital"},
                ],
                "lut": [0] * 9 + [5] + [0] * 8 + [7] + [0] * 17 + [3] + [0] * 27,
            },
        ),
        (
            # 4 conditions config
            [
                {
                    "conditions": [
                        {"channel": 0, "measurement": "digital", "level": "low"},
                        {"channel": 1, "measurement": "count", "level": "mid"},
                        {"channel": 2, "measurement": "digital", "level": "high"},
                        {"channel": 3, "measurement": "count", "level": "low"},
                    ],
                    "trigger": 3,
                },
                {
                    "conditions": [
                        {"channel": 0, "measurement": "digital", "level": "mid"},
                        {"channel": 1, "measurement": "count", "level": "high"},
                        {"channel": 2, "measurement": "digital", "level": "low"},
                        {"channel": 3, "measurement": "count", "level": "mid"},
                    ],
                    "trigger": 5,
                },
                {
                    "conditions": [
                        {"channel": 0, "measurement": "digital", "level": "high"},
                        {"channel": 1, "measurement": "count", "level": "low"},
                        {"channel": 2, "measurement": "digital", "level": "mid"},
                        {"channel": 3, "measurement": "count", "level": "high"},
                    ],
                    "trigger": 7,
                },
            ],
            # 4 conditions expected LUT
            {
                "src": [
                    {"ch": 0, "cfg": "digital"},
                    {"ch": 1, "cfg": "count"},
                    {"ch": 2, "cfg": "digital"},
                    {"ch": 3, "cfg": "count"},
                ],
                "lut": [0] * 36 + [3] + [0] * 36 + [5] + [0] * 72 + [7] + [0] * 109,
            },
        ),
    ],
    ids=["2 conditions", "3 conditions", "4 conditions"],
)
def test_multi_condition(config, expected_lut):
    tt_from_config = TruthTable.from_config(config)

    # Create a truth table object manually
    tt_manual = TruthTable()
    for entry in config:
        conditions = [
            Condition(ChannelMeasurement(cond["channel"], cond["measurement"]), cond["level"])
            for cond in entry["conditions"]
        ]
        tt_manual.add_conditions(conditions, entry["trigger"])

    assert tt_from_config.lut == expected_lut
    assert tt_manual.lut == expected_lut
    assert tt_from_config.lut == tt_manual.lut


def test_def_trg():
    def_trg = 1
    # Create a truth table object from a configuration
    config = [
        {
            "conditions": [
                {"channel": 0, "measurement": "count", "level": "low"},
                {"channel": 1, "measurement": "digital", "level": "mid"},
            ],
            "trigger": 3,
        },
        {
            "conditions": [
                {"channel": 0, "measurement": "count", "level": "mid"},
                {"channel": 1, "measurement": "digital", "level": "high"},
            ],
            "trigger": 5,
        },
        {
            "conditions": [
                {"channel": 0, "measurement": "count", "level": "high"},
                {"channel": 1, "measurement": "digital", "level": "low"},
            ],
            "trigger": 7,
        },
    ]
    tt_from_config = TruthTable.from_config(config, default_trigger_address=def_trg)

    # Create a truth table object manually
    tt_manual = TruthTable(default_trigger_address=def_trg)
    tt_manual.add_conditions(
        [
            Condition(ChannelMeasurement(0, "count"), "low"),
            Condition(ChannelMeasurement(1, "digital"), "mid"),
        ],
        3,
    )
    tt_manual.add_conditions(
        [
            Condition(ChannelMeasurement(0, "count"), "mid"),
            Condition(ChannelMeasurement(1, "digital"), "high"),
        ],
        5,
    )
    tt_manual.add_conditions(
        [
            Condition(ChannelMeasurement(0, "count"), "high"),
            Condition(ChannelMeasurement(1, "digital"), "low"),
        ],
        7,
    )

    # Expected LUT
    expected_lut = {
        "src": [{"ch": 0, "cfg": "count"}, {"ch": 1, "cfg": "digital"}],
        "lut": [1, 1, 7, 1, 3, 1, 1, 1, 1, 5, 1, 1, 1, 1, 1, 1],
    }

    assert tt_from_config.lut == expected_lut
    assert tt_manual.lut == expected_lut
    assert tt_from_config.lut == tt_manual.lut


def test_conflict():
    # Create a truth table object from a configuration
    config = [
        {
            "conditions": [
                {"channel": 0, "measurement": "count", "level": "low"},
                {"channel": 1, "measurement": "digital", "level": "mid"},
            ],
            "trigger": 3,
        },
        {
            "conditions": [
                {"channel": 2, "measurement": "count", "level": "low"},
            ],
            "trigger": 5,
        },
    ]

    with pytest.raises(ValueError) as e:
        TruthTable.from_config(config)

    assert str(e.value) == (
        "Conflict while setting LUT entry to trigger address 5.\n"
        "Condition (channel0_count_low && channel1_digital_mid && channel2_count_low) "
        "is already set to trigger address 3."
    )


def test_conflict_overwrite():
    # Create a truth table object from a configuration
    config = [
        {
            "conditions": [
                {"channel": 0, "measurement": "count", "level": "low"},
                {"channel": 1, "measurement": "digital", "level": "mid"},
            ],
            "trigger": 3,
        },
        {
            "conditions": [
                {"channel": 2, "measurement": "count", "level": "low"},
            ],
            "trigger": 5,
        },
    ]

    with warnings.catch_warnings(record=True) as w:
        TruthTable.from_config(config, overwrite_conflict=True)

    assert len(w) == 1
    assert issubclass(w[0].category, UserWarning)
    assert str(w[0].message) == (
        "Conflict while setting LUT entry to trigger address 5.\n"
        "Condition (channel0_count_low && channel1_digital_mid && channel2_count_low) "
        "is already set to trigger address 3.\n"
        "Overwriting with trigger address 5."
    )


def test_invalid_channel():
    expected_error = "Invalid channel '8'. Channel must be in range 0...7"

    # Create a truth table object from a configuration
    with pytest.raises(ValueError) as e:
        config = [
            {
                "conditions": [
                    {"channel": 8, "measurement": "digital", "level": "low"},
                ],
                "trigger": 3,
            }
        ]
        TruthTable.from_config(config)

    assert str(e.value) == expected_error

    # Create a truth table object manually
    with pytest.raises(ValueError) as e:
        tt_manual = TruthTable()
        tt_manual.add_conditions([Condition(ChannelMeasurement(8, "digital"), "low")], 3)

    assert str(e.value) == expected_error


def test_invalid_measurement():
    expected_error = "Invalid measurement type 'analog'. Valid options: ('count', 'digital')"

    # Create a truth table object from a configuration
    with pytest.raises(ValueError) as e:
        config = [
            {"conditions": [{"channel": 0, "measurement": "analog", "level": "low"}], "trigger": 3}
        ]
        TruthTable.from_config(config)

    assert str(e.value) == expected_error

    # Create a truth table object manually
    with pytest.raises(ValueError) as e:
        tt_manual = TruthTable()
        tt_manual.add_conditions([Condition(ChannelMeasurement(0, "analog"), "low")], 3)

    assert str(e.value) == expected_error


def test_invalid_level():
    expected_error = "Invalid level 'superhigh'. Valid options: ('low', 'mid', 'high', 'invalid')"

    # Create a truth table object from a configuration
    with pytest.raises(ValueError) as e:
        config = [
            {
                "conditions": [{"channel": 0, "measurement": "digital", "level": "superhigh"}],
                "trigger": 3,
            }
        ]
        TruthTable.from_config(config)

    assert str(e.value) == expected_error

    # Create a truth table object manually
    with pytest.raises(ValueError) as e:
        tt_manual = TruthTable()
        tt_manual.add_conditions([Condition(ChannelMeasurement(0, "digital"), "superhigh")], 3)

    assert str(e.value) == expected_error


def test_invalid_trigger_address():
    expected_error = "Invalid trigger address '16'. Trigger address must be in range 1...15"

    # Create a truth table object from a configuration
    with pytest.raises(ValueError) as e:
        config = [
            {
                "conditions": [{"channel": 0, "measurement": "digital", "level": "low"}],
                "trigger": 16,
            }
        ]
        TruthTable.from_config(config)

    assert str(e.value) == expected_error

    # Create a truth table object manually
    with pytest.raises(ValueError) as e:
        tt_manual = TruthTable()
        tt_manual.add_conditions([Condition(ChannelMeasurement(0, "digital"), "low")], 16)

    assert str(e.value) == expected_error


def test_invalid_default_trigger_address():
    expected_error = (
        "Invalid default trigger address '16'. Default trigger address must be in range 0...15"
    )

    # Create a truth table object from a configuration
    with pytest.raises(ValueError) as e:
        config = [
            {
                "conditions": [
                    {"channel": 0, "measurement": "digital", "level": "low"},
                ],
                "trigger": 3,
            }
        ]
        TruthTable.from_config(config, default_trigger_address=16)

    assert str(e.value) == expected_error

    # Create a truth table object manually
    with pytest.raises(ValueError) as e:
        tt_manual = TruthTable(default_trigger_address=16)
        tt_manual.add_conditions([Condition(ChannelMeasurement(0, "digital"), "low")], 3)

    assert str(e.value) == expected_error


def test_invalid_trigger_address_amount():
    expected_error = (
        "Trigger address 9 cannot be added. "
        "It exceeds the maximum number of trigger addresses (4). "
        "Current trigger addresses: {0, 3, 5, 7, 9}"
    )

    # Create a truth table object from a configuration
    with pytest.raises(ValueError) as e:
        config = [
            {
                "conditions": [{"channel": 0, "measurement": "digital", "level": "low"}],
                "trigger": 3,
            },
            {
                "conditions": [{"channel": 0, "measurement": "digital", "level": "mid"}],
                "trigger": 5,
            },
            {
                "conditions": [{"channel": 0, "measurement": "digital", "level": "high"}],
                "trigger": 7,
            },
            {
                "conditions": [{"channel": 0, "measurement": "digital", "level": "invalid"}],
                "trigger": 9,
            },
        ]
        TruthTable.from_config(config)

    assert str(e.value) == expected_error

    # Create a truth table object manually
    with pytest.raises(ValueError) as e:
        tt_manual = TruthTable()
        tt_manual.add_conditions([Condition(ChannelMeasurement(0, "digital"), "low")], 3)
        tt_manual.add_conditions([Condition(ChannelMeasurement(0, "digital"), "mid")], 5)
        tt_manual.add_conditions([Condition(ChannelMeasurement(0, "digital"), "high")], 7)
        tt_manual.add_conditions([Condition(ChannelMeasurement(0, "digital"), "invalid")], 9)

    assert str(e.value) == expected_error


def test_invalid_input_src_amount():
    expected_error = (
        "Only 4 distinct inputs are allowed. "
        "Current inputs: ["
        "ChannelMeasurement(channel=0, measurement='digital'), "
        "ChannelMeasurement(channel=1, measurement='count'), "
        "ChannelMeasurement(channel=2, measurement='digital'), "
        "ChannelMeasurement(channel=3, measurement='count'), "
        "ChannelMeasurement(channel=4, measurement='digital')"
        "]"
    )

    # Create a truth table object from a configuration
    with pytest.raises(ValueError) as e:
        config = [
            {
                "conditions": [
                    {"channel": 0, "measurement": "digital", "level": "low"},
                    {"channel": 1, "measurement": "count", "level": "mid"},
                    {"channel": 2, "measurement": "digital", "level": "high"},
                    {"channel": 3, "measurement": "count", "level": "low"},
                    {"channel": 4, "measurement": "digital", "level": "mid"},
                ],
                "trigger": 3,
            }
        ]
        TruthTable.from_config(config)

    assert str(e.value) == expected_error

    # Create a truth table object manually
    with pytest.raises(ValueError) as e:
        tt_manual = TruthTable()
        tt_manual.add_conditions(
            [
                Condition(ChannelMeasurement(0, "digital"), "low"),
                Condition(ChannelMeasurement(1, "count"), "mid"),
                Condition(ChannelMeasurement(2, "digital"), "high"),
                Condition(ChannelMeasurement(3, "count"), "low"),
                Condition(ChannelMeasurement(4, "digital"), "mid"),
            ],
            3,
        )

    assert str(e.value) == expected_error
