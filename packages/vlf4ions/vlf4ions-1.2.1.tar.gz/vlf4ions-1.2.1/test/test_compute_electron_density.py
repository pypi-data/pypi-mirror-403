import numpy as np
import vlf4ions.compute_electron_density as ced
import vlf4ions.class_definition as cd
import os
dirname = os.path.dirname(__file__)

def test_get_quiet_hb():
    sza_1 = 0 
    H_1, B_1 = ced.get_quiet_hb(sza_1)

    sza_2 = np.pi/4
    H_2, B_2 = ced.get_quiet_hb(sza_2)

    sza_3 = 45
    H_3, B_3 = ced.get_quiet_hb(sza_3)

    assert((np.abs(H_1 - 70.55) < 1e-4) and (np.abs(B_2 - 0.3668) < 1e-4) and (H_2 == H_3))

def test_LMP_findminimum():
    sza = 66.7753
    GQD = cd.station('GQD', 54.73, -2.88, 22.1, 24.4, ':45')
    A_quiet = 10.7639414407342
    P_quiet = 110.027930269667
    DA = 10.556409437684
    DP = 143.680907339525

    path_to_files = os.path.join(dirname, '')

    H, B = ced.LMP_findminimum(GQD, DA, DP, A_quiet, P_quiet, sza, path_to_files)
    print(H, B)

    assert((np.abs(H - 79.3) < 0.1) and (np.abs(B - 0.21) < 0.001))

