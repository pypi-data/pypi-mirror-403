#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""


from spacekernel.utils cimport Representable

from spacekernel.time cimport Time
from spacekernel.frames cimport Frame
from spacekernel.mathtools.ellipsoid cimport Ellipsoid


cdef class Ephemeris(Representable):

    cdef:
        readonly Frame frame
        readonly Time epoch

        double[:] _mass
        Py_ssize_t index


cdef class StateVectorEphemeris(Ephemeris):

    cdef:
        double[:, :] _r, _v


cdef class COEEphemeris(Ephemeris):

    cdef:
        double[:] _ecc, _sma, _inc, _raa, _arp, _tra, _slr
        readonly double GM, Re


cdef class GeoStateEphemeris(Ephemeris):

    cdef:
        readonly double[:] _lon, _lat, _alt, _lon_dot, _lat_dot, _alt_dot
        readonly Ellipsoid ell