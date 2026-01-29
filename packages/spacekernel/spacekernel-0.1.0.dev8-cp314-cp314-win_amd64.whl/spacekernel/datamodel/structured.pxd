#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

# ========== ========== ========== ========== ========== SurfCoord struct
cdef packed struct SurfCoord:
    double lat
    double lon


# ========== ========== ========== ========== ========== LLA struct
cdef packed struct LLA:
    double lat
    double lon
    double alt


# ========== ========== ========== ========== ========== GeodeticState
# cdef packed struct GeodeticState:
#     double lat
#     double lon
#     double alt
#     double lat_dot
#     double lon_dot
#     double alt_dot

cdef packed struct GeoState_t:
    double lat
    double lon
    double alt
    double lat_dot
    double lon_dot
    double alt_dot

# ========== ========== ========== ========== ========== Classical Orbital Elements
cdef packed struct COE_t:
    double ecc
    double sma
    double inc
    double raa
    double arp
    double tra
    double slr



# ========== ========== ========== ========== ========== ENU struct
cdef packed struct ENU_Frame:
    double[3] u_east
    double[3] u_north
    double[3] u_up


# ========== ========== ========== ========== ========== AER struct
cdef packed struct AER:
    double azimuth
    double elevation
    double range

# ========== ========== ========== ========== ========== Datetime fields
cdef packed struct DTF:  # datetime fields
    unsigned short year
    unsigned char month
    unsigned char day
    unsigned char hour
    unsigned char minute
    double second