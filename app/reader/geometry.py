"""Geometry utils"""

import numpy as np

def get_euler_distance(pt1, pt2):
    """Returns distance between two points in two-dimentional space"""
    return np.sqrt(np.square(pt1[0] - pt2[0]) + np.square(pt1[1] - pt2[1]))
