#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

import numpy, pandas
import pytest
from matplotlib import pyplot

from pathlib import Path

from numpy.typing import NDArray

from test.orekit import Orekit
from test import combine


from test.orekit.propagation import propagate_tle

from spacekernel import Time

from spacekernel.state import eca_from_mea, mea_from_eca
from spacekernel.state import tra_from_eca, eca_from_tra
from spacekernel.state import tra_from_mea, mea_from_tra

from spacekernel.state import orp_from_sma, sma_from_orp
from spacekernel.state import mnm_from_sma, sma_from_mnm

from spacekernel.state import coe_from_sv, sv_from_coe

from spacekernel.bodies import Earth


# ========== ========== ========== ========== ========== ==========
def eca_from_mea_ok(mea: NDArray, ecc: NDArray) -> NDArray:

    eca = numpy.zeros_like(mea)

    with Orekit():
        from org.orekit.time import AbsoluteDate
        from org.orekit.frames import FramesFactory
        from org.orekit.orbits import KeplerianOrbit, PositionAngleType
        from org.orekit.utils import Constants

        sma = 7000e3
        inc = 0.0
        arp = 0.0
        raa = 0.0

        GCRF = FramesFactory.getGCRF()

        for i in range(mea.shape[0]):
            eca[i] = KeplerianOrbit(sma, ecc[i], inc, arp, raa, mea[i],
                                   PositionAngleType.MEAN,
                                   GCRF,
                                   AbsoluteDate(),
                                   Constants.IERS2010_EARTH_MU).getEccentricAnomaly()

        return eca

def mea_from_eca_ok(ano: NDArray, ecc: NDArray) -> NDArray:

    new_ano = numpy.zeros_like(ano)

    with Orekit():
        from org.orekit.time import AbsoluteDate
        from org.orekit.frames import FramesFactory
        from org.orekit.orbits import KeplerianOrbit, PositionAngleType
        from org.orekit.utils import Constants

        sma = 7000e3
        inc = 0.0
        arp = 0.0
        raa = 0.0

        GCRF = FramesFactory.getGCRF()

        for i in range(ano.shape[0]):
            new_ano[i] = KeplerianOrbit(sma, ecc[i], inc, arp, raa, ano[i],
                                   PositionAngleType.ECCENTRIC,
                                   GCRF,
                                   AbsoluteDate(),
                                   Constants.IERS2010_EARTH_MU).getMeanAnomaly()

        return new_ano

def tra_from_eca_ok(ano: NDArray, ecc: NDArray) -> NDArray:

    new_ano = numpy.zeros_like(ano)

    with Orekit():
        from org.orekit.time import AbsoluteDate
        from org.orekit.frames import FramesFactory
        from org.orekit.orbits import KeplerianOrbit, PositionAngleType
        from org.orekit.utils import Constants

        sma = 7000e3
        inc = 0.0
        arp = 0.0
        raa = 0.0

        GCRF = FramesFactory.getGCRF()

        for i in range(ano.shape[0]):
            new_ano[i] = KeplerianOrbit(sma, ecc[i], inc, arp, raa, ano[i],
                                   PositionAngleType.ECCENTRIC,
                                   GCRF,
                                   AbsoluteDate(),
                                   Constants.IERS2010_EARTH_MU).getTrueAnomaly()

        return new_ano

def eca_from_tra_ok(ano: NDArray, ecc: NDArray) -> NDArray:

    new_ano = numpy.zeros_like(ano)

    with Orekit():
        from org.orekit.time import AbsoluteDate
        from org.orekit.frames import FramesFactory
        from org.orekit.orbits import KeplerianOrbit, PositionAngleType
        from org.orekit.utils import Constants

        sma = 7000e3
        inc = 0.0
        arp = 0.0
        raa = 0.0

        GCRF = FramesFactory.getGCRF()

        for i in range(ano.shape[0]):
            new_ano[i] = KeplerianOrbit(sma, ecc[i], inc, arp, raa, ano[i],
                                   PositionAngleType.TRUE,
                                   GCRF,
                                   AbsoluteDate(),
                                   Constants.IERS2010_EARTH_MU).getEccentricAnomaly()

        return new_ano

