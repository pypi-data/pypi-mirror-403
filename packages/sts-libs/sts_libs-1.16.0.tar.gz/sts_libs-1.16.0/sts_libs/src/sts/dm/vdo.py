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

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from sts.dm.base import DmDevice

if TYPE_CHECKING:
    from sts.blockdevice import BlockDevice


@dataclass
class VdoDevice(DmDevice):
    """VDO (Virtual Data Optimizer) target.

    Provides block-level deduplication, compression, and thin provisioning.
    VDO is a device mapper target that can add these features to the storage stack.

    Note: VDO volumes must be formatted with 'vdoformat' before use.

    Args format: V4 <storage device> <storage device size> <minimum I/O size>
                 <block map cache size> <block map era length> [optional arguments]

    Attributes:
        vdo_version: VDO version string (e.g., 'V4')
        storage_device: Storage device identifier
        storage_size_blocks: Storage device size in 4096-byte blocks
        minimum_io_size: Minimum I/O size in bytes
        block_map_cache_blocks: Block map cache size in 4096-byte blocks
        block_map_period: Block map era length
        ack_threads: Number of ack threads
        bio_threads: Number of bio threads
        bio_rotation: Bio rotation interval
        cpu_threads: Number of CPU threads
        hash_zone_threads: Number of hash zone threads
        logical_threads: Number of logical threads
        physical_threads: Number of physical threads
        max_discard: Maximum discard size in 4096-byte blocks
        deduplication: Whether deduplication is enabled
        compression: Whether compression is enabled

    Example:
        ```python
        target = VdoTarget(0, 2097152, 'V4 /dev/sdb 262144 4096 32768 16380')
        str(target)
        '0 2097152 vdo V4 /dev/sdb 262144 4096 32768 16380'
        target.storage_device
        '/dev/sdb'
        target.compression
        False
        ```
    """

    # Parsed attributes (populated by refresh)
    # Names match dmsetup parameter names
    vdo_version: str | None = field(init=False, default=None)
    storage_device: str | None = field(init=False, default=None)
    storage_size_blocks: int | None = field(init=False, default=None)
    minimum_io_size: int | None = field(init=False, default=None)
    block_map_cache_blocks: int | None = field(init=False, default=None)
    block_map_period: int | None = field(init=False, default=None)
    ack: int | None = field(init=False, default=None)
    bio: int | None = field(init=False, default=None)
    bioRotationInterval: int | None = field(init=False, default=None)  # noqa: N815
    cpu: int | None = field(init=False, default=None)
    hash: int | None = field(init=False, default=None)
    logical: int | None = field(init=False, default=None)
    physical: int | None = field(init=False, default=None)
    maxDiscard: int | None = field(init=False, default=None)  # noqa: N815
    deduplication: bool | None = field(init=False, default=None)
    compression: bool | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        """Set target type and initialize."""
        self.target_type = 'vdo'
        super().__post_init__()

    @classmethod
    def from_block_device(
        cls,
        device: BlockDevice,
        logical_size_sectors: int,
        *,
        start: int = 0,
        minimum_io_size: int = 4096,
        block_map_cache_size_mb: int = 128,
        block_map_period: int = 16380,
        **kwargs: int | bool | None,
    ) -> VdoDevice:
        """Create VdoTarget from BlockDevice.

        Args:
            device: Storage block device (must be pre-formatted with vdoformat)
            logical_size_sectors: Logical device size in 512-byte sectors
            start: Start sector in virtual device (default: 0)
            minimum_io_size: Minimum I/O size in bytes, 512 or 4096 (default: 4096)
            block_map_cache_size_mb: Block map cache size in MB (default: 128, min: 128)
            block_map_period: Block map era length (default: 16380, range: 1-16380)
            **kwargs: Optional VDO parameters (use dmsetup parameter names):
                ack: Number of ack threads (default: 1)
                bio: Number of bio threads (default: 4)
                bioRotationInterval: Bio rotation interval (default: 64, range: 1-1024)
                cpu: Number of CPU threads (default: 1)
                hash: Number of hash zone threads (default: 0, range: 0-100)
                logical: Number of logical threads (default: 0, range: 0-60)
                physical: Number of physical threads (default: 0, range: 0-16)
                maxDiscard: Maximum discard size in 4096-byte blocks (default: 1)
                deduplication: Enable deduplication (default: True)
                compression: Enable compression (default: False)

        Returns:
            VdoTarget instance

        Example:
            ```python
            device = BlockDevice('/dev/sdb')  # Pre-formatted with vdoformat
            target = VdoTarget.from_block_device(
                device,
                logical_size_sectors=2097152,  # 1 GB logical
                compression=True,
            )
            ```
        """
        # Get device identifier
        device_id = cls._get_device_identifier(device)

        # Calculate storage device size in 4096-byte blocks
        if device.size is None:
            raise ValueError('Cannot determine size: device size is unknown')
        storage_size_blocks = device.size // 4096

        # Convert block map cache size from MB to 4096-byte blocks
        block_map_cache_blocks = (block_map_cache_size_mb * 1024 * 1024) // 4096

        # Build required arguments
        args_parts = [
            'V4',
            device_id,
            str(storage_size_blocks),
            str(minimum_io_size),
            str(block_map_cache_blocks),
            str(block_map_period),
        ]

        # Build optional arguments as key-value pairs
        # NOTE: dm-vdo kernel constraint: if any of hash/logical/physical threads is
        # non-zero, all three must be specified and non-zero. This is NOT validated here
        # to allow testing negative cases - the kernel will reject invalid configurations.

        # Valid dmsetup parameter names for thread/discard settings
        optional_params = ('ack', 'bio', 'bioRotationInterval', 'cpu', 'hash', 'logical', 'physical', 'maxDiscard')
        optional_args: list[str] = []

        for param_name in optional_params:
            value = kwargs.get(param_name)
            if value is not None:
                optional_args.extend([param_name, str(value)])

        # Handle deduplication (only add if False, as True is default)
        dedup_val = kwargs.get('deduplication', True)
        deduplication_enabled = bool(dedup_val) if dedup_val is not None else True
        if not deduplication_enabled:
            optional_args.extend(['deduplication', 'off'])

        # Handle compression (only add if True, as False is default)
        comp_val = kwargs.get('compression', False)
        compression_enabled = bool(comp_val) if comp_val is not None else False
        if compression_enabled:
            optional_args.extend(['compression', 'on'])

        # Combine all arguments
        if optional_args:
            args_parts.extend(optional_args)

        args = ' '.join(args_parts)
        target = cls(start=start, size_sectors=logical_size_sectors, args=args)

        # Set attributes directly - we know the values
        target.vdo_version = 'V4'
        target.storage_device = device_id
        target.storage_size_blocks = storage_size_blocks
        target.minimum_io_size = minimum_io_size
        target.block_map_cache_blocks = block_map_cache_blocks
        target.block_map_period = block_map_period
        target.deduplication = deduplication_enabled
        target.compression = compression_enabled

        # Set optional parameters from kwargs
        for param_name in optional_params:
            value = kwargs.get(param_name)
            if value is not None:
                setattr(target, param_name, value)

        return target

    def refresh(self) -> None:
        """Parse args and update instance attributes.

        Extracts all VDO parameters from the args string and updates
        instance attributes. Useful after modifying args or when
        reconstructing from dmsetup table output.

        Updates:
            - vdo_version, storage_device, storage_size_blocks (required)
            - minimum_io_size, block_map_cache_blocks, block_map_period (required)
            - ack_threads, bio_threads, bio_rotation, cpu_threads (optional)
            - hash_zone_threads, logical_threads, physical_threads (optional)
            - max_discard, deduplication, compression (optional)

        Example:
            ```python
            target = VdoTarget(0, 2097152, 'V4 8:16 262144 4096 32768 16380 compression on')
            target.storage_device  # '8:16'
            target.compression  # True
            ```
        """
        parts = self.args.split()

        if len(parts) < 6:
            return

        # Parse required positional arguments
        self.vdo_version = parts[0]  # V4
        self.storage_device = parts[1]
        self.storage_size_blocks = int(parts[2])
        self.minimum_io_size = int(parts[3])
        self.block_map_cache_blocks = int(parts[4])
        self.block_map_period = int(parts[5])

        # Parse optional key-value arguments
        i = 6
        while i < len(parts) - 1:
            key = parts[i]
            value = parts[i + 1]

            # dmsetup parameter names used directly as attribute names
            if key == 'ack':
                self.ack = int(value)
            elif key == 'bio':
                self.bio = int(value)
            elif key == 'bioRotationInterval':
                self.bioRotationInterval = int(value)
            elif key == 'cpu':
                self.cpu = int(value)
            elif key == 'hash':
                self.hash = int(value)
            elif key == 'logical':
                self.logical = int(value)
            elif key == 'physical':
                self.physical = int(value)
            elif key == 'maxDiscard':
                self.maxDiscard = int(value)
            elif key == 'deduplication':
                self.deduplication = value == 'on'
            elif key == 'compression':
                self.compression = value == 'on'

            i += 2

    @classmethod
    def from_table_line(cls, table_line: str) -> VdoDevice | None:
        """Create VdoTarget from a dmsetup table line.

        Parses a full table line (including start, size, and type) and
        creates a VdoTarget instance. Useful for reconstructing targets
        from existing devices.

        Args:
            table_line: Full table line from 'dmsetup table' output

        Returns:
            VdoTarget instance or None if parsing fails

        Example:
            ```python
            line = '0 2097152 vdo V4 8:16 262144 4096 32768 16380'
            target = VdoTarget.from_table_line(line)
            target.size  # 2097152
            ```
        """
        parts = table_line.strip().split(None, 3)
        if len(parts) < 4:
            logging.warning(f'Invalid table line: {table_line}')
            return None

        start = int(parts[0])
        size = int(parts[1])
        target_type = parts[2]
        args = parts[3]

        if target_type != 'vdo':
            logging.warning(f'Not a VDO target: {target_type}')
            return None

        target = cls(start=start, size_sectors=size, args=args)
        target.refresh()  # Parse args to populate attributes
        return target

    @staticmethod
    def parse_status(status_line: str) -> dict[str, str | int]:
        """Parse VDO status output into a dictionary.

        Parses the output from 'dmsetup status' for a VDO device.

        Status format from dmsetup:
            <start> <size> vdo <device> <operating mode> <in recovery> <index state>
            <compression state> <physical blocks used> <total physical blocks>

        Args:
            status_line: Status line from 'dmsetup status' output

        Returns:
            Dictionary with parsed status fields:
            - start: Start sector
            - size: Size in sectors
            - device: VDO storage device
            - operating_mode: 'normal', 'recovering', or 'read-only'
            - in_recovery: 'recovering' or '-'
            - index_state: 'closed', 'closing', 'error', 'offline', 'online', 'opening', 'unknown'
            - compression_state: 'offline' or 'online'
            - physical_blocks_used: Number of physical blocks in use
            - total_physical_blocks: Total physical blocks available

        Example:
            ```python
            status = '0 2097152 vdo /dev/loop0 normal - online online 12345 262144'
            parsed = VdoDevice.parse_status(status)
            parsed['operating_mode']  # 'normal'
            parsed['physical_blocks_used']  # 12345
            ```
        """
        parts = status_line.strip().split()
        result: dict[str, str | int] = {}

        # Format: <start> <size> vdo <device> <mode> <recovery> <index> <compression> <used> <total>
        # Minimum 10 parts expected
        if len(parts) < 10:
            logging.warning(f'Invalid VDO status line (expected 10+ parts, got {len(parts)}): {status_line}')
            return result

        try:
            result['start'] = int(parts[0])
            result['size'] = int(parts[1])
        except ValueError:
            logging.warning(f'Failed to parse start/size from status: {status_line}')
            return result

        # parts[2] is 'vdo' (target type)
        result['device'] = parts[3]
        result['operating_mode'] = parts[4]
        result['in_recovery'] = parts[5]
        result['index_state'] = parts[6]
        result['compression_state'] = parts[7]

        try:
            result['physical_blocks_used'] = int(parts[8])
            result['total_physical_blocks'] = int(parts[9])
        except ValueError:
            logging.warning(f'Failed to parse block counts from status: {status_line}')

        return result

    @classmethod
    def create_positional(
        cls,
        device_path: str,
        storage_size_blocks: int,
        logical_size_sectors: int,
        *,
        start: int = 0,
        minimum_io_size: int = 4096,
        block_map_cache_blocks: int = 32768,
        block_map_period: int = 16380,
        **kwargs: int | str | bool,
    ) -> VdoDevice:
        """Create VdoTarget with positional arguments.

        This method allows direct specification of VDO parameters matching
        the dmsetup table format.

        Args:
            device_path: Storage device path (e.g., '/dev/sdb' or '8:16')
            storage_size_blocks: Storage device size in 4096-byte blocks
            logical_size_sectors: Logical device size in 512-byte sectors
            start: Start sector in virtual device (default: 0)
            minimum_io_size: Minimum I/O size in bytes (512 or 4096)
            block_map_cache_blocks: Block map cache in 4096-byte blocks (min: 32768)
            block_map_period: Block map era length (range: 1-16380)
            **kwargs: Optional key-value arguments (ack, bio, cpu, hash,
                     logical, physical, maxDiscard, deduplication, compression)

        Returns:
            VdoTarget instance

        Example:
            ```python
            target = VdoTarget.create_positional(
                '/dev/sdb',
                storage_size_blocks=262144,  # 1 GB
                logical_size_sectors=2097152,  # 1 GB
                compression='on',
            )
            ```
        """
        # Build required arguments
        args_parts = [
            'V4',
            device_path,
            str(storage_size_blocks),
            str(minimum_io_size),
            str(block_map_cache_blocks),
            str(block_map_period),
        ]

        # Process optional arguments
        for key, value in kwargs.items():
            if isinstance(value, bool):
                args_parts.extend([key, 'on' if value else 'off'])
            else:
                args_parts.extend([key, str(value)])

        args = ' '.join(args_parts)
        target = cls(start=start, size_sectors=logical_size_sectors, args=args)

        # Set attributes directly - we know the values
        target.vdo_version = 'V4'
        target.storage_device = device_path
        target.storage_size_blocks = storage_size_blocks
        target.minimum_io_size = minimum_io_size
        target.block_map_cache_blocks = block_map_cache_blocks
        target.block_map_period = block_map_period

        # Set optional parameters from kwargs (dmsetup names used directly)
        for key, value in kwargs.items():
            if isinstance(value, bool):
                setattr(target, key, value)
            elif isinstance(value, str) and value in ('on', 'off'):
                setattr(target, key, value == 'on')
            else:
                setattr(target, key, value)

        return target
