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
import vlf4ions.polarisation as polar

import numpy as np
import datetime as dt  # Necessary to use timezone
from datetime import datetime, timedelta, timedelta
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


# ----------------------- Receiver description -----------------
class receiver:
    """Characteristics of the receiver (for plotting purposes mainly and for sending alerts)

    :param name: Name of the receiver. Must match the name in the VLF data file names
    :param lat: Latitude of the receiver (for plotting)
    :param lon: Longitude of the receiver (for plotting)
    :param threshold: Amplitude threshold bellow which we declare a station not transmitting (default: 0.5)
    :param nb_errors: Number of reading errors, we keep track of them to alert in case of malfunction
    :param file_endings: List of strings found at the end of the data files. Default (for AWESOME): ["_100A", "_100B", "_101A", "_101B"]
    """

    def __init__(
        self,
        name,
        lat,
        lon,
        threshold=0.5,
        nb_error=0,
        file_endings=["_100A", "_100B", "_101A", "_101B"],
    ):
        self.name = name
        self.lat = lat
        self.lon = lon
        self.threshold = threshold
        self.nb_error = nb_error
        self.file_endings = file_endings


# ---------------------- Alerts, warnings and such --------------
class email_alerts:
    """Alerts sent in case of flare detection, antenna problems or such

    :param subject: Subject of the email alert
    :param body: Body of the email alert
    :param sender: Email adress of the sender
    :param password: Password of the email address of the sender
    :param recipiends: Recipients of the email alert (must be a list of strings)
    :param threshold: Flux threshold. If the probability of the flux being above this threshold
        is 10% or more, the alert will be sent (default: 0)
    :param files: List of files to include as attachment (default: empty)
    :param send_last_time: Computed internally; used to keep track of alerts already sent to avoid spamming people
    :param send_each_change: Boolean. If true, the recipients will receive an alert each time the flux estimation changes, as long
        as there is at least a 10% probability of the flux being above the threshold"""

    def __init__(
        self,
        subject,
        body,
        sender,
        password,
        recipients,
        threshold=0,
        files=[],
        sent_last_time=0,
        send_each_change=False,
    ):
        self.subject = subject
        self.body = body
        self.sender = sender
        self.password = password
        self.recipients = recipients
        self.threshold = threshold  # Only send the alerts if the proba of the flare is 10% above a threshold
        self.files = files  # Files to attach to the email
        self.sent_last_time = (
            sent_last_time  # Boolean, only useful for alerts on probas
        )
        self.send_each_change = (
            send_each_change  # Boolean, if True send each time the proba change
        )

    def update_detection_body(self, callsign, p1):
        """Just updates the body of the email with the relevant informations in case of flare detection"""

        self.body = "Detection with " + callsign + "\n Slope : " + str(p1) + " deg/hr."

    def get_path_to_fluxestimate(self, path):
        """Get the path to the file used by the 'craft_newsletter' function bellow

        :param path: Path to the flux estimate recap

        :return: filename, full name and path of the file with the flux estimations"""

        today = dt.datetime.now(dt.timezone.utc)
        if today.hour == 0:
            # This is the beginning of the day, so we want to send the recap
            # for the previous day
            today = today - dt.timedelta(days=1)

        la_date = today.strftime("%Y_%m_%d")
        filename = path + la_date + "_nowcast.csv"

        return filename

    def craft_newsletter(self, filename, completenamegiven=False):
        """Craft a newsletter based on the recapitulative file indicated by `filename'.
        It should include the highest flux estimated, its time, and each time the estimated
        flux was above M2 (with start, end time and peak times).

        :param filename: Path to the recapitulative file created with the 'write_fluxestimate' function. It can be found by calling the 'get_path_to_fileestimate' method just before
        :param completenamegiven: Boolean (default: False). If it is false, it assumes that the filename given is the path to the folder, and that the true filename must be computed (because it depends on the date)

        :return: - max_flux: List of peak fluxes for each flare detected during the day
            - max_times: List of each time of peak flux previously returned
            - starts: Start times of each detected flare (quiet < 1)
            - ends: End times of each detected flare (quiet == 1)

        """

        if not completenamegiven:
            filename = self.get_path_to_fluxestimate(filename)

        # Read the file and convert the data into a numpy array
        df = pd.read_csv(filename)
        data = df.to_numpy()

        # Convert data to convenient variables
        flux = data[:, 1]
        the_time = data[:, 0]
        quiet = data[:, 2]
        nb_stations = data[:, 3]

        # For each time when quiet is not one, get the beginning/end time and maximum estimated flux
        max_flux = []
        starts = []
        ends = []
        max_times = []

        # If quiet[0] < 1, it means that the first station in daytime has
        # detected a flare before the second station becomes in daytime
        if quiet[0] < 1:
            starts.append(the_time[0])
            i_start = 0

        # There must be a more elegant way to do this, but this works too
        for i in range(1, len(flux)):

            if quiet[i] < 1 and quiet[i - 1] == 1:  # Flare beginning
                starts.append(the_time[i])
                i_start = i
            elif (quiet[i] == 1 and quiet[i - 1] < 1) or (
                quiet[i] < 1 and i == len(flux)
            ):  # Flare ending
                ends.append(the_time[i])
                i_max = np.argmax(flux[i_start : i + 1])
                max_flux.append(flux[i_max + i_start])
                max_times.append(the_time[i_max + i_start])

        nb_flares = len(max_flux)

        # Write the body of the newletter
        body = "Today's detections : " + "\n"  # Initialisation
        body += "\n"
        body += (
            "From "
            + self._good_format_time(the_time[0])
            + " to "
            + self._good_format_time(the_time[-1])
            + " UT \n \n"
        )

        if nb_flares > 0:
            for f in range(nb_flares):
                body += "Flare " + str(f + 1) + " : \n"
                body += "-------------------- \n"
                body += "Start time : " + self._good_format_time(starts[f]) + " UT \n"
                body += (
                    "Max flux : "
                    + "{flux:.1e} W/m^2".format(flux=max_flux[f])
                    + "at "
                    + self._good_format_time(max_times[f])
                    + " UT \n"
                )
                body += "End time : " + self._good_format_time(ends[f]) + " UT \n \n"
        else:
            body += "No detection today !"

        # Reminder
        body += "\n Note: Please remember that the quality of the flux estimates depends on the data used to compute the probability functions"
        body += " If only M and weak X flares are used, the estimates will be skewed for C flares and strong X flares"
        self.body = body

        return max_flux, max_times, starts, ends

    def _good_format_time(self, the_time):
        """Convert a float like 13.1222222 to a string like '13:07'
        :param the_time: Time to convert to string
        :return: The time, converted to a string in the format '%H:%M'"""

        hour = np.floor(the_time)
        minute = np.round((the_time - hour) * 60)
        the_time = dt.time(int(hour), int(minute))

        the_time_str = the_time.strftime("%H:%M")

        return the_time_str

    def send_email(self):
        """Sends the email from the sender email adress to the recipients"""

        msg = MIMEMultipart()
        msg["From"] = self.sender
        msg["To"] = COMMASPACE.join(self.recipients)
        msg["Date"] = formatdate(localtime=True)
        msg["Subject"] = self.subject

        msg.attach(MIMEText(self.body))

        for path in self.files:
            part = MIMEBase("application", "octet-stream")
            with open(path, "rb") as file:
                part.set_payload(file.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition", "attachment; filename={}".format(Path(path).name)
            )
            msg.attach(part)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
            smtp_server.login(self.sender, self.password)
            smtp_server.sendmail(self.sender, self.recipients, msg.as_string())
            smtp_server.quit()

        self.sent_last_time = 1


