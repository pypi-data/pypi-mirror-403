import numpy as np
import vlf4ions.compute_electron_density as ced
import vlf4ions.class_definition as cd
import os

dirname = os.path.dirname(__file__)


def test_get_quiet_hb():
    sza_1 = 0
    H_1, B_1 = ced.get_quiet_hb(sza_1)

    sza_2 = np.pi / 4
    H_2, B_2 = ced.get_quiet_hb(sza_2)

    sza_3 = 45
    H_3, B_3 = ced.get_quiet_hb(sza_3)

    assert (
        (np.abs(H_1 - 70.55) < 1e-4) and (np.abs(B_2 - 0.3668) < 1e-4) and (H_2 == H_3)
    )


def test_LMP_findminimum():

    sza = 66.7753
    GQD = cd.station(
        "GQD", 54.73, -2.88, 22.1, 24.4, ":45", DP=143.680907339525, DA=10.556409437684
    )

    path_to_files = os.path.join(dirname, "Data/")

    H, B = ced.LMP_findminimum(GQD, sza, path_to_files)

    assert (np.abs(H - 69.4) < 0.1) and (np.abs(B - 0.13) < 0.001)


def test_both_function():

    GVT = cd.station("GVT", 54.91, -3.28, 19.58, 60.16, ":42", df=0, orientation=0)

    sza = np.pi / 4
    H_1, B_1 = ced.get_quiet_hb(sza)
    print(H_1)

    path_to_files = os.path.join(dirname, "Data/")
    H_2, B_2 = ced.LMP_findminimum(GVT, sza, path_to_files)
    print(H_2)

    assert np.abs(H_1 - H_2) < 0.05 and np.abs(B_1 - B_2) < 0.005
