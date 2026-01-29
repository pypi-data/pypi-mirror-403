#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

import numpy

from astropy.constants import GM_sun, R_sun
from astropy import coordinates

from spacekernel import Time
from spacekernel.bodies import Sun, Moon

from matplotlib import pyplot

from test.orekit.bodies import get_sun_GCRF, get_moon_GCRF


class TestSun:

    def test_access_static_attributes(self) -> None:
        assert numpy.isclose(Sun.GM_IAU2015, GM_sun.si.value)
        assert numpy.isclose(Sun.GM_JPL2021, GM_sun.si.value)
        assert numpy.isclose(Sun.GM, GM_sun.si.value)
        assert numpy.isclose(Sun.Re, R_sun.si.value)

    def test_position_and_unit_vector_GCRF(self) -> None:

        time = Time.range(start='2024-01-01 00:00:00',
                          end='2024-06-30 23:59:59',
                          n_points=1000)

        # ---------- ---------- ---------- ---------- ---------- orekit
        r_sun_orekit, v_sun_orekit = get_sun_GCRF(time.to_pandas())
        ur_sun_orekit = r_sun_orekit / numpy.linalg.norm(r_sun_orekit, axis=1)[:, None]

        # ---------- ---------- ---------- ---------- ---------- astropy
        r_sun_aspy = coordinates.get_sun(time.to_astropy()).cartesian.xyz.T.si.value
        ur_sun_aspy = r_sun_aspy / numpy.linalg.norm(r_sun_aspy, axis=1)[:, None]

        # ---------- ---------- ---------- ---------- ---------- spacekernel
        r_sun_spkn = Sun(time).r_GCRF
        ur_sun_spkn = Sun(time).ur_GCRF

        print(Sun(time).ephemeris)

        delta_aspy = r_sun_aspy - r_sun_spkn
        delta_norm_aspy = numpy.linalg.norm(delta_aspy, axis=1)

        delta_orekit = r_sun_orekit - r_sun_spkn
        delta_norm_orekit = numpy.linalg.norm(delta_orekit, axis=1)

        try:
            # difference from astropy's is smaller than 50 metres
            # I believe if TDB is used instead of TT, the diff may become even smaller
            assert numpy.allclose(r_sun_aspy, r_sun_spkn, rtol=0.0, atol=50)
            assert numpy.all(delta_norm_aspy < 50)
            assert numpy.allclose(ur_sun_aspy, ur_sun_spkn, rtol=0.0, atol=numpy.deg2rad(1.0e-7))

        except AssertionError as error:
            figure, axes = pyplot.subplots(5, sharex=True)

            axes[0].set_title('x-coord difference')
            axes[0].plot(time.datetime64, delta_aspy[:, 0], label='astropy')
            axes[0].plot(time.datetime64, delta_orekit[:, 0], label='orekit')
            axes[0].set_ylabel('m')

            axes[1].set_title('y-coord difference')
            axes[1].plot(time.datetime64, delta_aspy[:, 1])
            axes[1].plot(time.datetime64, delta_orekit[:, 1])
            axes[1].set_ylabel('m')

            axes[2].set_title('z-coord difference')
            axes[2].plot(time.datetime64, delta_aspy[:, 2])
            axes[2].plot(time.datetime64, delta_orekit[:, 2])
            axes[2].set_ylabel('m')

            axes[3].set_title('delta difference')
            axes[3].plot(time.datetime64, delta_norm_aspy)
            axes[3].plot(time.datetime64, delta_norm_orekit)
            axes[3].set_ylabel('m')

            axes[4].set_title('delta angle')
            axes[4].plot(time.datetime64, numpy.rad2deg(numpy.arccos((ur_sun_aspy*ur_sun_spkn).sum(axis=1))))
            axes[4].plot(time.datetime64, numpy.rad2deg(numpy.arccos((ur_sun_orekit*ur_sun_spkn).sum(axis=1))))
            axes[4].set_ylabel('deg')

            figure.legend()

            pyplot.show()

            raise error


class TestMoon:

    def test_access_static_attributes(self) -> None:
        print()
        print(Moon.GM)
        print(Moon.Re)

    def test_moon_position_and_unit_vector_GCRF(self) -> None:

        time = Time.range(start='2024-01-01 00:00:00',
                          end='2024-06-30 23:59:59',
                          n_points=1000)

        # ---------- ---------- ---------- ---------- ---------- orekit
        r_moon_orekit, v_moon_orekit = get_moon_GCRF(time.to_pandas())
        ur_moon_orekit = r_moon_orekit / numpy.linalg.norm(r_moon_orekit, axis=1)[:, None]

        # ---------- ---------- ---------- ---------- ---------- astropy
        r_moon_aspy = coordinates.get_body('moon', time.to_astropy()).cartesian.xyz.T.si.value
        ur_moon_aspy = r_moon_aspy / numpy.linalg.norm(r_moon_aspy, axis=1)[:, None]

        # ---------- ---------- ---------- ---------- ---------- spacekernel
        moon = Moon(time)
        r_moon_spkn = moon.r_GCRF
        ur_moon_spkn = moon.ur_GCRF

        assert numpy.all(time == moon.time)

        # ---------- ---------- ---------- ---------- ----------
        delta_aspy = r_moon_aspy - r_moon_spkn
        delta_norm_aspy = numpy.linalg.norm(delta_aspy, axis=1)

        delta_orekit = r_moon_orekit - r_moon_spkn
        delta_norm_orekit = numpy.linalg.norm(delta_orekit, axis=1)

        try:
            # difference from astropy's is about 45 km
            assert numpy.allclose(r_moon_aspy, r_moon_spkn, rtol=0.0, atol=45e3)
            assert numpy.all(delta_norm_aspy < 45e3)
            assert numpy.allclose(ur_moon_aspy, ur_moon_spkn, rtol=0.0, atol=numpy.deg2rad(0.01))

            # assert False

        except AssertionError as error:
            figure, axes = pyplot.subplots(5, sharex=True)

            axes[0].set_title('x-coord difference')
            axes[0].plot(time.datetime64, delta_aspy[:, 0], label='astropy')
            axes[0].plot(time.datetime64, delta_orekit[:, 0], label='orekit')
            axes[0].set_ylabel('m')

            axes[1].set_title('y-coord difference')
            axes[1].plot(time.datetime64, delta_aspy[:, 1])
            axes[1].plot(time.datetime64, delta_orekit[:, 1])
            axes[1].set_ylabel('m')

            axes[2].set_title('z-coord difference')
            axes[2].plot(time.datetime64, delta_aspy[:, 2])
            axes[2].plot(time.datetime64, delta_orekit[:, 2])
            axes[2].set_ylabel('m')

            axes[3].set_title('delta difference')
            axes[3].plot(time.datetime64, delta_norm_aspy)
            axes[3].plot(time.datetime64, delta_norm_orekit)
            axes[3].set_ylabel('m')

            axes[4].set_title('delta angle')
            axes[4].plot(time.datetime64, numpy.rad2deg(numpy.arccos((ur_moon_aspy*ur_moon_spkn).sum(axis=1))))
            axes[4].plot(time.datetime64, numpy.rad2deg(numpy.arccos((ur_moon_orekit*ur_moon_spkn).sum(axis=1))))
            axes[4].set_ylabel('deg')

            figure.legend()

            pyplot.show()

            raise error