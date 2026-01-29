#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""
import pytest

import numpy, pandas
from pathlib import Path

from matplotlib import pyplot

from astropy import coordinates, units

from spacekernel import Time
from spacekernel.frames import ITRF_from_GCRF, GCRF_from_ITRF, ITRF_from_TEME, TEME_from_ITRF
from spacekernel.frames.rotations import ITRF_from_GCRF as ITRF_from_GCRF_parallel

from spacekernel.frames import Frame, GCRF, ITRF, TEME, ENU

from test.orekit import Orekit
from test.orekit.propagation import propagate_tle as propagate_tle_orekit

from test import profile
from test.data import get_large_test_data


# ========== ========== ========== ========== ========== ==========
def ITRF_from_TEME_astropy(time: Time,
                           r_TEME: numpy.ndarray,
                           v_TEME: numpy.ndarray) -> tuple[numpy.ndarray, 2]:

    coords = coordinates.SkyCoord(
        x=r_TEME[:, 0] << units.m,
        y=r_TEME[:, 1] << units.m,
        z=r_TEME[:, 2] << units.m,
        v_x=v_TEME[:, 0] << units.m / units.s,
        v_y=v_TEME[:, 1] << units.m / units.s,
        v_z=v_TEME[:, 2] << units.m / units.s,
        frame='teme',
        obstime=time.to_astropy(),
        representation_type='cartesian'
    ).transform_to('itrs')
    coords.representation_type = 'cartesian'

    r_ITRF = coords.cartesian.xyz.T.si.value
    v_ITRF = numpy.concatenate([
        coords.v_x.reshape(-1, 1),
        coords.v_y.reshape(-1, 1),
        coords.v_z.reshape(-1, 1)
    ], axis=1).si.value

    return r_ITRF, v_ITRF

def ITRF_from_TEME_orekit(time: Time,
                          r_TEME: numpy.ndarray,
                          v_TEME: numpy.ndarray) -> tuple[numpy.ndarray, 2]:

    with Orekit():
        from org.orekit.time import AbsoluteDate, TimeScalesFactory
        from org.orekit.frames import FramesFactory, Transform
        from org.orekit.utils import IERSConventions
        from org.orekit.bodies import GeodeticPoint
        from org.orekit.bodies import OneAxisEllipsoid
        from org.orekit.utils import Constants, PVCoordinates

        from org.hipparchus.geometry.euclidean.threed import Vector3D

        # ---------- ---------- ---------- ---------- ----------
        utc = TimeScalesFactory.getUTC()

        def absolutedate_from_timestamp(t: pandas.Timestamp) -> AbsoluteDate:
            return AbsoluteDate(t.year, t.month, t.day, t.hour, t.minute, t.second, utc)

        # ---------- ---------- ---------- ---------- ---------- frames
        # GCRF = FramesFactory.getGCRF()
        TEME = FramesFactory.getTEME()
        ITRF = FramesFactory.getITRF(IERSConventions.IERS_2010, True)

        # ---------- ---------- ---------- ---------- ----------
        r_ITRF = numpy.zeros_like(r_TEME)
        v_ITRF = numpy.zeros_like(v_TEME)

        for index, t in enumerate(time.to_pandas()):
            date = absolutedate_from_timestamp(t)

            pos = Vector3D(r_TEME[index, 0], r_TEME[index, 1], r_TEME[index, 2])
            vel = Vector3D(v_TEME[index, 0], v_TEME[index, 1], v_TEME[index, 2])

            pv = PVCoordinates(pos, vel)
            transform = TEME.getTransformTo(ITRF, date)
            pv_ITRF = transform.transformPVCoordinates(pv)

            r_ITRF[index, 0] = pv_ITRF.getPosition().getX()
            r_ITRF[index, 1] = pv_ITRF.getPosition().getY()
            r_ITRF[index, 2] = pv_ITRF.getPosition().getZ()

            v_ITRF[index, 0] = pv_ITRF.getVelocity().getX()
            v_ITRF[index, 1] = pv_ITRF.getVelocity().getY()
            v_ITRF[index, 2] = pv_ITRF.getVelocity().getZ()

        return r_ITRF, v_ITRF

# ========== ========== ========== ========== ========== ==========
def TEME_from_ITRF_astropy(time: Time,
                           r_ITRF: numpy.ndarray,
                           v_ITRF: numpy.ndarray) -> tuple[numpy.ndarray, 2]:

    coords = coordinates.SkyCoord(
        x=r_ITRF[:, 0] << units.m,
        y=r_ITRF[:, 1] << units.m,
        z=r_ITRF[:, 2] << units.m,
        v_x=v_ITRF[:, 0] << units.m / units.s,
        v_y=v_ITRF[:, 1] << units.m / units.s,
        v_z=v_ITRF[:, 2] << units.m / units.s,
        frame='itrs',
        obstime=time.to_astropy(),
        representation_type='cartesian'
    ).transform_to('teme')
    coords.representation_type = 'cartesian'

    r_TEME = coords.cartesian.xyz.T.si.value
    v_TEME = numpy.concatenate([
        coords.v_x.reshape(-1, 1),
        coords.v_y.reshape(-1, 1),
        coords.v_z.reshape(-1, 1)
    ], axis=1).si.value

    return r_TEME, v_TEME

