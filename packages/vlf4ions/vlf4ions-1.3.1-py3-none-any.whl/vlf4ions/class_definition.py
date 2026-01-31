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

import pandas as pd

# For alerts
import smtplib
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders


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
    
    def __init__(self, subject, body, sender, password, recipients, threshold=0, files=[], sent_last_time=0, send_each_change=False):
        self.subject = subject
        self.body = body
        self.sender = sender
        self.password = password
        self.recipients = recipients
        self.threshold = threshold # Only send the alerts if the proba of the flare is 10% above a threshold
        self.files = files # Files to attach to the email
        self.sent_last_time = sent_last_time # Boolean, only useful for alerts on probas
        self.send_each_change = send_each_change # Boolean, if True send each time the proba change
    
    def update_detection_body(self, callsign, p1, decay='N/A'):
        self.body = 'Detection with ' + callsign + '\n Slope : ' + str(p1) + ' deg/hr.' + '\n Decay at : ' + str(decay)

    def send_email(self): 
        
        msg = MIMEMultipart()
        msg['From'] = self.sender
        msg['To'] = COMMASPACE.join(self.recipients)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = self.subject

        msg.attach(MIMEText(self.body))

        for path in self.files:
            part = MIMEBase('application', "octet-stream")
            with open(path, 'rb') as file:
                part.set_payload(file.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition',
                            'attachment; filename={}'.format(Path(path).name))
            msg.attach(part)
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
           smtp_server.login(self.sender, self.password)
           smtp_server.sendmail(self.sender, self.recipients, msg.as_string())  
           smtp_server.quit()
        
        self.sent_last_time = 1

#------------------- Stations and related functions --------------

def sliding_median(arr, window):
    return np.median(np.lib.stride_tricks.sliding_window_view(arr, (window,)), axis=1)
   
