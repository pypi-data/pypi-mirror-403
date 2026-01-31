from vlf4ions.flag import flags
import numpy as np
from datetime import datetime
import datetime as dt
import pytz
import os
from vlf4ions.class_definition import receiver, station

dirname = os.path.dirname(__file__)


def test_flags():

    # Synthetic data
    amp_NS = np.arange(1, 6, 1)
    amp_EW = amp_NS
    phase = amp_NS

    Nancay = receiver("NC", lat=47.3755933, lon=2.1944333, threshold=0.75)
    this_station = station('Test', 47, 2, 24, 1e4, reading_time=':00', sza_threshold= 85)

    # Test in normal time
    previous_nb_points = 4
    today = dt.datetime(2000, 1, 1, 12, 3, 0, 0, pytz.UTC)

    flag_1, data_length_1, data_1 = flags(
        amp_NS, previous_nb_points, today, this_station, Nancay, phase
    )

    # Test random phase
    phase_disturbed = np.arange(1, 400, 30)
    flag_phase, data_length_phase, data_phase = flags(
        amp_NS,
        previous_nb_points,
        today,
        this_station,
        Nancay,
        phase_disturbed,
    )

    # Expected data_1
    amp = amp_NS
    data_1_exp = np.median(amp)

    # Test antenna down
    flag_2, data_length_2, data_2 = flags(
        amp_NS, data_length_1, today, this_station, Nancay, phase
    )

    # Test nighttime
    # All the previous tests were in daytime, this one is in nighttime
    # (I only need to check that this detects nighttime, daytime has already been detected)
    night = dt.datetime(2000, 1, 1, 23, 0, 0, 0, pytz.UTC)
    amp_NS = np.ones((120, 1)) * 30
    amp_NS[0:60] = 0
    amp_EW = np.zeros((120, 1))
    amp = np.sqrt(amp_NS**2 + amp_EW**2)

    flag_3, data_length_3, data_3 = flags(
        amp, previous_nb_points, night, this_station, Nancay, phase
    )

    # Test transmetter down
    today = dt.datetime(2000, 1, 1, 12, 3, 0, 0, pytz.UTC)
    Nancay.threshold = 400
    flag_4, data_length_4, data_4 = flags(
        amp, previous_nb_points, today, this_station, Nancay, phase
    )

    assert (
        (flag_1 == 0)
        and (flag_2 == 1)
        and (flag_3 == 3)
        and (flag_4 == 2)
        and (data_1 == data_1_exp)
        and (data_4 == 30)
        and (flag_phase == 2)
    )
