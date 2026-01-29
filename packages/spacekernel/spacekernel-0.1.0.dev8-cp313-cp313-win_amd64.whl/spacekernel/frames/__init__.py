#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

from .geocentric import TEME_from_ITRF, ITRF_from_TEME, GCRF_from_ITRF, ITRF_from_GCRF

from .frames import get_GCRF, get_ITRF, get_TEME, Frame, ENU


GCRF = get_GCRF()
ITRF = get_ITRF()
TEME = get_TEME()

# ========== ========== ========== ========== ========== transforms
GCRF.register_transform(ITRF, GCRF.to_ITRF)
ITRF.register_transform(GCRF, ITRF.to_GCRF)
ITRF.register_transform(TEME, ITRF.to_TEME)
TEME.register_transform(ITRF, TEME.to_ITRF)