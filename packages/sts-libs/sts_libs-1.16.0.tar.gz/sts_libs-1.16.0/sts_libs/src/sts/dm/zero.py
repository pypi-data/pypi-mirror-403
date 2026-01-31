# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Device Mapper device management.

This module provides functionality for managing Device Mapper devices:
- Device discovery
- Device information
- Device operations
- Device Mapper targets

Device Mapper is a Linux kernel framework for mapping physical block devices
onto higher-level virtual block devices. It forms the foundation for (example):
- LVM (Logical Volume Management)
- Software RAID (dm-raid)
- Disk encryption (dm-crypt)
- Thin provisioning (dm-thin)

Class Hierarchy:
    BlockDevice
        └── DmDevice (base for all DM devices)
                ├── LinearDevice
                ├── DelayDevice
                ├── VdoDevice
                ├── MultipathTarget
                ├── ThinPoolDevice
                ├── ThinDevice
                ├── ZeroDevice
                └── ErrorDevice

Each device class can be in two states:
1. Configuration: has target config (start, size, args) but not yet created
2. Active: device exists on system, has path, name, dm_name, etc.
"""

from __future__ import annotations

from dataclasses import dataclass

from sts.dm.base import DmDevice


@dataclass
class ZeroDevice(DmDevice):
    """Zero target.

    Returns blocks of zeros when read. Writes are discarded.
    Useful for creating sparse devices or testing.

    Args format: (no arguments)

    Example:
        ```python
        target = ZeroTarget(0, 1000000, '')
        str(target)
        '0 1000000 zero'
        ```
    """

    def __post_init__(self) -> None:
        """Set target type and initialize."""
        self.target_type = 'zero'
        super().__post_init__()

    @classmethod
    def create_config(
        cls,
        start: int = 0,
        size: int | None = None,
    ) -> ZeroDevice:
        """Create ZeroTarget.

        Args:
            start: Start sector in virtual device (default: 0)
            size: Size in sectors (required)

        Returns:
            ZeroTarget instance

        Example:
            ```python
            target = ZeroTarget.create(size=2097152)
            str(target)
            '0 2097152 zero'
            ```
        """
        if size is None:
            raise ValueError('Size must be specified for zero targets')

        return cls(start=start, size_sectors=size, args='')
