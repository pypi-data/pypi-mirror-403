#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 21 10:16:58 2025

@author: pteysseyre
"""

''' Manages the file where the breakpoints and quiet amplitude and phase are written.'''

import os.path
import numpy as np
import pandas as pd

def get_lastbreakpoint(la_station, la_date, path, quiet=False):
    
    ''' Read the value of the last breakpoint, such as the time of detection, the slope, and the associated amplitude and phase.
    If quiet is True, it returns the values for the last quiet breakpoint.
    
    If there were no breakpoints today, return a series of zeros and create the file'''
    
    # Read the last breakpoint value OR create a new file if it is the first of the day
    # If there are no lines yet in the file, write header
    if not os.path.isfile(path+la_date+'_'+la_station+'.csv'):
        
        data = [[0,0,0,0,1, 0]]
        df = pd.DataFrame(data, columns = ['Time (UT)', 'Slope (deg/hr)', 'Amplitude (pT)', 'Phase (deg)', 'Quiet', 'DP'])
        df.to_csv(path+la_date+'_'+la_station+'.csv', index=False)
        
    else :
        df = pd.read_csv(path+la_date+'_'+la_station+'.csv')
    
    if quiet:
        df = df.loc[df['Quiet']==1]
        
    last_bp = df.iloc[-1]
        
    return last_bp['Time (UT)'], last_bp['Slope (deg/hr)'], last_bp['Amplitude (pT)'], last_bp['Phase (deg)'], last_bp['Quiet'], last_bp['DP']

def write_newbreakpoint(la_station, la_date, path, time_now, p1, amp, phase, quiet, DP):
    
    ''' Update the state file by adding the new detected breakpoint.
    Note: because the function get_lastbreakpoint has been called earlier in the Realtimescript, there
    is no need to check that a file exist, or to create a new one'''
    
    # Read the state file 
    df = pd.read_csv(path+la_date+'_'+la_station+'.csv')
    
    # Add the new values 
    df.loc[len(df)] = [time_now, p1, amp, phase, quiet, DP]
    
    # Write the new file
    df.to_csv(path+la_date+'_'+la_station+'.csv', index=False)
    
    return