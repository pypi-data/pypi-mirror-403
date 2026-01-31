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
    version='1.3.3b1',
    description='Functions necessary to analyse in real time the output of an AWESOME antenna and detect any solar flare',
    author='P. Teysseyre',
    install_requires=['pymatreader==1.0.0',
                      'schedule==1.2.2',
                      'pandas==2.2.3',
                      'numpy==1.26.4',
                      'basemap==1.4.1',
                      'matplotlib==3.8.0',
                      'pysolar==0.13',
                      'pytz==2025.2',
                      'scipy==1.15.2',
                      'datetime==5.5',
                      'pre-commit==4.2.0',
                      'pytest==8.3.5',
                      'coverage==7.8.0',
                      ],
)
