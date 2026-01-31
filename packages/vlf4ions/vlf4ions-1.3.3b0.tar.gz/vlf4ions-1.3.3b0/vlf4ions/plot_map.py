#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 15 14:48:32 2025

@author: pteysseyre
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from mpl_toolkits.basemap import Basemap
import matplotlib.cm as cm
from operator import attrgetter

def plot_map(stations_l, thisreceiver, today, path_to_results, Nemax=1e10):
    '''Plots the current state on a geographical map
    
    :param stations_l: list of station class instances
    :param this_receiver: Receiver class instance
    :param today: Datetime (in UT !) of interest
    :param path_to_results: path to where the plot will be stored
    :param Ne_max: Maximum possible electron density to ajust the colorbar (default, 1e11 m^-3). Automatically adjusted if Ne for a function is more than Nemax.'''

    # Automatically center the map on the receiver/transmitters' paths
    max_lat = max(stations_l, key=attrgetter('lat'))
    max_lat = max_lat.lat
    max_lat = max(max_lat, thisreceiver.lat) + 5
    max_lon = max(stations_l, key=attrgetter('lon'))
    max_lon = max_lon.lon
    max_lon = max(max_lon, thisreceiver.lon) + 5
    min_lat = min(stations_l, key=attrgetter('lat'))
    min_lat = min_lat.lat
    min_lat = min(min_lat, thisreceiver.lat) - 5
    min_lon = min(stations_l, key=attrgetter('lon'))
    min_lon = min_lon.lon
    min_lon = min(min_lon, thisreceiver.lon) - 5
    max_Ne = max(stations_l, key=attrgetter('Ne'))
    max_Ne = max_Ne.Ne

    if max_Ne > Nemax:
        Ne_max = max_Ne

    fig, ax = plt.subplots(1, 1, figsize=(6, 8))  # setup the plot
    m = Basemap(llcrnrlon=min_lon,
            llcrnrlat=min_lat,
            urcrnrlon=max_lon,
            urcrnrlat=max_lat,
            projection='merc')
    m.drawmapboundary(fill_color='white', linewidth=0)
    m.fillcontinents(color='grey', alpha=0.7, lake_color='grey')
    m.drawcoastlines(linewidth=0.1, color="white")
    
    norm = mpl.colors.LogNorm(vmin=1e8, vmax=Nemax)
    cmap = cm.RdYlGn_r
    sm = cm.ScalarMappable(norm=norm, cmap=cmap)
    m.nightshade(today, alpha=0.25)
        

    for st in stations_l:

        color  = sm.to_rgba(st.Ne)

        if st.flag == 0:
            m.drawgreatcircle(st.lon, st.lat, thisreceiver.lon, thisreceiver.lat, linestyle = '-',  linewidth=3, color=color)
            
            if st.name == 'GQD':
                plt.annotate(st.name, xy=m(st.lon+3, st.lat), xytext =(-40, -4), textcoords='offset points', fontsize = 12)
            else:
                plt.annotate(st.name, xy=m(st.lon+3, st.lat), xytext =(1, -5), textcoords='offset points', fontsize = 12)

    
    
    sm = cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([]) # can be an empty list, only needed for matplotlib < 3.1
    # ...
    cb = fig.colorbar(sm, ax=ax, orientation = 'horizontal', pad = 0.02)
    cb.set_label('Ne ($m^{-3}$)', rotation=360)
    plt.title(today.strftime("%d/%m/%y %H:%M:%S"))
    plt.savefig(path_to_results + 'last_map.pdf')
    plt.close()

    return 


