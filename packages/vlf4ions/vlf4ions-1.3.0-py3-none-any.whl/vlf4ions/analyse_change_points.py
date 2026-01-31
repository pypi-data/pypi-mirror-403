#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  7 14:28:49 2025

@author: pteysseyre
"""

import numpy as np


def analyse_breakpoint(current_time, current_p1, amp, phase,
                       the_time, quiet, quiet_phase, quiet_amp, last_time,
                       last_p1, detection_threshold, quiet_p1, quiet_breakpoint):

    """This is the part of the code that will decide if the  breakpoint is a
    flare signature or not.

    Several cases can occur:

        1) This is the beginning of a flare. In this case, we can estimate the
        current X-ray strength and electron density by taking as a reference
        the last 'quiet' breakpoint. We can also estimate the state of the
        ionosphere in 1 and 5 minassuming that the trend doesn't change

        2) This is the first brekapoint to signal a flare decay. We can
        estimate the current X-ray flux, electron density, and give an estimate
        of when things will have decreased to half of their increase

        3) This is a quiet point: this is either a slight positive slope, a
        negative slope after a quiet breakpoint, or a negative
        slope after a flare has decayed by more than half of its increase

        4) This is a flare decay, but this is not the first detection and the
        flare has not gone down by more than half of its increase. We can
        update the estimated X-ray flux and Ne, and estimate the new time to
        the end of the flare

        Parameters:
        ---------------------------

        - la_station, phase: the transmitter, recorded & corrected phase (in °)
          since beginning of file
        - amp: median over the last minute of amplitude data.
        - detection_threshold: Standard deviation of slopes in quiet times
        - the_time: time-array. Dimension should match  phase
        - pathtoCSVfiles: path to the CSV files obtained with the LMP model
        - current_p1, current_time : current breakpoint slope detected and
            time  of detection
        - last_p1, last_time: last  breakpoint slope and detection time
        - quiet: is True if the last brealpoint detected was a quiet
            breakpoint. Is False otherwise (flares)
        - quiet_phase, quiet_amp: last read phase & amp (to avoid reading it
            and looking for it)
        - quiet_p1: slope measured for the last quiet point, used to compute
            DP
        - quiet_breakpoint: time of the last computed breakpoint

        Outputs:
        ---------------------------

        - quiet_now : is True if the current breakpoint is in quiet time
        - flux : estimated X-ray flux and confidence interval
        - prev_1min : estimated Ne in 1 min
        - prev_5min : estimated Ne in 5 min
        - prev_timedecay : estimated time of decay


        IMPORTANT NOTE:
        --------------------------
        1) Right now (Feb. 2025), we are concentrating on the phase (Ne in code
        is phase). However, we can for a second step concentrate on the
        electron density at an altitude of 70 km; moreover, the interesting
        quantity for us is the HF absorption. Thus, in the future, the HF
        absorption should be computed and the time of the flare's decay, as
        well as the previsions for the next minutes or so should be based
        on this quantity instead.
    
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
    phase_nowifquiet = quiet_phase + quiet_p1*(current_time - quiet_breakpoint)
    DP_now = phase[-1] - phase_nowifquiet

    DA = amp - quiet_amp

    if current_p1 > 0:

        if (current_p1 < detection_threshold):

            if (quiet == 1):  # This is a quiet time
                quiet_now = 1
                DP = 0
                DA = 0

            else:  # That's either a flare max OR a flare that has decayed

                # We look for the phase maximum to get DP
                the_time, phase = _keep_between(phase, the_time, last_time,
                                                current_time)
                ind_max = np.argmax(phase)
                DP = phase[ind_max] - phase_nowifquiet
                time_max = the_time[ind_max]

                if DP_now < DP/2:  # The flare has already decayed
                    quiet_now = 1
                    DP = 0
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

        else:  # Last breakpoint was a flare decay

            if last_p1 > 0:  # Last breakpoint was a flare onset

                ### TODO: Use Ne instead of phase

                # We look for the phase maximum to get DP
                the_time, phase = _keep_between(phase, the_time, last_time, 
                                                current_time)
                ind_max = np.argmax(phase)
                DP = phase[ind_max] - quiet_phase
                time_max = the_time[ind_max]

                # We estimate the decay time assuming that the trend is 
                # constant & the decay linear
                prev_timedecay = -DP/(2*current_p1) + time_max

            else:

                # Check if the flare has decayed 
                # (lost more than half its increase)
                ### TODO: change for Ne or abs

                # We look for the phase maximum to get DP
                the_time, phase = _keep_between(phase, the_time, last_time,
                                                 current_time)
                ind_max = np.argmax(phase)
                DP = phase[ind_max] - phase_nowifquiet
                time_max = the_time[ind_max]

                if DP_now < DP/2:  # The flare has ended
                    quiet_now = True

                else:  # The flare is ongoing but we can update our previsions
                    prev_timedecay = 1/current_p1*(DP/2 - DP_now) 
                    + the_time[-1]



    return (quiet_now, prev_timedecay, DP_now, DA)



def _keep_between(data, the_time, time_inf, time_sup):

    """ This is just a short bit of code to constrain the data between 
    time_inf & time_sup """

    if len(data) != len(the_time):

        print('Careful, lengths do not match - keep_between')

    else:

        ind_inf = np.argmin(np.abs(the_time - time_inf))
        ind_sup = np.argmin(np.abs(the_time - time_sup))

        the_time = the_time[ind_inf:ind_sup]
        data = data[ind_inf:ind_sup]

        return the_time, data