def TEME_from_ITRF_orekit(time: Time,
                          r_ITRF: numpy.ndarray,
                          v_ITRF: numpy.ndarray) -> tuple[numpy.ndarray, 2]:

    with Orekit():
        from org.orekit.time import AbsoluteDate, TimeScalesFactory
        from org.orekit.frames import FramesFactory, Transform
        from org.orekit.utils import IERSConventions
        from org.orekit.bodies import GeodeticPoint
        from org.orekit.bodies import OneAxisEllipsoid
        from org.orekit.utils import Constants, PVCoordinates

        from org.hipparchus.geometry.euclidean.threed import Vector3D

        # ---------- ---------- ---------- ---------- ----------
        utc = TimeScalesFactory.getUTC()

        def absolutedate_from_timestamp(t: pandas.Timestamp) -> AbsoluteDate:
            return AbsoluteDate(t.year, t.month, t.day, t.hour, t.minute, t.second, utc)

        # ---------- ---------- ---------- ---------- ---------- frames
        # GCRF = FramesFactory.getGCRF()
        TEME = FramesFactory.getTEME()
        ITRF = FramesFactory.getITRF(IERSConventions.IERS_2010, True)

        # ---------- ---------- ---------- ---------- ----------
        r_TEME = numpy.zeros_like(r_ITRF)
        v_TEME = numpy.zeros_like(v_ITRF)

        for index, t in enumerate(time.to_pandas()):
            date = absolutedate_from_timestamp(t)

            pos = Vector3D(r_ITRF[index, 0], r_ITRF[index, 1], r_ITRF[index, 2])
            vel = Vector3D(v_ITRF[index, 0], v_ITRF[index, 1], v_ITRF[index, 2])

            pv = PVCoordinates(pos, vel)
            transform = ITRF.getTransformTo(TEME, date)
            pv_TEME = transform.transformPVCoordinates(pv)

            r_TEME[index, 0] = pv_TEME.getPosition().getX()
            r_TEME[index, 1] = pv_TEME.getPosition().getY()
            r_TEME[index, 2] = pv_TEME.getPosition().getZ()

            v_TEME[index, 0] = pv_TEME.getVelocity().getX()
            v_TEME[index, 1] = pv_TEME.getVelocity().getY()
            v_TEME[index, 2] = pv_TEME.getVelocity().getZ()

        return r_TEME, v_TEME


# ========== ========== ========== ========== ========== ==========
def ITRF_from_GCRF_astropy(time: Time,
                           r_GCRF: numpy.ndarray,
                           v_GCRF: numpy.ndarray) -> tuple[numpy.ndarray, 2]:

    coords = coordinates.SkyCoord(
        x=r_GCRF[:, 0] << units.m,
        y=r_GCRF[:, 1] << units.m,
        z=r_GCRF[:, 2] << units.m,
        v_x=v_GCRF[:, 0] << units.m / units.s,
        v_y=v_GCRF[:, 1] << units.m / units.s,
        v_z=v_GCRF[:, 2] << units.m / units.s,
        frame='gcrs',
        obstime=time.to_astropy(),
        representation_type='cartesian'
    ).transform_to('itrs')
    coords.representation_type = 'cartesian'

    r_ITRF = coords.cartesian.xyz.T.si.value
    v_ITRF = numpy.concatenate([
        coords.v_x.reshape(-1, 1),
        coords.v_y.reshape(-1, 1),
        coords.v_z.reshape(-1, 1)
    ], axis=1).si.value

    return r_ITRF, v_ITRF

def ITRF_from_GCRF_orekit(time: Time,
                          r_GCRF: numpy.ndarray,
                          v_GCRF: numpy.ndarray) -> tuple[numpy.ndarray, 2]:

    with Orekit():
        from org.orekit.time import AbsoluteDate, TimeScalesFactory
        from org.orekit.frames import FramesFactory, Transform
        from org.orekit.utils import IERSConventions
        from org.orekit.bodies import GeodeticPoint
        from org.orekit.bodies import OneAxisEllipsoid
        from org.orekit.utils import Constants, PVCoordinates

        from org.hipparchus.geometry.euclidean.threed import Vector3D

        # ---------- ---------- ---------- ---------- ----------
        utc = TimeScalesFactory.getUTC()

        def absolutedate_from_timestamp(t: pandas.Timestamp) -> AbsoluteDate:
            return AbsoluteDate(t.year, t.month, t.day, t.hour, t.minute, t.second, utc)

        # ---------- ---------- ---------- ---------- ---------- frames
        GCRF = FramesFactory.getGCRF()
        # TEME = FramesFactory.getTEME()
        ITRF = FramesFactory.getITRF(IERSConventions.IERS_2010, True)

        # ---------- ---------- ---------- ---------- ----------
        r_ITRF = numpy.zeros_like(r_GCRF)
        v_ITRF = numpy.zeros_like(v_GCRF)

        for index, t in enumerate(time.to_pandas()):
            date = absolutedate_from_timestamp(t)

            pos = Vector3D(r_GCRF[index, 0], r_GCRF[index, 1], r_GCRF[index, 2])
            vel = Vector3D(v_GCRF[index, 0], v_GCRF[index, 1], v_GCRF[index, 2])

            pv = PVCoordinates(pos, vel)
            transform = GCRF.getTransformTo(ITRF, date)
            pv_ITRF = transform.transformPVCoordinates(pv)

            r_ITRF[index, 0] = pv_ITRF.getPosition().getX()
            r_ITRF[index, 1] = pv_ITRF.getPosition().getY()
            r_ITRF[index, 2] = pv_ITRF.getPosition().getZ()

            v_ITRF[index, 0] = pv_ITRF.getVelocity().getX()
            v_ITRF[index, 1] = pv_ITRF.getVelocity().getY()
            v_ITRF[index, 2] = pv_ITRF.getVelocity().getZ()

        return r_ITRF, v_ITRF

# ========== ========== ========== ========== ========== ==========
def GCRF_from_ITRF_astropy(time: Time,
                           r_ITRF: numpy.ndarray,
                           v_ITRF: numpy.ndarray) -> tuple[numpy.ndarray, 2]:

    coords = coordinates.SkyCoord(
        x=r_ITRF[:, 0] << units.m,
        y=r_ITRF[:, 1] << units.m,
        z=r_ITRF[:, 2] << units.m,
        v_x=v_ITRF[:, 0] << units.m / units.s,
        v_y=v_ITRF[:, 1] << units.m / units.s,
        v_z=v_ITRF[:, 2] << units.m / units.s,
        frame='itrs',
        obstime=time.to_astropy(),
        representation_type='cartesian'
    ).transform_to('gcrs')
    coords.representation_type = 'cartesian'

    r_GCRF = coords.cartesian.xyz.T.si.value
    v_GCRF = numpy.concatenate([
        coords.v_x.reshape(-1, 1),
        coords.v_y.reshape(-1, 1),
        coords.v_z.reshape(-1, 1)
    ], axis=1).si.value

    return r_GCRF, v_GCRF

