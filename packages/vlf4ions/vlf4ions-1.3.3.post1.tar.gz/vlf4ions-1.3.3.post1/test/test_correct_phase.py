import vlf4ions.correct_phase as cp
import datetime as dt
from vlf4ions.class_definition import station
import os
import numpy as np

dirname = os.path.dirname(__file__)


def test_compute_df():

    # Required parameters
    date_inf = dt.datetime(2024, 5, 1)
    date_sup = dt.datetime(2024, 5, 5)
    NRK = station("NRK", 56.2, -7.6, 37.5, 22.02, ":10", df=1.4136e-4, orientation=0)
    path_to_files = os.path.join(dirname, "/Data/")
    file_endings = ["_100A", "_100B", "_101A", "_101B"]
    epsilon = 5

    df = cp.compute_df(date_inf, date_sup, NRK, path_to_files, file_endings, epsilon)

    assert np.abs(df - 1.3672e-4) < 0.1e-4
