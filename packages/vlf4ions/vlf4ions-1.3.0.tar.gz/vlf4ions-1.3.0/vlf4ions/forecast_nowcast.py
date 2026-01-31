# From probas computations
from scipy.stats import norm
from scipy.integrate import cumulative_simpson

# General
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt
from datetime import datetime

# To compute electron density
import vlf4ions.compute_electron_density as ced
import vlf4ions.plot_map as pm
import vlf4ions.sunrise_sunset as srss


# --------------------- Plots ------------------

def plot_probas(probas, flux, path_to_results):

    ## Total probas
    integral = cumulative_simpson(probas)
    tenpercent = np.argmin(np.abs(integral/integral[-1] - 0.90))
    fiftypercent = np.argmin(np.abs(integral/integral[-1] - 0.50))
    seventyfive = np.argmin(np.abs(integral/integral[-1] - 0.25))
    best_guess = np.argmax(probas)

    flux = 10**flux

    # Prepare plot
    plt.rcParams.update({'font.size': 15})

    plt.figure()
    plt.axvline(1e-5, linewidth=2, ls=':', color='k')
    plt.axvline(1e-4, linewidth=2, ls=':', color='k')
    plt.plot(flux, probas, linewidth=3, color='#24492E', label='Posterior distribution')

    plt.axvline(flux[best_guess], color='#24492E', label='Best guess: %1.1e'%flux[best_guess])
    plt.axvline(flux[tenpercent], color='#E69B99FF', label='P(flux > %1.1e) = 0.10'%flux[tenpercent])
    plt.axvline(flux[fiftypercent], color='#BA7999FF', label='P(flux > %1.1e) = 0.50'%flux[fiftypercent])
    plt.axvline(flux[seventyfive], color='#89689D', label='P(flux > %1.1e) = 0.75'%flux[seventyfive])

    plt.fill_between(flux[seventyfive:-1], probas[seventyfive:-1], color='#89689D', alpha=0.5)
    plt.fill_between(flux[fiftypercent:-1], probas[fiftypercent:-1], color='#BA7999FF', alpha=0.5)
    plt.fill_between(flux[tenpercent:-1], probas[tenpercent:-1], color='#E69B99FF', alpha=0.5)

    plt.legend(loc='lower left', fontsize=10)
    plt.xscale('log')
    plt.xlabel('Flux (W/m^2)')
    plt.ylabel('Probability (a.u.)')
    plt.savefig(path_to_results + 'last.pdf')
    plt.close()

    return(flux[tenpercent], flux[fiftypercent], flux[seventyfive])

# --------------------- Probabilities and forecast -------------------

class nowcast:

    def __init__(self, stations, receiver, alerts, reading_time=':00', ten=6.6e-06, fifty=2.2e-06, seventyfive=1.4e-06):

        self.stations = stations # Stations to consider
        self.receiver = receiver
        self.alerts = alerts
        self.reading_time = reading_time
        self.ten = ten
        self.fifty = fifty
        self.seventyfive = seventyfive
    
    def run(self, path_to_probas, path_to_results, path_to_CSVfiles): # Compute flux estimate

        today = dt.datetime.now(dt.timezone.utc) # The time zone is necessary to use get_sza later

        flux = np.linspace(-6, -3, 1000)
        prior = norm(-6, 1)
        probas = prior.pdf(flux)

        for station in self.stations:

            if station.flag == 0:
                station.get_pdf_coeff(path_to_probas)
                proba_station = norm(station.mu, station.sigma)
                probas = probas*proba_station.pdf(flux)
        
                # For a quick visual check 
                # print(station.name + ' -  DP: ' + str(station.DP) + ' °')
            
                # Compute Ne
                sza = srss.get_sza(today, station.lat, station.lon)
                H, B = ced.LMP_findminimum(station, sza, path_to_CSVfiles)
                station.Ne = ced.compute_Ne(70, H, B)

            #else:

                # For a quick visual check 
                # print(station.name + ' -  Flag: ' + str(station.flag))
        
        ten, fifty, seventyfive = plot_probas(probas, flux, path_to_results)
        pm.plot_map(self.stations, self.receiver, today, path_to_results)

        for alert in self.alerts:

            if ten > alert.threshold and alert.sent_last_time == 0: 

                # This is the beginning of the warning
                alert.send_email()

            elif ten < alert.threshold and alert.sent_last_time == 1:

                # This is its end
                old_body = alert.body
                alert.body = 'End of alert'
                alert.send_email()
                alert.body = old_body
                alert.sent_last_time = 0
            
            elif alert.send_each_change and (np.abs(ten - self.ten)/self.ten > 0.1 or np.abs(fifty - self.fifty)/self.fifty > 0.1 or np.abs(seventyfive - self.seventyfive)/self.seventyfive > 0.1):

                alert.send_email()
                self.ten = ten
                self.fifty = fifty
                self.seventyfive = seventyfive 

        print('Nowcast - ', today.strftime("%H:%M:%S"), ' - Done')
                


class forecast:

    def __init__(self, stations):

        self.stations = stations