def GCRF_from_ITRF_orekit(time: Time,
                          r_ITRF: numpy.ndarray,
                          v_ITRF: numpy.ndarray) -> tuple[numpy.ndarray, 2]:

    with Orekit():
        from org.orekit.time import AbsoluteDate, TimeScalesFactory
        from org.orekit.frames import FramesFactory, Transform
        from org.orekit.utils import IERSConventions
        from org.orekit.bodies import GeodeticPoint
        from org.orekit.bodies import OneAxisEllipsoid
        from org.orekit.utils import Constants, PVCoordinates

        from org.hipparchus.geometry.euclidean.threed import Vector3D

        # ---------- ---------- ---------- ---------- ----------
        utc = TimeScalesFactory.getUTC()

        def absolutedate_from_timestamp(t: pandas.Timestamp) -> AbsoluteDate:
            return AbsoluteDate(t.year, t.month, t.day, t.hour, t.minute, t.second, utc)

        # ---------- ---------- ---------- ---------- ---------- frames
        GCRF = FramesFactory.getGCRF()
        ITRF = FramesFactory.getITRF(IERSConventions.IERS_2010, True)

        # ---------- ---------- ---------- ---------- ----------
        r_GCRF = numpy.zeros_like(r_ITRF)
        v_GCRF = numpy.zeros_like(v_ITRF)

        for index, t in enumerate(time.to_pandas()):
            date = absolutedate_from_timestamp(t)

            pos = Vector3D(r_ITRF[index, 0], r_ITRF[index, 1], r_ITRF[index, 2])
            vel = Vector3D(v_ITRF[index, 0], v_ITRF[index, 1], v_ITRF[index, 2])

            pv = PVCoordinates(pos, vel)
            transform = ITRF.getTransformTo(GCRF, date)
            pv_GCRF = transform.transformPVCoordinates(pv)

            r_GCRF[index, 0] = pv_GCRF.getPosition().getX()
            r_GCRF[index, 1] = pv_GCRF.getPosition().getY()
            r_GCRF[index, 2] = pv_GCRF.getPosition().getZ()

            v_GCRF[index, 0] = pv_GCRF.getVelocity().getX()
            v_GCRF[index, 1] = pv_GCRF.getVelocity().getY()
            v_GCRF[index, 2] = pv_GCRF.getVelocity().getZ()

        return r_GCRF, v_GCRF

# ========== ========== ========== ========== ========== ==========
def GCRF_from_TEME_astropy(time: Time,
                           r_TEME: numpy.ndarray,
                           v_TEME: numpy.ndarray) -> tuple[numpy.ndarray, 2]:

    coords = coordinates.SkyCoord(
        x=r_TEME[:, 0] << units.m,
        y=r_TEME[:, 1] << units.m,
        z=r_TEME[:, 2] << units.m,
        v_x=v_TEME[:, 0] << units.m / units.s,
        v_y=v_TEME[:, 1] << units.m / units.s,
        v_z=v_TEME[:, 2] << units.m / units.s,
        frame='teme',
        obstime=time.to_astropy(),
        representation_type='cartesian'
    ).transform_to('gcrs')
    coords.representation_type = 'cartesian'

    r_GCRF = coords.cartesian.xyz.T.si.value
    v_GCRF = numpy.concatenate([
        coords.v_x.reshape(-1, 1),
        coords.v_y.reshape(-1, 1),
        coords.v_z.reshape(-1, 1)
    ], axis=1).si.value

    return r_GCRF, v_GCRF

def GCRF_from_TEME_orekit(time: Time,
                          r_TEME: numpy.ndarray,
                          v_TEME: numpy.ndarray) -> tuple[numpy.ndarray, 2]:

    with Orekit():
        from org.orekit.time import AbsoluteDate, TimeScalesFactory
        from org.orekit.frames import FramesFactory, Transform
        from org.orekit.utils import IERSConventions
        from org.orekit.bodies import GeodeticPoint
        from org.orekit.bodies import OneAxisEllipsoid
        from org.orekit.utils import Constants, PVCoordinates

        from org.hipparchus.geometry.euclidean.threed import Vector3D

        # ---------- ---------- ---------- ---------- ----------
        utc = TimeScalesFactory.getUTC()

        def absolutedate_from_timestamp(t: pandas.Timestamp) -> AbsoluteDate:
            return AbsoluteDate(t.year, t.month, t.day, t.hour, t.minute, t.second, utc)

        # ---------- ---------- ---------- ---------- ---------- frames
        GCRF = FramesFactory.getGCRF()
        TEME = FramesFactory.getTEME()
        # ITRF = FramesFactory.getITRF(IERSConventions.IERS_2010, True)

        # ---------- ---------- ---------- ---------- ----------
        r_GCRF = numpy.zeros_like(r_TEME)
        v_GCRF = numpy.zeros_like(v_TEME)

        for index, t in enumerate(time.to_pandas()):
            date = absolutedate_from_timestamp(t)

            pos = Vector3D(r_TEME[index, 0], r_TEME[index, 1], r_TEME[index, 2])
            vel = Vector3D(v_TEME[index, 0], v_TEME[index, 1], v_TEME[index, 2])

            pv = PVCoordinates(pos, vel)
            transform = TEME.getTransformTo(GCRF, date)
            pv_GCRF = transform.transformPVCoordinates(pv)

            r_GCRF[index, 0] = pv_GCRF.getPosition().getX()
            r_GCRF[index, 1] = pv_GCRF.getPosition().getY()
            r_GCRF[index, 2] = pv_GCRF.getPosition().getZ()

            v_GCRF[index, 0] = pv_GCRF.getVelocity().getX()
            v_GCRF[index, 1] = pv_GCRF.getVelocity().getY()
            v_GCRF[index, 2] = pv_GCRF.getVelocity().getZ()

        return r_GCRF, v_GCRF

