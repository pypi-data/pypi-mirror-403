# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""LVM device management.

This package provides functionality for managing LVM devices:
- Physical Volume (PV) operations
- Volume Group (VG) operations
- Logical Volume (LV) operations

LVM (Logical Volume Management) provides flexible disk space management:
1. Physical Volumes (PVs): Physical disks or partitions
2. Volume Groups (VGs): Pool of space from PVs
3. Logical Volumes (LVs): Virtual partitions from VG space

Key benefits:
- Resize filesystems online
- Snapshot and mirror volumes
- Stripe across multiple disks
- Move data between disks
"""

from __future__ import annotations

from sts.lvm.base import LvmDevice
from sts.lvm.logical_volume import LogicalVolume, ThinPool
from sts.lvm.lvconf import LvmConfig
from sts.lvm.physical_volume import PhysicalVolume
from sts.lvm.volume_group import VolumeGroup

__all__ = [
    'LogicalVolume',
    'LvmConfig',
    'LvmDevice',
    'PhysicalVolume',
    'ThinPool',
    'VolumeGroup',
]
