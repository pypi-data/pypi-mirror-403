#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 14:44:17 2025

@author: pteysseyre
"""

# CAREFUL, that works !

import smtplib
from email.mime.text import MIMEText  

def send_email(reason, recipients, receiver):
    
    ''' This is the function called outside of this file, but really it only sends a message'''
    
    subject, body, sender, password = _get_mail_content(receiver, reason)
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
       smtp_server.login(sender, password)
       smtp_server.sendmail(sender, recipients, msg.as_string())
    print("Message sent!")


def _get_mail_content(receiver, reason):
    
    '''This function takes into account a reason to send a message and decides on the contents
    
    Parameters:
    ------------------------------
    - reason: If the antenna is down, 'reason' = 'Antenna down'. 'Error' is only used for testing, to send me a message when there was a problem reading the file or such.
    
    TODO: So far, it only alerts if the antenna is down. But it actually needs to give alerts & estimations in case of flares !
    Note : Maybe not all users will be interested in the same alerts.
    
    '''
    
    sender = 'ptey.secondary@gmail.com'
    password = 'ewkl zcfi qcjb wxdx'
    
    if reason == 'Antenna down':
        
        subject = 'Antenna down'
        body = receiver, 'antenna is down - The recording should be checked and launched again if needed'
    
    if reason == 'Error':
        
        subject = 'Error in ' + receiver
        body = 'Check the log file, there was an error in the file reading/breakpoint analysis'
    
    return(subject, body, sender, password)


        
        
def send_alerts(la_station, receiver, time_now, p1, recipients):

        subject = 'Detection in ' + receiver + ' - ' + la_station
        sender = 'ptey.secondary@gmail.com'
        password = 'ewkl zcfi qcjb wxdx'
        
        body = 'Detection at ' + str(time_now) + ' UT \n Slope : ' + str(p1) + ' deg/hr.'
        
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = ', '.join(recipients)
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
           smtp_server.login(sender, password)
           smtp_server.sendmail(sender, recipients, msg.as_string())
        print("Message sent!")
        
        return