class station:
    ''' Characteristics of the transmitter.
    
    :param name: call-sign (e.g. 'GVT')
    :param lat: latitude of the transmitter
    :param lon: latitude of the transmitter
    :param freq: Frequency (kHz)
    :param detection_threshold: Phase slope above which we detect a solar flare
    :param reading_time: second after the minute at which we read the data. NOTE: They should be unique for each station
    :param time_average: Time resolution of the smoothed signal (default: 60 s)
    :param delta: Delta parameter of the incremental algorithm (Guralnik & Srivastava, 1999. Default:0.1)
    :param nb_data_points: number of data points last time the file was read (default : 0, used for flagging)
    :param nb_error: consecutive number of errors in the file reading (default : 0, used for flagging)
    :param Ne: Average electron density computed in the path (not done yet, but I needed this for data analysis)
    :param DA/DP: Computed internally, variations of the amplitude and phase compared to quiet times
    :param mu/sigma: This is computed internally, and is the average and std of the flux probability density function given DA and DP
    
    ---------------
    History: 
        Written by P. Teysseyre in January 2025
        Re-written under current format in April 2025
    
    
    
    '''
    def __init__(self, name, lat, lon, freq, detection_threshold, reading_time, Cal_NS = 0.14, Cal_EW = 0.08, df = 0, time_average = 60, delta = 0.1, nb_data_points = 0, nb_error = 0, Ne=1e8, DP=0, DA=0, p1=0, quiet=1, flag=0, mu=-6, sigma = 1):
        self.name = name # Call-sign
        self.lat = lat # Latitude
        self.lon = lon # Longitude
        self.freq = freq # Frequency
        self.detection_threshold = detection_threshold 
        self.reading_time = reading_time # When the data is read (must not be the same for two stations)
        self.Cal_NS = Cal_NS # Calibration number in the N/S orientation
        self.Cal_EW = Cal_EW # Calibration number in the E/W orientation
        self.time_average = time_average # Time-resolution
        self.delta = delta # Delta parameters for the detection (see Guralnik & Srivasta, 1999)
        self.nb_data_points = nb_data_points 
        self.nb_error = nb_error
        self.Ne = Ne
        self.df = df # For phase correction
        self.DP = DP # Phase increase compared to quiet
        self.DA = DA # Amplitude increase compared to quiet
        self.p1 = p1 # Last breakpoint slope
        self.quiet = quiet # Is 1 if it is quiet
        self.flag = flag # Is 1 if the station is transmitting
        self.mu = mu # Average of the flux pdf
        self.sigma = sigma # Std of the flux pdf


    
    def update_breakpoints(self, path_breakpoint, path_mau, path_sunrise, alerts_antenna, alerts_detection):


        try:
            # Get today's date in a good format
            today = dt.datetime.now(dt.timezone.utc) # The time zone is necessary to use get_sza later
            la_date = today.strftime("%Y_%m_%d")
            
            # Read data & corrects the phase
            amp_NS, amp_EW, phase_NS, phase_EW, the_time, nb_error = rf.read_Narrowband_real_time(self, path_mau)
            phase, jumps = correct_phase.correctionphaseparDw(self, phase_EW, the_time)
            
            # Flag the data if needed
            # CAREFUL: amp is the median of the amplitude recorded over the last minute at most
            path_sunrise = path_sunrise +self.name+'_sunrise_sunset.txt'
            flag, nb_data_points, amp = fl.flags(amp_NS, amp_EW, self.nb_data_points, today, path_sunrise)
            self.nb_data_points = nb_data_points
            self.flag = flag
            
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
                    
                    quiet_now, prev_timedecay, DP, DA = acp.analyse_breakpoint(the_time[-1], p1, amp, phase, the_time, quiet, quiet_phase, quiet_amp, last_breakpoint, last_p1, self.detection_threshold, quiet_p1, quiet_breakpoint)
                    
                    # Write new breakpoint in file
                    msf.write_newbreakpoint(self.name, la_date, path_breakpoint, the_time[-1], p1, amp, phase[-1], quiet_now, DP)
                    
                    print('New breakpoint !')

                    # Update the station
                    self.p1 = p1
                    self.quiet = quiet_now
                    self.DP = DP
                    self.DA = DA
                    
                    # Send alerts if needed
                    if quiet_now == 0 and quiet == 1:
                        
                        alerts_detection.update_detection_body(self.name, p1, prev_timedecay)
                        alerts_detection.send_email()
                
                print('Done - ', today.strftime("%H:%M:%S"), '-', self.name)
            
                
            elif flag == 3:
                
                print(self.name, ' at ', today.strftime("%H:%M:%S"), ' : nighttime')
                self.quiet = 1
                
            else : 
                
                print(self.name, ' is not transmitting at ', today.strftime("%H:%M:%S"))
                self.quiet = 1
        
                
        except Exception as e: # If there was an error, we update the log file
        
            self.nb_error += 1
            
            # Configuration of the logging file
            logging.basicConfig(filename='detection.log', encoding='utf-8')
            logging.error('Error at %s', 'division', exc_info=e)
            print(self.name, ' - error at ', today.strftime("%H:%M:%S"), ' - see log')
        
        if self.nb_error == 5: # it's been five minutes since the antenna stopped or had problems
            
            alerts_antenna.send_email()
        
    def get_pdf_coeff(self, path_to_probas):
        '''Returns the mu and sigma coefficients, defining a gaussian probabiility
        distribution function associated to a station and a value of DP'''

        if self.DP < 0:
            self.DP = 0

        if self.DP > 0:
            probas = pd.read_csv(path_to_probas + self.name + '_probas.csv')

            # Get the correct row
            rows = probas[probas['Low'] <= self.DP]
            row = rows.tail(1)
            self.mu = row['mu'].iloc[0]
            self.sigma = row['sigma'].iloc[0]

        else : # This is quiet time, we return the quiet proba

            # The prior chosen is centered in C1
            self.mu = -6 # log(1e-6)
            self.sigma = 1

