#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 27 11:42:43 2024

@author: pteysseyre
"""

import numpy as np


def find_break_point_realtime(the_time, data, delta=0.1):
    """
    Based on the incremental algorithm presented by Guralnik & Srivastava (1999)

    :param the_time: time-array
    :param data: the phase data that has just been read (time-averaged & smoothed if needed)
    :param delta: in percent/100 (default : 0.1). This is the threshold over which we
     decide that a breakpoint is indeed a breakpoint and not due to noise. In
     Guralnik & Srivastava's paper, this is also called delta and only appears
     for the incremental algorithm.

    :return: - detec: Boolean, 'True' if a breakpoint was detected, 'False' if not
     - p1: Slope of the detected breakpoint

    """

    L = len(data)

    if L > 9:  # At least 9 points are necessary for this

        # Compute likelihood assuming no breakpoints:
        likelihood_without_bp, n = _compute_likelihood_criteria(0, L, the_time, data)

        # Compute the likelihood criteria, assuming a breakpoint 5 points ago:
        likelihood_with_bp, p1 = _compute_likelihood_criteria_several_change_points(
            the_time, data, np.array([0, L - 6, L - 1])
        )

        # Determine whether there is a new breakpoint
        detec = (
            likelihood_without_bp - likelihood_with_bp
        ) / likelihood_without_bp > delta

    else:

        detec = False
        p1 = 0

    return detec, p1


def detect_change_points(the_time, data, threshold):
    """Based on Guralnik, V. & Srivastava, J. (1999)
    Detect change_points in the 'data' array in post_processing (bash algorithm)

    :param the_time: time-array
    :param data: Data array
    :param threshold: Criterion used to end the search for breakpoints. (s in the article)

    :return: change_points: time of breakpoints found in the data array"""

    # Initialisation
    change_points = np.array([0, len(data)])
    likelihood, dummy = _compute_likelihood_criteria(
        change_points[0], change_points[1], the_time, data
    )
    last_likelihood = likelihood
    stopping_criterion = 1
    loop_counter = 0

    while stopping_criterion > threshold and loop_counter < 1e3:

        loop_counter += 1
        N = len(change_points) - 1  # Number of segments

        for s in range(0, N):

            if change_points[s + 1] - change_points[s] > 5:
                new_candidate = _find_candidate_detection(
                    change_points[s], change_points[s + 1], the_time, data
                )
                temp_change_points = np.insert(change_points, s + 1, new_candidate)
                new_likelihood_criterion = (
                    _compute_likelihood_criteria_several_change_points(
                        the_time, data, temp_change_points
                    )
                )

                if new_likelihood_criterion < likelihood:
                    likelihood = new_likelihood_criterion
                    new_change_points = temp_change_points

        # Prepare for next iteration
        change_points = new_change_points
        stopping_criterion = (last_likelihood - likelihood) / last_likelihood

    return change_points


def _compute_likelihood_criteria_several_change_points(the_time, data, change_points):
    """Based on Guralnik, V., & Srivastava, J. (1999). Computes the total likelihood criterion for data,
     knowing that there are change_points at specified locations

    :param the_time: time-array
    :param data: Data in which to look for change points
    :param change_points: list of indices of the changepoints already computed.
     The first index is 0 (for the beggining of the 'data' array), the last is
     the number of elements in the 'data' array.

    :return: - total_L: total likelihood criterion
    - a: slope associated with the last breakpoint"""

    N = len(change_points) - 1
    total_L = 0

    for k in range(0, N):
        likelihood_criteria, a = _compute_likelihood_criteria(
            change_points[k], change_points[k + 1], the_time, data
        )
        total_L += likelihood_criteria

    return total_L, a


def _find_candidate_detection(i, j, the_time, data):
    """Based on Guralnik, V., & Srivastava, J. (1999).,

    Finds the best candidate to be a change-point in the array data[i:j].

    :param i: indice of the start of the interval of interest
    :param j: indice of the end of the interval
    :param the_time: time-array
    :param data: data array

    :return: the indice in the array data (! not data[i:j]!) of this best candidate.
    """

    optimal_likelihood_criteria = 1e14  # Minimum likelihood criteria. The point with the lowest likelihood criteria will be the best candidate
    split = 0

    for k in range(i + 2, j - 2):

        likelihood_first_segment, dummy = _compute_likelihood_criteria(
            i, k, the_time, data
        )
        likelihood_second_segment, dummy = _compute_likelihood_criteria(
            k + 1, j, the_time, data
        )
        likelihood_all_segments = likelihood_first_segment + likelihood_second_segment

        if likelihood_all_segments < optimal_likelihood_criteria:
            optimal_likelihood_criteria = likelihood_all_segments
            split = k

    return split


def _compute_likelihood_criteria(i, j, the_time, data):
    """Computes the likelihood criteria assuming an heteroscedastic error model.
    Based on Guralnik, V., & Srivastava, J. (1999, August). Event detection from time series data. In Proceedings of the fifth ACM SIGKDD international conference on Knowledge discovery and data mining (pp. 33-42).

    :param i: indice of the start of the interval of interest
    :param j: indice of the end of the interval
    :param the_time: time-array
    :param data: data array

    :return: - L, Likelihood criteria on the interval
        - a, slope of the linear fit for the data"""

    m = j - i + 1  # Number of elements in the the_time & data arrays

    a, b = np.polyfit(
        the_time[i : j + 1], data[i : j + 1], 1
    )  # Use a linear model to fit the segment. THIS CAN BE CHANGED !

    rss = np.sum(np.square(a * the_time[i : j + 1] + b - data[i : j + 1]))

    L = m * np.log(rss / m)

    return L, a
