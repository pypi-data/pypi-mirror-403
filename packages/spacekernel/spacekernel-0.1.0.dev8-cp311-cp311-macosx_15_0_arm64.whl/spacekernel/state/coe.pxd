#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

from libc.math cimport INFINITY, NAN, pi
from libc.math cimport acos, sin, cos
from libc.math cimport sqrt, cbrt, fabs

from spacekernel.datamodel cimport COE_t
from spacekernel.mathtools.misc cimport atan2_asymmetric as atan2


# cdef inline double _2PI = 2*pi

DEF _2PI = 6.283185307179586

# ========== ========== ========== ========== Conversion between SMA, MNM and ORP
cdef inline double c_orp_from_sma(const double sma, double GM) nogil:
    return _2PI * sma * sqrt(sma / GM)

cdef inline double c_sma_from_orp(const double orp, double GM) nogil:
    return cbrt(GM * orp / _2PI * orp / _2PI)

cdef inline double c_mnm_from_sma(const double sma, double GM) nogil:
    return sqrt(GM / sma) / sma

cdef inline double c_sma_from_mnm(const double mnm, double GM) nogil:
    return cbrt(GM / mnm / mnm)

# ========== ========== ========== ========== Conversion between anomalies
cdef double c_eca_from_mea(const double mea, const double ecc) nogil

cdef inline double c_mea_from_eca(const double eca, const double ecc) nogil:
    return eca - ecc * sin(eca)

cdef inline double c_eca_from_tra(const double tra, const double ecc) nogil:
    return atan2(sqrt(1.0 - ecc*ecc) * sin(tra), (ecc + cos(tra)))

cdef inline double c_tra_from_eca(const double eca, const double ecc) nogil:
    return atan2(sqrt(1.0 - ecc*ecc) * sin(eca), cos(eca) - ecc)

cdef inline double c_tra_from_mea(const double mea, const double ecc) nogil:
    return c_tra_from_eca(c_eca_from_mea(mea, ecc), ecc)

cdef inline double c_mea_from_tra(const double tra, const double ecc) nogil:
    return c_mea_from_eca(c_eca_from_tra(tra, ecc), ecc)

# ========== ========== ========== ========== conversion using Apogee and Perigee
# ========== ========== ========== ========== ========== ==========
# APOGEE, PERIGEE <=> SMA, ECC
# ========== ========== ========== ========== ========== ==========
cdef inline double c_pge_from_sma_ecc(const double sma, const double ecc, const double Re) nogil:
    return sma * (1.0 - ecc) - Re

cdef inline double c_apg_from_sma_ecc(const double sma, const double ecc, const double Re) nogil:
    return sma * (1.0 + ecc) - Re

# ---------- ---------- ---------- ---------- retrieving sma
cdef inline double c_sma_from_pge_apg(const double pge, const double apg, const double Re) nogil:
    return 0.5 * (pge + apg) + Re

cdef inline double c_sma_from_ecc_pge(const double ecc, const double pge, const double Re) nogil:
    return (pge + Re) / (1.0 - ecc)

cdef inline double c_sma_from_ecc_apg(const double ecc, const double apg, const double Re) nogil:
    return (apg + Re) / (1.0 + ecc)

# ---------- ---------- ---------- ---------- retrieving ecc
cdef inline double c_ecc_from_pge_apg(const double pge, const double apg, const double Re) nogil:
    return (apg - pge) / (pge + apg + Re + Re)

cdef inline double c_ecc_from_sma_pge(const double sma, const double pge, const double Re) nogil:
    return 1.0 - (pge + Re) / sma

cdef inline double c_ecc_from_sma_apg(const double sma, const double apg, const double Re) nogil:
    return (apg + Re) / sma - 1.0

# ========== ========== ========== ==========  COE -> SV
cdef void c_coe_from_sv(const double[3] r,
                        const double[3] v,
                        const double GM,
                        COE_t* coe) nogil

cdef void c_sv_from_coe(const COE_t coe,
                        const double GM,
                        double[3] r,
                        double[3] v) nogil