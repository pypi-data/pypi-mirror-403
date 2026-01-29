#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""


from typing import Callable

from spacekernel.mathtools.ellipsoid import Ellipsoid, WGS84
from spacekernel.typing import DatetimeLike

from numpy.typing import NDArray


class Frame:

    _instances: dict[str, Frame] = {}

    def __class_getitem__(cls, item: str) -> Frame: ...

    def __hash__(self) -> int: ...

    @classmethod
    def is_frame(cls, item: str) -> bool: ...

    @classmethod
    def get_route(cls, source: Frame|str, target: Frame|str) -> list[Frame]: ...

    def transforms(self) -> dict[Frame, Callable]: ...

    def register_transform(self, target_frame: Frame, transform: Callable) -> None: ...

    def remove_transform(self, target_frame: Frame) -> None: ...

    def transform_to(self, frame: Frame|str, time: DatetimeLike, r: NDArray, v: NDArray) -> tuple[NDArray, 2]: ...

    @property
    def name(self) -> str: ...


# ========== ========== ========== ========== ========== ========== GCRF
class _GCRF(Frame):

    def to_ITRF(self, time: DatetimeLike, r_GCRF: NDArray, v_GCRF: NDArray) -> tuple[NDArray, 2]: ...

    def transforms(self) -> dict[Frame, Callable]: ...


def get_GCRF() -> Frame: ...


# ========== ========== ========== ========== ========== ========== ITRF
class _ITRF(Frame):

    def transforms(self) -> dict[Frame, Callable]: ...

    def to_GCRF(self, time: DatetimeLike, r_ITRF: NDArray, v_ITRF: NDArray) -> tuple[NDArray, 2]: ...

    def to_TEME(self, time: DatetimeLike, r_ITRF: NDArray, v_ITRF: NDArray) -> tuple[NDArray, 2]: ...


def get_ITRF() -> Frame: ...


# ========== ========== ========== ========== ========== ========== TEME
class _TEME(Frame):


    def to_ITRF(self, time: DatetimeLike, r_TEME: NDArray, v_TEME: NDArray) -> tuple[NDArray, 2]: ...

    def transforms(self) -> dict[Frame, Callable]: ...


def get_TEME() -> Frame: ...

# ========== ========== ========== ========== ========== ========== ENU
class ENU(Frame):

    def __init__(self, lon: float, lat: float, alt: float, ell: Ellipsoid = WGS84) -> None: ...

    def rot_to_ITRF(self) -> NDArray: ...

    def rot_from_ITRF(self) -> NDArray: ...

    def to_ITRF(self,
                time: DatetimeLike,
                r_ENU: NDArray,
                v_ENU: NDArray) -> tuple[NDArray, 2]: ...

    def from_ITRF(self,
                  time: DatetimeLike,
                  r_ITRF: NDArray,
                  v_ITRF: NDArray) -> tuple[NDArray, 2]:

    @property
    def r_station_ITRF(self) -> NDArray: ...