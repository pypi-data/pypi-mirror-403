"""Computes the polarisation parameters to avoid correcting the phase"""

import numpy as np


def EllipseParams(amp_NS, amp_EW, phase_NS, phase_EW):
    """Computes the polarisation parameters
    From Gross et al, 2018 et their Matlab code sent in private communication

    :param amp_NS, amp_EW: Amplitude in the NS and EW direction
    :param phase_NS, phase_EW: Phase in the NS and EW direction

    :returns: Phi_start, start phase. The other parameters are computed, but only this one is needed
    """

    # Delete the last value of some of the arrays so that everything has the same length
    # (This problem arises when an additional antenna measurement is made between the time when the first file is read and the last one)
    min_length = np.min(
        [np.size(amp_NS), np.size(amp_EW), np.size(phase_NS), np.size(phase_EW)]
    )
    amp_NS = amp_NS[0:min_length]
    amp_EW = amp_EW[0:min_length]
    phase_NS = phase_NS[0:min_length]
    phase_EW = phase_EW[0:min_length]

    # 1 - Compute the declination angle from transmitter to geomagnetic north
    # To do this at first approach, tan(theta) = amp_NS/amp_EW
    theta = np.arctan(amp_EW[-1] / amp_NS[-1])  # in radians

    # Convert to complex quantities
    b_NS = amp_NS * np.exp(1j * phase_NS * np.pi / 180)
    b_EW = amp_EW * np.exp(1j * phase_EW * np.pi / 180)

    # Rotate the data so that it points towards the transmitter
    R = np.zeros((2, 2))
    R[0, 0] = np.cos(theta + np.pi / 2)
    R[0, 1] = np.sin(theta + np.pi / 2)
    R[1, 0] = -np.sin(theta + np.pi / 2)
    R[1, 1] = np.cos(theta + +np.pi / 2)
    rot_xy = R @ np.vstack((b_NS, -b_EW))
    by = rot_xy[0, :]  # Br
    bx = rot_xy[1, :]  # Btheta

    # Compute ellipse parameters

    # Convert bx & by to real quantities
    bx_abs = np.abs(bx)
    by_abs = np.abs(by)
    bx_phi = np.angle(bx)
    by_phi = np.angle(by)

    # Equations 6 to 8 of Gross et al., 2018
    gamma = by_abs / bx_abs
    phi_0 = by_phi - bx_phi  # Angle between the two vectors
    tau_rad = 0.5 * np.arctan((2 * gamma) / (1 - gamma**2) * np.cos(phi_0))
    # Convert tau_rad to be correct (uncertainty on arctan)
    i_convert = by_abs > bx_abs
    tau_rad[i_convert] = tau_rad[i_convert] - np.sign(tau_rad[i_convert]) * np.pi / 2
    tau = tau_rad * 180 / np.pi  # Degrees

    # Ellipticity angle (Equation 9)
    chi = 0.5 * np.arcsin(2 * gamma / (1 + gamma**2) * np.sin(phi_0))
    chi = chi * 180 / np.pi  # Degrees

    # B_major and B_minor (Equation 11)
    b_major = by * (np.sin(tau_rad)) + bx * np.cos(tau_rad)
    b_minor = -np.sin(tau_rad) * bx + np.cos(tau_rad) * by

    # Start phase (Equation 12)
    start_phase = np.angle(b_major)
    start_phase = start_phase * 180 / np.pi  # Degree

    return start_phase
