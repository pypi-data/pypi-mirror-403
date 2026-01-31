import vlf4ions.sunrise_sunset as srst
import vlf4ions as vlf
import datetime as dt
from datetime import datetime
import os 
import pytz


def test_sunrise_sunset():

    dirname = os.path.dirname(__file__)
    la_station = 'NWC'
    today = dt.datetime(2025, 5, 13, 14, 28, 22, 323128, pytz.UTC)
    path = os.path.join(dirname, la_station + '_sunrise_sunset.txt')

    sunrise, sunset = srst.get_sunrise_sunset(today, path)

    assert((sunrise == dt.time(3, 48)) and (sunset == dt.time(12, 47)))

def test_check_if_daytime():

    dirname = os.path.dirname(__file__)
    la_station = 'NWC'
    path = os.path.join(dirname, la_station + '_sunrise_sunset.txt')
    today = dt.datetime(2025, 5, 13, 3, 47, 0, 0, pytz.UTC)

    sunrise, sunset = srst.get_sunrise_sunset(today, path)

    flag = 0 # List of flags, 0 if in daytime, 3 in nighttime

    # Times to check
    today = dt.datetime(2025, 5, 13, 3, 48, 0, 0, pytz.UTC)
    if not srst.check_if_daytime(today, path):
        flag += 3
    today = dt.datetime(2025, 5, 13, 3, 49, 0, 0, pytz.UTC)
    if not srst.check_if_daytime(today, path):
        flag += 3
    today = dt.datetime(2025, 5, 13, 12, 46, 0, 0, pytz.UTC)
    if not srst.check_if_daytime(today, path):
        flag += 3
    today = dt.datetime(2025, 5, 13, 12, 47, 0, 0, pytz.UTC)
    if not srst.check_if_daytime(today, path):
        flag += 3

    assert(flag == 6)  

# Not sure I need to test the get_sza function, since it only calls the get_altitude function from the pysolar library.