def mea_from_tra_ok(ano: NDArray, ecc: NDArray) -> NDArray:

    new_ano = numpy.zeros_like(ano)

    with Orekit():
        from org.orekit.time import AbsoluteDate
        from org.orekit.frames import FramesFactory
        from org.orekit.orbits import KeplerianOrbit, PositionAngleType
        from org.orekit.utils import Constants

        sma = 7000e3
        inc = 0.0
        arp = 0.0
        raa = 0.0

        GCRF = FramesFactory.getGCRF()

        for i in range(ano.shape[0]):
            new_ano[i] = KeplerianOrbit(sma, ecc[i], inc, arp, raa, ano[i],
                                   PositionAngleType.TRUE,
                                   GCRF,
                                   AbsoluteDate(),
                                   Constants.IERS2010_EARTH_MU).getMeanAnomaly()

        return new_ano

def tra_from_mea_ok(ano: NDArray, ecc: NDArray) -> NDArray:

    new_ano = numpy.zeros_like(ano)

    with Orekit():
        from org.orekit.time import AbsoluteDate
        from org.orekit.frames import FramesFactory
        from org.orekit.orbits import KeplerianOrbit, PositionAngleType
        from org.orekit.utils import Constants

        sma = 7000e3
        inc = 0.0
        arp = 0.0
        raa = 0.0

        GCRF = FramesFactory.getGCRF()

        for i in range(ano.shape[0]):
            new_ano[i] = KeplerianOrbit(sma, ecc[i], inc, arp, raa, ano[i],
                                   PositionAngleType.MEAN,
                                   GCRF,
                                   AbsoluteDate(),
                                   Constants.IERS2010_EARTH_MU).getTrueAnomaly()

        return new_ano


class TestConversionBetweenAnomalies:

    @pytest.fixture
    def ano_ecc(self) -> tuple[NDArray, 2]:
        ano = numpy.linspace(0.0, 2 * numpy.pi, 50)[:-1]
        ecc = numpy.linspace(0.0, 1.0, 50)[:-1]

        return combine(ano, ecc)

    def test_eca_from_mea(self, ano_ecc: tuple[NDArray, 2]) -> None:

        mea, ecc = ano_ecc

        eca_sk = eca_from_mea(mea, ecc)
        eca_ok = eca_from_mea_ok(mea, ecc)

        assert numpy.allclose(eca_sk, eca_ok)

    def test_mea_from_eca(self, ano_ecc: tuple[NDArray, 2]) -> None:

        eca, ecc = ano_ecc

        mea_sk = mea_from_eca(eca, ecc)
        mea_ok = mea_from_eca_ok(eca, ecc)

        assert numpy.allclose(mea_sk, mea_ok)

    def test_tra_from_eca(self, ano_ecc: tuple[NDArray, 2]) -> None:

        eca, ecc = ano_ecc

        tra_sk = tra_from_eca(eca, ecc)
        tra_ok = tra_from_eca_ok(eca, ecc)

        assert numpy.allclose(tra_sk, tra_ok)

    def test_eca_from_tra(self, ano_ecc: tuple[NDArray, 2]) -> None:

        tra, ecc = ano_ecc

        eca_sk = eca_from_tra(tra, ecc)
        eca_ok = eca_from_tra_ok(tra, ecc)

        assert numpy.allclose(eca_sk, eca_ok)

    def test_mea_from_tra(self, ano_ecc: tuple[NDArray, 2]) -> None:

        tra, ecc = ano_ecc

        mea_sk = mea_from_tra(tra, ecc)
        mea_ok = mea_from_tra_ok(tra, ecc)

        assert numpy.allclose(mea_sk, mea_ok)

    def test_tra_from_mea(self, ano_ecc: tuple[NDArray, 2]) -> None:

        mea, ecc = ano_ecc

        tra_sk = tra_from_mea(mea, ecc)
        tra_ok = tra_from_mea_ok(mea, ecc)

        assert numpy.allclose(tra_sk, tra_ok)


