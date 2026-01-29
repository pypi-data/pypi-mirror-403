#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""


import pytest

import numpy, pandas

from pathlib import Path

from matplotlib import pyplot

from spacekernel.units import deg
from spacekernel.time import Time
from spacekernel.state import StateVector, COE, GeoState

from test.orekit.propagation import propagate_tle

from spacekernel.frames import GCRF, TEME, ITRF

@pytest.fixture
def data() -> dict:

    filepath = Path(__file__).parent / 'data' / 'molniya_2-9.csv'

    if not filepath.is_file():

        # MOLNIYA 2-9
        line1 = '1  7276U 74026A   25145.84713414  .00000013  00000-0  00000+0 0  9993'
        line2 = '2  7276  64.3566  79.2896 6584676 266.9325  21.8190  2.45096989275692'

        time = Time.range(start='2025-05-28', end='2025-05-30', step=3600)

        frame = propagate_tle(line1, line2, time.to_pandas())
        frame.index.name = 'time'

        frame.to_csv(filepath)

    else:
        frame = pandas.read_csv(filepath, parse_dates=['time'])
        time = Time(frame['time'].values)

    r_TEME = frame[['rx_TEME', 'ry_TEME', 'rz_TEME']].values
    v_TEME = frame[['vx_TEME', 'vy_TEME', 'vz_TEME']].values

    r_GCRF = frame[['rx_GCRF', 'ry_GCRF', 'rz_GCRF']].values
    v_GCRF = frame[['vx_GCRF', 'vy_GCRF', 'vz_GCRF']].values

    r_ITRF = frame[['rx_ITRF', 'ry_ITRF', 'rz_ITRF']].values
    v_ITRF = frame[['vx_ITRF', 'vy_ITRF', 'vz_ITRF']].values


    return {
        'time': time,
        'r_TEME': r_TEME,
        'v_TEME': v_TEME,
        'r_GCRF': r_GCRF,
        'v_GCRF': v_GCRF,
        'r_ITRF': r_ITRF,
        'v_ITRF': v_ITRF,
    }


@pytest.fixture
def sv(data) -> StateVector:

    r = data['r_GCRF'][0]
    v = data['v_GCRF'][0]
    epoch = data['time'][0]

    return StateVector(epoch, r, v, mass=3000, frame=GCRF)


class TestStateVector:

    def test_instantiation(self, sv: StateVector) -> None:
        print()
        print(sv)

    def test_copy(self, sv: StateVector) -> None:

        sv2 = sv.copy()

        assert numpy.all(sv.r == sv2.r)
        assert numpy.all(sv.v == sv2.v)
        assert numpy.all(sv.mass == sv2.mass)
        assert sv.epoch == sv2.epoch
        assert sv.frame == sv2.frame

    def test_transform_to(self, sv: StateVector) -> None:
        print()

        sv_gcrf = sv
        sv_itrf = sv_gcrf.transform_to(ITRF)

        assert sv_itrf.frame is ITRF
        assert numpy.all(sv_itrf.epoch == sv.epoch)

        r_ITRF_ref, v_ITRF_ref = GCRF.transform_to(ITRF, sv.epoch, sv.r.reshape(1, 3), sv.v.reshape(1, 3))

        assert numpy.all(sv_itrf.r == r_ITRF_ref[0])
        assert numpy.all(sv_itrf.v == v_ITRF_ref[0])

    def test_getitem(self, sv: StateVector) -> None:
        print()

        sv_gcrf = sv
        sv_itrf = sv_gcrf.itrf

        assert sv_itrf.frame is ITRF
        assert numpy.all(sv_itrf.epoch == sv.epoch)

        r_ITRF_ref, v_ITRF_ref = GCRF.transform_to(ITRF, sv.epoch, sv.r.reshape(1, 3), sv.v.reshape(1, 3))

        assert numpy.all(sv_itrf.r == r_ITRF_ref[0])
        assert numpy.all(sv_itrf.v == v_ITRF_ref[0])

    def test_x(self, sv: StateVector) -> None:

        assert numpy.all(sv.x == numpy.hstack([sv.r, sv.v]))

    def test_to_coe(self, sv) -> None:
        print()

        coe = sv.to_coe()

        print(coe)

    def test_to_geostate(self, sv) -> None:
        print()

        geo = sv.to_geostate()

        print(geo)
        print(geo.lon_dot)
        print(geo.lat_dot)

class TestCOE:

    def test_to_sv(self, sv) -> None:
        coe = sv.to_coe()
        sv1 = coe.to_sv()

        assert sv1.frame is sv.frame
        assert sv1.epoch == sv.epoch
        assert numpy.allclose(sv1.r, sv.r)
        assert numpy.allclose(sv1.v, sv.v)

    def test_copy(self, sv) -> None:

        coe = sv.to_coe()

        coe2 = coe.copy()

        assert coe.frame is coe2.frame
        assert coe.epoch == coe2.epoch
        assert coe.sma == coe2.sma


class TestGeoState:

    def test_to_sv(self, sv) -> None:

        sv = sv.itrf

        geo = sv.to_geostate()
        sv1 = geo.to_sv()

        assert sv1.frame is sv.frame
        assert sv1.epoch == sv.epoch
        assert numpy.allclose(sv1.r, sv.r)
        assert numpy.allclose(sv1.v, sv.v)

    def test_copy(self, sv) -> None:

        coe = sv.to_coe()

        coe2 = coe.copy()

        assert coe.frame is coe2.frame
        assert coe.epoch == coe2.epoch
        assert coe.sma == coe2.sma