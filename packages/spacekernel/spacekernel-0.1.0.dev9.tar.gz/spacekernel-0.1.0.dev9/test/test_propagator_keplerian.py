#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""
import numpy
from matplotlib import pyplot

from test.data import molniya
from test.orekit.propagation import propagate_keplerian

from spacekernel import Time
from spacekernel.state import StateVector
from spacekernel.units import *
from spacekernel.propagators.analytical.keplerian import Keplerian
from spacekernel.mathtools import StateTransitionMatrix

class TestKeplerianPropagator:

    def test_result(self, molniya) -> None:

        time = molniya['time']

        r = molniya['r_GCRF']
        v = molniya['v_GCRF']

        t = time.to_pandas()

        # ---------- ---------- ---------- ---------- ---------- ok
        r_ok, v_ok = propagate_keplerian(r[0], v[0], t[0], t)

        # ---------- ---------- ---------- ---------- ---------- sk
        sv = StateVector(time[0], r[0], v[0])

        propagator = Keplerian()

        eph = propagator.propagate(time, sv)

        r_sk = eph.r
        v_sk = eph.v

        # ---------- ---------- ---------- ---------- ----------
        try:
            assert numpy.allclose(r_sk, r_ok)
            assert numpy.allclose(v_sk, v_ok)

        except AssertionError as error:

            figure, axes = pyplot.subplots(2, sharex=True)

            dr = r_ok - r_sk
            dv = v_ok - v_sk

            axes[0].plot(time.datetime64, numpy.linalg.norm(dr, axis=1))
            axes[1].plot(time.datetime64, numpy.linalg.norm(dv, axis=1))

            pyplot.show()

            raise error

    def test_jacobian(self, molniya) -> None:
        print()
        time = molniya['time']

        r = molniya['r_GCRF']
        v = molniya['v_GCRF']

        # ---------- ---------- ---------- ---------- ---------- sk
        sv = StateVector(time[0], r[0], v[0])

        propagator = Keplerian()

        eph = propagator.propagate(time, sv)
        jac = propagator.jacobian(eph)

        for i in range(eph.size):
            assert numpy.all(jac[i, :3, :3] == 0.0)
            assert numpy.all(jac[i, :3, 3:] == numpy.eye(3))
            assert numpy.all(jac[i, 3:, 3:] == 0.0)

            r = eph.r[i].reshape(3, 1)
            r_norm = numpy.linalg.norm(r)
            r2 = r_norm**2
            r5 = r_norm**5

            _jac = propagator.GM / r5 * (3*r@r.T - r2 * numpy.eye(3))

            assert numpy.allclose(jac[i, 3:, :3], _jac)

            if i > 1000:
                break

    def test_transition_matrix(self, molniya):

        print()
        time = molniya['time']

        r = molniya['r_GCRF']
        v = molniya['v_GCRF']

        # ---------- ---------- ---------- ---------- ---------- sk
        sv = StateVector(time[0], r[0], v[0])

        time = Time.range(start=time[0], end=time[0] + 10*hour, step=1*second)
        propagator = Keplerian()

        eph = propagator.propagate(time, sv)
        jac = propagator.jacobian(eph)

        phi = StateTransitionMatrix(time, jac, step=0.1)
        phi.plot_estimation_performance(show=True)

        phi(time[5], time[3])
        phi(time, time[3])
        phi(time[-1], time)


