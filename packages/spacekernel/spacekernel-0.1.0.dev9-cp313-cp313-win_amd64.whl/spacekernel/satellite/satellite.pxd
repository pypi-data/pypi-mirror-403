#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

from spacekernel.time cimport Time
from spacekernel.propagators cimport Propagator

# ctypedef unsigned long long u64
#
# cdef:
#     const u64 CIRCULAR_BIT = 1 << 0
#     const u64 ELLIPTIC_BIT = 1 << 1
#     const u64


cdef class Satellite:

    cdef:
        Time time

        Propagator propagator

        str _name, _description