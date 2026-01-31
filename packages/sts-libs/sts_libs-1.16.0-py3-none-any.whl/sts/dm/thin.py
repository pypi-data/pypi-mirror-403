# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Device Mapper thin provisioning targets.

This module provides functionality for managing thin-pool and thin devices:
- ThinPoolDevice: Manages a pool of storage for thin provisioning
- ThinDevice: Virtual device that allocates space from a pool on demand

Thin provisioning allows allocating more virtual space than physical storage,
with actual allocation happening on-demand as data is written.

Class Hierarchy:
    DmDevice
        ├── ThinPoolDevice (parent - manages pool and child thin devices)
        └── ThinDevice (child - allocates from pool)

The ThinPoolDevice tracks its child ThinDevice instances and provides methods
for creating, deleting, and snapshotting thin volumes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from sts.dm.base import DmDevice

if TYPE_CHECKING:
    from sts.blockdevice import BlockDevice


@dataclass
class ThinPoolDevice(DmDevice):
    """Thin pool target.

    Manages a pool of storage space from which thin volumes can be allocated.
    Enables thin provisioning - allocating more virtual space than physical.

    Tracks child ThinDevice instances and provides methods for managing them.

    Args format: <metadata dev> <data dev> <block size> <low water mark> <flags> <args>

    Example:
        ```python
        # Create pool from block devices
        pool = ThinPoolDevice.from_block_devices(metadata_dev, data_dev)
        pool.create('my-pool')

        # Create thin volume from pool
        thin = pool.create_thin(thin_id=0, size=2097152, dm_name='my-thin')

        # Create snapshot
        snap = pool.create_snapshot(origin_id=0, snap_id=1, dm_name='my-snap')

        # Cleanup
        pool.delete_thin(1)  # Delete snapshot
        pool.delete_thin(0)  # Delete origin
        pool.remove()
        ```
    """

    # Track child thin devices: thin_id -> ThinDevice
    thin_devices: dict[int, ThinDevice] = field(init=False, default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        """Set target type and initialize."""
        self.target_type = 'thin-pool'
        super().__post_init__()

    @classmethod
    def from_block_devices(
        cls,
        metadata_device: BlockDevice,
        data_device: BlockDevice,
        block_size_sectors: int = 128,
        low_water_mark: int = 0,
        features: list[str] | None = None,
        start: int = 0,
        size: int | None = None,
    ) -> ThinPoolDevice:
        """Create ThinPoolDevice from BlockDevices.

        Args:
            metadata_device: Device for storing thin pool metadata
            data_device: Device for storing actual data
            block_size_sectors: Block size in sectors (default: 128 = 64KB)
            low_water_mark: Low water mark in sectors (default: 0 = auto)
            features: List of thin pool features (default: ['skip_block_zeroing'])
            start: Start sector in virtual device (default: 0)
            size: Size in sectors (default: data device size)

        Returns:
            ThinPoolDevice instance

        Example:
            ```python
            metadata_dev = BlockDevice('/dev/sdb1')  # Small device for metadata
            data_dev = BlockDevice('/dev/sdb2')  # Large device for data
            pool = ThinPoolDevice.from_block_devices(metadata_dev, data_dev)
            ```
        """
        if size is None and data_device.size is not None:
            # Use data device size, converted to sectors using actual sector size
            size = data_device.size // data_device.sector_size

        if features is None:
            features = ['skip_block_zeroing']

        metadata_id = cls._get_device_identifier(metadata_device)
        data_id = cls._get_device_identifier(data_device)

        # Build args: <metadata dev> <data dev> <block size> <low water mark> <# feature args> <feature args>
        args_parts = [
            metadata_id,
            data_id,
            str(block_size_sectors),
            str(low_water_mark),
            str(len(features)),
            *features,
        ]

        args = ' '.join(args_parts)
        if size is None:
            raise ValueError('size must be provided or data_device.size must be available')
        return cls(start=start, size_sectors=size, args=args)

    def create_thin(
        self,
        thin_id: int,
        size: int,
        dm_name: str,
        *,
        activate: bool = True,
    ) -> ThinDevice | None:
        """Create a new thin volume in the pool.

        Sends 'create_thin' message to the pool and optionally activates the device.

        Args:
            thin_id: Unique ID for this thin volume within the pool
            size: Size in sectors for the thin volume
            dm_name: Device mapper name for the activated device
            activate: Whether to activate the device (default: True)

        Returns:
            ThinDevice instance if successful, None otherwise

        Example:
            ```python
            pool.create('my-pool')
            thin = pool.create_thin(thin_id=0, size=2097152, dm_name='my-thin')
            ```
        """
        if not self.is_created:
            logging.error('Pool must be created before creating thin devices')
            return None

        if thin_id in self.thin_devices:
            logging.error(f'Thin device with ID {thin_id} already exists in pool')
            return None

        # Send create_thin message to pool
        if not self.message(0, f'"create_thin {thin_id}"'):
            logging.error(f'Failed to create thin device {thin_id} in pool')
            return None

        logging.info(f'Created thin device ID {thin_id} in pool {self.dm_name}')

        # Create ThinDevice configuration
        thin_dev = ThinDevice.create_from_pool(
            pool=self,
            thin_id=thin_id,
            size=size,
        )

        if activate and not thin_dev.create(dm_name):
            logging.error(f'Failed to activate thin device {dm_name}')
            # Clean up the thin device from pool
            self.message(0, f'"delete {thin_id}"')
            return None

        # Track the thin device
        self.thin_devices[thin_id] = thin_dev
        return thin_dev

    def delete_thin(self, thin_id: int, *, force: bool = False) -> bool:
        """Delete a thin volume from the pool.

        Removes the thin device mapping and deletes it from the pool.

        Args:
            thin_id: ID of the thin volume to delete
            force: Force removal even if device is in use

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            pool.delete_thin(0)
            ```
        """
        if not self.is_created:
            logging.error('Pool must be created before deleting thin devices')
            return False

        # Remove the DM device if it's tracked and activated
        if thin_id in self.thin_devices:
            thin_dev = self.thin_devices[thin_id]
            if thin_dev.is_created and not thin_dev.remove(force=force):
                logging.error(f'Failed to remove thin device {thin_dev.dm_name}')
                return False

        # Delete thin from pool
        if not self.message(0, f'"delete {thin_id}"'):
            logging.error(f'Failed to delete thin device {thin_id} from pool')
            return False

        # Remove from tracking
        self.thin_devices.pop(thin_id, None)
        logging.info(f'Deleted thin device ID {thin_id} from pool {self.dm_name}')
        return True

    def create_snapshot(
        self,
        origin_id: int,
        snap_id: int,
        dm_name: str,
        *,
        size: int | None = None,
        activate: bool = True,
    ) -> ThinDevice | None:
        """Create a snapshot of an existing thin volume.

        Creates an internal snapshot using 'create_snap' message.
        The origin device should be suspended during snapshot creation.

        Args:
            origin_id: ID of the origin thin volume to snapshot
            snap_id: Unique ID for the new snapshot
            dm_name: Device mapper name for the activated snapshot
            size: Size in sectors (default: same as origin)
            activate: Whether to activate the snapshot device (default: True)

        Returns:
            ThinDevice instance for the snapshot if successful, None otherwise

        Example:
            ```python
            # Suspend origin before snapshot
            origin = pool.thin_devices[0]
            origin.suspend()

            # Create snapshot
            snap = pool.create_snapshot(origin_id=0, snap_id=1, dm_name='my-snap')

            # Resume origin
            origin.resume()
            ```
        """
        if not self.is_created:
            logging.error('Pool must be created before creating snapshots')
            return None

        if snap_id in self.thin_devices:
            logging.error(f'Thin device with ID {snap_id} already exists in pool')
            return None

        # Determine size from origin if not specified
        if size is None:
            if origin_id in self.thin_devices:
                size = self.thin_devices[origin_id].size_sectors
            else:
                logging.error(f'Origin {origin_id} not tracked, size must be specified')
                return None

        # Send create_snap message to pool
        if not self.message(0, f'"create_snap {snap_id} {origin_id}"'):
            logging.error(f'Failed to create snapshot {snap_id} of {origin_id}')
            return None

        logging.info(f'Created snapshot ID {snap_id} of origin {origin_id} in pool {self.dm_name}')

        # Create ThinDevice configuration for snapshot
        snap_dev = ThinDevice.create_from_pool(
            pool=self,
            thin_id=snap_id,
            size=size,
        )

        if activate and not snap_dev.create(dm_name):
            logging.error(f'Failed to activate snapshot device {dm_name}')
            # Clean up the snapshot from pool
            self.message(0, f'"delete {snap_id}"')
            return None

        # Track the snapshot device
        self.thin_devices[snap_id] = snap_dev
        return snap_dev

    def remove(self, *, force: bool = False, retry: bool = False, deferred: bool = False) -> bool:
        """Remove the thin pool device.

        Removes all child thin devices first, then removes the pool.

        Args:
            force: Replace table with one that fails all I/O
            retry: Retry removal for a few seconds if it fails
            deferred: Enable deferred removal when device is in use

        Returns:
            True if successful, False otherwise
        """
        # Remove all tracked thin devices first
        for thin_id in list(self.thin_devices.keys()):
            self.delete_thin(thin_id, force=force)

        # Remove the pool itself
        return super().remove(force=force, retry=retry, deferred=deferred)


@dataclass
class ThinDevice(DmDevice):
    """Thin target.

    A virtual device that allocates space from a thin pool on demand.
    Enables over-provisioning of storage.

    Maintains a reference to its parent pool for proper lifecycle management.

    Args format: <pool dev> <dev id>

    Example:
        ```python
        # Create via pool (recommended)
        thin = pool.create_thin(thin_id=0, size=2097152, dm_name='my-thin')

        # Or create manually
        thin = ThinDevice.from_thin_pool(pool, thin_id=1, size=2097152)
        thin.create('another-thin')
        ```
    """

    # Reference to parent pool
    pool: ThinPoolDevice | None = field(init=False, default=None, repr=False)

    # Thin device ID within pool
    thin_id: int | None = field(init=False, default=None, repr=False)

    def __post_init__(self) -> None:
        """Set target type and initialize."""
        self.target_type = 'thin'
        super().__post_init__()

    @classmethod
    def create_from_pool(
        cls,
        pool: ThinPoolDevice,
        thin_id: int,
        size: int,
        start: int = 0,
    ) -> ThinDevice:
        """Create ThinDevice configuration from pool.

        This is used by ThinPoolDevice.create_thin() and create_snapshot()
        to create the device configuration before activation.

        Args:
            pool: The parent thin pool device
            thin_id: Unique ID for this thin volume within the pool
            size: Size in sectors
            start: Start sector in virtual device (default: 0)

        Returns:
            ThinDevice instance (not yet activated)
        """
        pool_id = cls._get_device_identifier(pool)
        args = f'{pool_id} {thin_id}'

        device = cls(start=start, size_sectors=size, args=args)
        device.pool = pool
        device.thin_id = thin_id
        return device

    @classmethod
    def from_thin_pool(
        cls,
        pool_device: DmDevice,
        thin_id: int,
        start: int = 0,
        size: int | None = None,
    ) -> ThinDevice:
        """Create ThinDevice from thin pool device.

        Note: For full parent-child tracking, use ThinPoolDevice.create_thin() instead.

        Args:
            pool_device: The thin pool device
            thin_id: Unique ID for this thin volume within the pool
            start: Start sector in virtual device (default: 0)
            size: Size in sectors (required for thin targets)

        Returns:
            ThinDevice instance

        Raises:
            ValueError: If size is not provided

        Example:
            ```python
            pool = DmDevice(dm_name='pool')
            thin = ThinDevice.from_thin_pool(pool, thin_id=1, size=2097152)
            ```
        """
        if size is None:
            raise ValueError('Size must be specified for thin targets')

        pool_id = cls._get_device_identifier(pool_device)
        args = f'{pool_id} {thin_id}'

        device = cls(start=start, size_sectors=size, args=args)
        device.thin_id = thin_id

        # Set pool reference if it's a ThinPoolDevice
        if isinstance(pool_device, ThinPoolDevice):
            device.pool = pool_device

        return device
