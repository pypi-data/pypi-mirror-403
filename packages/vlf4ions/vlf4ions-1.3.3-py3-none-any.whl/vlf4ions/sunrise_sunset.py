#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  1 17:10:28 2025

@author: pteysseyre
"""

import pandas as pd
import datetime as dt
from datetime import timedelta, datetime
from pysolar.solar import get_altitude
import pytz
import numpy as np

""" This file deals with checking that we are in daytime.
It is based on previously computed sunrise and sunset times from https://nrc.canada.ca/en/research-development/products-services/software-applications/sun-calculator/

As a precaution, we define nighttime as between from one hour before sunset to one hour after sunrise.


History:
------------------

Updated in April 2025 to include calculation of the solar zenith angle


"""


def get_sza(today, lat, lon):
    """Returns the solar zenith angle (in rad) at the latitude/longitude given in input

    :param today: Datetime for the time of interest
    :param lat: Latitude of interest (in °)
    :param lon: Longitude of interest (in °)

    :return: sza, solar zenith angle (in rad)"""

    sza = float(90) - get_altitude(lat, lon, today)
    sza = sza * np.pi / 180

    return sza


def get_sunrise_sunset(today, path):
    """Returns the sunrise (civil + 1 hr) and sunset (civil - 1 hr) times (in UT)

    :param today: datetime (may only contain the year, month and day)
    :param path: path to the precomputed sunrise/sunset times

    :return: sunrise and sunset times for this day (in UT)"""

    # Must be an easier way to do this, but get the year, month, and dayofyear of today.
    doy = today - dt.datetime(today.year, 1, 1, 0, 0, 0, 0, pytz.UTC)
    doy = doy.days

    # Get the sunrise / sunset time for that particular day
    file_sunrise = pd.read_csv(path, header=1)

    sunrise = file_sunrise.iat[doy - 1, 3]
    sunrise = datetime.strptime(sunrise, "%H:%M") + timedelta(hours=1)
    sunrise = sunrise.time()

    sunset = file_sunrise.iat[doy - 1, 5]
    sunset = datetime.strptime(sunset, "%H:%M") - timedelta(hours=1)
    sunset = sunset.time()

    return sunrise, sunset


def check_if_daytime(today, path):
    """Check whether the current time is greater than the sunrise time and less than sunset
    for this particular station and day

    :param today: datetime (may only contain the year, month and day)
    :param path: path to the precomputed sunrise/sunset times

    :return: Boolean, if we are in daytime
    """

    sunrise, sunset = get_sunrise_sunset(today, path)

    return today.time() > sunrise and today.time() < sunset