# ========== ========== ========== ========== ========== ==========
def TEME_from_GCRF_astropy(time: Time,
                           r_GCRF: numpy.ndarray,
                           v_GCRF: numpy.ndarray) -> tuple[numpy.ndarray, 2]:

    coords = coordinates.SkyCoord(
        x=r_GCRF[:, 0] << units.m,
        y=r_GCRF[:, 1] << units.m,
        z=r_GCRF[:, 2] << units.m,
        v_x=v_GCRF[:, 0] << units.m / units.s,
        v_y=v_GCRF[:, 1] << units.m / units.s,
        v_z=v_GCRF[:, 2] << units.m / units.s,
        frame='gcrs',
        obstime=time.to_astropy(),
        representation_type='cartesian'
    ).transform_to('teme')
    coords.representation_type = 'cartesian'

    r_TEME = coords.cartesian.xyz.T.si.value
    v_TEME = numpy.concatenate([
        coords.v_x.reshape(-1, 1),
        coords.v_y.reshape(-1, 1),
        coords.v_z.reshape(-1, 1)
    ], axis=1).si.value

    return r_TEME, v_TEME

def TEME_from_GCRF_orekit(time: Time,
                          r_GCRF: numpy.ndarray,
                          v_GCRF: numpy.ndarray) -> tuple[numpy.ndarray, 2]:

    with Orekit():
        from org.orekit.time import AbsoluteDate, TimeScalesFactory
        from org.orekit.frames import FramesFactory, Transform
        from org.orekit.utils import IERSConventions
        from org.orekit.bodies import GeodeticPoint
        from org.orekit.bodies import OneAxisEllipsoid
        from org.orekit.utils import Constants, PVCoordinates

        from org.hipparchus.geometry.euclidean.threed import Vector3D

        # ---------- ---------- ---------- ---------- ----------
        utc = TimeScalesFactory.getUTC()

        def absolutedate_from_timestamp(t: pandas.Timestamp) -> AbsoluteDate:
            return AbsoluteDate(t.year, t.month, t.day, t.hour, t.minute, t.second, utc)

        # ---------- ---------- ---------- ---------- ---------- frames
        GCRF = FramesFactory.getGCRF()
        TEME = FramesFactory.getTEME()
        # ITRF = FramesFactory.getITRF(IERSConventions.IERS_2010, True)

        # ---------- ---------- ---------- ---------- ----------
        r_TEME = numpy.zeros_like(r_GCRF)
        v_TEME = numpy.zeros_like(v_GCRF)

        for index, t in enumerate(time.to_pandas()):
            date = absolutedate_from_timestamp(t)

            pos = Vector3D(r_GCRF[index, 0], r_GCRF[index, 1], r_GCRF[index, 2])
            vel = Vector3D(v_GCRF[index, 0], v_GCRF[index, 1], v_GCRF[index, 2])

            pv = PVCoordinates(pos, vel)
            transform = GCRF.getTransformTo(TEME, date)
            pv_GCRF = transform.transformPVCoordinates(pv)

            r_TEME[index, 0] = pv_GCRF.getPosition().getX()
            r_TEME[index, 1] = pv_GCRF.getPosition().getY()
            r_TEME[index, 2] = pv_GCRF.getPosition().getZ()

            v_TEME[index, 0] = pv_GCRF.getVelocity().getX()
            v_TEME[index, 1] = pv_GCRF.getVelocity().getY()
            v_TEME[index, 2] = pv_GCRF.getVelocity().getZ()

        return r_TEME, v_TEME