# ========== ========== ========== ========== ========== ==========
def orp_from_sma_ok(sma: NDArray) -> NDArray:

    res = numpy.zeros_like(sma)

    with Orekit():
        from org.orekit.time import AbsoluteDate
        from org.orekit.frames import FramesFactory
        from org.orekit.orbits import KeplerianOrbit, PositionAngleType
        from org.orekit.utils import Constants

        ecc = 0.5
        inc = 0.0
        arp = 0.0
        raa = 0.0

        GCRF = FramesFactory.getGCRF()

        for i in range(res.shape[0]):
            res[i] = KeplerianOrbit(sma[i], ecc, inc, arp, raa, 0.0,
                                   PositionAngleType.MEAN,
                                   GCRF,
                                   AbsoluteDate(),
                                   Constants.IERS2010_EARTH_MU).getKeplerianPeriod()

        return res

def mnm_from_sma_ok(sma: NDArray) -> NDArray:

    res = numpy.zeros_like(sma)

    with Orekit():
        from org.orekit.time import AbsoluteDate
        from org.orekit.frames import FramesFactory
        from org.orekit.orbits import KeplerianOrbit, PositionAngleType
        from org.orekit.utils import Constants

        ecc = 0.5
        inc = 0.0
        arp = 0.0
        raa = 0.0

        GCRF = FramesFactory.getGCRF()

        for i in range(res.shape[0]):
            res[i] = KeplerianOrbit(sma[i], ecc, inc, arp, raa, 0.0,
                                   PositionAngleType.MEAN,
                                   GCRF,
                                   AbsoluteDate(),
                                   Constants.IERS2010_EARTH_MU).getKeplerianMeanMotion()

        return res

def sma_from_orp_ok(orp: NDArray) -> NDArray:

    with Orekit():
        from org.orekit.time import AbsoluteDate
        from org.orekit.frames import FramesFactory
        from org.orekit.orbits import KeplerianOrbit, PositionAngleType
        from org.orekit.utils import Constants

        MU = Constants.IERS2010_EARTH_MU  # m³/s²

        def period_to_semimajor(period, mu=MU):
            """Convert orbital period to semi-major axis."""
            return (mu * (period / (2 * numpy.pi)) ** 2) ** (1 / 3)

        return period_to_semimajor(orp, mu=MU)

def sma_from_mnm_ok(mnm: NDArray) -> NDArray:

    with Orekit():
        from org.orekit.time import AbsoluteDate
        from org.orekit.frames import FramesFactory
        from org.orekit.orbits import KeplerianOrbit, PositionAngleType
        from org.orekit.utils import Constants

        MU = Constants.IERS2010_EARTH_MU  # m³/s²

        def mean_motion_to_semimajor(n, mu=MU):
            """Convert mean motion to semi-major axis."""
            return (mu / n ** 2) ** (1 / 3)

        return mean_motion_to_semimajor(mnm, mu=MU)


class TestConversionFromToSMA:

    def test_orp_from_sma(self) -> None:

        sma = numpy.linspace(7000e3, 42000e3, 50)

        res_sk = orp_from_sma(sma)
        res_ok = orp_from_sma_ok(sma)

        try:
            assert numpy.allclose(res_sk, res_ok)

        except AssertionError as error:

            figure, axes = pyplot.subplots()

            axes.plot(res_sk)
            axes.plot(res_ok)

            pyplot.show()

            raise error

    def test_mnm_from_sma(self) -> None:

        sma = numpy.linspace(7000e3, 42000e3, 50)

        res_sk = mnm_from_sma(sma)
        res_ok = mnm_from_sma_ok(sma)

        try:
            assert numpy.allclose(res_sk, res_ok)

        except AssertionError as error:

            figure, axes = pyplot.subplots()

            axes.plot(res_sk)
            axes.plot(res_ok)

            pyplot.show()

            raise error

    def test_sma_from_orp(self) -> None:

        orp = numpy.linspace(90*60, 86400, 50)

        res_sk = sma_from_orp(orp)
        res_ok = sma_from_orp_ok(orp)

        try:
            assert numpy.allclose(res_sk, res_ok)

        except AssertionError as error:

            figure, axes = pyplot.subplots()

            axes.plot(res_sk)
            axes.plot(res_ok)

            pyplot.show()

            raise error

    def test_sma_from_mnm(self) -> None:

        orp = numpy.linspace(90*60, 86400, 50)
        mnm = 2*numpy.pi / orp

        res_sk = sma_from_mnm(mnm)
        res_ok = sma_from_mnm_ok(mnm)

        try:
            assert numpy.allclose(res_sk, res_ok)

        except AssertionError as error:

            figure, axes = pyplot.subplots()

            axes.plot(res_sk)
            axes.plot(res_ok)

            pyplot.show()

            raise error


