#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

from typing import Any, Optional, Union
import numpy as np


from spacekernel.typing import DatetimeLike
from spacekernel.time import Time
from spacekernel.frames import Frame, ITRF, GCRF
from spacekernel.state import State
from spacekernel.utils import Representable
from spacekernel.bodies import Earth
from spacekernel.mathtools.ellipsoid import Ellipsoid, WGS84


class StateVector(State, Representable):
    """
    Representation of a time-stamped Cartesian state vector (position and velocity).
    """

    def _get_header(self) -> str: ...
    def _get_body(self) -> str: ...

    epoch: Time
    frame: Frame
    mass: float

    @property
    def r(self) -> np.ndarray:
        """
        Position vector in the reference frame.
        """
        ...

    @property
    def v(self) -> np.ndarray:
        """
        Velocity vector in the reference frame.
        """
        ...

    @property
    def x(self) -> np.ndarray:
        """
        Combined position and velocity vectors.
        """
        ...

    def __init__(
        self,
        epoch: DatetimeLike,
        r: Union[np.ndarray, list[float], tuple[float, float, float]],
        v: Union[np.ndarray, list[float], tuple[float, float, float]],
        frame: Optional[Union[Frame, str]] = Frame.GCRF,
        mass: float = float("nan")
    ) -> None: ...

    def __getattr__(self, item: str) -> "StateVector": ...

    def copy(self) -> "StateVector": ...

    def transform_to(self, frame: Frame) -> "StateVector": ...

    def to_coe(
        self,
        GM: float = Earth.GM,
        Re: float = Earth.Re,
        frame: Frame = Frame.GCRF
    ) -> COE: ...

    def to_geostate(self) -> GeoState: ...


class COE(State, Representable):
    """
    Classical Orbital Elements (COE) representation of an orbit.
    """

    epoch: Time
    frame: Frame
    mass: float
    GM: float
    Re: float

    # ---------- Orbital elements ----------
    @property
    def sma(self) -> float: ...
    """Semimajor axis [meters]."""

    @property
    def ecc(self) -> float: ...
    """Eccentricity (unitless)."""

    @property
    def inc(self) -> float: ...
    """Inclination [radians]."""

    @property
    def raa(self) -> float: ...
    """Right ascension of ascending node (RAAN) [radians]."""

    @property
    def arp(self) -> float: ...
    """Argument of periapsis [radians]."""

    @property
    def tra(self) -> float: ...
    """True anomaly [radians]."""

    @property
    def slr(self) -> float: ...
    """Semilatus rectum [meters]."""

    # ---------- Derived properties ----------
    @property
    def orp(self) -> float: ...
    """Orbital period [seconds]."""

    @property
    def mnm(self) -> float: ...
    """Mean motion [radians/second]."""

    @property
    def mea(self) -> float: ...
    """Mean anomaly [radians]."""

    @property
    def eca(self) -> float: ...
    """Eccentric anomaly [radians]."""

    @property
    def pge(self) -> float: ...
    """Perigee radius [meters]."""

    @property
    def apg(self) -> float: ...
    """Apogee radius [meters]."""

    # ---------- Init ----------
    def __init__(
        self,
        epoch: DatetimeLike,
        frame: Optional[Union[Frame, str]] = GCRF,
        GM: float = Earth.GM,
        Re: float = Earth.Re,
        mass: float = float("nan"),
        **kwargs: Any
    ) -> None: ...
    """
    Initialize a COE object.
    Accepts keyword arguments for orbital elements and auxiliary parameters.
    """

    # ---------- Public Methods ----------
    def copy(self) -> "COE": ...
    """Return a deep copy of this COE object."""

    def to_sv(self) -> StateVector: ...
    """Convert this COE to a StateVector (position and velocity)."""

    def _get_header(self) -> str: ...
    def _get_body(self) -> str: ...



class GeoState(State, Representable):
    """
    Geodetic state representation of position and velocity on Earth.

    Contains longitude, latitude, altitude and their time derivatives.
    """

    epoch: Time
    frame: Frame
    ell: Ellipsoid
    mass: float

    # ---------- Geodetic properties ----------
    @property
    def lon(self) -> float: ...
    """Longitude [radians]."""

    @property
    def lat(self) -> float: ...
    """Latitude [radians]."""

    @property
    def alt(self) -> float: ...
    """Altitude above ellipsoid [meters]."""

    @property
    def lon_dot(self) -> float: ...
    """Longitude rate [radians/second]."""

    @property
    def lat_dot(self) -> float: ...
    """Latitude rate [radians/second]."""

    @property
    def alt_dot(self) -> float: ...
    """Altitude rate [meters/second]."""

    # ---------- Init ----------
    def __init__(
        self,
        epoch: DatetimeLike,
        frame: Optional[Union[Frame, str]] = ITRF,
        ell: Ellipsoid = WGS84,
        mass: float = float("nan"),
        **kwargs: Any
    ) -> None: ...
    """
    Initialize a GeoState object.

    Parameters
    ----------
    epoch : DatetimeLike
        Epoch of the state.
    frame : Frame or str, optional
        Reference frame. Default is ITRF.
    ell : Ellipsoid, optional
        Reference ellipsoid. Default is WGS84.
    mass : float, optional
        Mass of the object [kg]. Default is NaN.
    **kwargs : dict
        Can include:
        - lon : Longitude [rad]
        - lat : Latitude [rad]
        - alt : Altitude [m]
        - lon_dot : Longitude rate [rad/s]
        - lat_dot : Latitude rate [rad/s]
        - alt_dot : Altitude rate [m/s]
    """

    # ---------- Public Methods ----------
    def copy(self) -> "GeoState": ...
    """Return a deep copy of this GeoState."""

    def to_sv(self) -> StateVector: ...
    """Convert this GeoState to a StateVector (Cartesian position and velocity)."""

    def _get_header(self) -> str: ...
    def _get_body(self) -> str: ...
