#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

from spacekernel.time cimport Time
from spacekernel.datamodel cimport LLA
from spacekernel.mathtools.ellipsoid cimport Ellipsoid

cdef class Frame:
    """"""

    cdef public object _transforms

# ========== ========== ========== ========== ========== ========== GCRF
cdef class _GCRF(Frame):
    """"""

    cdef void c_to_ITRF(self,
                           Time time,
                           double[:, :] r_GCRF,
                           double[:, :] v_GCRF,
                           double[:, :] r_ITRF,
                           double[:, :] v_ITRF)

cdef _GCRF GCRF


# ========== ========== ========== ========== ========== ========== ITRF
cdef class _ITRF(Frame):

    cdef void c_to_GCRF(self,
                        Time time,
                        double[:, :] r_ITRF,
                        double[:, :] v_ITRF,
                        double[:, :] r_GCRF,
                        double[:, :] v_GCRF)

    cdef void c_to_TEME(self,
                         Time time,
                         double[:, :] r_ITRF,
                         double[:, :] v_ITRF,
                         double[:, :] r_TEME,
                         double[:, :] v_TEME)

cdef _ITRF ITRF


# ========== ========== ========== ========== ========== ========== TEME
cdef class _TEME(Frame):

    cdef void c_to_ITRF(self,
                        Time time,
                        double[:, :] r_TEME,
                        double[:, :] v_TEME,
                        double[:, :] r_ITRF,
                        double[:, :] v_ITRF)

cdef _TEME TEME


# ========== ========== ========== ========== ========== ========== ENU
cdef class ENU(Frame):

    cdef:
        readonly Ellipsoid ell
        double[3] r_gs  # ground station
        LLA lla

    cdef void c_rot_to_ITRF(self, double[3][3] rot) nogil
    cdef void c_rot_from_ITRF(self, double[3][3] rot) nogil
    cdef void c_to_ITRF(self,
                            Time time,
                            const double[:, :] r_ENU,
                            const double[:, :] v_ENU,
                            double[:, :] r_ITRF,
                            double[:, :] v_ITRF) nogil
    cdef void c_from_ITRF(self,
                              Time time,
                              const double[:, :] r_ITRF,
                              const double[:, :] v_ITRF,
                              double[:, :] r_ENU,
                              double[:, :] v_ENU) nogil