#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

from .ellipsoid import Ellipsoid, create


WGS84 = create('WGS84')
WGS72 = create('WGS72')
GRS80 = create('GRS80')