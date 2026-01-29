#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

from typing import Any, Tuple
import numpy
from spacekernel.time import Time

class StateTransitionMatrix:
    time: Time
    t: numpy.ndarray

    def __cinit__(self, time: Time, jac: numpy.ndarray, step: float = 1.0) -> None: ...
    def __call__(self, tb: Time, ta: Time) -> numpy.ndarray: ...
    def __getitem__(self, item: Tuple[int, int]) -> numpy.ndarray: ...
    def plot_estimation_performance(self, show: bool = False) -> Tuple[Any, Any]: ...
    def jac(self, time: Time) -> numpy.ndarray: ...