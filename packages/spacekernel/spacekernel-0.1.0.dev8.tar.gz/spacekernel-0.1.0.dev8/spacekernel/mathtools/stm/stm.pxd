#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

from numpy cimport ndarray

from spacekernel.time cimport Time


cdef class StateTransitionMatrix:

    cdef:
        readonly Time time
        readonly ndarray t

        readonly object spline_jac, spline_Phi_t_t0, spline_Phi_tf_t