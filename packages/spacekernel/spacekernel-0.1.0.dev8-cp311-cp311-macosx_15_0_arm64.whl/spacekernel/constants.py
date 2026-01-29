#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

from spacekernel.mathtools.ellipsoid import WGS84

EARTH_GM_JPL2021: float = 398_600_435_507_000.0
EARTH_GM_IAU2015: float = 3.986_004e14
EARTH_GM_SEI1992: float = 3.986_004_415e14
EARTH_GM: float = EARTH_GM_JPL2021

EARTH_Re_IAU2015: float = 6.3781e6
EARTH_Re_WGS84: float = WGS84.Re
EARTH_Re_SEI1992: float = 6.378_136_300e6
EARTH_Re: float = EARTH_Re_WGS84


AU: float = 149597870.7e3