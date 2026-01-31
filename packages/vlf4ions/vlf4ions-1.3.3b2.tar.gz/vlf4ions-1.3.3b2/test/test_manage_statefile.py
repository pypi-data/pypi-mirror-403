import vlf4ions.manage_statefile as ms
import datetime as dt
from vlf4ions.class_definition import station
from datetime import datetime, timedelta
import os
import pandas as pd
import pytz
import glob

dirname = os.path.dirname(__file__)


def test_write_fluxestimation():

    today = dt.datetime(2000, 1, 1, 12, 3, 0, 0, pytz.UTC)
    path_to_files = os.path.join(dirname, "Results/")
    filename = path_to_files + "2000_01_01_test.csv"

    # Remove file if it exists
    if os.path.exists(filename):
        os.remove(filename)

    # Test file creation
    ms.write_fluxestimate(1e-5, 0, today, path_to_files, "test", 3)

    # Test adding new data
    today = dt.datetime(2000, 1, 1, 12, 5, 0, 0, pytz.UTC)
    ms.write_fluxestimate(1e-6, 1, today, path_to_files, "test", 4)

    # Read the file
    df = pd.read_csv(path_to_files + "2000_01_01_test.csv")
    first_line = df.iloc[0]
    second_line = df.iloc[1]

    assert (
        df.size == 8
        and first_line["Time (UT)"] == 12.05
        and second_line["Quiet"] == 1
        and second_line["Number of stations"] + first_line["Number of stations"] == 7
    )


def test_write_df():

    NRK = station("NRK", 56.2, -7.6, 37.5, 22.02, ":10", df=1.4136e-4, orientation=0)
    NAA = station("NAA", 51.6, -33.5, 24.0, 32.39, ":18", df=3.1128e-5, orientation=0)
    stations = [NRK, NAA]

    path_to_results = os.path.join(dirname, "Results/")

    # Remove all previous files
    filename = glob.glob(path_to_results + "*_df.csv")
    filename = max(filename, key=os.path.getctime)  # To get a filename and not a list

    # Remove file if it exists
    if os.path.exists(filename):
        os.remove(filename)

    ms.write_file_with_df(stations, path_to_results)

    # Read the file for TODAY (list of files needs to be reload)
    filename = glob.glob(path_to_results + "*_df.csv")
    filename = max(filename, key=os.path.getctime)  # To get a filename and not a list
    df = pd.read_csv(filename)
    first_line = df.iloc[0]

    assert df.size == 2 and first_line["NAA"] == 3.1128e-5


def test_manage_bp():

    path = os.path.join(dirname, "Results/")

    # Remove all previous files
    filename = glob.glob(path + "*Test_ms.csv")

    # Remove file if it exists
    for f in filename:
        if os.path.exists(f):
            os.remove(f)

    # Create parameters for test
    la_station = "Test_ms"

    # Get today's date in a good format
    today = dt.datetime.now(
        dt.timezone.utc
    )  # The time zone is necessary to use get_sza later
    la_date = today.strftime("%Y_%m_%d")

    # Quiet is False
    the_time, slope, amp, phase, quiet, DP = ms.get_lastbreakpoint(
        la_station, la_date, path, check_yesterday=False
    )

    # Write new breakpoint
    ms.write_newbreakpoint(la_station, la_date, path, 2, 2, 2, 2, 0, 2)

    # Get last breakpoint
    the_time_2, slope_2, amp_2, phase_2, quiet_2, DP_2 = ms.get_lastbreakpoint(
        la_station, la_date, path, check_yesterday=False
    )

    # Get last quiet breakpoint
    the_time_1, slope_1, amp_1, phase_1, quiet_1, DP_1 = ms.get_lastbreakpoint(
        la_station, la_date, path, quiet=True, check_yesterday=False
    )

    assert (
        (the_time == 0)
        and quiet == 1
        and quiet_1 == 1
        and quiet_2 == 0
        and slope_2 == 2
        and amp_2 == 2
        and phase_1 == 0
        and DP == 0
    )

def test_midnight_crossing():

    # Specifically tests the case when a flare happens across midnight

    path = os.path.join(dirname, "Results/")

    # Remove all previous files
    filename = glob.glob(path + "*Test_midnight.csv")

    # Remove file if it exists
    for f in filename:
        if os.path.exists(f):
            os.remove(f)

    # Create parameters for test
    la_station = "Test_midnight"

    # Get today's date in a good format
    today = dt.datetime.now(dt.timezone.utc)
    la_date = today.strftime("%Y_%m_%d")

    # Get yesterday as well
    yesterday = today - dt.timedelta(days=1)
    hier = yesterday.strftime("%Y_%m_%d")

    # Create file for 'yesterday'
    the_time, slope, amp, phase, quiet, DP = ms.get_lastbreakpoint(
        la_station, hier, path, check_yesterday=False
    )

    # Add a flare breakpoint
    ms.write_newbreakpoint(la_station, hier, path, 12, 12, 0, 0, 0, 38)

    # Create file for today
    the_time, slope, amp, phase, quiet, DP = ms.get_lastbreakpoint(
        la_station, la_date, path, check_yesterday=True
    )

    # Normally, there should be two lines in the new file, with yesterday's data

    # Get last quiet breakpoint for today
    the_time_q, slope, amp, phase, quiet, DP = ms.get_lastbreakpoint(
        la_station, la_date, path, check_yesterday=False, quiet=True
    )

    # Get last breakpoint for today
    the_time, slope, amp, phase, quiet, DP = ms.get_lastbreakpoint(
        la_station, la_date, path, check_yesterday=False, quiet=False
    )

    assert(the_time==-12 and the_time_q==-24)