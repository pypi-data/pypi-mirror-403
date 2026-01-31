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

# To write result in file
import vlf4ions.manage_statefile as ms


# --------------------- Plots ------------------


def plot_probas(probas, flux, path_to_results, today, stations_on):
    """Plots the flux estimation from the values of DP. Returns the values above which there
    a 10%, 50% and 75% chance that the flux is.

    :param probas: probability density function estimated from the station DP
    :param flux: Defined internally, possible flux values (from 1e-6 to 1e-3 W/m^2)
    :param path_to_results: path to the place where the plot will be stored
    :type path_to_results: string
    :param today: Date and time of the call to the function (defined internally)
    :type today: datetime
    :param stations_on: Names of the stations which are transmitting in daytime
    :type stations_on: string

    :return: flux above which there is a 10%, 50% or 75% chance of the flux value being

    """

    ## Total probas
    integral = cumulative_simpson(probas)
    tenpercent = np.argmin(np.abs(integral / integral[-1] - 0.90))
    fiftypercent = np.argmin(np.abs(integral / integral[-1] - 0.50))
    seventyfive = np.argmin(np.abs(integral / integral[-1] - 0.25))
    best_guess = np.argmax(probas)

    flux = 10**flux

    # Prepare plot
    plt.rcParams.update({"font.size": 15})

    plt.figure()
    # plt.axvline(1e-5, linewidth=2, ls=':', color='k')
    # plt.axvline(1e-4, linewidth=2, ls=':', color='k')
    plt.plot(flux, probas, linewidth=3, color="#24492E")

    plt.axvline(
        flux[best_guess], color="#24492E", label="Best guess: %1.1e" % flux[best_guess]
    )
    plt.axvline(
        flux[tenpercent],
        color="#E69B99FF",
        label="P(flux > %1.1e) = 0.10" % flux[tenpercent],
    )
    plt.axvline(
        flux[fiftypercent],
        color="#BA7999FF",
        label="P(flux > %1.1e) = 0.50" % flux[fiftypercent],
    )
    plt.axvline(
        flux[seventyfive],
        color="#89689D",
        label="P(flux > %1.1e) = 0.75" % flux[seventyfive],
    )

    plt.fill_between(
        flux[seventyfive:-1], probas[seventyfive:-1], color="#89689D", alpha=0.5
    )
    plt.fill_between(
        flux[fiftypercent:-1], probas[fiftypercent:-1], color="#BA7999FF", alpha=0.5
    )
    plt.fill_between(
        flux[tenpercent:-1], probas[tenpercent:-1], color="#E69B99FF", alpha=0.5
    )

    plt.legend(loc="lower left", fontsize=10)
    plt.xscale("log")
    plt.xlabel("Flux (W/m^2)")
    plt.ylabel("Probability (a.u.)")
    plt.suptitle(today.strftime("%d/%m/%y %H:%M:%S"))
    plt.title(stations_on)
    plt.savefig(path_to_results + "last.pdf")
    plt.close()

    return (flux[tenpercent], flux[fiftypercent], flux[seventyfive], flux[best_guess])


# --------------------- Probabilities and forecast -------------------


