# ----------------------------------------------------------------------------
# Description    : Predistortion tests
# Git repository : https://gitlab.com/qblox/packages/software/qblox_instruments.git
# Copyright (C) Qblox BV (2025)
# ----------------------------------------------------------------------------


# -- include -----------------------------------------------------------------

import numpy as np
import pytest

from qblox_instruments.simulations import (
    exponential_overshoot_correction,
    fir_correction,
    get_filter_delay,
    get_impulse_response,
)

# -- functions ---------------------------------------------------------------


def rel_tol() -> float:
    return 1e-7


def test_get_filter_delay():
    assert get_filter_delay(2, False) == pytest.approx(1.6e-7, rel=rel_tol())
    assert get_filter_delay(2, True) == pytest.approx(2.4e-7, rel=rel_tol())
    assert get_filter_delay(3, False) == pytest.approx(2.1e-7, rel=rel_tol())
    assert get_filter_delay(3, True) == pytest.approx(2.9e-7, rel=rel_tol())


def test_exponential_overshoot_correction():
    np.testing.assert_allclose(
        exponential_overshoot_correction(np.array([0.1, 0.2, 0.3]), 0.1, 1.5),
        np.array([0.09486583, 0.19222986, 0.2908765]),
        rtol=rel_tol(),
    )
    np.testing.assert_allclose(
        exponential_overshoot_correction(np.array([0.4, 0.5, 0.6]), 0.2, 2.0),
        np.array([0.35147755, 0.45843903, 0.56266139]),
        rtol=rel_tol(),
    )


def test_fir_correction():
    np.testing.assert_allclose(
        fir_correction(np.array([0.1, 0.2, 0.3]), np.array([0.01, 0.02])),
        np.array([0.001, 0.004, 0.007]),
        rtol=rel_tol(),
    )
    np.testing.assert_allclose(
        fir_correction(np.array([0.4, 0.5]), np.array([0.03, 0.04, 0.05])),
        np.array([0.012, 0.031]),
        rtol=rel_tol(),
    )


def test_get_impulse_response():
    np.testing.assert_allclose(
        get_impulse_response(3, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8),
        np.array([0.73204205, 0.19819139, 0.05228996]),
        rtol=rel_tol(),
    )
    np.testing.assert_allclose(
        get_impulse_response(3, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, np.array([1.0, 2.0])),
        np.array([0.73204205, 1.66227549, 0.44867275]),
        rtol=rel_tol(),
    )
