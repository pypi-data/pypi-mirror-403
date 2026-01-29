#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

from numpy.typing import NDArray
import numpy
from spacekernel.time import Time
from typing import Tuple

def find_minima(time: Time,
                signal: NDArray[numpy.double],
                **kwargs) -> Tuple[Time, NDArray[numpy.double]]: ...
