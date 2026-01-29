#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""
import pytest

from pathlib import Path

import numpy

from spacekernel import Time
from spacekernel.frames import ITRF, GCRF
from spacekernel.state.ephemeris import StateVectorEphemeris, COEEphemeris, GeoStateEphemeris, read_sp_ephemeris_file

from test.data import molniya



class TestStatVectorEphemeris:

    @pytest.fixture
    def ephemeris(self, molniya) -> StateVectorEphemeris:
        t = molniya['time']
        r = molniya['r_GCRF']
        v = molniya['v_GCRF']
        return StateVectorEphemeris(t, r, v, frame='GCRF')

    def test_instantiate(self, ephemeris) -> None:
        print()
        print(ephemeris)
        ephemeris.plot(show=True, plot_mass=False)

    def test_interpolate(self, ephemeris) -> None:

        time = Time.range(start=ephemeris.epoch[50], end=ephemeris.epoch[-50], n_points=100)

        print(ephemeris.interpolate(time))

    def test_transform_frame(self, ephemeris) -> None:
        print()

        sv_gcrf = ephemeris
        sv_itrf = sv_gcrf.transform_to(ITRF)

        assert sv_itrf.frame is ITRF
        assert numpy.all(sv_itrf.epoch == sv_gcrf.epoch)

        r_ITRF_ref, v_ITRF_ref = GCRF.transform_to(ITRF,
                                                   sv_gcrf.epoch,
                                                   sv_gcrf.r,
                                                   sv_gcrf.v)

        assert numpy.all(sv_itrf.r == r_ITRF_ref)
        assert numpy.all(sv_itrf.v == v_ITRF_ref)

    def test_get_item(self, ephemeris) -> None:
        print()
        print(ephemeris[0])
        print(ephemeris[-1])

        for sv in ephemeris[:10]:
            print(sv.epoch)

        print(ephemeris[:'2025-05-29'])
        print(ephemeris['2025-05-29':])

    def test_concatenate(self, ephemeris) -> None:

        eph = ephemeris
        eph_obt = StateVectorEphemeris.concatenate(eph[:'2025-05-29'], eph['2025-05-29':])

        assert numpy.all(eph_obt.epoch == eph.epoch)
        assert numpy.all(eph_obt.r == eph.r)
        assert numpy.all(eph_obt.v == eph.v)
        assert numpy.all(eph_obt.frame == eph.frame)


class TestCOEEphemeris:

    @pytest.fixture
    def ephemeris(self, molniya) -> COEEphemeris:
        t = molniya['time']
        r = molniya['r_GCRF']
        v = molniya['v_GCRF']
        return StateVectorEphemeris(t, r, v, frame='GCRF').to_coe()

    def test_instantiate(self, ephemeris) -> None:
        print()

        print(ephemeris)

        ephemeris.plot(show=True, plot_mass=False)

    def test_to_sv(self, ephemeris) -> None:

        sv = ephemeris.to_sv()

        print(sv)

    def test_get_item(self, ephemeris) -> None:
        print()
        print(ephemeris[0])
        print(ephemeris[-1])

        for sv in ephemeris[:10]:
            print(sv.epoch)

        print(ephemeris[:'2025-05-29'])
        print(ephemeris['2025-05-29':])


class TestGeoStateEphemeris:

    @pytest.fixture
    def ephemeris(self, molniya) -> GeoStateEphemeris:
        t = molniya['time']
        r = molniya['r_GCRF']
        v = molniya['v_GCRF']
        return StateVectorEphemeris(t, r, v, frame='GCRF').to_geostate()

    def test_instantiate(self, ephemeris) -> None:
        print()

        print(ephemeris)

        ephemeris.plot(show=True, plot_mass=False)

    def test_to_sv(self, ephemeris) -> None:

        sv = ephemeris.to_sv()

        print(sv)

    def test_get_item(self, ephemeris) -> None:
        print()
        print(ephemeris[0])
        print(ephemeris[-1])

        for sv in ephemeris[:10]:
            print(sv.epoch)

        print(ephemeris[:'2025-05-29'])
        print(ephemeris['2025-05-29':])


def test_read_sp_ephemeris_file() -> None:

    sp_filepath = Path(__file__).parent / 'data' / '60539.eci'

    sv_eph = read_sp_ephemeris_file(sp_filepath)

    print(sv_eph)