#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 10:29:16 2024

@author: pteysseyre
"""

import numpy as np
import datetime as dt
from datetime import datetime, timedelta  # To get today's date
import vlf4ions.read_files as rf


def correctionphase(station, phase, the_time):
    """Completely corrects the phase in real time the phase so that all phase jumps from -180° to 180° are corrected, and the phase detrended

    :param station: station class instance
    :param phase: phase data (in °)
    :param the_time: time-array in UT (or at least in hr)

    :return: phase_corr, corrected phase data
    """

    phase_corr = correctionphaseparDw(station, phase, the_time)

    return phase_corr


def unwrap_moco(Data_In, UnwrapNumber):
    """Originally written by M. Cohen in Matlab. Unwraps 'Data_in',
    by compensating any jumps more than UnwrapNumer/2

    :param Data_In: Data to unwrap
    :param UnwrapNumber: Value of the jumps to compensate

    :return: Unwrapped data and position of the jumps"""

    # Remove all NaN point and reconcatanate
    Data_NaN = np.isnan(Data_In)
    Data_In_NonNaN = Data_In[Data_NaN == False]
    Indices_NonNaN = np.arange(0, np.size(Data_In_NonNaN))

    # Take differential
    Data_In_NonNaN_Diff = np.diff(Data_In_NonNaN)

    # Identify points where signal jumps by more than unwrap/2 threshold
    Indices_NonNaN = Indices_NonNaN[0:-1]
    JumpIndices = Indices_NonNaN[np.abs(Data_In_NonNaN_Diff) > UnwrapNumber / 2]
    Data_In_NonNaN_Diff_Jumps = Data_In_NonNaN_Diff[JumpIndices]

    # Round jumps to nearest value of unwrap number
    Data_In_NonNaN_Diff_Jumps = (
        np.round(Data_In_NonNaN_Diff_Jumps / UnwrapNumber) * UnwrapNumber
    )

    # Integrates jump to original concatanated vector. Add 1 to indices to reference later point of two differential elements
    Indices_NonNaN_Jump = Indices_NonNaN[JumpIndices]

    # Go back to original version with the NaNs and create derivative
    Data_In_Diff_Jumps = Data_In * 0
    Data_In_Diff_Jumps[np.isnan(Data_In_Diff_Jumps)] = 0
    Data_In_Diff_Jumps[Indices_NonNaN_Jump] = Data_In_NonNaN_Diff_Jumps

    # Integrates to get the function that needs to be substracted
    Data_In_Jumps = np.cumsum(Data_In_Diff_Jumps)

    # Substract from original
    Data_Out = Data_In - Data_In_Jumps

    # nb_jumps_station = np.size(JumpIndices)

    return Data_Out, Data_In_Jumps[-1]


def correctionphaseparDw(station, phase, the_time):
    """Corrects the phase by compensating for the phase detrend induced by the
    transmitter frequency not being exactly stable

    :param station: station class instance
    :param phase: phase data array (in °)
    :param the_time: time-array (in hr or UT)

    :return: phase_corr (unwrapped and detrended phase) and jumps (position of the 90° jumps)
    """

    Deltaf = station.df

    Deltaw = 2 * np.pi * Deltaf

    phase_un = np.unwrap(phase, 85)

    phase_corr = phase_un + (Deltaw * the_time * 3600) * 180 / np.pi

    # For now (03/24) because there is both a 90° uncertainty on the measurements and the modelling
    # we choose to keep the phase between 90 and 180° for quiet daytime conditions

    return phase_corr


def compute_df(date_inf, date_sup, station, path_to_files, file_endings, epsilon):
    """Compute the value of df for a specific station over a specified time period

    :param date_inf: Datetime object, date from which we want to compute df
    :param date_sup: Datetime object, date before which we want to compute df
    :param station: Station class instance
    :param path_to_files: Path to the data files
    :param file_endings: List of string. Endings of the files for amp_NS, phase_NS, amp_EW and phase_EW in that order
    :param epsilon: Maximum phase jump (in °) that we accept in average from one day to the next

    :return: df value for the station

    """

    # Compute number of days between date_inf and date_sup
    delta = date_sup - date_inf
    nb_days = delta.days

    # We check that there is enough data
    if nb_days < 2:
        print("Not enough days to compute df")

    # At the start, df is the one given in `station`

    df_inf = -1e-2
    df_sup = 1e-2  # in Hz

    eps = epsilon * 2  # Initialisation
    loop_counter = 0

    while eps > epsilon:  # This is the bissection method

        loop_counter += 1

        eps = _loop_for_compute_df(
            nb_days, date_inf, station, path_to_files, file_endings
        )

        if np.abs(eps) < epsilon or loop_counter > 1e4:
            return station.df

        elif eps < 0:  # df is too small

            df_inf = station.df
            station.df = (station.df + df_sup) / 2

        else:  # df is too large

            df_sup = station.df
            station.df = (station.df + df_inf) / 2

    return station.df


def _loop_for_compute_df(nb_days, date_inf, station, path_to_files, file_endings):
    """This is just a short function to make compute_df easier to read

    :param nb_days: Number of days on which to loop
    :param date_inf: Datetime object, date from which we want to compute df
    :param station: Station class instance
    :param path_to_files: Path to the data files
    :param file_endings: List of string. Endings of the files for amp_NS, phase_NS, amp_EW and phase_EW in that order

    :return: Average jumps between days on the time-period inputted
    """

    all_jumps = 0  # This will be the quantity to minimise
    last_phase_value = 0  # Last value of the phase on the last day

    days_with_data = nb_days

    for i in range(nb_days):

        # Day of interest, in the correct format
        today = date_inf + dt.timedelta(days=i)
        la_date = today.strftime("%Y_%m_%d")

        # Read the file

        try:
            amp_NS, amp_EW, phase_NS, phase_EW, the_time = (
                rf.read_Narrowband_postprocessing(
                    la_date, station.name, path_to_files, file_endings
                )
            )

            if station.orientation == 1:
                phase = phase_EW
            else:
                phase = phase_NS
            phase, jumps = correctionphaseparDw(station, phase, the_time)

            if i > 0:  # We do not make this calculation for the first day

                all_jumps += phase[-1] - last_phase_value

            last_phase_value = phase[-1]  # We keep track of the last value of the day

        except:  # There is no data for this day

            print("Data not available on " + la_date)
            last_phase_value = np.nan
            days_with_data = days_with_data - 1

    all_jumps = all_jumps / (
        days_with_data - 1
    )  # There are nb_days - 1 midnight crossings

    return all_jumps
