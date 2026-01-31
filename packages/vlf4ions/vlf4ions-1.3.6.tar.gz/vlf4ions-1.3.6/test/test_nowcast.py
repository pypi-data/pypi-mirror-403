import vlf4ions.forecast_nowcast as fn
import vlf4ions.class_definition as cd
import vlf4ions.compute_electron_density as ced
import numpy as np
import datetime as dt
import os

dirname = os.path.dirname(__file__)


def test_nowcast():
    """Test the nowcast function EXCEPT how alerts are sent"""

    # Create two test stations and the receiver
    st1 = cd.station("NRK", 0, 5, 24, 10, ":00", flag=0, quiet=1, sza=0, DP=0, DA=0)
    st2 = cd.station("GVT", 0, 5, 24, 10, ":00", flag=0, quiet=0)
    st3 = cd.station("T3", 0, 5, 24, 10, ":00", flag=1, quiet=0)
    rcv = cd.receiver("Receiver", 10, 10)

    # Create nowcast object
    ncst = fn.nowcast([st1, st2, st3], rcv, [])

    # Other parameters
    path_to_probas = os.path.join(dirname, "Data/")

    ncst.run(path_to_probas, path_to_probas, path_to_probas)

    error_Ne = np.abs(st1.Ne - ced.compute_Ne(70, 70.55, 0.395)) / ced.compute_Ne(
        70, 70.55, 0.395
    )  # Error on estimate of Ne (%)

    # The proba computation has already been tested elsewhere, here is it jsut to check that everything runs together

    assert ncst.nb_stations_on == 2 and error_Ne < 0.05


def test_plot_probas():
    """Test of the proba plot and in particular the threshold returned"""

    # Triangular 'proba' with peak at flux = 2 and total area equal to 1
    flux = np.linspace(1, 3, 10000)
    probas = np.zeros(np.shape(flux))
    probas[flux <= 2] = flux[flux <= 2] - 1
    probas[flux > 2] = -flux[flux > 2] + 3

    path_to_results = os.path.join(dirname, "Results/")
    today = dt.datetime.now()
    nb_stations_on = 2

    flux_notlog = np.log10(flux)

    ten, fifty, seventy, best = fn.plot_probas(
        probas, flux_notlog, path_to_results, today, nb_stations_on
    )

    # Check results
    errors = []

    if not np.abs(best - 2) < 0.01:
        errors.append("Plot_probas - Incorrect best guess")

    if not np.abs(best - fifty) < 0.01:
        errors.append("Plot_probas - Incorrect 50%")

    # Check 10%
    id = np.argmin(np.abs(ten - flux))
    area_10 = (3 - ten) * probas[id] / 2

    if not np.abs(area_10 - 0.1) < 0.01:
        errors.append("Plot_probas - Incorrect 10%")

    # Check 75%
    id = np.argmin(np.abs(seventy - flux))
    area_75 = (seventy - 1) * probas[id] / 2

    if not np.abs(area_75 - 0.25) < 0.01:
        errors.append("Plot_probas - Incorrect 75%")

    assert not errors, "errors occured:\n{}".format("\n".join(errors))
