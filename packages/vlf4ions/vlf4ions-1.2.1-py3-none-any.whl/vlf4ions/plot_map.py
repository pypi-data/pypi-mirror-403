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

def plot_map(stations_l, thisreceiver, today, Nemax=1e10):

    '''Plots the current state on a geographical map'''

    fig, ax = plt.subplots(1, 1, figsize=(6, 8))  # setup the plot
    m = Basemap(llcrnrlon=-72,
            llcrnrlat=35,
            urcrnrlon=25,
            urcrnrlat=60,
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

    return m


def get_latlong(la_station, file):
    ''' Returns the latitude and longitude of the station considered, from the 'file' given as input'''

    stations = pd.read_csv(file)

    station = stations[stations.Callsign == la_station]
    lat = station.iloc[0]['Latitude']
    long = station.iloc[0]['Longitude']
    Ne = station.iloc[0]['Ne']

    return lat, long, Ne


