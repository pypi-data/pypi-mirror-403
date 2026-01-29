#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

import pytest

from spacekernel import Time
from spacekernel.scenario import Scenario


class TestScenario:

    @pytest.fixture
    def time(self) -> Time:
        return Time.range(start='2025-01-01', end='2025-01-02', step=30)

    def test_instantiate(self, time: Time) -> None:
        print()

        scn = Scenario(time)

        print(f'Scenario name: {scn.name}')
        scn.name = 'Scenario Test'
        print(f'Scenario name: {scn.name}')

        print(scn.sun.ephemeris)
        print(scn.moon.ephemeris)
        print(scn.time)



