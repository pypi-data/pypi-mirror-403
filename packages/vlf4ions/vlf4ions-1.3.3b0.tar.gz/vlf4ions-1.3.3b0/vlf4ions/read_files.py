#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 11:47:33 2024

@author: pteysseyre
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 09:59:31 2024

@author: pteysseyre
"""

import numpy as np
from pymatreader import read_mat # To read the mau files
import os.path # Useful to determine if a file exist or not (to write headers in a new file)
import glob

#======================== Read mau files ======================================

def read_Narrowband_postprocessing(la_date, la_station, path, file_endings = ['_100A', '_100B', '_101A', '_101B']): 
    """
    Reads the data for the station and the day asked and stores them in the output arrays
    Needs the path to the data files
    Reads the .mat files (already ended)
    Written by C. Briand on 16//10/2022
    Converted to Python by P. Teysseyre on 18/03/2024
    
    :param la_date: Date when the files need to be read (e.g. '2023_01_25')
    :param la_station: Transmitter call sign
    :param path: path to the files
    :param file_endings: List of string. Endings of the files for amp_NS, phase_NS, amp_EW and phase_EW in that order"""

        
    Cal_NS = 0.14
    Cal_EW = 0.08
    
    nb_errors = 0
    
    # amp_NS
    list_of_files = glob.glob(path+'NC*'+la_station+'_100A.mat')
    latest_file = max(list_of_files, key=os.path.getctime)

    try :
        data = read_mat(latest_file)
        amp_NS = data['data']*Cal_NS
        start_time = data['start_hour'] + data['start_minute']/60 + data['start_second']/3600
    except (TypeError, ValueError):
        print('TypeError - amp_NS')
        amp_NS = 0
        nb_errors += 1
        start_time = 0
    
    # phase_EW
    list_of_files = glob.glob(path+'NC*'+la_station+'_101B.mat')
    latest_file = max(list_of_files, key=os.path.getctime)

    try :
        data = read_mat(latest_file)
        phase_EW = data['data']
        start_time = data['start_hour'] + data['start_minute']/60 + data['start_second']/3600
    except (TypeError, ValueError):
        print('TypeError - phase_EW')
        
        # If there is a pb with the phase_EW files, a solution is to take the phase_NS ones
        # phase_NS
        list_of_files = glob.glob(path+'NC*'+la_station+'_100B.mat')
        latest_file = max(list_of_files, key=os.path.getctime)

        try :
            data = read_mat(latest_file)
            phase_EW = data['data']
            start_time = data['start_hour'] + data['start_minute']/60 + data['start_second']/3600
        except (TypeError, ValueError):
            print('TypeError - phase_NS')
            phase_EW = 0
            nb_errors += 1
            start_time = 0
    
    
    # amp_EW
    list_of_files = glob.glob(path+'NC*'+la_station+'_101A.mat')
    latest_file = max(list_of_files, key=os.path.getctime)

    try :
        data = read_mat(latest_file)
        amp_EW = data['data']*Cal_EW
        start_time = data['start_hour'] + data['start_minute']/60 + data['start_second']/3600
    except (TypeError, ValueError):
        print('TypeError - amp_EW')
        amp_EW = 0
        nb_errors += 1
        start_time = 0

    # phase_NS
    list_of_files = glob.glob(path+'NC*'+la_station+'_100B.mat')
    latest_file = max(list_of_files, key=os.path.getctime)

    try :
        data = read_mat(latest_file)
        phase_NS = data['data']
        start_time = data['start_hour'] + data['start_minute']/60 + data['start_second']/3600
    except (TypeError, ValueError):
        print('TypeError - phase_NS')
        phase_NS = 0
        nb_errors += 1
        start_time = 0
    
    Fs = data['Fs']
    tstep = 1/Fs/3600
    the_time = np.linspace(start_time, tstep*np.size(phase_EW), np.size(phase_EW))
    
    return (amp_NS, amp_EW, phase_NS, phase_EW, the_time)

def read_Narrowband_real_time(station, path, receiver): 

    """
    Reads the data for the station and the day asked and stores them in the output arrays
    Reads the .mat files still being written
    Needs the path to the files
    Written by C. Briand on 16//10/2022
    Converted to Python on 18/03/2024
    
    :param station: 'station' class instance 
    :paraam path: Path to the files being read
    :param receiver: Receiver class instance"""

    nb_errors = 0
    
    # amp_NS
    list_of_files = glob.glob(path+'*'+station.name+receiver.file_endings[0] + '.mau')
    latest_file = max(list_of_files, key=os.path.getctime)
    #fname = shutil.copy2(f, pathdest) # If we want to copy the files, decomment the line and change the following f to fname
    try :
        data = read_mat(latest_file)
        amp_NS = data['data']*station.Cal_NS
        start_time = data['start_hour'] + data['start_minute']/60 + data['start_second']/3600
    except (TypeError, ValueError):
        print('TypeError - amp_NS')
        amp_NS = 0
        nb_errors += 1
        start_time = 0
    #os.remove(fname)
    
    # phase_EW
    list_of_files = glob.glob(path+'*'+station.name+receiver.file_endings[3] + '.mau')
    latest_file = max(list_of_files, key=os.path.getctime)
        #fname = shutil.copy2(f, pathdest)
    try :
        data = read_mat(latest_file)
        phase_EW = data['data']
        start_time = data['start_hour'] + data['start_minute']/60 + data['start_second']/3600
    except (TypeError, ValueError):
        print('TypeError - phase_EW')
        phase_EW = 0
        nb_errors += 1
        start_time = 0
    
    
    # amp_EW
    list_of_files = glob.glob(path+'*'+station.name+receiver.file_endings[2] + '.mau')
    latest_file = max(list_of_files, key=os.path.getctime)
        #fname = shutil.copy2(f, pathdest)
    try :
        data = read_mat(latest_file)
        amp_EW = data['data']*station.Cal_EW
        start_time = data['start_hour'] + data['start_minute']/60 + data['start_second']/3600
    except (TypeError, ValueError):
        print('TypeError - amp_EW')
        amp_EW = 0
        nb_errors += 1
        start_time = 0
        #os.remove(fname)

    # phase_NS
    list_of_files = glob.glob(path+'*'+station.name+receiver.file_endings[1] + '.mau')
    latest_file = max(list_of_files, key=os.path.getctime)
        #fname = shutil.copy2(f, pathdest)
    try :
        data = read_mat(latest_file)
        phase_NS = data['data']
        start_time = data['start_hour'] + data['start_minute']/60 + data['start_second']/3600
    except (TypeError, ValueError):
        print('TypeError - phase_NS')
        phase_NS = 0
        nb_errors += 1
        start_time = 0
        #os.remove(fname)
    
    Fs = data['Fs']
    tstep = 1/Fs/3600
    the_time = np.linspace(start_time, tstep*np.size(phase_EW), np.size(phase_EW))
    
    return (amp_NS, amp_EW, phase_NS, phase_EW, the_time, nb_errors)
