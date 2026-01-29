#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""


from spacekernel.time cimport Time


cdef class CelestialBody:

    cdef:
        readonly Time time
        double[:, :] _r_GCRF, _v_GCRF


cdef class Earth(CelestialBody):
    """..."""


cdef class Sun(CelestialBody):

    @staticmethod
    cdef double[:, :] calculate_position(Time time)


cdef class Moon(CelestialBody):

    @staticmethod
    cdef void calculate_state_GCRF(Time time, double[:, :] r_GCRF, double[:, :] v_GCRF)