class nowcast:
    """Looks at the state of all received stations, and estimate the X-flux from the Sun.
    If needed, sends alerts to specified recipients.

    :param stations: List of station class instances
    :param receiver: Receiver class instance
    :param alerts: List of potential alerts to send. Each alert may have different
     sender, recipients or trigger.
    :param reading_time: Second after the minute when the nowcast is done. It must not
     interfere with the times when the reading_time of each station. Default: ':00'.
    :param ten: Flux value above which there is a ten percent probability for the flux estimation
    :param fifty: Flux value above which there is a fifty percent probability for the flux estimation
    :param seventyfive: Flux value above which there is a seventy five percent probability for the flux estimation
    :param debug: If it is 1, show the values of DP for each station each time it is called. If it is 2, also show there flags
    """

    def __init__(
        self,
        stations,
        receiver,
        alerts,
        reading_time=":00",
        ten=6.6e-06,
        fifty=2.2e-06,
        seventyfive=1.4e-06,
        debug=0,
    ):

        self.stations = stations  # Stations to consider
        self.receiver = receiver
        self.alerts = alerts
        self.reading_time = reading_time
        self.ten = ten
        self.fifty = fifty
        self.seventyfive = seventyfive
        self.nb_stations_on = len(self.stations)
        self.debug = debug

    def run(
        self, path_to_probas, path_to_results, path_to_CSVfiles
    ):  # Compute flux estimate
        """Compute flux estimate and electron density over each path and plots them

        :param path_to_probas: path to the files where the mu/sigma values are stored for the probability computation
        :param path_to_results: path where the plots will be stored
        :param path_to_CSVfiles: path to the results from LMP"""

        today = dt.datetime.now(
            dt.timezone.utc
        )  # The time zone is necessary to use get_sza later

        flux = np.linspace(-6, -3, 1000).T

        # Uniform prior
        prior = np.ones((len(flux)))
        probas = prior

        # We keep track of stations which are on
        stations_on = ""
        nb_stations_on = 0
        quiet = 0

        for station in self.stations:

            if station.flag == 0:

                nb_stations_on += 1
                quiet += station.quiet
                stations_on = stations_on + " - " + station.name

                station.get_pdf_coeff(path_to_probas)
                proba_station = np.exp(-(((flux - station.mu) / station.sigma) ** 2))
                probas = probas * proba_station / prior

                if self.debug > 0:
                    # For a quick visual check
                    print(station.name + " -  DP: " + str(station.DP) + " °")

                # Compute Ne
                sza = srss.get_sza(today, station.lat, station.lon)
                H, B = ced.LMP_findminimum(station, sza, path_to_CSVfiles)
                station.Ne = ced.compute_Ne(70, H, B)

            if self.debug == 1:

                # For a quick visual check
                print(station.name + " -  Flag: " + str(station.flag))

        ten, fifty, seventyfive, best_guess = plot_probas(
            probas, flux, path_to_results, today, stations_on
        )
        pm.plot_map(self.stations, self.receiver, today, path_to_results)

        if (
            nb_stations_on > 1
        ):  # If there is no station, or only one station working, no alerts are sent

            # If this is the case for the first time, the user is warned
            if self.nb_stations_on == 1:

                for alert in self.alerts:
                    if alert.threshold == 0:
                        old_body = alert.body
                        old_subject = alert.subject
                        alert.body = "At least one transmitter is now usable - Flare detection is now possible again"
                        alert.subject = self.receiver.name + " - Working"
                        alert.send_email()
                        alert.body = old_body
                        alert.subject = old_subject
                        alert.sent_last_time = 0

            quiet = quiet / nb_stations_on

            # Write everything in a file
            ms.write_fluxestimate(
                best_guess, quiet, today, path_to_results, "nowcast", nb_stations_on
            )
            if self.debug == 2:
                print(quiet)
                print(best_guess)

            for alert in self.alerts:

                if alert.threshold > 0:
                    if ten > alert.threshold and alert.sent_last_time == 0:

                        # This is the beginning of the warning
                        alert.send_email()

                    elif ten < alert.threshold and alert.sent_last_time == 1:

                        # This is its end
                        old_body = alert.body
                        alert.body = "End of alert"
                        alert.send_email()
                        alert.body = old_body
                        alert.sent_last_time = 0

                    elif (
                        alert.send_each_change
                        and (
                            np.abs(ten - self.ten) / self.ten > 0.1
                            or np.abs(fifty - self.fifty) / self.fifty > 0.1
                            or np.abs(seventyfive - self.seventyfive) / self.seventyfive
                            > 0.1
                        )
                        and self.nb_stations_on == nb_stations_on
                        and quiet < 1
                        and ten > alert.threshold
                    ):

                        # This is sent each time the flux estimation changes
                        alert.send_email()
                        self.ten = ten
                        self.fifty = fifty
                        self.seventyfive = seventyfive

        else:  # We need to warn people that no stations are usable at this point

            for alert in self.alerts:
                if alert.threshold == 0 and alert.sent_last_time == 0:
                    old_body = alert.body
                    old_subject = alert.subject
                    alert.body = "All transmitters are off or in nighttime - No flare detection is possible"
                    alert.subject = self.receiver.name + " - On hold"
                    alert.send_email()
                    alert.body = old_body
                    alert.subject = old_subject
                    alert.sent_last_time = 1

                # Make sure to signal internally end of alert (do not send emails)
                elif ten < alert.threshold and alert.sent_last_time == 1:
                    alert.send_last_time = 0

        self.nb_stations_on = nb_stations_on

        print("Nowcast - ", today.strftime("%H:%M:%S"), " - Done")
