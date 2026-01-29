#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

from .time import Time
from .state import State, StateVector, COE, GeoState
from .propagators.analytical.sgp4.tle import TLE, ELSET


try:
    # this will run if the spacekernel package is installed
    from importlib.metadata import version, PackageNotFoundError
    __version__ = version("spacekernel")
except PackageNotFoundError:
    # this will run during development
    from toml import load
    from pathlib import Path

    pyproject_toml = Path(__file__).parent.parent / "pyproject.toml"

    with pyproject_toml.open() as file:
        data = load(file)

    __version__ = data["project"]["version"]