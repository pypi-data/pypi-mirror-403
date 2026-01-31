#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 10:29:16 2024

@author: pteysseyre
"""

import numpy as np
from pymatreader import read_mat # To read the mau files
from datetime import datetime # To get today's date
import schedule # To loop on time
import pandas as pd # NOTE : we only need this to read csv files; there may be an easier way to do this, though that works too
#import shutil # To copy the files being read
import time # Only needed here so that the script keeps running even when it's not computing anything
import os.path # Useful to determine if a file exist or not (to write headers in a new file)
#from os import remove # Deletes the copied file at the end reading it 
import glob

def correctionphase(la_station, phase, the_time):
    """Completely corrects the phase in real time the phase so that:
    # 1) All phase jumps from -180° to 180° are corrected, and the phase detrended
    # 2) The absolute value of the phase is also given 

    # CURRENT hypothesis: (08/24)
    # 1) The value of the phase in quiet time during the day is between 90° and 180° 

    # CURRENT STATE : 
    # The phase is currently only unwrapped and detrended
    """
    
    phase_corr, jumps = correctionphaseparDw(la_station, phase, the_time)
    
    return phase_corr


def unwrap_moco(Data_In, UnwrapNumber):
    """Originally written by M. Cohen in Matlab. Unwraps 'Data_in', 
    by compensating any jumps more than UnwrapNumer/2"""
    
    # Remove all NaN point and reconcatanate
    Data_NaN = np.isnan(Data_In)
    Data_In_NonNaN = Data_In[Data_NaN == False]
    Indices_NonNaN = np.arange(0, np.size(Data_In_NonNaN))
    
    # Take differential
    Data_In_NonNaN_Diff = np.diff(Data_In_NonNaN)
    
    # Identify points where signal jumps by more than unwrap/2 threshold
    Indices_NonNaN = Indices_NonNaN[0:-1]
    JumpIndices = Indices_NonNaN[np.abs(Data_In_NonNaN_Diff)>UnwrapNumber/2]
    Data_In_NonNaN_Diff_Jumps = Data_In_NonNaN_Diff[JumpIndices]
    
    # Round jumps to nearest value of unwrap number
    Data_In_NonNaN_Diff_Jumps = np.round(Data_In_NonNaN_Diff_Jumps/UnwrapNumber) * UnwrapNumber
    
    # Integrates jump to original concatanated vector. Add 1 to indices to reference later point of two differential elements
    Indices_NonNaN_Jump = Indices_NonNaN[JumpIndices]
    
    # Go back to original version with the NaNs and create derivative
    Data_In_Diff_Jumps = Data_In*0
    Data_In_Diff_Jumps[np.isnan(Data_In_Diff_Jumps)] = 0
    Data_In_Diff_Jumps[Indices_NonNaN_Jump] = Data_In_NonNaN_Diff_Jumps
    
    # Integrates to get the function that needs to be substracted
    Data_In_Jumps = np.cumsum(Data_In_Diff_Jumps)
    
    # Substract from original 
    Data_Out = Data_In - Data_In_Jumps
    
    # nb_jumps_station = np.size(JumpIndices)
    
    return Data_Out, Data_In_Jumps[-1]

def correctionphaseparDw(la_station, phase, the_time):
    """Corrects the phase by compensating for the phase detrend induced by the 
    transmitter frequency not being exactly stable
    
    NOTE : The values were obtained from the function 'find_dw' written in Matlab
    They are only valid for the stations considered below, and only for the Nançay 
    AWESOME antenna"""
    
    if la_station == 'DHO':
        Deltaf = - 0.0013
    elif (la_station == 'NSC') or (la_station == 'NSY'):
        Deltaf = 2.0697e-4
    elif la_station == 'NRK':
        Deltaf = 1.4136e-4
    elif la_station == 'NAU':
        Deltaf = 6.9227e-5
    elif la_station == 'NAA':
        Deltaf = 1.6403e-5
    else:
        Deltaf = 0
        
    Deltaw = 2*np.pi*Deltaf
    
    phase_un, jumps = unwrap_moco(phase, 90) 
    
    phase_corr = phase_un + (Deltaw*the_time*3600)*180/np.pi
    
    # For now (03/24) because there is both a 90° uncertainty on the measurements and the modelling
    # we choose to keep the phase between 90 and 180° for quiet daytime conditions
    
    
    return phase_corr, jumps

