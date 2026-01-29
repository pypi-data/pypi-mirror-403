#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

from numpy cimport ndarray

from spacekernel.time cimport Time
from spacekernel.bodies cimport Sun, Moon, Earth
from spacekernel.mathtools.ellipsoid cimport Ellipsoid


cdef class Scenario:

    cdef:
        readonly Time time

        readonly Sun sun
        readonly Earth earth
        readonly Moon moon
        readonly Ellipsoid ellipsoid

        str _name, _description, _author

        ndarray _rot_GCRF_from_ITRF



