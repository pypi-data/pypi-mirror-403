#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 22 14:10:40 2025

@author: pteysseyre
"""

import vlf4ions.read_files as rf
import vlf4ions.detect_change_points as dcp
import vlf4ions.correct_phase as correct_phase
import vlf4ions.flag as fl
import vlf4ions.analyse_change_points as acp
import vlf4ions.manage_statefile as msf

import numpy as np
import datetime as dt # Necessary to use timezone
from datetime import datetime
import logging

# For alerts
import smtplib
from email.mime.text import MIMEText  


#----------------------- Receiver description -----------------
class receiver:
    ''' Characteristics of the receiver (for plotting purposes mainly and for sending alerts) '''
    def __init__(self, name, lat, lon):
        self.name = name
        self.lat = lat
        self.lon = lon

#---------------------- Alerts, warnings and such --------------
class email_alerts: 
    """ Alerts sent in case of flare detection, antenna problems or such """
    
    def __init__(self, subject, body, sender, password, recipients):
        self.subject = subject
        self.body = body
        self.sender = sender
        self.password = password
        self.recipients = recipients
    
    def update_detection_body(self, callsign, p1):
        self.body = 'Detection with ' + callsign + '\n Slope : ' + str(p1) + ' deg/hr.'
        
    def send_email(self): 
        
        msg = MIMEText(self.body)
        msg['Subject'] = self.subject
        msg['From'] = self.sender
        msg['To'] = ', '.join(self.recipients)
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
           smtp_server.login(self.sender, self.password)
           smtp_server.sendmail(self.sender, self.recipients, msg.as_string())  

#------------------- Stations and related functions --------------

def sliding_median(arr, window):
    return np.median(np.lib.stride_tricks.sliding_window_view(arr, (window,)), axis=1)
   
class station:
    ''' Characteristics of the transmitter.
    
    ---------------
    Params:
    - name: call-sign (e.g. 'GVT')
    - lat/lon: latitude and longitude of the transmitter
    - freq: Frequency (kHz)
    - detection_threshold: Phase slope above which we detect a solar flare
    - reading_time: second after the minute at which we read the data. NOTE: They should be unique for each station
    - time_average: Time resolution of the smoothed signal (default: 60 s)
    - delta: Delta parameter of the incremental algorithm (Guralnik & Srivastava, 1999. Default:0.1)
    - nb_data_points: number of data points last time the file was read (default : 0, used for flagging)
    - nb_error: consecutive number of errors in the file reading (default : 0, used for flagging)
    - Ne: Average electron density computed in the path (not done yet, but I needed this for data analysis)
    
    ---------------
    History: 
        Written by P. Teysseyre in January 2025
        Re-written under current format in April 2025
    
    
    
    '''
    def __init__(self, name, lat, lon, freq, detection_threshold, reading_time, df = 0, time_average = 60, delta = 0.1, nb_data_points = 0, nb_error = 0, Ne=1e8):
        self.name = name
        self.lat = lat
        self.lon = lon
        self.freq = freq
        self.detection_threshold = detection_threshold
        self.reading_time = reading_time
        self.time_average = time_average
        self.delta = delta
        self.nb_data_points = nb_data_points
        self.nb_error = nb_error
        self.Ne = Ne
        self.df = df
    
    
    def update_breakpoints(self, path_breakpoint, path_mau, path_sunrise, alerts_antenna, alerts_detection):
        
        try:
            # Get today's date in a good format
            today = dt.datetime.now(dt.timezone.utc) # The time zone is necessary to use get_sza later
            la_date = today.strftime("%Y_%m_%d")
            
            # Read data & corrects the phase
            amp_NS, amp_EW, phase_NS, phase_EW, the_time, nb_error = rf.read_Narrowband_real_time(la_date, self.name, path_mau)
            phase, jumps = correct_phase.correctionphaseparDw(self, phase_EW, the_time)
            
            # Flag the data if needed
            # CAREFUL: amp is the median of the amplitude recorded over the last minute at most
            path_sunrise = path_sunrise +self.name+'_sunrise_sunset.txt'
            flag, nb_data_points, amp = fl.flags(amp_NS, amp_EW, self.nb_data_points, today, path_sunrise)
            self.nb_data_points = nb_data_points
            
            if flag == 1: # The antenna has stopped
                self.nb_error += 1
                
                
            elif flag == 0:
                
                self.nb_error = 0
                
                # Time average the data & apply median filter
                time_average = np.min([self.time_average, len(the_time)])
                the_time = sliding_median(the_time, self.time_average)
                the_time = the_time[0::time_average]
                phase = sliding_median(phase, self.time_average)
                phase = phase[0::time_average]
                
                # Read the last breakpoint value OR create a new file if it is the first of the day
                last_breakpoint, last_p1, last_amp, last_phase, quiet, DP = msf.get_lastbreakpoint(self.name, la_date, path_breakpoint)
                
                # Keep the data after last breakpoint
                mask_time = (the_time > last_breakpoint)
                the_time = the_time[mask_time]
                phase = phase[mask_time]
                
                try :
                    # Shorten the data if it is too long
                    if the_time[-1] - the_time[0] > 2:
                        two_hours = int(np.floor(7200/self.time_average))
                        phase = phase[-1 - two_hours:]
                        the_time = the_time[-1 - two_hours:]
                        
                except :
                    self.nb_error += 1
            
                # Look if there are new breakpoints now
                detec, p1 = dcp.find_break_point_realtime(the_time, phase, self.delta)
            
                # If there is a new breakpoint, write it in a file
                if detec:   
                
                    # Get last QUIET breakpoint
                    quiet_breakpoint, quiet_p1, quiet_amp, quiet_phase, quiet_quiet, quiet_DP = msf.get_lastbreakpoint(self.name, la_date, path_breakpoint, quiet=True)
                    # NOTE: quiet_quiet is useless and is always 1 (same for quiet_DP who is always 0)
                    
                    quiet_now, prev_1min, prev_5min, prev_timedecay, DP = acp.analyse_breakpoint(the_time[-1], p1, self.name, amp, phase, the_time, quiet, quiet_phase, quiet_amp, last_breakpoint, last_p1, self.detection_threshold, DP)
                    
                    # Write new breakpoint in file
                    msf.write_newbreakpoint(self.name, la_date, path_breakpoint, the_time[-1], p1, amp, phase[-1], quiet_now, DP)
                    
                    print('New breakpoint !')
                    
                    # Send alerts if needed
                    if quiet_now == 0 and quiet == 1:
                        
                        alerts_detection.update_detection_body(self.name, p1)
                        alerts_detection.send_email()
                
                print('Done -  ', today.strftime("%H:%M:%S"), '-', self.name)
            
                
            elif flag == 3:
                
                print(self.name, ' at ', today.strftime("%H:%M:%S"), ' : nighttime')
                
            else : 
                
                print(self.name, ' is not transmitting at ', today.strftime("%H:%M:%S"))
        
                
        except Exception as e: # If there was an error, we update the log file
        
            self.nb_error += 1
            
            # Configuration of the logging file
            logging.basicConfig(filename='detection.log', encoding='utf-8')
            logging.error('Error at %s', 'division', exc_info=e)
            print(self.name, ' - error at ', today.strftime("%H:%M:%S"), ' - see log')
        
        if self.nb_error == 5: # it's been five minutes since the antenna stopped or had problems
            
            alerts_antenna.send_email()
            
            