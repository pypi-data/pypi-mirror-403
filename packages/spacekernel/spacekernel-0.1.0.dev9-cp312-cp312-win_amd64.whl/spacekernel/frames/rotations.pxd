#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

from spacekernel.sofa cimport iauIr, iauRx, iauRy, iauRz
from spacekernel.sofa cimport iauEra00
from spacekernel.sofa cimport iauSp00, iauPom00



# ========== ========== ========== ========== ========== TIRS - CIRS
cdef inline void rot_TIRS_from_CIRS(double jd1_tt,
                                    double jd2_tt,
                                    double[3][3] rot) nogil:
    """..."""
    iauIr(rot)
    iauRz(iauEra00(jd1_tt, jd2_tt), rot)

# ========== ========== ========== ========== ========== ITRF - TIRS
cdef inline void rot_ITRF_from_TIRS_IERS1996(double xp,
                                             double yp,
                                             double[3][3] rot) nogil:
    """
    From section 5.2 of sofa_pn_c.pdf cookbook
    """
    iauIr(rot)
    iauRx(-yp, rot)
    iauRy(-xp, rot)


cdef inline void rot_ITRF_from_TIRS_IERS2003(double jd1_tt,
                                             double jd2_tt,
                                             double xp,
                                             double yp,
                                             double[3][3] rot) nogil:
    """
    From sections 5.3, 5.4, 5.5, and 5.6 of sofa_pn_c.pdf cookbook
    """
    iauPom00(xp, yp, iauSp00(jd1_tt, jd2_tt), rot)