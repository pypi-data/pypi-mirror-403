#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

from spacekernel.time cimport jd_t
from numpy cimport ndarray, npy_datetime, int64_t


cdef class Time:

    cdef:
        Py_ssize_t[2] shape
        Py_ssize_t[2] strides
        Py_ssize_t length
        str _scale  # should this be changed to bytes?
        bint _is_scalar
        jd_t[:, :] _jd12  # SOFA internal format
        int64_t[:] _int64_buf