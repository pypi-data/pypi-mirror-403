#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 10:00:48 2024

@author: pteysseyre
"""

from setuptools import find_packages, setup

setup(
    name='vlf4ions',
    packages=find_packages(include=['vlf4ions']),
    version='1.3.1',
    description='Functions necessary to analyse in real time the output of an AWESOME antenna and detect any solar flare',
    author='P. Teysseyre',
    install_requires=['pymatreader', 
                      'datetime', 
                      'schedule', 
                      'pandas', 
                      'numpy==1.26.4', 
                      'basemap', 
                      'matplotlib==3.8.0',
                      'pysolar',
                      'pytz',
                      'scipy', 
                      ],
)