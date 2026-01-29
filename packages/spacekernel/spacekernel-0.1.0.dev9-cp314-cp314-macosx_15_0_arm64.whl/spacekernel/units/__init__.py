#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""
import sys
from .units import units


for unit, value in units.items():
    setattr(sys.modules[__name__], unit, value)