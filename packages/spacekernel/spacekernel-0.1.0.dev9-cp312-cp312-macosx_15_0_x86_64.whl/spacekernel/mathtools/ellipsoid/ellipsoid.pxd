#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

from libc.math cimport tan, atan

from spacekernel.datamodel cimport SurfCoord, ENU_Frame, LLA, AER, GeoState_t

cdef class Ellipsoid:

    cdef:
        readonly double Re, f, Rp

    cdef inline double c_reduced_lat_from_geodetic_lat(self, const double geodetic_lat) noexcept nogil:
        return atan(tan(geodetic_lat) * (1.0 - self.f))

    cdef inline double c_geodetic_lat_from_reduced_lat(self, const double reduced_lat) noexcept nogil:
        return atan(tan(reduced_lat) / (1.0 - self.f))

    cdef void surf_normal_vector(self, const SurfCoord point, double * u_normal) noexcept nogil

    cdef void surf_tangent_vector(self, const SurfCoord point, double * u_east, double * u_north) noexcept nogil

    cdef void c_enu(self, const SurfCoord point, ENU_Frame * enu) nogil

    cdef void c_surf_pos_from_surf_coord(self, const SurfCoord point, double[3] r_surf) nogil

    cdef void c_surf_coord_from_surf_pos(self, const double[3] r_surf, SurfCoord * point) nogil

    cdef double c_solve_reduced_lat_equation(self, const double[3] r) nogil

    cdef void c_lla_from_pos(self, const double[3] r, LLA * lla) nogil

    cdef void c_pos_from_lla(self, const LLA lla, double[3] r) nogil

    cdef void c_geodetic_state_from_state_vector(self, const double[3] r, const double[3] v, GeoState_t * geostate) nogil

    cdef void c_state_vector_from_geodetic_state(self, const GeoState_t geostate, double[3] r, double[3] v) nogil

    cdef void c_surf_pos_of_ray_first_intersection(self, const double[3] r_ray, const double[3] u_ray, double[3] r_surf) nogil

    cdef void c_aer_coords(self, const double[3] r_target, const LLA lla_obs, AER * aer) nogil


cpdef Ellipsoid create(str name)

cdef Ellipsoid WGS84
cdef Ellipsoid WGS72
cdef Ellipsoid GRS80