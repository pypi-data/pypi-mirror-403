#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

from spacekernel.time cimport Time
from spacekernel.utils cimport Representable


cdef packed struct TLE_t:
    char[70] line1
    char[70] line2



cdef class TLE(Representable):

    cdef:

        char[70] _line1
        char[70] _line2
        bint strict_validation

        char[6] _satno

        readonly Time epoch
        readonly double inc, raa, ecc, mea, arp, mnm, sma, orp, eca, tra, pge, apg

    cdef void parse_line1(self)

    cdef void parse_line2(self) nogil


cdef class ELSET(Representable):
    """TODO: must behave like Ephemeris"""

    cdef:
        readonly Time epoch
        int _satno

        list[TLE] elements
        double[:] _ecc, _sma, _inc, _raa, _arp, _tra
        double[:] _mnm, _orp, _eca, _mea, _pge, _apg