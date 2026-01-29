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
from spacekernel.state import StateVector, COE, GeoState, coe_from_sv

from test.orekit.propagation import propagate_tle

from spacekernel.frames import GCRF, TEME, ITRF


@pytest.fixture
def data() -> dict:
    filepath = Path(__file__).parent / 'data' / 'molniya_2-9.csv'

    if not filepath.is_file():

        # MOLNIYA 2-9
        line1 = '1  7276U 74026A   25145.84713414  .00000013  00000-0  00000+0 0  9993'
        line2 = '2  7276  64.3566  79.2896 6584676 266.9325  21.8190  2.45096989275692'

        time = Time.range(start='2025-05-28', end='2025-05-30', step=5)

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
    time = data['time']
    r_GCRF = data['r_GCRF']
    v_GCRF = data['v_GCRF']

    return StateVector(time, r_GCRF, v_GCRF)

@pytest.fixture
def coe(sv) -> COE:
    return sv.to_coe()

    # result = {name: data[name] for name in data.dtype.names}

@pytest.fixture
def geo(sv) -> GeoState:
    return sv.to_geostate()


class TestStateVector:

    def test_instantiate(self, data: dict) -> None:

        time = data['time']
        r_GCRF = data['r_GCRF']
        v_GCRF = data['v_GCRF']

        sv = StateVector(time, r_GCRF, v_GCRF)

        assert sv.frame is GCRF
        assert numpy.all(sv.time == time)
        assert numpy.all(sv.r == r_GCRF)
        assert numpy.all(sv.v == v_GCRF)

    def test_transform_frame(self, data: dict) -> None:
        print()

        time = data['time']
        r_GCRF = data['r_GCRF']
        v_GCRF = data['v_GCRF']

        sv_gcrf = StateVector(time, r_GCRF, v_GCRF)
        sv_itrf = sv_gcrf.transform_to(ITRF)

        assert sv_itrf.frame is ITRF
        assert numpy.all(sv_itrf.time == time)

        r_ITRF_ref, v_ITRF_ref = GCRF.transform_to(ITRF, time, r_GCRF, v_GCRF)

        assert numpy.all(sv_itrf.r == r_ITRF_ref)
        assert numpy.all(sv_itrf.v == v_ITRF_ref)

    def test_to_coe(self, data: dict) -> None:
        print()

        time = data['time']
        r_GCRF = data['r_GCRF']
        v_GCRF = data['v_GCRF']

        sv = StateVector(time, r_GCRF, v_GCRF)

        coe_ref = coe_from_sv(r_GCRF, v_GCRF)
        coe = sv.to_coe().to_numpy()

        for key in ['ecc', 'sma', 'inc', 'raa', 'arp', 'tra']:
            assert numpy.all(coe_ref[key] == coe[key])


class TestCOE:

    def test_instantiate(self, coe) -> None:

        figure, axes = pyplot.subplots()

        axes.plot(numpy.rad2deg(coe.mea))
        axes.plot(numpy.rad2deg(coe.eca))
        axes.plot(numpy.rad2deg(coe.tra))

        pyplot.show()

    def test_to_sv(self, sv, coe) -> None:

        sv_obt = coe.to_sv()

        assert numpy.allclose(sv.r, sv_obt.r)
        assert numpy.allclose(sv.v, sv_obt.v)

class TestGeoState:

    def test_instantiate(self, geo) -> None:

        figure, axes = pyplot.subplots(2, sharex=True)

        axes[0].plot(geo.time.datetime64, geo.lon / deg)
        axes[1].plot(geo.time.datetime64, geo.lon_dot / deg)

        pyplot.show()

    def test_to_sv(self, sv, geo) -> None:

        sv = sv.itrf
        sv_obt = geo.to_sv()

        assert numpy.allclose(sv.r, sv_obt.r)
        assert numpy.allclose(sv.v, sv_obt.v)

    def test_partial_instantiate(self, geo) -> None:

        geo = GeoState(geo.time, geo.lon, 50*deg)

        figure, axes = pyplot.subplots(2, sharex=True)

        axes[0].plot(geo.time.datetime64, geo.lat / deg)
        axes[1].plot(geo.time.datetime64, geo.lat_dot / deg)

        pyplot.show()