#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

import pytest

import numpy, pandas

from pathlib import Path

from matplotlib import pyplot

from beeprint import pp
from pyvista.core.utilities.cell_type_helper import n_points

from spacekernel import Time
from spacekernel.mathtools.ellipsoid import Ellipsoid

from numpy.typing import NDArray

from test.orekit.propagation import propagate_tle


@pytest.fixture
def data() -> dict:
    filepath = Path(__file__).parent / 'data' / 'molniya_2-9_lla.csv'

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

    r_ITRF = frame[['rx_ITRF', 'ry_ITRF', 'rz_ITRF']].values
    v_ITRF = frame[['vx_ITRF', 'vy_ITRF', 'vz_ITRF']].values

    return {
        'time': time,
        'r_ITRF': r_ITRF,
        'v_ITRF': v_ITRF,
        'lon': frame['lon'],
        'lat': frame['lat'],
        'alt': frame['alt'],
    }


class TestEllipsoid:

    @pytest.fixture
    def WGS84(self) -> Ellipsoid:
        return Ellipsoid(6378137.0, 0.0033528106647474805)

    @pytest.fixture
    def lat_lon(self) -> tuple[NDArray, 2]:

        lat = numpy.linspace(-90.0, 90.0, 100)
        lon = numpy.linspace(-180.0, 180.0, 100)

        return numpy.deg2rad(lat), numpy.deg2rad(lon)

    def test_access_to_properties(self, WGS84) -> None:

        assert WGS84.Re == 6378137.0
        assert WGS84.f == 0.0033528106647474805

    def test_method_reduced_lat_from_geodetic_lat(self, WGS84, lat_lon) -> None:

        geo_lat = lat_lon[0]
        red_lat_obtained = WGS84.reduced_lat_from_geodetic_lat(geo_lat)
        red_lat_expected = numpy.arctan(numpy.tan(geo_lat) * (1 - WGS84.f))

        assert numpy.all(red_lat_obtained == red_lat_expected)

    def test_method_geodetic_lat_from_reduced_lat(self, WGS84, lat_lon) -> None:

        red_lat = lat_lon[0]
        geo_lat_obtained = WGS84.geodetic_lat_from_reduced_lat(red_lat)
        geo_lat_expected = numpy.arctan(numpy.tan(red_lat) / (1 - WGS84.f))

        assert numpy.all(geo_lat_obtained == geo_lat_expected)

    def test_method_enu_local_frame(self, WGS84, lat_lon) -> None:
        print()

        lat, lon = lat_lon

        frame = WGS84.enu(lat, lon)

        print(frame['u_east'])
        print(frame['u_north'])
        print(frame['u_up'])

        print(numpy.linalg.norm(frame['u_east'], axis=1))

    def test_method_surf_pos_from_surf_coord(self, WGS84, lat_lon) -> None:
        print()

        lat, lon = lat_lon

        r_surf = WGS84.surf_pos_from_surf_coord(lat, lon)

        print(r_surf)

    def test_method_surf_coord_from_surf_pos(self, WGS84, lat_lon) -> None:
        print()

        lat, lon = lat_lon

        r_surf = WGS84.surf_pos_from_surf_coord(lat, lon)

        lat_lon = WGS84.surf_coord_from_surf_pos(r_surf)

        assert numpy.allclose(lat_lon['lat'], lat)
        assert numpy.allclose(lat_lon['lon'], lon)

    def test_method_solve_reduced_lat_equation(self, WGS84, lat_lon) -> None:
        print()

        lat, lon = lat_lon

        r_pos = WGS84.surf_pos_from_surf_coord(lat, lon)
        u_up = WGS84.enu(lat, lon)['u_up']

        h = numpy.linspace(10.0, 1e7, len(lat))

        r_sat = r_pos + h[:, numpy.newaxis] * u_up

        # ---------- ---------- ----------
        beta = WGS84.solve_reduced_lat_equation(r_sat)

        phi = WGS84.geodetic_lat_from_reduced_lat(beta)

        assert numpy.allclose(phi, lat)

    def test_method_lla_from_pos(self, WGS84, lat_lon) -> None:
        print()

        lat, lon = lat_lon
        alt = numpy.linspace(10.0, 1e7, len(lat))

        r_pos = WGS84.surf_pos_from_surf_coord(lat, lon)
        u_up = WGS84.enu(lat, lon)['u_up']

        r_sat = r_pos + alt[:, numpy.newaxis] * u_up

        assert abs(r_sat[0, 2]) - WGS84.Re * (1 - WGS84.f) == alt[0]
        assert abs(r_sat[-1, 2]) - WGS84.Re * (1 - WGS84.f) == alt[-1]

        # ---------- ---------- ----------
        lla = WGS84.lla_from_pos(r_sat)

        lat_obtained = lla['lat']
        lon_obtained = lla['lon']
        alt_obtained = lla['alt']

        assert numpy.allclose(lat_obtained, lat)
        assert numpy.allclose(lon_obtained, lon)
        assert numpy.allclose(alt_obtained, alt)

    def test_method_pos_from_lla(self, WGS84, lat_lon) -> None:
        print()

        lat, lon = lat_lon
        alt = numpy.linspace(10.0, 1e7, len(lat))

        r_surf = WGS84.surf_pos_from_surf_coord(lat, lon)
        u_up = WGS84.enu(lat, lon)['u_up']

        r_expected = r_surf + alt[:, numpy.newaxis] * u_up
        r_obtained = WGS84.pos_from_lla(lat, lon, alt)

        numpy.allclose(r_obtained, r_expected)

    def test_method_surf_pos_of_ray_first_intersection(self, WGS84) -> None:
        print()

        lat = numpy.deg2rad(45.0)
        lon = numpy.deg2rad(45.0)
        alt = 500e3

        r_source = WGS84.pos_from_lla(lat, lon, alt)

        u_ray = -r_source / numpy.linalg.norm(r_source)

        print(r_source)
        print(u_ray)

        r_surf = WGS84.surf_pos_of_ray_first_intersection(r_source, u_ray)

        coord = WGS84.surf_coord_from_surf_pos(r_surf)

        print(coord['lon'], lon)
        print(coord['lat'], lat)

    def test_method_aer_coords(self, WGS84, lat_lon) -> None:
        print()

        # ---------- ---------- ---------- ---------- target
        lat, lon = lat_lon
        alt = numpy.linspace(10.0, 1e7, len(lat))

        r_target = WGS84.pos_from_lla(lat, lon, alt)

        # ---------- ---------- ---------- ---------- observer
        lat_obs = numpy.deg2rad(45.0)
        lon_obs = numpy.deg2rad(45.0)
        alt_obs = 2000

        aer = WGS84.aer_coords(r_target, lat_obs, lon_obs, alt_obs)

        print(numpy.rad2deg(aer['azimuth']))
        print(numpy.rad2deg(aer['elevation']))
        print(aer['range'] / 1000)

    def test_geodetic_state_from_state_vector(self, WGS84, data) -> None:
        print()

        t = data['time']
        r = data['r_ITRF']
        v = data['v_ITRF']

        print(2*WGS84.f - WGS84.f**2)

        geostate = WGS84.geodetic_state_from_state_vector(r, v)

        assert numpy.allclose(geostate['lon'], data['lon'])
        assert numpy.allclose(geostate['lat'], data['lat'])
        assert numpy.allclose(geostate['alt'], data['alt'])

        figure, axes = pyplot.subplots(2, sharex=True)
        #
        # axes[0].plot(t.datetime64, numpy.rad2deg(geostate['lon']))
        # axes[0].plot(t.datetime64, numpy.rad2deg(data['lon']))
        # axes[1].plot(t.datetime64, numpy.rad2deg(geostate['lon_dot']))

        axes[0].plot(t.datetime64, numpy.rad2deg(geostate['lat']))
        axes[0].plot(t.datetime64, numpy.rad2deg(data['lat']))
        axes[1].plot(t.datetime64, numpy.rad2deg(geostate['lat_dot']))

        # axes[0].plot(t.datetime64, geostate['alt'])
        # axes[0].plot(t.datetime64, data['alt'])
        # axes[1].plot(t.datetime64, geostate['alt_dot'])

        pyplot.show()

    def test_state_vector_from_geodetic_state(self, WGS84, data) -> None:
        print()

        t = data['time']
        r = data['r_ITRF']
        v = data['v_ITRF']

        geostate = WGS84.geodetic_state_from_state_vector(r, v)

        r_obtained, v_obtained = WGS84.state_vector_from_geodetic_state(geostate)

        assert numpy.allclose(r_obtained, r)
        assert numpy.allclose(v_obtained, v)

        # assert numpy.allclose(geostate['lon'], data['lon'])
        # assert numpy.allclose(geostate['lat'], data['lat'])
        # assert numpy.allclose(geostate['alt'], data['alt'])
        #
        # figure, axes = pyplot.subplots(2, sharex=True)
        # #
        # # axes[0].plot(t.datetime64, numpy.rad2deg(geostate['lon']))
        # # axes[0].plot(t.datetime64, numpy.rad2deg(data['lon']))
        # # axes[1].plot(t.datetime64, numpy.rad2deg(geostate['lon_dot']))
        #
        # axes[0].plot(t.datetime64, numpy.rad2deg(geostate['lat']))
        # axes[0].plot(t.datetime64, numpy.rad2deg(data['lat']))
        # axes[1].plot(t.datetime64, numpy.rad2deg(geostate['lat_dot']))
        #
        # # axes[0].plot(t.datetime64, geostate['alt'])
        # # axes[0].plot(t.datetime64, data['alt'])
        # # axes[1].plot(t.datetime64, geostate['alt_dot'])
        #
        # pyplot.show()



