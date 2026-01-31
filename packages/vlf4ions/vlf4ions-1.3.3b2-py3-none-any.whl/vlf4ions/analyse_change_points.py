#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  7 14:28:49 2025

@author: pteysseyre
"""

import numpy as np

def analyse_breakpoint(
    current_time,
    current_p1,
    amp,
    phase,
    the_time,
    quiet,
    quiet_phase,
    quiet_amp,
    last_time,
    last_p1,
    detection_threshold,
    quiet_p1,
    quiet_breakpoint,
):
    """This is the part of the code that will decide if the  breakpoint is a
    flare signature or not.

    Several cases can occur:

        1) This is the beginning of a flare.
        2) This is a flare maximum
        3) This is a quiet point: this is either a slight positive slope, a negative slope after a quiet breakpoint, or a negative slope after a flare has decayed by more than half of its increase
        4) This is a flare decay, with a negative slope and the phase has not gone down by more than half of its increase.

    :param current_time: Time (in UT) of the last data reading
    :param current_p1: Slope of the new breakpoints
    :param amp: median amplitude measured over the last minute
    :param phase: phase data, since the beginning of the file or for the last two hours
    :param the_time: time-array, must match the one for phase
    :param quiet: status of the last breakpoint. If quiet==1, the last breakpoint was a quiet one, if not it was a flare time
    :param quiet_phase: phase at the last quiet breakpoint
    :param quiet_amp: amplitude at the last quiet breakpoint
    :param last_time: time of the last breakpoint OR two hours before if the last breakpoint was too long ago
    :param last_p1: Last breakpoint slope
    :param detection_threshold: attribute of the station class, slope above which we consider that it is flare time
    :param quiet_p1: slope of the last quiet breakpoint
    :param quiet_breakpoint: time of the last quiet breakpoint

    :return: - quiet_now (is 1 if the new breakpoint is considered to be quiet)
        - prev_timedecay which is the predicted time to decay (in UT)
        - DP_now (increase of phase (in °), compared to what the value of the phase should have been)
        - DA (value of the amplitude increase compared to last quiet amp)

    History:
    ----------------------
    - Written in February 2025
    - Revised in June 2025 to change the way DP was computed

    """
    # TODO: Think about the flares happening in a very fast sucession
    # Init: most of what is returned will not be systematically useful
    prev_timedecay = 0.0
    quiet_now = 0

    # Changed in June 2025 (to avoid having negatives DP)
    # DP_now = phase[-1] - quiet_phase
    # Now the DP is computed using the last quiet breakpoint slope

    # TO CORRECT later if needed
    if quiet_p1 < 0:
        quiet_p1 = 0

    phase_nowifquiet = quiet_phase + quiet_p1 * (current_time - quiet_breakpoint)
    DP_now = phase[-1] - phase_nowifquiet

    DA = amp - quiet_amp

    if current_p1 > 0:

        if current_p1 < detection_threshold:

            if quiet == 1:  # This is a quiet time
                quiet_now = 1
                DP_now = 0
                DA = 0

            else:  # That's either a flare max OR a flare that has decayed

                # We look for the phase maximum to get DP
                the_time, phase = _keep_between(
                    phase, the_time, last_time, current_time
                )
                ind_max = np.argmax(phase)
                DP = phase[ind_max] - phase_nowifquiet
                time_max = the_time[ind_max]

                if DP_now < DP / 2:  # The flare has already decayed
                    quiet_now = 1
                    DP_now = 0

                else:  # This is the max of the flare
                    quiet_now = 0
                    prev_1min = DP
                    prev_5min = DP
        else:
            # This is a flare, but everything has already been done
            quiet_now = 0

    else:  # This is either quiet time, or a flare's decay

        if quiet:  # Last breakpoint is quiet
            quiet_now = True
            DP_now = 0

        else:  # Last breakpoint was a flare decay

            if last_p1 > 0:  # Last breakpoint was a flare onset

                # We look for the phase maximum to get DP
                the_time, phase = _keep_between(
                    phase, the_time, last_time, current_time
                )
                ind_max = np.argmax(phase)
                DP = phase[ind_max] - quiet_phase
                time_max = the_time[ind_max]

                # We estimate the decay time assuming that the trend is
                # constant & the decay linear
                prev_timedecay = -DP / (2 * current_p1) + time_max

            else:

                # Check if the flare has decayed
                # (lost more than half its increase)
                ### TODO: change for Ne or abs

                # We look for the phase maximum to get DP
                the_time, phase = _keep_between(
                    phase, the_time, last_time, current_time
                )
                ind_max = np.argmax(phase)
                DP = phase[ind_max] - phase_nowifquiet
                time_max = the_time[ind_max]

                if DP_now < DP / 2:  # The flare has ended
                    quiet_now = True
                    DP_now = 0

                else:  # The flare is ongoing but we can update our previsions
                    prev_timedecay = 1 / current_p1 * (DP / 2 - DP_now) + the_time[-1]

    return (quiet_now, prev_timedecay, DP_now, DA)


def _keep_between(data, the_time, time_inf, time_sup):
    """This is just a short bit of code to constrain the data between
    time_inf & time_sup

    :param data: data to be constrained
    :param the_time: time-array (the length must be the same as data)
    :param time_inf: Lowest limit to constrain the data array
    :param time_sup: Upper limit to constran the data array

    :return: the_time, new time-array constained between `time_inf` and `time_sup`
    :return: data, new data array constained between `time_inf` and `time_sup`"""

    if len(data) != len(the_time):

        print("Careful, lengths do not match - keep_between")

    else:

        ind_inf = np.argmin(np.abs(the_time - time_inf))
        ind_sup = np.argmin(np.abs(the_time - time_sup))

        the_time = the_time[ind_inf:ind_sup]
        data = data[ind_inf:ind_sup]

        return the_time, data
