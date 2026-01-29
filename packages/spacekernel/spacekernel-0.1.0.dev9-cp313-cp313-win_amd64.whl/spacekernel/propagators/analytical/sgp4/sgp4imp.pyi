#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

from typing import Any
from spacekernel.state import StateVectorEphemeris, TLE
from spacekernel.propagators import TLE, Propagator

class SGP4(Propagator):
    def propagate_state(self, time: Any, state: TLE, **kwargs) -> StateVectorEphemeris: ...
