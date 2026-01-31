# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Device Mapper device management.

This package provides functionality for managing Device Mapper devices.
"""

from __future__ import annotations

from sts.dm.base import DmDevice
from sts.dm.cache import CacheDevice
from sts.dm.delay import DelayDevice
from sts.dm.error import ErrorDevice
from sts.dm.flakey import FlakeyDevice
from sts.dm.linear import LinearDevice
from sts.dm.thin import ThinDevice, ThinPoolDevice
from sts.dm.vdo import VdoDevice
from sts.dm.zero import ZeroDevice

__all__ = [
    'CacheDevice',
    'DelayDevice',
    'DmDevice',
    'ErrorDevice',
    'FlakeyDevice',
    'LinearDevice',
    'ThinDevice',
    'ThinPoolDevice',
    'VdoDevice',
    'ZeroDevice',
]
