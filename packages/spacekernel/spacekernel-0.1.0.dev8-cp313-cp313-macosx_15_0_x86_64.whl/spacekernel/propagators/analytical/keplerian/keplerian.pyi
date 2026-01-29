#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

from typing import Any
import numpy
from spacekernel.time import Time
from spacekernel.state import State, StateVectorEphemeris, COE
from spacekernel.propagators import Propagator

class Keplerian(Propagator):
    def __cinit__(self, GM: float = ...) -> None: ...
    def propagate_state(self, time: Any, state: State, **kwargs) -> StateVectorEphemeris: ...
    def jacobian(self, eph: StateVectorEphemeris) -> numpy.ndarray: ...
