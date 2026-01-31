#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 10:44:38 2024

@author: pteysseyre
"""

import numpy as np
import vlf4ions.sunrise_sunset as srst


def flags(amp_NS, amp_EW, previous_nb_points, today, path, this_receiver, phase):
    """Flags 1 if the antenna is down, 2 if the transmitter is down, 3 if it is nighttime

    :param amp_NS: Amplitude in the N/S direction
    :param amp_EW: Amplitude in the E/W direction
    :param previous_nb_points: Number of points read last time
    :param today: Datetime, instant of file reading
    :param path: path to the precomputed sunrise/sunset times
    :param this_receiver: receiver class instance
    :param phase: Phase, before any filtering

    :return: - flag: flag indicating the state of the transmitter/receiver
        - length_data: number of points read this time
        - data_last_min: median total amplitude over the last minute"""

    flag = 0
    data_last_min = 0
    length_data = min(
        len(amp_NS), len(amp_EW)
    )  # this is necessary as there may be one more point in amp_EW than amp_NS, as it is read later

    # Check that we are in daytime
    daytime = srst.check_if_daytime(today, path)

    if daytime:
        # Antenna down: the number of data points in the last written file stays the same
        if length_data == previous_nb_points:
            flag = 1
        else:
            previous_nb_points = length_data

            if length_data > 60:
                amp_NS = amp_NS[-60:]
                amp_EW = amp_EW[-60:]
            else:
                amp_NS = amp_NS[-length_data:]
                amp_EW = amp_EW[-length_data:]

            amp = np.sqrt(np.square(amp_NS) + np.square(amp_EW))
            data_last_min = np.median(amp)

        if (data_last_min < this_receiver.threshold and flag != 1) or np.abs(
            phase[-1] - phase[-2]
        ) > 20:

            # If the amplitude is too low, the station is not transmitting
            # If the phase is not well-decoded, the signal will be random and will vary greatly between two datapoints
            flag = 2
    else:
        flag = 3

    return flag, length_data, data_last_min
