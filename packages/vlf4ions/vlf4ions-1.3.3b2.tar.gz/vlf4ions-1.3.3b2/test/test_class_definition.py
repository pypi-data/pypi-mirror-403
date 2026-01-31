import vlf4ions.class_definition as cd
import vlf4ions.manage_statefile as ms
import numpy as np
import os

import pandas as pd
import datetime as dt
from datetime import datetime

dirname = os.path.dirname(__file__)


def test_email_alert_update_body():
    test_alert = cd.email_alerts(
        "test_subject", "test_body", "test_sender", "test_password", ["test_recipients"]
    )
    test_alert.update_detection_body("NRK", 0)
    # print(test_alert.body)
    assert test_alert.body != "test_body"


# TODO: test send_email


def test_sliding_median():
    test_array = np.arange(6)
    res = cd.sliding_median(test_array, 3)

    assert all(res == [1.0, 2.0, 3.0, 4.0])


def test_craft_newsletter():

    # Define alert
    test = cd.email_alerts(
        "Test", "Placeholder", "fakesender", "fakepassword", "fakerecipients"
    )

    path = os.path.join(dirname, "Data/Test_flux.csv")
    flux, times, starts, ends = test.craft_newsletter(path, True)

    assert (
        test.body.count("\n") == 15
        and flux == [2, 5]
        and times == [2, 6]
        and starts == [1, 5]
        and ends == [3, 7]
    )


def test_two_hours_data():

    # Station
    st = cd.station("Test", 0, 0, 0, 0.01, ":00", orientation=0)
    st.p1 = 0
    Nancay = cd.receiver("NC", lat=47.3755933, lon=2.1944333, threshold=-1)

    # Paths
    path_to_data = os.path.join(dirname, "Data/")

    # Create breakpoint file (must have the date in the name, that's why we create
    # it each time we test the function)
    today = dt.datetime.now(
        dt.timezone.utc
    )  # The time zone is necessary to use get_sza later
    la_date = today.strftime("%Y_%m_%d")
    ms.get_lastbreakpoint("Test", la_date, path_to_data, check_yesterday=False)

    # Update breakpoint with synthetic data longer than two hours
    st.update_breakpoints(path_to_data, path_to_data, path_to_data, [], [], Nancay)

    # Remove created file
    filename = path_to_data + la_date + "_Test.csv"

    # Remove file if it exists
    if os.path.exists(filename):
        os.remove(filename)

    # The slope in the test file is exactly 1 for the past 9 minutes and 0 before
    # Since the Test station has been set with a threshold of 0.01, if the code
    # works, the detected slope should be 1 (because the data is longer than two
    # hours without a breakpoint). It thus should counts as a flare detection,
    # except we actually set quiet to be 1 manually.
    assert np.abs(st.p1 - 1) < 0.01 and st.quiet == 1
