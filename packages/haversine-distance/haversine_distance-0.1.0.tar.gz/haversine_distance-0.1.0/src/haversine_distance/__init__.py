# SPDX-FileCopyrightText: 2026-present Artem Lykhvar <me@a10r.com>
#
# SPDX-License-Identifier: MIT
import sys
from types import ModuleType

from haversine_distance.haversine import haversine

__all__ = ["haversine"]


class _Callable(ModuleType):
    def __call__(self, lon1, lat1, lon2,  lat2):
        return haversine(lon1, lat1, lon2,  lat2)


sys.modules[__name__].__class__ = _Callable
