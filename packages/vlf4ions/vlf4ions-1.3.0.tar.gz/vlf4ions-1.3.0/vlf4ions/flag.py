#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 10:44:38 2024

@author: pteysseyre
"""

import numpy as np
import vlf4ions.sunrise_sunset as srst

def flags(amp_NS, amp_EW, previous_nb_points, today, path):
    """Flags 1 if the antenna is down, 2 if the transmitter is down, 3 if it is nighttime"""
    
    flag = 0
    data_last_min = 0
    length_data = min(len(amp_NS), len(amp_EW)) # this is necessary as there may be one more point in amp_EW than amp_NS, as it is read later
    
    #Check that we are in daytime
    daytime = srst.check_if_daytime(today, path)
    
    if daytime:
        # Antenna down: the number of data points in the last written file stays the same
        if length_data == previous_nb_points:
            flag = 1
        else:
            previous_nb_points = length_data
        
            # Transmitter down: the amplitude is less than 0.3 pT
            
            if length_data > 60:
                amp_NS = amp_NS[-60:]
                amp_EW = amp_EW[-60:]
            else:
                amp_NS = amp_NS[-length_data:]
                amp_EW = amp_EW[-length_data:]
                
            amp = np.sqrt(np.square(amp_NS) + np.square(amp_EW))
            data_last_min = np.median(amp)
        
        if data_last_min < 0.4: # 0.3 pT is the antenna sensibility
            flag = 2
    else:
        flag = 3
        
    return flag, length_data, data_last_min
    