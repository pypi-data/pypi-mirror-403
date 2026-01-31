import vlf4ions.read_files as rf
import os
import numpy as np

dirname = os.path.dirname(__file__)


def test_read_Narrowband():

    # Parameters
    la_date = "2024_05_02"
    la_station = "Test"
    path = os.path.join(dirname, "Data/")

    amp_NS, amp_EW, phase_NS, phase_EW, the_time = rf.read_Narrowband_postprocessing(
        la_date, la_station, path
    )

    errors = []

    # Check the time
    if not (
        np.size(the_time) == 86400
        and the_time[0] == 0
        and np.abs(the_time[1] - the_time[0] - 1 / 3600) < 0.0001
    ):
        errors.append("Read_files - Problem with the_time")

    print(amp_NS[50000])

    # Check other arrays
    if not (
        np.abs(amp_NS[50000] - 0.8791) < 0.01
        and np.abs(phase_NS[50000] + 104.6759) < 0.01
        and np.abs(amp_EW[50000] - 2.5119) < 0.01
        and np.abs(phase_EW[50000] - 83.4476) < 0.01
    ):
        errors.append("Read_files - Problem with the data")

    assert not errors, "errors occured:\n{}".format("\n".join(errors))
