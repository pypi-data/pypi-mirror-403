#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 10:44:38 2024

@author: pteysseyre
"""

import numpy as np

def flags(phase, previous_nb_points):
    """Flags 1 if the antenna is down, 2 if the transmitter is down"""
    
    flag = 0
    
    length_data = len(phase)
    
    # Antenna down: the number of data points in the last written file stays the same
    if length_data == previous_nb_points:
        flag = 1
    else:
        previous_nb_points = length_data
    
    # Transmitter down: the phase varies randomly; the std of the phase over the last minute is greater than 20°
    ind_beginning_last_min = max(0, length_data - 60) # If the receiver or day has just started, then there isn't one minute of data yet
    data_last_min = phase[ind_beginning_last_min:-1]
    std_last_min = np.std(data_last_min)
    
    if std_last_min > 20:
        flag = 2
        
        return flag
    