# ========== ========== ========== ========== ========== ==========
class TestGeocentricFrameConversion:

    @pytest.fixture
    def data(self) -> dict:

        filepath = Path(__file__).parent / 'data' / 'molniya_2-9.csv'

        if not filepath.is_file():

            # MOLNIYA 2-9
            line1 = '1  7276U 74026A   25145.84713414  .00000013  00000-0  00000+0 0  9993'
            line2 = '2  7276  64.3566  79.2896 6584676 266.9325  21.8190  2.45096989275692'

            time = Time.range(start='2025-05-28', end='2025-05-30', step=3600)

            frame = propagate_tle_orekit(line1, line2, time.to_pandas())
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

    def test_ITRF_from_TEME(self, data) -> None:

        time = data['time']
        r_TEME = data['r_TEME']
        v_TEME = data['v_TEME']
        
        # ---------- ---------- ---------- ---------- ---------- ----------
        r_ITRF_aspy, v_ITRF_aspy = ITRF_from_TEME_astropy(time, r_TEME, v_TEME)
        r_ITRF_ok, v_ITRF_ok = ITRF_from_TEME_orekit(time, r_TEME, v_TEME)
        r_ITRF_sk, v_ITRF_sk = ITRF_from_TEME(time, r_TEME, v_TEME)

        r_error_sk_astropy = numpy.linalg.norm(r_ITRF_sk - r_ITRF_aspy, axis=1)
        r_error_sk_orekit = numpy.linalg.norm(r_ITRF_sk - r_ITRF_ok, axis=1)

        v_error_sk_astropy = numpy.linalg.norm(v_ITRF_sk - v_ITRF_aspy, axis=1)
        v_error_sk_orekit = numpy.linalg.norm(v_ITRF_sk - v_ITRF_ok, axis=1)

        # ========== ========== ========== ========== ========== ==========
        try:
            assert numpy.allclose(r_error_sk_orekit, 0.0, atol=10.0, rtol=0.0)
            assert numpy.allclose(v_error_sk_orekit, 0.0, atol=0.002, rtol=0.0)

            assert numpy.allclose(r_error_sk_astropy, 0.0, atol=0.10, rtol=0.0)
            assert numpy.allclose(v_error_sk_astropy, 0.0, atol=0.000_150, rtol=0.0)

        except AssertionError as error:

            figure, axes = pyplot.subplots(2, sharex=True)

            axes[0].set_title('Error in position')
            axes[0].plot(time.datetime64, r_error_sk_astropy, label='Error from astropy')
            axes[0].plot(time.datetime64, r_error_sk_orekit, label='Error from orekit')
            axes[0].set_ylabel('m')

            axes[1].set_title('Error in velocity')
            axes[1].plot(time.datetime64, v_error_sk_astropy)
            axes[1].plot(time.datetime64, v_error_sk_orekit)
            axes[1].set_ylabel(r'm/s')

            figure.legend(ncol=2, loc='lower center')

            pyplot.show()

            raise error

    def test_TEME_from_ITRF(self, data) -> None:

        time = data['time']
        r_ITRF = data['r_ITRF']
        v_ITRF = data['v_ITRF']

        # ---------- ---------- ---------- ---------- ---------- ----------
        r_TEME_aspy, v_TEME_aspy = TEME_from_ITRF_astropy(time, r_ITRF, v_ITRF)
        r_TEME_ok, v_TEME_ok = TEME_from_ITRF_orekit(time, r_ITRF, v_ITRF)
        r_TEME_sk, v_TEME_sk = TEME_from_ITRF(time, r_ITRF, v_ITRF)

        r_error_sk_astropy = numpy.linalg.norm(r_TEME_sk - r_TEME_aspy, axis=1)
        r_error_sk_orekit = numpy.linalg.norm(r_TEME_sk - r_TEME_ok, axis=1)

        v_error_sk_astropy = numpy.linalg.norm(v_TEME_sk - v_TEME_aspy, axis=1)
        v_error_sk_orekit = numpy.linalg.norm(v_TEME_sk - v_TEME_ok, axis=1)

        # ========== ========== ========== ========== ========== ==========
        try:
            assert numpy.allclose(r_error_sk_orekit, 0.0, atol=10.0, rtol=0.0)
            assert numpy.allclose(v_error_sk_orekit, 0.0, atol=0.002, rtol=0.0)

            assert numpy.allclose(r_error_sk_astropy, 0.0, atol=0.10, rtol=0.0)
            assert numpy.allclose(v_error_sk_astropy, 0.0, atol=0.000_150, rtol=0.0)

        except AssertionError as error:

            figure, axes = pyplot.subplots(2, sharex=True)

            axes[0].set_title('Error in position')
            axes[0].plot(time.datetime64, r_error_sk_astropy, label='Error from astropy')
            axes[0].plot(time.datetime64, r_error_sk_orekit, label='Error from orekit')
            axes[0].set_ylabel('m')

            axes[1].set_title('Error in velocity')
            axes[1].plot(time.datetime64, v_error_sk_astropy)
            axes[1].plot(time.datetime64, v_error_sk_orekit)
            axes[1].set_ylabel(r'm/s')

            figure.legend(ncol=2, loc='lower center')

            pyplot.show()

            raise error

    def test_ITRF_from_GCRF(self, data) -> None:

        time = data['time']
        r_GCRF = data['r_GCRF']
        v_GCRF = data['v_GCRF']

        # ---------- ---------- ---------- ---------- ---------- ----------
        r_ITRF_aspy, v_ITRF_aspy = ITRF_from_GCRF_astropy(time, r_GCRF, v_GCRF)
        r_ITRF_ok, v_ITRF_ok = ITRF_from_GCRF_orekit(time, r_GCRF, v_GCRF)
        r_ITRF_sk, v_ITRF_sk = ITRF_from_GCRF(time, r_GCRF, v_GCRF)

        r_error_sk_astropy = numpy.linalg.norm(r_ITRF_sk - r_ITRF_aspy, axis=1)
        r_error_sk_orekit = numpy.linalg.norm(r_ITRF_sk - r_ITRF_ok, axis=1)

        v_error_sk_astropy = numpy.linalg.norm(v_ITRF_sk - v_ITRF_aspy, axis=1)
        v_error_sk_orekit = numpy.linalg.norm(v_ITRF_sk - v_ITRF_ok, axis=1)

        # ========== ========== ========== ========== ========== ==========
        try:
            assert numpy.allclose(r_error_sk_orekit, 0.0, atol=5.0, rtol=0.0)
            assert numpy.allclose(v_error_sk_orekit, 0.0, atol=0.002, rtol=0.0)

            assert numpy.allclose(r_error_sk_astropy, 0.0, atol=0.2, rtol=0.0)
            assert numpy.allclose(v_error_sk_astropy, 0.0, atol=0.0003, rtol=0.0)

        except AssertionError as error:

            figure, axes = pyplot.subplots(2, sharex=True)

            axes[0].set_title('Error in position')
            axes[0].plot(time.datetime64, r_error_sk_astropy, label='Error from astropy')
            axes[0].plot(time.datetime64, r_error_sk_orekit, label='Error from orekit')
            axes[0].set_ylabel('m')

            axes[1].set_title('Error in velocity')
            axes[1].plot(time.datetime64, v_error_sk_astropy)
            axes[1].plot(time.datetime64, v_error_sk_orekit)
            axes[1].set_ylabel(r'm/s')

            figure.legend(ncol=2, loc='lower center')

            pyplot.show()

            raise error

    def test_GCRF_from_ITRF(self, data) -> None:

        time = data['time']
        r_ITRF = data['r_ITRF']
        v_ITRF = data['v_ITRF']

        # ---------- ---------- ---------- ---------- ---------- ----------
        r_GCRF_aspy, v_GCRF_aspy = GCRF_from_ITRF_astropy(time, r_ITRF, v_ITRF)
        r_GCRF_ok, v_GCRF_ok = GCRF_from_ITRF_orekit(time, r_ITRF, v_ITRF)
        r_GCRF_sk, v_GCRF_sk = GCRF_from_ITRF(time, r_ITRF, v_ITRF)

        r_error_sk_astropy = numpy.linalg.norm(r_GCRF_sk - r_GCRF_aspy, axis=1)
        r_error_sk_orekit = numpy.linalg.norm(r_GCRF_sk - r_GCRF_ok, axis=1)

        v_error_sk_astropy = numpy.linalg.norm(v_GCRF_sk - v_GCRF_aspy, axis=1)
        v_error_sk_orekit = numpy.linalg.norm(v_GCRF_sk - v_GCRF_ok, axis=1)

        # ========== ========== ========== ========== ========== ==========
        try:
            assert numpy.allclose(r_error_sk_orekit, 0.0, atol=10.0, rtol=0.0)
            assert numpy.allclose(v_error_sk_orekit, 0.0, atol=0.002, rtol=0.0)

            assert numpy.allclose(r_error_sk_astropy, 0.0, atol=0.2, rtol=0.0)
            assert numpy.allclose(v_error_sk_astropy, 0.0, atol=0.000_160, rtol=0.0)

        except AssertionError as error:

            figure, axes = pyplot.subplots(2, sharex=True)

            axes[0].set_title('Error in position')
            axes[0].plot(time.datetime64, r_error_sk_astropy, label='Error from astropy')
            axes[0].plot(time.datetime64, r_error_sk_orekit, label='Error from orekit')
            axes[0].set_ylabel('m')

            axes[1].set_title('Error in velocity')
            axes[1].plot(time.datetime64, v_error_sk_astropy)
            axes[1].plot(time.datetime64, v_error_sk_orekit)
            axes[1].set_ylabel(r'm/s')

            figure.legend(ncol=2, loc='lower center')

            pyplot.show()

            raise error

    # ========== ========== ========== ========== performance
    @profile
    def test_performance_ITRF_from_GCRF(self) -> None:

        N = None
        N = 10001

        data = get_large_test_data()

        time = data['time'][:N]
        r_GCRF = data['r_GCRF'][:N]
        v_GCRF = data['v_GCRF'][:N]
        r_ITRF = data['r_ITRF'][:N]
        v_ITRF = data['v_ITRF'][:N]

        print(time.size)

        r_ITRF_serial, v_ITRF_serial = ITRF_from_GCRF(time, r_GCRF, v_GCRF)
        r_ITRF_prange, v_ITRF_prange = ITRF_from_GCRF_parallel(time, r_GCRF, v_GCRF)

        try:
            assert numpy.allclose(r_ITRF_serial, r_ITRF, atol=10.0, rtol=0.0)
            assert numpy.allclose(v_ITRF_serial, v_ITRF, atol=1.0, rtol=0.0)

            assert numpy.allclose(r_ITRF_prange, r_ITRF, atol=10.0, rtol=0.0)
            assert numpy.allclose(v_ITRF_prange, v_ITRF, atol=1.0, rtol=0.0)

        except AssertionError as error:
            figure, axes = pyplot.subplots(2, sharex=True)

            dr_serial = numpy.linalg.norm(r_ITRF - r_ITRF_serial, axis=1)
            dr_prange = numpy.linalg.norm(r_ITRF - r_ITRF_prange, axis=1)

            axes[0].plot(time.datetime64, dr_serial, label='Serial error')
            axes[0].plot(time.datetime64, dr_prange, label='Parallel error')

            dv_serial = numpy.linalg.norm(v_ITRF - v_ITRF_serial, axis=1)
            dv_prange = numpy.linalg.norm(v_ITRF - v_ITRF_prange, axis=1)

            axes[1].plot(time.datetime64, dv_serial)
            axes[1].plot(time.datetime64, dv_prange)

            figure.legend(ncol=2, loc='lower center')

            figure.autofmt_xdate()

            pyplot.show()

            raise error


