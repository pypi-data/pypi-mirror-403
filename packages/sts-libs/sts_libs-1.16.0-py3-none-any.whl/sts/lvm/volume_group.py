# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""LVM Volume Group management.

This module provides functionality for managing LVM Volume Groups (VGs).

A Volume Group (VG) combines Physical Volumes into a storage pool that can be divided into Logical Volumes.

Key features:
- Combine multiple PVs
- Manage extent allocation
- Handle PV addition/removal
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import ClassVar

from sts.lvm.base import LvmDevice
from sts.utils.cmdline import run


@dataclass
class VolumeGroup(LvmDevice):
    """Volume Group device.

    A Volume Group (VG) combines Physical Volumes into a storage pool.
    This pool can then be divided into Logical Volumes.

    Key features:
    - Combine multiple PVs
    - Manage storage pool
    - Track extent allocation
    - Handle PV addition/removal

    Args:
        name: Device name (optional)
        path: Device path (optional, defaults to /dev/<name>)
        size: Device size in bytes (optional, discovered from device)
        model: Device model (optional)
        yes: Automatically answer yes to prompts
        force: Force operations without confirmation
        pvs: List of Physical Volumes (optional, discovered from device)

    Example:
        ```python
        vg = VolumeGroup(
            name='vg0'
        )  # Creates Volume Group with name (this doesn't create the VG on the system, only creates the object)
        vg.create(['/dev/sda1'])  # Creates VG with name 'vg0' on the system using the Physical Volume '/dev/sda1'
        ```
    """

    # Optional parameters for this class
    pvs: list[str] = field(default_factory=list)  # Member PVs

    # Available VG commands
    COMMANDS: ClassVar[list[str]] = [
        'vgcfgbackup',  # Backup VG metadata
        'vgcfgrestore',  # Restore VG metadata
        'vgchange',  # Change VG attributes
        'vgck',  # Check VG metadata
        'vgconvert',  # Convert VG metadata format
        'vgcreate',  # Create VG
        'vgdisplay',  # Show VG details
        'vgexport',  # Make VG inactive
        'vgextend',  # Add PVs to VG
        'vgimport',  # Make VG active
        'vgimportclone',  # Import cloned PVs
        'vgimportdevices',  # Import PVs into VG
        'vgmerge',  # Merge VGs
        'vgmknodes',  # Create VG special files
        'vgreduce',  # Remove PVs from VG
        'vgremove',  # Remove VG
        'vgrename',  # Rename VG
        'vgs',  # List VGs
        'vgscan',  # Scan for VGs
        'vgsplit',  # Split VG into two
    ]

    def discover_pvs(self) -> list[str] | None:
        """Discover PVs if name is available."""
        if self.name:
            result = run(f'vgs {self.name} -o pv_name --noheadings')
            if result.succeeded:
                self.pvs = result.stdout.strip().splitlines()
                return self.pvs
        return None

    def create(self, **options: str) -> bool:
        """Create Volume Group.

        Creates a new VG from specified PVs:
        - Initializes VG metadata
        - Sets up extent allocation
        - Creates device mapper devices

        Args:
            **options: VG options (see LvmOptions)

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            vg = VolumeGroup(name='vg0', pvs=['/dev/sda1'])
            vg.create()
            True
            ```
        """
        if not self.name:
            logging.error('Volume group name required')
            return False
        if not self.pvs:
            logging.error('Physical volumes required')
            return False

        result = self._run('vgcreate', self.name, *self.pvs, **options)
        return result.succeeded

    def remove(self, **options: str) -> bool:
        """Remove Volume Group.

        Removes VG and its metadata:
        - All LVs must be removed first
        - PVs are released but not removed

        Args:
            **options: VG options (see LvmOptions)

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            vg = VolumeGroup(name='vg0')
            vg.remove()
            True
            ```
        """
        if not self.name:
            logging.error('Volume group name required')
            return False

        result = self._run('vgremove', self.name, **options)
        return result.succeeded

    def activate(self, **options: str) -> bool:
        """Activate Volume Group.

        Makes the VG and all its LVs available for use.

        Args:
            **options: VG options (see LvmOptions)

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            vg = VolumeGroup(name='vg0')
            vg.activate()
            ```
        """
        if not self.name:
            logging.error('Volume group name required')
            return False

        result = self._run('vgchange', '-a', 'y', self.name, **options)
        return result.succeeded

    def deactivate(self, **options: str) -> bool:
        """Deactivate Volume Group.

        Makes the VG and all its LVs unavailable.

        Args:
            **options: VG options (see LvmOptions)

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            vg = VolumeGroup(name='vg0')
            vg.deactivate()
            ```
        """
        if not self.name:
            logging.error('Volume group name required')
            return False

        result = self._run('vgchange', '-a', 'n', self.name, **options)
        return result.succeeded
