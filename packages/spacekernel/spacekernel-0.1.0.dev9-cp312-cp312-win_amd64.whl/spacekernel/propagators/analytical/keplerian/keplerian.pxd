#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""


from spacekernel.propagators.propagators cimport Propagator

from spacekernel.time cimport Time
from spacekernel.state cimport COE
from spacekernel.state.ephemeris cimport COEEphemeris


cdef class Keplerian(Propagator):

    cdef:
        readonly double GM

    cdef double[:] propagate_tra(self, double[:] t, double tra0, double ecc, double mnm)

    cdef COEEphemeris c_propagate_state(self, Time time, COE coe)

    cdef void c_jacobian(self, double[3] r, double[6][6] jac) nogil

    cdef void c_jac_r(self, Time time, double[3] r, double[3] v, double[3][3] jac_r) nogil