class TestSVCOEConversion:

    @pytest.fixture
    def data(self) -> dict:
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

    def test_coe_from_state_vector(self, data: dict) -> None:
        print()

        r = data['r_GCRF']
        v = data['v_GCRF']

        coe_obt = coe_from_sv(r, v)

        # ========== ========== ========== ========== ========== inclination
        l = numpy.cross(r, v)
        l_norm = numpy.linalg.norm(l, axis=1)

        inc = numpy.arccos(l[:, 2] / l_norm)

        assert numpy.all(coe_obt['inc'] == inc)
        # assert numpy.allclose(coe_obt['inc'], inc)

        # ========== ========== ========== ========== ========== eccentricity
        e_vec = numpy.cross(v, l) / Earth.GM - r / numpy.linalg.norm(r, axis=1).reshape(-1, 1)

        ecc = numpy.linalg.norm(e_vec, axis=1)

        # assert numpy.all(coe_obt['ecc'] == ecc)
        assert numpy.allclose(coe_obt['ecc'], ecc)


        # ========== ========== ========== ========== ========== sma
        sma = l_norm**2 / Earth.GM / (1 - ecc**2)

        assert numpy.allclose(coe_obt['sma'], sma)

        # ========== ========== ========== ========== ========== raa
        n = numpy.cross([0, 0, 1], l)

        n = n / numpy.linalg.norm(n, axis=1).reshape(-1, 1)

        raa = numpy.arctan2(n[:, 1], n[:, 0])

        assert numpy.allclose(numpy.cos(coe_obt['raa']), numpy.cos(raa))
        assert numpy.allclose(numpy.sin(coe_obt['raa']), numpy.sin(raa))

        # ========== ========== ========== ========== ========== arp
        q = numpy.cross(l, n)
        q = q / numpy.linalg.norm(q, axis=1).reshape(-1, 1)

        arp = numpy.arctan2(numpy.sum(e_vec*q, axis=1), numpy.sum(e_vec*n, axis=1))

        assert numpy.allclose(numpy.cos(coe_obt['arp']), numpy.cos(arp))
        assert numpy.allclose(numpy.sin(coe_obt['arp']), numpy.sin(arp))

        # ========== ========== ========== ========== ========== tra
        p = numpy.cross(l, e_vec)
        p = p / numpy.linalg.norm(p, axis=1).reshape(-1, 1)

        e = e_vec / numpy.linalg.norm(e_vec, axis=1).reshape(-1, 1)

        tra = numpy.arctan2(numpy.sum(r*p, axis=1), numpy.sum(r*e, axis=1))

        # figure, axes = pyplot.subplots(2, sharex=True)
        #
        # axes[0].plot(numpy.cos(coe_obt['tra']) - numpy.cos(tra))
        # axes[1].plot(numpy.sin(coe_obt['tra']) - numpy.sin(tra))
        #
        # pyplot.show()

        assert numpy.allclose(numpy.cos(coe_obt['tra']), numpy.cos(tra))
        assert numpy.allclose(numpy.sin(coe_obt['tra']), numpy.sin(tra))

        # ========== ========== ========== ========== ========== slr
        slr = l_norm**2 / Earth.GM

        assert numpy.allclose(coe_obt['slr'], slr)

    def test_state_vector_from_coe(self, data: dict) -> None:
        print()

        r = data['r_GCRF']
        v = data['v_GCRF']

        coe = coe_from_sv(r, v)

        r_obt, v_obt = sv_from_coe(coe)

        assert numpy.allclose(r_obt, r)
        assert numpy.allclose(v_obt, v)