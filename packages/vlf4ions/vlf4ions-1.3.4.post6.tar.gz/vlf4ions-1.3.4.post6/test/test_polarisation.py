import vlf4ions.polarisation as polar
import numpy as np


def test_ellipseparams():

    # Synthetic data (matches the tests by Gross et al, although we flip their start phase to match the measured phase sign)
    # Without Nans because we don't have them in the data in real time
    amp_NS = np.array([1, 0.1])
    amp_EW = amp_NS
    phase_NS = np.array([0, 45])
    phase_EW = np.array([5, 53])

    start_phase = polar.EllipseParams(amp_NS, amp_EW, phase_NS, phase_EW)
    print(start_phase)

    assert (
        np.max(np.abs(start_phase + np.array([180, 127]))) < 5
    )  # We allow 5° because our declination is 45° and theirs 20°