# ========== ========== ========== ========== ========== ==========
@pytest.fixture
def data() -> dict:

    filepath = Path(__file__).parent / 'data' / 'molniya_2-9.csv'

    if not filepath.is_file():

        # MOLNIYA 2-9
        line1 = '1  7276U 74026A   25145.84713414  .00000013  00000-0  00000+0 0  9993'
        line2 = '2  7276  64.3566  79.2896 6584676 266.9325  21.8190  2.45096989275692'

        time = Time.range(start='2025-05-28', end='2025-05-30', step=3600)

        frame = propagate_tle_orekit(line1, line2, time.to_pandas())
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


class TestFrame:

    def test_name(self):

        assert GCRF.name == 'GCRF'
        assert ITRF.name == 'ITRF'
        assert TEME.name == 'TEME'

    def test_getitem(self):

        assert Frame['GCRF'] is GCRF
        assert Frame['gcrf'] is GCRF
        assert Frame['gcrf'] == GCRF

    def test_contains(self):
        assert Frame.is_frame('GCRF')
        assert Frame.is_frame('gcrf')

    def test_route(self) -> None:
        print()

        result = [frame.name for frame in Frame.get_route('GCRF', 'TEME')]
        expected = ['GCRF', 'ITRF', 'TEME']

        assert result == expected

        result = [frame.name for frame in Frame.get_route('TEME', 'GCRF')]
        expected = ['GCRF', 'ITRF', 'TEME'][::-1]

        assert result == expected

    def test_ITRF_from_TEME(self, data) -> None:

        time = data['time']
        r_TEME = data['r_TEME']
        v_TEME = data['v_TEME']

        r_ITRF_sk, v_ITRF_sk = TEME.transform_to(ITRF, time, r_TEME, v_TEME)
        r_ITRF_aspy, v_ITRF_aspy = ITRF_from_TEME_astropy(time, r_TEME, v_TEME)
        r_ITRF_ok, v_ITRF_ok = ITRF_from_TEME_orekit(time, r_TEME, v_TEME)

        r_error_sk_astropy = numpy.linalg.norm(r_ITRF_sk - r_ITRF_aspy, axis=1)
        r_error_sk_orekit = numpy.linalg.norm(r_ITRF_sk - r_ITRF_ok, axis=1)

        v_error_sk_astropy = numpy.linalg.norm(v_ITRF_sk - v_ITRF_aspy, axis=1)
        v_error_sk_orekit = numpy.linalg.norm(v_ITRF_sk - v_ITRF_ok, axis=1)

        # ========== ========== ========== ========== ========== ==========
        try:
            assert numpy.allclose(r_error_sk_orekit, 0.0, atol=10.0, rtol=0.0)
            assert numpy.allclose(v_error_sk_orekit, 0.0, atol=0.002, rtol=0.0)

            assert numpy.allclose(r_error_sk_astropy, 0.0, atol=0.50, rtol=0.0)
            assert numpy.allclose(v_error_sk_astropy, 0.0, atol=0.002, rtol=0.0)

        except AssertionError as error:

            figure, axes = pyplot.subplots(2, sharex=True)

            axes[0].set_title('Error in position')
            axes[0].plot(time.datetime64, r_error_sk_astropy, label='Error from astropy')
            axes[0].plot(time.datetime64, r_error_sk_orekit, label='Error from orekit')
            axes[0].set_ylabel('m')

            axes[1].set_title('Error in velocity')
            axes[1].plot(time.datetime64, v_error_sk_astropy)
            axes[1].plot(time.datetime64, v_error_sk_orekit)
            axes[1].set_ylabel(r'm/s')

            figure.legend(ncol=2, loc='lower center')

            pyplot.show()

            raise error

    def test_TEME_from_ITRF(self, data) -> None:

        time = data['time']
        r_ITRF = data['r_ITRF']
        v_ITRF = data['v_ITRF']

        r_TEME_sk, v_TEME_sk = ITRF.transform_to(TEME, time, r_ITRF, v_ITRF)
        r_TEME_aspy, v_TEME_aspy = TEME_from_ITRF_astropy(time, r_ITRF, v_ITRF)
        r_TEME_ok, v_TEME_ok = TEME_from_ITRF_orekit(time, r_ITRF, v_ITRF)

        r_error_sk_astropy = numpy.linalg.norm(r_TEME_sk - r_TEME_aspy, axis=1)
        r_error_sk_orekit = numpy.linalg.norm(r_TEME_sk - r_TEME_ok, axis=1)

        v_error_sk_astropy = numpy.linalg.norm(v_TEME_sk - v_TEME_aspy, axis=1)
        v_error_sk_orekit = numpy.linalg.norm(v_TEME_sk - v_TEME_ok, axis=1)

        # ========== ========== ========== ========== ========== ==========
        try:
            assert numpy.allclose(r_error_sk_orekit, 0.0, atol=10.0, rtol=0.0)
            assert numpy.allclose(v_error_sk_orekit, 0.0, atol=0.002, rtol=0.0)

            assert numpy.allclose(r_error_sk_astropy, 0.0, atol=0.50, rtol=0.0)
            assert numpy.allclose(v_error_sk_astropy, 0.0, atol=0.002, rtol=0.0)

        except AssertionError as error:

            figure, axes = pyplot.subplots(2, sharex=True)

            axes[0].set_title('Error in position')
            axes[0].plot(time.datetime64, r_error_sk_astropy, label='Error from astropy')
            axes[0].plot(time.datetime64, r_error_sk_orekit, label='Error from orekit')
            axes[0].set_ylabel('m')

            axes[1].set_title('Error in velocity')
            axes[1].plot(time.datetime64, v_error_sk_astropy)
            axes[1].plot(time.datetime64, v_error_sk_orekit)
            axes[1].set_ylabel(r'm/s')

            figure.legend(ncol=2, loc='lower center')

            pyplot.show()

            raise error

    def test_ITRF_from_GCRF(self, data) -> None:
        time = data['time']
        r_GCRF = data['r_GCRF']
        v_GCRF = data['v_GCRF']

        # ---------- ---------- ---------- ---------- ---------- ----------
        r_ITRF_sk, v_ITRF_sk = GCRF.transform_to(ITRF, time, r_GCRF, v_GCRF)
        r_ITRF_aspy, v_ITRF_aspy = ITRF_from_GCRF_astropy(time, r_GCRF, v_GCRF)
        r_ITRF_ok, v_ITRF_ok = ITRF_from_GCRF_orekit(time, r_GCRF, v_GCRF)

        r_error_sk_astropy = numpy.linalg.norm(r_ITRF_sk - r_ITRF_aspy, axis=1)
        r_error_sk_orekit = numpy.linalg.norm(r_ITRF_sk - r_ITRF_ok, axis=1)

        v_error_sk_astropy = numpy.linalg.norm(v_ITRF_sk - v_ITRF_aspy, axis=1)
        v_error_sk_orekit = numpy.linalg.norm(v_ITRF_sk - v_ITRF_ok, axis=1)

        # ========== ========== ========== ========== ========== ==========
        try:
            assert numpy.allclose(r_error_sk_orekit, 0.0, atol=5.0, rtol=0.0)
            assert numpy.allclose(v_error_sk_orekit, 0.0, atol=0.002, rtol=0.0)

            assert numpy.allclose(r_error_sk_astropy, 0.0, atol=0.5, rtol=0.0)
            assert numpy.allclose(v_error_sk_astropy, 0.0, atol=0.002, rtol=0.0)

        except AssertionError as error:

            figure, axes = pyplot.subplots(2, sharex=True)

            axes[0].set_title('Error in position')
            axes[0].plot(time.datetime64, r_error_sk_astropy, label='Error from astropy')
            axes[0].plot(time.datetime64, r_error_sk_orekit, label='Error from orekit')
            axes[0].set_ylabel('m')

            axes[1].set_title('Error in velocity')
            axes[1].plot(time.datetime64, v_error_sk_astropy)
            axes[1].plot(time.datetime64, v_error_sk_orekit)
            axes[1].set_ylabel(r'm/s')

            figure.legend(ncol=2, loc='lower center')

            pyplot.show()

            raise error

    def test_GCRF_from_ITRF(self, data) -> None:

        time = data['time']
        r_ITRF = data['r_ITRF']
        v_ITRF = data['v_ITRF']

        # ---------- ---------- ---------- ---------- ---------- ----------
        r_GCRF_sk, v_GCRF_sk = ITRF.transform_to(GCRF, time, r_ITRF, v_ITRF)
        r_GCRF_aspy, v_GCRF_aspy = GCRF_from_ITRF_astropy(time, r_ITRF, v_ITRF)
        r_GCRF_ok, v_GCRF_ok = GCRF_from_ITRF_orekit(time, r_ITRF, v_ITRF)

        r_error_sk_astropy = numpy.linalg.norm(r_GCRF_sk - r_GCRF_aspy, axis=1)
        r_error_sk_orekit = numpy.linalg.norm(r_GCRF_sk - r_GCRF_ok, axis=1)

        v_error_sk_astropy = numpy.linalg.norm(v_GCRF_sk - v_GCRF_aspy, axis=1)
        v_error_sk_orekit = numpy.linalg.norm(v_GCRF_sk - v_GCRF_ok, axis=1)

        # ========== ========== ========== ========== ========== ==========
        try:
            assert numpy.allclose(r_error_sk_orekit, 0.0, atol=10.0, rtol=0.0)
            assert numpy.allclose(v_error_sk_orekit, 0.0, atol=0.002, rtol=0.0)

            assert numpy.allclose(r_error_sk_astropy, 0.0, atol=0.2, rtol=0.0)
            assert numpy.allclose(v_error_sk_astropy, 0.0, atol=0.002, rtol=0.0)

        except AssertionError as error:

            figure, axes = pyplot.subplots(2, sharex=True)

            axes[0].set_title('Error in position')
            axes[0].plot(time.datetime64, r_error_sk_astropy, label='Error from astropy')
            axes[0].plot(time.datetime64, r_error_sk_orekit, label='Error from orekit')
            axes[0].set_ylabel('m')

            axes[1].set_title('Error in velocity')
            axes[1].plot(time.datetime64, v_error_sk_astropy)
            axes[1].plot(time.datetime64, v_error_sk_orekit)
            axes[1].set_ylabel(r'm/s')

            figure.legend(ncol=2, loc='lower center')

            pyplot.show()

            raise error

    def test_GCRF_from_TEME(self, data) -> None:

        time = data['time']
        r_TEME = data['r_TEME']
        v_TEME = data['v_TEME']

        r_GCRF_sk, v_GCRF_sk = TEME.transform_to(GCRF, time, r_TEME, v_TEME)
        r_GCRF_aspy, v_GCRF_aspy = GCRF_from_TEME_astropy(time, r_TEME, v_TEME)
        r_GCRF_ok, v_GCRF_ok = GCRF_from_TEME_orekit(time, r_TEME, v_TEME)

        r_error_sk_astropy = numpy.linalg.norm(r_GCRF_sk - r_GCRF_aspy, axis=1)
        r_error_sk_orekit = numpy.linalg.norm(r_GCRF_sk - r_GCRF_ok, axis=1)

        v_error_sk_astropy = numpy.linalg.norm(v_GCRF_sk - v_GCRF_aspy, axis=1)
        v_error_sk_orekit = numpy.linalg.norm(v_GCRF_sk - v_GCRF_ok, axis=1)

        # ========== ========== ========== ========== ========== ==========
        try:
            assert numpy.allclose(r_error_sk_orekit, 0.0, atol=10.0, rtol=0.0)
            assert numpy.allclose(v_error_sk_orekit, 0.0, atol=0.002, rtol=0.0)

            assert numpy.allclose(r_error_sk_astropy, 0.0, atol=0.10, rtol=0.0)
            assert numpy.allclose(v_error_sk_astropy, 0.0, atol=0.002, rtol=0.0)

        except AssertionError as error:

            figure, axes = pyplot.subplots(2, sharex=True)

            axes[0].set_title('Error in position')
            axes[0].plot(time.datetime64, r_error_sk_astropy, label='Error from astropy')
            axes[0].plot(time.datetime64, r_error_sk_orekit, label='Error from orekit')
            axes[0].set_ylabel('m')

            axes[1].set_title('Error in velocity')
            axes[1].plot(time.datetime64, v_error_sk_astropy)
            axes[1].plot(time.datetime64, v_error_sk_orekit)
            axes[1].set_ylabel(r'm/s')

            figure.legend(ncol=2, loc='lower center')

            pyplot.show()

            raise error

    def test_TEME_from_GCRF(self, data) -> None:

        time = data['time']
        r_GCRF = data['r_GCRF']
        v_GCRF = data['v_GCRF']

        r_TEME_sk, v_TEME_sk = GCRF.transform_to(TEME, time, r_GCRF, v_GCRF)
        r_TEME_aspy, v_TEME_aspy = TEME_from_GCRF_astropy(time, r_GCRF, v_GCRF)
        r_TEME_ok, v_TEME_ok = TEME_from_GCRF_orekit(time, r_GCRF, v_GCRF)

        r_error_sk_astropy = numpy.linalg.norm(r_TEME_sk - r_TEME_aspy, axis=1)
        r_error_sk_orekit = numpy.linalg.norm(r_TEME_sk - r_TEME_ok, axis=1)

        v_error_sk_astropy = numpy.linalg.norm(v_TEME_sk - v_TEME_aspy, axis=1)
        v_error_sk_orekit = numpy.linalg.norm(v_TEME_sk - v_TEME_ok, axis=1)

        # ========== ========== ========== ========== ========== ==========
        try:
            assert numpy.allclose(r_error_sk_orekit, 0.0, atol=10.0, rtol=0.0)
            assert numpy.allclose(v_error_sk_orekit, 0.0, atol=0.002, rtol=0.0)

            assert numpy.allclose(r_error_sk_astropy, 0.0, atol=0.10, rtol=0.0)
            assert numpy.allclose(v_error_sk_astropy, 0.0, atol=0.002, rtol=0.0)

        except AssertionError as error:

            figure, axes = pyplot.subplots(2, sharex=True)

            axes[0].set_title('Error in position')
            axes[0].plot(time.datetime64, r_error_sk_astropy, label='Error from astropy')
            axes[0].plot(time.datetime64, r_error_sk_orekit, label='Error from orekit')
            axes[0].set_ylabel('m')

            axes[1].set_title('Error in velocity')
            axes[1].plot(time.datetime64, v_error_sk_astropy)
            axes[1].plot(time.datetime64, v_error_sk_orekit)
            axes[1].set_ylabel(r'm/s')

            figure.legend(ncol=2, loc='lower center')

            pyplot.show()

            raise error


