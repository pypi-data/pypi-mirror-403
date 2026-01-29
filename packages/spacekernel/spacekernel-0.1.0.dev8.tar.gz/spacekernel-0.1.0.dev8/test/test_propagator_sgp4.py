#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

import pytest

from spacekernel.units import *
from spacekernel import TLE, ELSET, Time
from spacekernel.propagators import SGP4
from test.data import intelsat_elset

@pytest.fixture
def tles() -> list[TLE]:

    df = intelsat_elset()

    return [TLE(row.line1, row.line2) for index, row in df.iterrows()]


class TestSGP4:

    def test_propagate(self, tles):

        elsets = ELSET(*tles)

        # print(elsets.epoch)

        sgp4 = SGP4()

        time = Time.range(start='2025-03-01', end='2025-04-01', step=30)

        eph = sgp4.propagate(time, tles).gcrf
        print(eph)

        coe = eph.to_coe()

        coe.plot(show=True)