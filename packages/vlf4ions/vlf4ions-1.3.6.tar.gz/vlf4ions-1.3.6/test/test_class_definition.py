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
        test.body.count("\n") == 17
        and flux == [2.0, 5.0]
        and times == [2.0, 6.0]
        and starts == [1.0, 5.0]
        and ends == [3.0, 7.0]
    )


def test_craft_newsletter_quiet():
    """Test the newsletter when there is no detection"""

    # Define alert
    test = cd.email_alerts(
        "Test", "Placeholder", "fakesender", "fakepassword", "fakerecipients"
    )

    path = os.path.join(dirname, "Data/Test_flux_quiet.csv")
    flux, times, starts, ends = test.craft_newsletter(path, True)

    assert len(flux) == 0 and test.body.count("\n") == 5 and test.body.count("!") == 1


def test_good_format_time():

    test = cd.email_alerts(
        "Test", "Placeholder", "fakesender", "fakepassword", "fakerecipients"
    )

    time_1 = 13
    time_1str = test._good_format_time(time_1)

    time_2 = 13.20
    time_2str = test._good_format_time(time_2)

    time_3 = 13.21
    time_3str = test._good_format_time(time_3)

    time_4 = 13.75
    time_4str = test._good_format_time(time_4)

    assert (
        time_1str == "13:00"
        and time_2str == "13:12"
        and time_3str == "13:13"
        and time_4str == "13:45"
    )


def test_craft_newsletter_quiet():
    """Test the newsletter when there is no detection"""

    # Define alert
    test = cd.email_alerts(
        "Test", "Placeholder", "fakesender", "fakepassword", "fakerecipients"
    )

    path = os.path.join(dirname, "Data/Test_flux_quiet.csv")
    flux, times, starts, ends = test.craft_newsletter(path, True)

    assert len(flux) == 0 and test.body.count("\n") == 5 and test.body.count("!") == 1


def test_good_format_time():

    test = cd.email_alerts(
        "Test", "Placeholder", "fakesender", "fakepassword", "fakerecipients"
    )

    time_1 = 13
    time_1str = test._good_format_time(time_1)

    time_2 = 13.20
    time_2str = test._good_format_time(time_2)

    time_3 = 13.21
    time_3str = test._good_format_time(time_3)

    time_4 = 13.75
    time_4str = test._good_format_time(time_4)

    assert (
        time_1str == "13:00"
        and time_2str == "13:12"
        and time_3str == "13:13"
        and time_4str == "13:45"
    )


def test_two_hours_data():

    errors=[]

    # Station
    st = cd.station("Test", 0, 0, 0, 0.01, ":00", sza_threshold=200)

    # NOTE: we put sza threshold too high to avoid not being able to run the tests in nighttime

    st.p1 = 0
    Nancay = cd.receiver("NC", lat=47.3755933, lon=2.1944333, threshold=-1)
    alert_antenna = cd.email_alerts("", "", "", "", "")

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
    st.update_breakpoints(
        path_to_data, path_to_data, path_to_data, alert_antenna, [], Nancay
    )

    if np.abs(st.p1 - 1) > 0.5 or st.quiet != 1:

        # The slope in the test file is exactly 1 for the past 9 minutes and 0 before
        # Since the Test station has been set with a threshold of 0.01, if the code
        # works, the detected slope should be 1 (because the data is longer than two
        # hours without a breakpoint). It thus should counts as a flare detection,
        # except we actually set quiet to be 1 manually.
        # Because of all the noise I added to the synthetic files, we allow 0.5°/hr error on the slope
        errors.append('Error in test_two_hours data')

    # Remove created file
    filename = path_to_data + la_date + "_Test.csv"

    # Remove file if it exists
    if os.path.exists(filename):
        os.remove(filename)

    # Redo the same, but now we have an error in the last five minutes
    last_time_problem = today.hour + today.minute - 5/60
    st.last_time_problem = last_time_problem

    ms.get_lastbreakpoint("Test", la_date, path_to_data, check_yesterday=False)

    # Update breakpoint with synthetic data longer than two hours
    st.update_breakpoints(
        path_to_data, path_to_data, path_to_data, alert_antenna, [], Nancay)
    
    if np.abs(st.p1) > 0.5:

        errors.append('Problem with test_two_hours: case when there is a problem in the last few minutes')


    # assert no error message has been registered, else print messages
    assert not errors, "errors occured:\n{}".format("\n".join(errors))
