#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""


from libc.math cimport sqrt, acos

cdef inline void scale(const double scalar, const double[3] a, double[3] c) nogil:
    c[0] = scalar * a[0]
    c[1] = scalar * a[1]
    c[2] = scalar * a[2]

cdef inline void add(const double[3] a, const double[3] b, double[3] c) nogil:
    c[0] = a[0] + b[0]
    c[1] = a[1] + b[1]
    c[2] = a[2] + b[2]

cdef inline void sub(const double[3] a, const double[3] b, double[3] c) nogil:
    c[0] = a[0] - b[0]
    c[1] = a[1] - b[1]
    c[2] = a[2] - b[2]

cdef inline double dot(const double[3] a, const double[3] b) nogil:
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]


cdef inline void cross(const double[3] a, const double[3] b, double[3] c) nogil:
    c[0] = a[1]*b[2] - a[2]*b[1]
    c[1] = a[2]*b[0] - a[0]*b[2]
    c[2] = a[0]*b[1] - a[1]*b[0]


# ========== ========== ========== ========== ========== ==========
cdef inline double norm(const double[3] a) nogil:
    return sqrt(dot(a, a))

cdef double[:] norm_array(const double[:, :] a)


# ========== ========== ========== ========== ========== ==========
cdef inline double angle(const double[3] a, const double[3] b) nogil:
    return acos(dot(a, b) / norm(a) / norm(b))


# ========== ========== ========== ========== ========== ==========
cdef inline void normalize(const double[3] a, double[3] u) nogil:
    scale(1.0 / norm(a), a, u)

cdef double[:, :] normalize_array(const double[:, :] a)

# ========== ========== ========== ========== ========== ==========
cdef void mat_x_vec(const double[3][3] M, const double[3] a, double[3] b) nogil

cdef void mat_x_mat(const double[3][3] A, const double[3][3] B, double[3][3] C) nogil

cdef void mat_transpose(const double[3][3] A, double[3][3] C) nogil