#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

import numpy
from scipy.cluster.vq import kmeans
from scipy.linalg import expm

from test import profile

from spacekernel.units import *
from spacekernel.propagators.analytical.keplerian import Keplerian
from spacekernel.state import COE
from spacekernel.time import Time

from spacekernel.mathtools.matrix import exp

@profile
def test_exp():

    numpy.random.seed(0)

    for i in range(10000):
        a = 0.001*numpy.random.rand(6, 6)

        expa_spker = exp(a)
        expa_scipy = expm(a)

        try:
            assert numpy.allclose(expa_spker, expa_scipy)

        except AssertionError as error:
            print()

            print(f'iteration: {i}')
            print(a)
            print(expa_spker)
            print(expa_scipy)
            print()

            print(numpy.max(numpy.abs(expa_spker - expa_scipy)))

            raise error


@profile
def test_exp_jac_keplerian():
    """
    The goal of this test was to verify if exp would perform greater than expm
    for real life transition matrices. The conclusion is that exp is slightly
    faster than exp for steps below 5 seconds and slower for steps above 30s.
    But there is no significant reason to stop using expm. Scipy is great!
    """
    coe = COE(
        '2025-01-01',
        sma = 7000*km,
        ecc = 0.65,
        inc = 60*deg,
        raa = 0,
        arp = 0,
        tra = 0)

    time = Time.range(start=coe.epoch, step=0.1, end=coe.epoch + hour)

    propagator = Keplerian()
    eph = propagator.propagate(time, coe)
    jac = propagator.jacobian(eph)

    dt = time[1:] - time[:-1]
    J = 0.5 * (jac[1:] + jac[:-1])

    Jdt = J*dt.reshape(-1, 1, 1)

    for a in Jdt:

        expa_spker = exp(a)
        expa_scipy = expm(a)

        try:
            assert numpy.allclose(expa_spker, expa_scipy)

        except AssertionError as error:
            print()

            print(a)
            print(expa_spker)
            print(expa_scipy)
            print()

            print(numpy.max(numpy.abs(expa_spker - expa_scipy)))

            raise error



