#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 10:41:33 2024

@author: pteysseyre
"""

import numpy as np
import pandas as pd # NOTE : we only need this to read csv files; there may be an easier way to do this, though that works too

def LMP_findminimum(la_station, amp, goodphase, pathtoCSVfiles):
    """ Gives the time profile of H, B
    # NOTE : Make sure that the relevant csv files are stored on the computer AND that they have been detrended
    # They should also only contain A/P values (not H' and beta)
    # Lastly, because of the detrend, the modelled phase may be shifted by a multiple of 90° 
    # The convention chosen here is that the phase is between 90 and 180° at 74 km / 0.3 km^-1
    #---------------------
    # Inputs : 
    # - la_station / la_date : transmitter call sign and date of insterest (ex:
    # 'GBZ', '2023_09_21')
    # - amp, goodphase : measured amplitude and phase (in pT and °). The phase must have been corrected beforehand
    # --------------------------
    # Output : 
    # - H, B : H' and beta arrays
    
    # History : written in march 2024 by P.Teysseyre
    # Based on golden ratio method"""
        
    #the_year, the_month, the_day = la_date.split('_')
    #ladate = the_year + the_month + the_day
    
    data = np.array([amp, goodphase])
    
    # Read the files for modelled amplitude and phase
    # DO NOT open the files with Numbers before !
    A = pd.read_csv(pathtoCSVfiles+'Amplitude'+la_station+'.csv', header=None)
    P = pd.read_csv(pathtoCSVfiles+'Phase'+la_station+'.csv', header=None)
    
    A = A.to_numpy()
    P = P.to_numpy()

    # Get the ranges of parameters H' and beta
    h = np.arange(50, 87.1, 0.1)
    b = np.arange(0.1, 0.61, 0.01)
    
    #----------------------------
    # From that point onwards, the code compares the data and the modelled amp and phase to get H' and beta
    
        
    (rows, columns) = np.shape(A)
    
    # We remove all the NaNs
    P = P[~np.isnan(A)]
    A = A[~np.isnan(A)]
    
    
    # Compute the matrices of relative errors:
    Aq = np.abs(A - data[0])/(data[0] + 1e-2)
    Pq = np.abs(P - data[1])/(data[1] + 1e-2)
    
    # We normalise the matrices (otherwise the errors on the phase are given too much weight 
    # as the phase has a much higher range than the amplitude)
    A_new = (Aq - np.min(Aq))/(np.max(Aq) - np.min(Aq))
    P_new = (Pq - np.min(Pq))/(np.max(Pq) - np.min(Pq))
    
    # The aim is to find eps such that only one point has an error in phase and amp less than eps
    
    # For the golden ratio method, four points are necessary:
    #   - the upper point will be eps_up, with corresponding matrices A_new, P_new and rc
    #   - then eps_3, with A_new3, P_new3, rc3 and rc_new3
    #   - then eps_4, with A_new4, P_new4, rc4, rc_new4
    #   - lastly eps_down, with no corresponding matrix
    
    # A_new's and P_new's are the amplitude and phase of the points with relative 

    
    # Loop counter:
    i = 0
    
    # Golden ratio number
    r = 1/((1 + np.sqrt(5))/2)
    
    # Initialisation of the interations 
    eps_up = np.max([np.max(A_new), np.max(P_new)])
    eps_down = 0    
    interval = eps_up - eps_down
    eps_4 = r**2 * interval + eps_down
    eps_3 = r * interval + eps_down
    
    # Initialisation of rc (Technically, only the last line is absolutely necessary. The lines before just flatten A_new and P_new)
    rc = ((A_new <= eps_up) & (np.abs(P_new) <= eps_up))
    A_new = A_new[rc]
    P_new = P_new[rc]
    rc = np.arange(np.size(A_new))
    
    
    # Initialisation of A_new4, P_new4 and rc4
    rc_new4 = ((A_new < eps_4) & (np.abs(P_new) < eps_4))
    A_new4 = A_new[rc_new4]
    P_new4 = P_new[rc_new4]
    rc4 = rc[rc_new4]

    # Initialisation of A_new3, P_new3 and rc3
    rc_new3 = ((A_new < eps_3) & (np.abs(P_new) < eps_3))
    A_new3 = A_new[rc_new3]
    P_new3 = P_new[rc_new3]
    rc3 = rc[rc_new3]
    
    while ((np.size(rc3) != 1) or (np.size(rc4) != 1)) and (i < 100):
        i += 1
        
        if np.size(A_new4) == 0: # the new interval will be from eps_4 to eps_up
            eps_down = eps_4
            
            eps_4 = eps_3
            A_new4 = A_new3
            P_new4 = P_new3
            rc4 = rc3
            
            interval = eps_up - eps_down
            
            # Recompute eps_3, A_new3, P_new3 and rc_3
            eps_3 = r*interval + eps_down
            rc_3 = ((A_new < eps_3) & (np.abs(P_new) < eps_3))
            A_new3 = A_new[rc_3]
            P_new3 = P_new[rc_3]
            
        else : # New interval will be from eps_down to eps_3
            eps_up = eps_3
            A_new = A_new3
            P_new = P_new3
            rc = rc3
            
            eps_3 = eps_4
            A_new3 = A_new4
            P_new3 = P_new4
            rc3 = rc4
            
            interval = eps_up - eps_down
            
            # Recompute eps_4, A_new4, P_new4 and rc_4
            eps_4 = r**2 * interval + eps_down
            rc_new4 = ((A_new3 < eps_4) & (np.abs(P_new3) < eps_4))
            A_new4 = A_new3[rc_new4]
            P_new4 = P_new3[rc_new4] 
            rc4 = rc3[rc_new4] 
    
    if np.size(A_new4) == 1:
        rc = rc4
    else: 
        rc = rc3
    
    if np.size(rc) != 1: # if the loop as not converge in 100 iterations, NaN values are kept
        H = float('nan')
        B = float('nan')
    else:
        row, col = np.unravel_index(rc[0], (rows, columns))
        H = h[col]
        B = b[row]
    return (H, B)

def compute_Ne(z, H, B):
    
    """Applies Wait's profile to H and B to obtain Ne at altitude z"""
    
    Ne = 1.43e13 * np.exp(-0.15*H)*np.exp((B - 0.15)*(z - H))
    
    return Ne
