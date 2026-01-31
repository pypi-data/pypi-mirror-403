#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 10:44:38 2024

@author: pteysseyre
"""

import numpy as np
import vlf4ions.sunrise_sunset as srst


def flags(amp, previous_nb_points, today, this_station, this_receiver, phase):
    """Flags 1 if the antenna is down, 2 if the transmitter is down, 3 if it is nighttime

    :param amp: Amplitude (pT)
    :param previous_nb_points: Number of points read last time
    :param today: Datetime, instant of file reading. Must be timezone-aware
    :param this_station: station class instance
    :param this_receiver: receiver class instance
    :param phase: Phase, before any filtering

    :return: - flag: flag indicating the state of the transmitter/receiver
        - length_data: number of points read this time
        - data_last_min: median total amplitude over the last minute"""

    flag = 0
    data_last_min = 0
    length_data = min(
        len(amp), len(phase)
    )  # this is necessary as there may be one more point in the phase than the amplitude, as it is read later

    # Check that we are in daytime
    daytime, sza = srst.is_daytime(
        this_station, this_receiver, today, this_station.sza_threshold
    )

    if daytime:
        # Antenna down: the number of data points in the last written file stays the same
        if length_data == previous_nb_points:
            flag = 1
        else:
            previous_nb_points = length_data

            if length_data > 60:
                amp = amp[-60:]
            else:
                amp = amp[-length_data:]

            data_last_min = np.median(amp)

        if (data_last_min < this_receiver.threshold and flag != 1) or np.abs(
            phase[-1] - phase[-2]
        ) > 20:

            # If the amplitude is too low, the station is not transmitting
            # If the phase is not well-decoded, the signal will be random and will vary greatly between two datapoints
            flag = 2
    else:
        flag = 3

    # We update the mean solar zenith angle in the path
    this_station.sza = sza

    return flag, length_data, data_last_min
