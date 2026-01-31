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
from typing import TYPE_CHECKING

from sts.dm.base import DmDevice

if TYPE_CHECKING:
    from sts.blockdevice import BlockDevice


@dataclass
class LinearDevice(DmDevice):
    """Linear device mapper device.

    The simplest DM device type - maps a linear range of the virtual device
    directly onto a linear range of another device.

    Args format: <destination device> <sector offset>

    Example:
        ```python
        device = LinearDevice.from_block_device(backing_dev, size_sectors=1000000)
        device.create('my-linear')
        str(device)
        '0 1000000 linear 8:16 0'
        ```
    """

    def __post_init__(self) -> None:
        """Set target type and initialize."""
        self.target_type = 'linear'
        super().__post_init__()

    @classmethod
    def from_block_device(
        cls,
        device: BlockDevice,
        start: int = 0,
        size_sectors: int | None = None,
        offset: int = 0,
    ) -> LinearDevice:
        """Create LinearDevice from BlockDevice.

        Args:
            device: Source block device
            start: Start sector in virtual device (default: 0)
            size_sectors: Size in sectors (default: device size in sectors)
            offset: Offset in source device (default: 0)

        Returns:
            LinearDevice instance

        Example:
            ```python
            device = BlockDevice('/dev/sdb')
            linear = LinearDevice.from_block_device(device, size_sectors=1000000)
            linear.create('my-linear')
            ```
        """
        if size_sectors is None and device.size is not None:
            size_sectors = device.size // device.sector_size

        device_id = cls._get_device_identifier(device)
        args = f'{device_id} {offset}'

        if size_sectors is None:
            raise ValueError('size_sectors must be provided or device.size must be available')
        return cls(start=start, size_sectors=size_sectors, args=args)

    @classmethod
    def create_positional(
        cls,
        device_path: str,
        offset: int = 0,
        start: int = 0,
        size_sectors: int | None = None,
    ) -> LinearDevice:
        """Create LinearDevice with positional arguments.

        Args:
            device_path: Target device path (e.g., '/dev/sdb' or '8:16')
            offset: Offset in source device sectors (default: 0)
            start: Start sector in virtual device (default: 0)
            size_sectors: Size in sectors (required)

        Returns:
            LinearDevice instance

        Example:
            ```python
            linear = LinearDevice.create_positional('/dev/sdb', offset=0, size_sectors=2097152)
            linear.create('my-linear')
            ```
        """
        if size_sectors is None:
            raise ValueError('Size must be specified for linear devices')

        args = f'{device_path} {offset}'
        return cls(start=start, size_sectors=size_sectors, args=args)
