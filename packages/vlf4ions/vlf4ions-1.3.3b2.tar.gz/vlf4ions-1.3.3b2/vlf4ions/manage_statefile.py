#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 21 10:16:58 2025

@author: pteysseyre
"""

""" Manages the file where the breakpoints and quiet amplitude and phase are written."""

import os.path
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import datetime as dt


def get_lastbreakpoint(la_station, la_date, path, quiet=False, check_yesterday=True):
    """Read the value of the last breakpoint, such as the time of detection, the slope, and the associated amplitude and phase.
    If quiet is True, it returns the values for the last quiet breakpoint.
    If there were no breakpoints today, return a series of zeros and create the file

    :param la_station: Call-sign of the station of interest
    :param la_date: Date of interest (e.g. '2023_11_05')
    :param path: path to where the results will be stored
    :param quiet: Boolean, is True if we want the last quiet breakpoint, False otherwise (default: False)
    :param check_yesterday: Boolean. If True, will get the last breakpoint of the previous day if needed (for file initialisation)

    :return: Last time, slope, amplitude, phase, quiet and DP of the last breakpoint."""

    # Read the last breakpoint value OR create a new file if it is the first of the day
    # If there are no lines yet in the file, write header, using the last breakpoint of the previous day
    if not os.path.isfile(path + la_date + "_" + la_station + ".csv"):

        today = datetime.strptime(la_date, "%Y_%m_%d")

        if check_yesterday:
            try:
                yesterday = today - timedelta(days=1)
                yesterday = yesterday.strftime("%Y_%m_%d")
                last_bp_t, last_bp_s, last_bp_a, last_bp_p, last_bp_q, last_bp_d = (
                    get_lastbreakpoint(
                        la_station, yesterday, path, check_yesterday=False
                    )
                )

                if last_bp_q == 1: # Last breakpoint was quiet
                    data = [[last_bp_t - 24, last_bp_s, last_bp_a, last_bp_p, last_bp_q, last_bp_d]]

                else: # Last breakpoint was not quiet, but we also need the last quiet breakpoint
                    quiet_bp_t, quiet_bp_s, quiet_bp_a, quiet_bp_p, quiet_bp_q, quiet_bp_d = (
                        get_lastbreakpoint(
                            la_station, yesterday, path, quiet=True, check_yesterday=False
                        )
                    )
                    data = [[quiet_bp_t-24, quiet_bp_s, quiet_bp_a, quiet_bp_p, quiet_bp_q, quiet_bp_d], [last_bp_t - 24, last_bp_s, last_bp_a, last_bp_p, last_bp_q, last_bp_d]]


            except:  # There were no data yesterday OR there were no quiet breakpoints yesterday
                data = [[0, 0, 0, 0, 1, 0]]

        else:  # If we don't check yesterday (to avoid infinite recursive loop)
            data = [[0, 0, 0, 0, 1, 0]]

        df = pd.DataFrame(
            data,
            columns=[
                "Time (UT)",
                "Slope (deg/hr)",
                "Amplitude (pT)",
                "Phase (deg)",
                "Quiet",
                "DP",
            ],
        )
        df.to_csv(path + la_date + "_" + la_station + ".csv", index=False)

    else:
        df = pd.read_csv(path + la_date + "_" + la_station + ".csv")

    if quiet:
        df = df.loc[df["Quiet"] == 1]

    last_bp = df.iloc[-1]

    return (
        last_bp["Time (UT)"],
        last_bp["Slope (deg/hr)"],
        last_bp["Amplitude (pT)"],
        last_bp["Phase (deg)"],
        last_bp["Quiet"],
        last_bp["DP"],
    )


def write_newbreakpoint(la_station, la_date, path, time_now, p1, amp, phase, quiet, DP):
    """Update the state file by adding the new detected breakpoint.
    Note: because the function get_lastbreakpoint has been called earlier in the Realtimescript, there
    is no need to check that a file exist, or to create a new one

    :param la_station: Station call-sign
    :param la_date: Date of interest
    :param path: path to where the results are stored
    :param time_now: time when the data was last read
    :param p1: Last breakpoint slope
    :param amp: Median amplitude over the last minute
    :param phase: Median phase over the last minute
    :param quiet: Boolean, is True if we are in quiet time, False otherwise
    :param DP: Phase increase compared to its quiet time value"""

    # Read the state file
    df = pd.read_csv(path + la_date + "_" + la_station + ".csv")

    # Add the new values
    df.loc[len(df)] = [time_now, p1, amp, phase, quiet, DP]

    # Write the new file
    df.to_csv(path + la_date + "_" + la_station + ".csv", index=False)

    return


def write_fluxestimate(best_guess, quiet, today, path, ending, nb_stations_on):
    """Writes in a file the best guess for the flux estimation and informations
    about how it was computed. This includes the DP values for each stations as
    well as the 'quiet' flag for each station.

    :param best_guess: Best estimate for the X-ray flux
    :param quiet: quiet value. It is proportional to the number of transmitters for which a quiet value was detected. If it is equal to 0, all transmitters have detected a flare time
    :param today: Datetime object, time in UT
    :param path: Destination of the file
    :param ending: Ending of the file name created
    :param nb_stations_on: Number of working station at the time"""

    time_now = today.hour + today.minute / 60
    la_date = today.strftime("%Y_%m_%d")

    # Data to write
    data = [time_now, best_guess, quiet, nb_stations_on]

    # Read the last breakpoint value OR create a new file if it is the first of the day
    # If there are no lines yet in the file, write header, using the last breakpoint of the previous day
    if not os.path.isfile(path + la_date + "_" + ending + ".csv"):

        df = pd.DataFrame(
            [data],
            columns=["Time (UT)", "Best estimate", "Quiet", "Number of stations"],
        )
        df.to_csv(path + la_date + "_" + ending + ".csv", index=False)

    else:

        # Read the state file
        df = pd.read_csv(path + la_date + "_" + ending + ".csv")

        # Add the new values
        df.loc[len(df)] = data

        # Write the new file
        df.to_csv(path + la_date + "_" + ending + ".csv", index=False)

    return


def write_file_with_df(stations, path_to_result):
    """Write a file with the current df values for each station

    :param stations: List of stations recorded
    :param path_to_result: Path to the file which will be written"""

    data = []
    names = []

    for st in stations:

        names.append(st.name)
        data.append(st.df)

    # Get date (for file name)
    today = dt.datetime.now(
        dt.timezone.utc
    )  # The time zone is necessary to use get_sza later
    la_date = today.strftime("%Y_%m_%d")

    # Write file
    df = pd.DataFrame([data], columns=names)
    df.to_csv(path_to_result + la_date + "_df.csv", index=False)

    return
