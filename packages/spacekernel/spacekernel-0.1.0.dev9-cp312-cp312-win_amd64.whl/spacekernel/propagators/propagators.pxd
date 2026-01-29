#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

from spacekernel.time cimport Time

cdef class Propagator:
    """"""

    cdef void c_jac_r(self, Time time, double[3] r, double[3] v, double[3][3] jac_r) nogil
    cdef void c_jac_v(self, Time time, double[3] r, double[3] v, double[3][3] jac_v) nogil
    cdef void c_jac_x(self, Time time, double[3] r, double[3] v, double[6][6] jac_x) nogil