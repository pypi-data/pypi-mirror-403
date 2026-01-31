from vlf4ions.flag import flags
import numpy as np
from datetime import datetime
import datetime as dt
import pytz
import os
from vlf4ions.class_definition import receiver

dirname = os.path.dirname(__file__)


def test_flags():

    # Synthetic data
    amp_NS = np.arange(1, 6, 1)
    amp_EW = amp_NS

    Nancay = receiver("NC", lat=47.3755933, lon=2.1944333, threshold=0.75)

    # Test in normal time
    previous_nb_points = 4
    today = dt.datetime(2000, 1, 1, 12, 3, 0, 0, pytz.UTC)
    path_to_files = os.path.join(dirname, "Data/DHO_sunrise_sunset.txt")

    flag_1, data_length_1, data_1 = flags(
        amp_NS, amp_EW, previous_nb_points, today, path_to_files, Nancay
    )

    # Expected data_1
    amp = np.sqrt(amp_NS**2 + amp_EW**2)
    data_1_exp = np.median(amp)

    # Test antenna down
    flag_2, data_length_2, data_2 = flags(
        amp_NS, amp_EW, data_length_1, today, path_to_files, Nancay
    )

    # Test nighttime
    night = dt.datetime(2000, 1, 1, 23, 0, 0, 0, pytz.UTC)
    amp_NS = np.ones((120, 1)) * 30
    amp_NS[0:60] = 0
    amp_EW = np.zeros((120, 1))

    flag_3, data_length_3, data_3 = flags(
        amp_NS, amp_EW, previous_nb_points, night, path_to_files, Nancay
    )

    # Test transmetter down
    Nancay.threshold = 400
    flag_4, data_length_4, data_4 = flags(
        amp_NS, amp_EW, previous_nb_points, today, path_to_files, Nancay
    )

    assert (
        (flag_1 == 0)
        and (flag_2 == 1)
        and (flag_3 == 3)
        and (flag_4 == 2)
        and (data_1 == data_1_exp)
        and (data_4 == 30)
    )