# ========== ========== ========== ========== ========== ==========
class TestENU:

    @pytest.fixture
    def lla(self) -> tuple[float, 3]:

        lon = numpy.deg2rad(-47.92969)
        lat = numpy.deg2rad(-15.77953)
        alt = 1200 * 1e3

        return lon, lat, alt

    def test_instantiate(self, lla) -> None:
        enu = ENU(*lla)

        assert Frame.get_route(enu, TEME) == [enu, ITRF, TEME]
        assert Frame.get_route(enu, GCRF) == [enu, ITRF, GCRF]

    def test_rot_matrix(self, lla) -> None:

        enu = ENU(*lla)

        ITRF_from_ENU = enu.rot_to_ITRF()
        ENU_from_ITRF = enu.rot_from_ITRF()

        assert numpy.allclose(ITRF_from_ENU, ENU_from_ITRF.T)
        assert numpy.allclose(ENU_from_ITRF@ITRF_from_ENU, numpy.eye(3))

    def test_conversion(self, lla, data) -> None:

        time = data['time']
        r_GCRF = data['r_GCRF']
        v_GCRF = data['v_GCRF']

        enu = ENU(*lla)

        r_ENU, v_ENU = GCRF.transform_to(enu, time, r_GCRF, v_GCRF)

        print(r_ENU)
        print(v_ENU)

        print(enu.r_station_ITRF)

