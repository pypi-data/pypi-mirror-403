import os
import vlf4ions.class_definition as cd
import numpy as np

dirname = os.path.dirname(__file__)


def test_get_pdf_coeff():

    errors = []
    NRK = cd.station("NRK", 63.85, -22.47, 37.5, 22.02, ":15", df=1.4136e-4)
    path_to_files = os.path.join(dirname, "Data/")

    NRK.DP = 0
    NRK.get_pdf_coeff(path_to_files)
    if NRK.mu != -6 or NRK.sigma != 1:
        errors.append("Problem with the prior")

    NRK.DP = 10
    NRK.get_pdf_coeff(path_to_files)
    if (
        np.abs(NRK.mu + 4.66905892623818) > 1e-4
        or np.abs(NRK.sigma - 0.199174407925015) > 1e-4
    ):
        errors.append("Problem with the first row")

    NRK.DP = 200
    NRK.get_pdf_coeff(path_to_files)
    if (
        np.abs(NRK.mu + 4.10760899331066) > 1e-4
        or np.abs(NRK.sigma - 0.481437593395161) > 1e-4
    ):
        errors.append("Problem with the last row")

    # assert no error message has been registered, else print messages
    assert not errors, "errors occured:\n{}".format("\n".join(errors))
