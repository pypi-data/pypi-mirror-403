#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  7 14:28:49 2025

@author: pteysseyre
"""

import numpy as np
import vlf4ions.compute_electron_density as cne


def analyse_breakpoint(la_station, amp, phase, the_time, pathtoCSVfiles, current_p1, current_time, last_p1, last_time, quiet, Ne_max, Ne_quiet, quiet_phase, quiet_amp):
    
    """This is the part of the code that will decide if the  breakpoint is a flare signature or not.

    Several cases can occur:
        
        1) This is the beginning of a flare. In this case, we can estimate the current X-ray strength and electron density
        by taking as a reference the last 'quiet' breakpoint. We can also estimate the state of the ionosphere in 1 and 5 min 
        assuming that the trend doesn't change
        
        2) This is the first brekapoint to signal a flare decay. We can estimate the current X-ray flux, electron density, and
        give an estimate of when things will have decreased to half of their increase
        
        3) This is a quiet point: this is either a slight positive slope, a negative slope after a quiet breakpoint, or a negative 
        slope after a flare has decayed by more than half of its increase
        
        4) This is a flare decay, but this is not the first detection and the flare has not gone down by more than half of its
        increase. We can update the estimated X-ray flux and Ne, and estimate the new time to the end of the flare
        
        Parameters:
        ---------------------------
        
        - la_station, amp, phase: the transmitter, recorded amplitude (in pT), recorded & corrected phase (in °) since beginning of file
        - the_time: time-array. Dimension should match amp & phase
        - pathtoCSVfiles: path to access the CSV files obtained with the LMP model
        - current_p1, current_time : current breakpoint slope detected and time  of detection
        - last_p1 , last_time: last  breakpoint slope detected and time of detection
        - quiet: is True if the last brealpoint detected was a quiet breakpoint. Is False otherwise (flares)
        - Ne_max, Ne_quiet: same values if the last point is quiet, else Ne_max is the maximum Ne at the peak of flare, 
            and Ne_quiet is the reference taken for the decay 
        - quiet_phase, quiet_amp: last read phase & amp (to avoid reading it and looking for it)
        
        Outputs:
        ---------------------------
    
        - quiet_now : is True if the current breakpoint is in quiet time, False otherwise
        - flux : estimated X-ray flux and confidence interval
        - Ne : estimated electron density 
        - Ne_max : maximum of the electron density (in case of flare, else is zero)
        - prev_1min : estimated Ne in 1 min
        - prev_5min : estimated Ne in 5 min
        - prev_timedecay : estimated time of decay 
        
        
        IMPORTANT NOTE:
        --------------------------
        1) Right now (Feb. 2025), we are concentrating on the phase (Ne in code is phase). 
        However, we can for a second step concentrate on the electron density at an altitude of 70 km; 
        moreover, the interesting quantity for us is the HF absorption. Thus, in the future, the HF absorption should be 
        computed and the time of the flare's decay, as well as the previsions for the next minutes or so should be based
        on this quantity instead.
        
        2) Right now (Feb. 2024), the quiet electron density is estimated to be given by H = 74 km and B = 0.3 km^-1 in 
        Wait's model. This can easily be improved upon by using different values from the works by Thomson for example.
        
        Documentation and diagrams:
        ----------------------------
        See project vlf4ions on GitLab, 'Redaction.zip' for the full documentation """
        
    ### TODO: Think about the flares happening is a very quiet sucession
    
    # Initialisation: most of what is returned will not be systematically useful
    flux, Ne, prev_timedecay, Ne_max, prev_1min, prev_5min = np.zeros(6)
    quiet_now = False 
    
    
    if current_p1 > 0:
            
        if current_p1 < 10: # TODO: update to 'real' threshold
            quiet_now = True
            
        else: # This is a flare
            
            # DP # TODO: change for Ne or abs
            DP = phase[-1] - quiet_phase
            DA = amp[-1] - quiet_amp
                
            # Compute Ne here
            # TODO: Estimate X-ray flux here
            
            # Estimate phase in 1 or 5 min
            prev_1min = current_p1*1/60 + phase[-1]
            prev_5min = current_p1*5/60 + phase[-1]
                
            
    else: # This is either quiet time, or a flare's decay
        
        if quiet: # Last breakpoint is quiet
            quiet_now = True
            
        else: # Last breakpoint was a flare decay
        
            if last_p1 > 0: # Last breakpoint was a flare onset
                
                ### TODO: Use Ne instead of phase
                
                
                # We look for the phase maximum to get DP 
                the_time, phase = _keep_between(phase, the_time, last_time, current_time)
                ind_max = np.argmax(phase)
                DNe = phase[ind_max] - Ne_quiet
                time_max = the_time[ind_max]
                
                # We estimate the decay time assuming that the trend is constant & the decay linear
                prev_timedecay = -DNe/(2*current_p1) + time_max
                Ne_max = phase[-1] ### TODO: change for Ne or absorption
                
            else :
                
                # Check if the flare has decayed (lost more than half its increase)
                ### TODO: change for Ne or abs
                
                current_DNe = phase[-1] - Ne_quiet
                DNe = Ne_max - Ne_quiet
                
                if current_DNe < DNe/2: # The flare has ended
                    quiet_now = True
                
                else: # The flare is still ongoing but we can update our previsions
                    prev_timedecay = 1/current_p1*(DNe/2 - current_DNe) + the_time[-1]
                    
                
                
    return (quiet_now, flux, Ne, Ne_max, prev_1min, prev_5min, prev_timedecay)



def _keep_between(data, the_time, time_inf, time_sup):
    
    """ This is just a short bit of code to constrain the data between time_inf & time_sup """
    
    if len(data) != len(the_time):
        
        print('Careful, lengths do not match - keep_betwween')
        
    else:
        
        ind_inf = np.argmin(np.abs(the_time - time_inf))
        ind_sup = np.argmin(np.abs(the_time - time_sup))
        
        the_time = the_time[ind_inf:ind_sup]
        data = data[ind_inf:ind_sup]
        
        return the_time, data
        
                
            
            
            
            
                
            
            

            
    
     