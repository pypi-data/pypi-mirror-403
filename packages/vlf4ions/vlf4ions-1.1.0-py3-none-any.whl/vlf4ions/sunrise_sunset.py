#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  1 17:10:28 2025

@author: pteysseyre
"""

import pandas as pd
from datetime import datetime, timedelta


""" This file deals with checking that we are in daytime.
It is based on previously computed sunrise and sunset times from https://nrc.canada.ca/en/research-development/products-services/software-applications/sun-calculator/

As a precaution, we define nighttime as between from one hour before sunset to one hour after sunrise.

"""

def get_sunrise_sunset(today, path):
    
    # Must be an easier way to do this, but get the year, month, and dayofyear of today.
    doy = today - datetime(year = today.year, month = 1, day = 1)
    doy = doy.days
    
    # Get the sunrise / sunset time for that particular day
    file_sunrise = pd.read_csv(path, header = 1)
    
    sunrise = file_sunrise.iat[doy - 1, 3]
    sunrise = datetime.strptime(sunrise, '%H:%M') + timedelta(hours=1)
    sunrise = sunrise.time()
    
    sunset = file_sunrise.iat[doy - 1, 5]
    sunset = datetime.strptime(sunset, '%H:%M')  - timedelta(hours=1)
    sunset = sunset.time()
    
    return sunrise, sunset

    
def check_if_daytime(today, path):
    
    """ Check whether the current time is greater than the sunrise time and less than sunset
    for this particular station and day """
    
    sunrise, sunset = get_sunrise_sunset(today, path)
  
    return (today.time() > sunrise and today.time() < sunset)