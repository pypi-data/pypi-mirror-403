# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""LVM device management.

This module provides functionality for managing LVM devices:
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

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from sts.lvm.base import LvmDevice
from sts.utils.cmdline import run

if TYPE_CHECKING:
    from sts.blockdevice import BlockDevice


@dataclass
class PVInfo:
    """Physical Volume information.

    Stores key information about a Physical Volume:
    - Volume group membership
    - Format type (lvm2)
    - Attributes (allocatable, exported, etc)
    - Size information (total and free space)

    Args:
        vg: Volume group name (None if not in a VG)
        fmt: PV format (usually 'lvm2')
        attr: PV attributes (e.g. 'a--' for allocatable)
        psize: PV size (e.g. '1.00t')
        pfree: PV free space (e.g. '500.00g')
    """

    vg: str | None
    fmt: str
    attr: str
    psize: str
    pfree: str


@dataclass
class PhysicalVolume(LvmDevice):
    """Physical Volume device.

    A Physical Volume (PV) is a disk or partition used by LVM.
    PVs provide the storage pool for Volume Groups.

    Key features:
    - Initialize disks/partitions for LVM use
    - Track space allocation
    - Handle bad block management
    - Store LVM metadata

    Args:
        name: Device name (optional)
        path: Device path (optional, defaults to /dev/<name>)
        size: Device size in bytes (optional, discovered from device)
        model: Device model (optional)
        yes: Automatically answer yes to prompts
        force: Force operations without confirmation
        vg: Volume group name (optional, discovered from device)
        fmt: PV format (optional, discovered from device)
        attr: PV attributes (optional, discovered from device)
        pfree: PV free space (optional, discovered from device)

    Example:
        ```python
        pv = PhysicalVolume(name='sda1')  # Discovers other values
        pv = PhysicalVolume.create('/dev/sda1')  # Creates new PV
        ```
    """

    # Optional parameters for this class
    vg: str | None = None  # Volume Group membership
    fmt: str | None = None  # PV format (usually lvm2)
    attr: str | None = None  # PV attributes
    pfree: str | None = None  # Free space

    # Available PV commands
    COMMANDS: ClassVar[list[str]] = [
        'pvchange',  # Modify PV attributes
        'pvck',  # Check PV metadata
        'pvcreate',  # Initialize PV
        'pvdisplay',  # Show PV details
        'pvmove',  # Move PV data
        'pvremove',  # Remove PV
        'pvresize',  # Resize PV
        'pvs',  # List PVs
        'pvscan',  # Scan for PVs
    ]

    # Discover PV info if path is available
    def discover_pv_info(self) -> None:
        """Discovers PV information if path is available.

        Volume group membership.
        Format and attributes.
        Size information.
        """
        result = run(f'pvs {self.path} --noheadings --separator ","')
        if result.succeeded:
            # Parse PV info line
            # Format: PV,VG,Fmt,Attr,PSize,PFree
            parts = result.stdout.strip().split(',')
            if len(parts) == 6:
                _, vg, fmt, attr, _, pfree = parts
                if not self.vg:
                    self.vg = vg or None
                if not self.fmt:
                    self.fmt = fmt
                if not self.attr:
                    self.attr = attr
                if not self.pfree:
                    self.pfree = pfree

    def create(self, **options: str) -> bool:
        """Create Physical Volume.

        Initializes a disk or partition for use with LVM:
        - Creates LVM metadata area
        - Prepares device for VG membership

        Args:
            **options: PV options (see LvmOptions)

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            pv = PhysicalVolume(path='/dev/sda1')
            pv.create()
            True
            ```
        """
        if not self.path:
            logging.error('Device path required')
            return False

        result = self._run('pvcreate', str(self.path), **options)
        if result.succeeded:
            self.discover_pv_info()
        return result.succeeded

    def remove(self, **options: str) -> bool:
        """Remove Physical Volume.

        Removes LVM metadata from device:
        - Device must not be in use by a VG
        - Data on device is not erased

        Args:
            **options: PV options (see LvmOptions)

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            pv = PhysicalVolume(path='/dev/sda1')
            pv.remove()
            True
            ```
        """
        if not self.path:
            logging.error('Device path required')
            return False

        result = self._run('pvremove', str(self.path), **options)
        return result.succeeded

    @classmethod
    def from_blockdevice(cls, block_device: BlockDevice, *, create: bool = False, **options: str) -> PhysicalVolume:
        """Create PhysicalVolume from BlockDevice.

        Creates a PhysicalVolume instance from an existing BlockDevice,
        optionally initializing it with pvcreate.

        Args:
            block_device: BlockDevice instance to create PV from
            create: Whether to run pvcreate to initialize the device
            **options: Additional pvcreate options (see pvcreate man page)

        Returns:
            PhysicalVolume instance

        Raises:
            ValueError: If block_device is None or has no path
            RuntimeError: If create=True and pvcreate fails

        Example:
            ```python
            from sts.blockdevice import BlockDevice

            # Create PV without initializing
            bd = BlockDevice('/dev/sda1')
            pv = PhysicalVolume.from_blockdevice(bd)

            # Create and initialize PV
            pv = PhysicalVolume.from_blockdevice(bd, create=True)

            # Create with options
            pv = PhysicalVolume.from_blockdevice(bd, create=True, dataalignment='1m')
            ```
        """
        if not block_device:
            msg = 'BlockDevice instance is required'
            raise ValueError(msg)

        if not block_device.path:
            msg = 'BlockDevice must have a valid path'
            raise ValueError(msg)

        # Create PhysicalVolume instance with attributes from BlockDevice
        pv = cls(
            path=str(block_device.path),
            size=block_device.size,
            model=block_device.model,
        )

        # Initialize the device if requested
        if create:
            success = pv.create(**options)
            if not success:
                msg = f'Failed to create physical volume on {block_device.path}'
                raise RuntimeError(msg)

        return pv

    @classmethod
    def get_all(cls) -> dict[str, PVInfo]:
        """Get all Physical Volumes.

        Returns:
            Dictionary mapping PV names to their information

        Example:
            ```python
            PhysicalVolume.get_all()
            {'/dev/sda1': PVInfo(vg='vg0', fmt='lvm2', ...)}
            ```
        """
        result = run('pvs --noheadings --separator ","')
        if result.failed:
            logging.debug('No Physical Volumes found')
            return {}

        # Format: PV,VG,Fmt,Attr,PSize,PFree
        pv_info_regex = r'\s+(\S+),(\S+)?,(\S+),(.*),(.*),(.*)$'
        pv_dict = {}

        for line in result.stdout.splitlines():
            if match := re.match(pv_info_regex, line):
                pv_dict[match.group(1)] = PVInfo(
                    vg=match.group(2) or None,  # VG can be empty
                    fmt=match.group(3),
                    attr=match.group(4),
                    psize=match.group(5),
                    pfree=match.group(6),
                )

        return pv_dict
