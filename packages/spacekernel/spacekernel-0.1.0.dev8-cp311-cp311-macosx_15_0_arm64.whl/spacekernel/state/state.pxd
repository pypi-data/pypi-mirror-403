#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""


from spacekernel.time cimport Time
from spacekernel.frames cimport Frame
from spacekernel.bodies.bodies cimport CelestialBody
from spacekernel.mathtools.ellipsoid cimport Ellipsoid, WGS84

from spacekernel.datamodel cimport COE_t, GeoState_t
from spacekernel.utils cimport Representable

# ========== ========== ========== ========== ========== ========== State
cdef class State(Representable):

    cdef:
        readonly Time epoch
        readonly Frame frame
        readonly double mass


cdef class StateVector(State):

    cdef:
        double[3] _r, _v


cdef class COE(State):

    cdef:
        readonly double ecc, sma, inc, raa, arp, tra, slr, GM, Re

    cdef void to_struct(self, COE_t * coe) nogil


cdef class GeoState(State):

    cdef:
        readonly double lon, lat, alt, lon_dot, lat_dot, alt_dot
        readonly Ellipsoid ell

    cdef void to_struct(self, GeoState_t * geo) nogil