# ------------------- Stations and related functions --------------


def sliding_median(arr, window):
    return np.median(np.lib.stride_tricks.sliding_window_view(arr, (window,)), axis=1)


class station:
    """Characteristics of the transmitter.

    :param name: call-sign (e.g. 'GVT')
    :param lat: latitude of the transmitter
    :param lon: latitude of the transmitter
    :param freq: Frequency (kHz)
    :param detection_threshold: Phase slope above which we detect a solar flare
    :param reading_time: second after the minute at which we read the data. NOTE: They should be unique for each station
    :param time_average: Time resolution of the smoothed signal (default: 60 s)
    :param delta: Delta parameter of the incremental algorithm (Guralnik & Srivastava, 1999. Default:0.1)
    :param nb_data_points: number of data points last time the file was read (default : 0, used for flagging)
    :param Ne: Average electron density computed in the path (not done yet, but I needed this for data analysis)
    :param DA/DP: Computed internally, variations of the amplitude and phase compared to quiet times
    :param mu/sigma: This is computed internally, and is the average and std of the flux probability density function given DA and DP
    :param orientation: Is 1 if the phase considered is E/W, 0 if it is N/S (default: 1). The idea is that the phase can be much noisier in
        one direction, so the optimal orientation is left as a choice for the user

    ---------------
    History:
        Written by P. Teysseyre in January 2025
        Re-written under current format in April 2025



    """

    def __init__(
        self,
        name,
        lat,
        lon,
        freq,
        detection_threshold,
        reading_time,
        Cal_NS=0.14,
        Cal_EW=0.08,
        df=0,
        time_average=60,
        delta=0.1,
        nb_data_points=0,
        nb_error=0,
        Ne=1e8,
        DP=0,
        DA=0,
        p1=0,
        quiet=1,
        flag=0,
        mu=-6,
        sigma=1,
    ):
        self.name = name  # Call-sign
        self.lat = lat  # Latitude
        self.lon = lon  # Longitude
        self.freq = freq  # Frequency
        self.detection_threshold = detection_threshold
        self.reading_time = reading_time  # When the data is read (must not be the same for two stations)
        self.Cal_NS = Cal_NS  # Calibration number in the N/S orientation
        self.Cal_EW = Cal_EW  # Calibration number in the E/W orientation
        self.time_average = time_average  # Time-resolution
        self.delta = (
            delta  # Delta parameters for the detection (see Guralnik & Srivasta, 1999)
        )
        self.nb_data_points = nb_data_points
        self.Ne = Ne
        self.df = df  # For phase correction
        self.DP = DP  # Phase increase compared to quiet
        self.DA = DA  # Amplitude increase compared to quiet
        self.p1 = p1  # Last breakpoint slope
        self.quiet = quiet  # Is 1 if it is quiet
        self.flag = flag  # Is 1 if the station is transmitting
        self.mu = mu  # Average of the flux pdf
        self.sigma = sigma  # Std of the flux pdf

    def update_df(self, this_receiver, path_to_data, epsilon=5, nb_days=30):
        """Updates the value of df for the station, as it depends on the transmitter and may vary in time

        :param receiver: Receiver class instance
        :param path_to_data: Path to the data files
        :param epsilon: Maximum phase jump (in °) that we allow on average (default: 5)
        :param nb_days: Number of days on which we want to compute df (default: 30)"""

        # Get today's date, date_inf (yesterday - nb_days) and date_sup (yesterday)
        today = dt.datetime.now(
            dt.timezone.utc
        )  # The time zone is necessary to use get_sza later
        date_sup = today - dt.timedelta(days=1)
        date_inf = date_sup - dt.timedelta(days=nb_days)

        # Compute the new df
        df = correct_phase.compute_df(
            date_inf, date_sup, self, path_to_data, this_receiver.file_endings, epsilon
        )

        # Update the df value
        self.df = df

    def update_breakpoints(
        self,
        path_breakpoint,
        path_mau,
        path_sunrise,
        alerts_antenna,
        alerts_detection,
        this_receiver,
    ):
        """Checks the phase and detects perturbations due to flares. If needed, send alerts to users

        :param path_breakpoint: path to the files where the breakpoints are stores
        :param path_mau: path to the data being written
        :param path_sunrise: path to the files with precomputed sunrise and sunset times
        :param alerts_antenna: instance of 'alert' class, alert to send if the antenna is down
        :param alerts_detection: instance of 'alert' class, alert to send if there is a detection
        :param this_receiver: Receiver class instance
        """

        try:
            # Get today's date in a good format
            today = dt.datetime.now(
                dt.timezone.utc
            )  # The time zone is necessary to use get_sza later
            la_date = today.strftime("%Y_%m_%d")

            # Read data & corrects the phase
            amp_NS, amp_EW, phase_NS, phase_EW, the_time, nb_error = (
                rf.read_Narrowband_real_time(self, path_mau, this_receiver, today)
            )

            # Before v1.3.3.post5
            phase = polar.EllipseParams(amp_NS, amp_EW, phase_NS, phase_EW)
            phase, jumps = correct_phase.correctionphaseparDw(self, phase, the_time)

            # Flag the data if needed
            # CAREFUL: amp is the median of the amplitude recorded over the last minute at most
            path_sunrise = path_sunrise + self.name + "_sunrise_sunset.txt"
            flag, nb_data_points, amp = fl.flags(
                amp_NS,
                amp_EW,
                self.nb_data_points,
                today,
                path_sunrise,
                this_receiver,
                phase,
            )
            self.nb_data_points = nb_data_points
            self.flag = flag

            if flag == 1:  # The antenna has stopped
                self.nb_error += 1
                if alerts_antenna.sent_last_time == 0 and self.nb_error == 5:
                    alerts_antenna.send_email()

            elif flag == 0:

                this_receiver.nb_error = 0
                alerts_antenna.sent_last_time = 1

                # Time average the data & apply median filter
                time_average = np.min([self.time_average, len(the_time)])
                the_time = sliding_median(the_time, self.time_average)
                the_time = the_time[0::time_average]
                phase = sliding_median(phase, self.time_average)
                phase = phase[0::time_average]

                # Read the last breakpoint value OR create a new file if it is the first of the day
                last_breakpoint, last_p1, last_amp, last_phase, quiet, DP = (
                    msf.get_lastbreakpoint(self.name, la_date, path_breakpoint)
                )

                # Keep the data after last breakpoint
                mask_time = the_time > last_breakpoint
                the_time = the_time[mask_time]
                phase = phase[mask_time]

                # Shorten the data if it is too long
                # Also consider that it is quiet time, as there would have been more changes if it was flare time
                if np.max(the_time) - the_time[0] > 2:
                    two_hours = int(
                        np.floor(7200 / self.time_average)
                    )  # Number of indices in those two hours
                    phase = phase[-1 - two_hours :]
                    the_time = the_time[-1 - two_hours :]

                    # Look if there are new breakpoints now
                    detec, p1 = dcp.find_break_point_realtime(
                        the_time, phase, self.delta
                    )

                    # NOTE: Here, the p1 value is the one corresponding to the last nine minutes of data

                    # Write new breakpoint in file
                    msf.write_newbreakpoint(
                        self.name,
                        la_date,
                        path_breakpoint,
                        the_time[-1],
                        p1,
                        amp,
                        phase[-1],
                        1,
                        0,
                    )

                    print("New breakpoint, after two quiet hours")

                    # Change the station's characteritics
                    self.quiet = 1
                    self.DA = 0
                    self.DP = 0
                    self.p1 = p1

                else:
                    # Look if there are new breakpoints now
                    detec, p1 = dcp.find_break_point_realtime(
                        the_time, phase, self.delta
                    )

                    # If there is a new breakpoint, write it in a file
                    if detec:

                        # Get last QUIET breakpoint
                        (
                            quiet_breakpoint,
                            quiet_p1,
                            quiet_amp,
                            quiet_phase,
                            quiet_quiet,
                            quiet_DP,
                        ) = msf.get_lastbreakpoint(
                            self.name, la_date, path_breakpoint, quiet=True
                        )
                        # NOTE: quiet_quiet is useless and is always 1 (same for quiet_DP who is always 0)

                        quiet_now, prev_timedecay, DP, DA = acp.analyse_breakpoint(
                            the_time[-1],
                            p1,
                            amp,
                            phase,
                            the_time,
                            quiet,
                            quiet_phase,
                            quiet_amp,
                            last_breakpoint,
                            last_p1,
                            self.detection_threshold,
                            quiet_p1,
                            quiet_breakpoint,
                        )

                        if quiet_now == 1:
                            DP = 0
                            DA = 0

                        # Write new breakpoint in file
                        msf.write_newbreakpoint(
                            self.name,
                            la_date,
                            path_breakpoint,
                            the_time[-1],
                            p1,
                            amp,
                            phase[-1],
                            quiet_now,
                            DP,
                        )

                        print("New breakpoint !")

                        # Update the station
                        self.p1 = p1
                        self.quiet = quiet_now
                        self.DP = DP
                        self.DA = DA

                        # Send alerts if needed
                        if quiet_now == 0 and quiet == 1:

                            alerts_detection.update_detection_body(self.name, p1)
                            alerts_detection.send_email()

                    print("Done - ", today.strftime("%H:%M:%S"), "-", self.name)

            elif flag == 3:

                print(self.name, " at ", today.strftime("%H:%M:%S"), " : nighttime")
                self.quiet = 1
                self.DP = 0
                self.DA = 0
                this_receiver.nb_error = 0
                alerts_antenna.sent_last_time = 1

            else:

                print(self.name, " is not transmitting at ", today.strftime("%H:%M:%S"))
                self.quiet = 1
                alerts_antenna.sent_last_time = 1

        except Exception as e:  # If there was an error, we update the log file

            this_receiver.nb_error += 1

            # Configuration of the logging file
            logging.basicConfig(filename="detection.log", encoding="utf-8")
            logging.error("Error at %s", "division", exc_info=e)
            print(self.name, " - error at ", today.strftime("%H:%M:%S"), " - see log")

    def get_pdf_coeff(self, path_to_probas):
        """Returns the mu and sigma coefficients, defining a gaussian probabiility
        distribution function associated to a station and a value of DP

        :param path_to_probas: path to the files containing the mu and sigma values
            for the porbability computations"""

        if self.DP < 0:
            self.DP = 0

        if (
            self.DP > 5
        ):  # Only do it for high DP, the other ones may be due to small noise

            probas = pd.read_csv(path_to_probas + self.name + "_probas.csv")

            # Get the correct row
            rows = probas[probas["Low"] <= self.DP]
            row = rows.tail(1)
            self.mu = row["mu"].iloc[0]
            self.sigma = row["sigma"].iloc[0]

        else:  # This is quiet time, we return the quiet proba centered in C1

            self.mu = -6  # log(1e-6)
            self.sigma = 1
