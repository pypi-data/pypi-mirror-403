# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Device Mapper cache target.

dm-cache improves performance of a block device (e.g., a spindle) by
dynamically migrating some of its data to a faster, smaller device (e.g., an SSD).

The target requires three devices:
1. Origin device - the big, slow one (e.g., HDD)
2. Cache device - the small, fast one (e.g., SSD)
3. Metadata device - records which blocks are in cache

Table format:
    cache <metadata dev> <cache dev> <origin dev> <block size>
          <#feature args> [<feature arg>]* <policy> <#policy args> [policy args]*

Cache modes:
    - writeback (default): writes go only to cache, marked dirty
    - writethrough: writes go to both cache and origin
    - passthrough: all I/O goes to origin, useful for coherency

Policies:
    - default: alias for best performing policy
    - smq: stochastic multi-queue (recommended)
    - mq: multi-queue (legacy)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sts.dm.base import DmDevice

if TYPE_CHECKING:
    from sts.blockdevice import BlockDevice


@dataclass
class CacheDevice(DmDevice):
    """Cache target.

    Caches data from a slow origin device on a fast cache device.
    Improves I/O performance by keeping frequently accessed data on SSD.

    Args format: <metadata> <cache> <origin> <block_size> <#features> [features] <policy> <#policy_args> [policy_args]

    Example:
        ```python
        # Writeback cache with default policy
        target = CacheDevice(0, 1000000, '253:0 253:1 253:2 512 1 writeback default 0')
        str(target)
        '0 1000000 cache 253:0 253:1 253:2 512 1 writeback default 0'
        ```
    """

    def __post_init__(self) -> None:
        """Set target type and initialize."""
        self.target_type = 'cache'
        super().__post_init__()

    @classmethod
    def from_block_devices(
        cls,
        metadata_device: BlockDevice,
        cache_device: BlockDevice,
        origin_device: BlockDevice,
        block_size_sectors: int = 512,
        policy: str = 'default',
        policy_args: dict[str, str] | None = None,
        start: int = 0,
        size_sectors: int | None = None,
        *,
        writethrough: bool = False,
        passthrough: bool = False,
        metadata2: bool = False,
        no_discard_passdown: bool = False,
    ) -> CacheDevice:
        """Create CacheDevice from BlockDevices.

        Args:
            metadata_device: Device for storing cache metadata
            cache_device: Fast device for cached data (e.g., SSD)
            origin_device: Slow device with original data (e.g., HDD)
            block_size_sectors: Cache block size in sectors (default: 512 = 256KB)
                Must be between 64 (32KB) and 2097152 (1GB), multiple of 64
            writethrough: Use writethrough mode (writes go to both devices)
            passthrough: Use passthrough mode (all I/O to origin)
            metadata2: Use version 2 metadata format
            no_discard_passdown: Don't pass discards to origin
            policy: Cache policy name (default: 'default')
            policy_args: Policy-specific key/value arguments
            start: Start sector in virtual device (default: 0)
            size_sectors: Size in sectors (default: origin device size)

        Returns:
            CacheDevice instance

        Example:
            ```python
            metadata = BlockDevice('/dev/sdb1')  # Small metadata device
            cache = BlockDevice('/dev/nvme0n1')  # Fast SSD cache
            origin = BlockDevice('/dev/sda')  # Slow HDD origin

            cache_dev = CacheDevice.from_block_devices(
                metadata_device=metadata,
                cache_device=cache,
                origin_device=origin,
                block_size_sectors=1024,  # 512KB blocks
                policy='smq',
            )
            ```
        """
        if size_sectors is None and origin_device.size is not None:
            size_sectors = origin_device.size // origin_device.sector_size

        metadata_id = cls._get_device_identifier(metadata_device)
        cache_id = cls._get_device_identifier(cache_device)
        origin_id = cls._get_device_identifier(origin_device)

        # Build feature list
        features: list[str] = []
        if writethrough:
            features.append('writethrough')
        if passthrough:
            features.append('passthrough')
        if metadata2:
            features.append('metadata2')
        if no_discard_passdown:
            features.append('no_discard_passdown')

        # Build policy args list
        policy_args_list: list[str] = []
        if policy_args:
            for key, value in policy_args.items():
                policy_args_list.extend([key, str(value)])

        # Build args: <metadata> <cache> <origin> <block_size> <#features> [features] <policy> <#policy_args> [args]
        args_parts = [
            metadata_id,
            cache_id,
            origin_id,
            str(block_size_sectors),
            str(len(features)),
        ]
        args_parts.extend(features)
        args_parts.append(policy)
        args_parts.append(str(len(policy_args_list)))
        args_parts.extend(policy_args_list)

        args = ' '.join(args_parts)
        if size_sectors is None:
            raise ValueError('size_sectors must be provided or origin_device.size must be available')
        return cls(start=start, size_sectors=size_sectors, args=args)

    @staticmethod
    def parse_status(status: str) -> dict[str, str | int]:
        """Parse cache device status string.

        Raw status format (from dmsetup status):
            <start> <size> cache <metadata_block_size> <used_meta>/<total_meta>
            <cache_block_size> <used_cache>/<total_cache> <read_hits> <read_misses>
            <write_hits> <write_misses> <demotions> <promotions> <dirty>
            <#features> [features] <#core_args> [core_args] <policy>
            <#policy_args> [policy_args] <mode> <needs_check>

        Example:
            0 524288 cache 8 13/65536 512 0/1024 0 20 0 0 0 0 0 1 writeback 2 migration_threshold 2048 smq 0 rw -

        Args:
            status: Raw status string from dmsetup status

        Returns:
            Dictionary with parsed status fields
        """
        parts = status.split()
        result: dict[str, str | int] = {}

        # Status includes table header: <start> <size> cache <actual status...>
        # Skip first 3 fields to get to actual cache status
        if len(parts) >= 14 and parts[2] == 'cache':
            offset = 3  # Skip: start, size, "cache"
            result['metadata_block_size'] = int(parts[offset])
            if '/' in parts[offset + 1]:
                used, total = parts[offset + 1].split('/')
                result['used_metadata_blocks'] = int(used)
                result['total_metadata_blocks'] = int(total)
            result['cache_block_size'] = int(parts[offset + 2])
            if '/' in parts[offset + 3]:
                used, total = parts[offset + 3].split('/')
                result['used_cache_blocks'] = int(used)
                result['total_cache_blocks'] = int(total)
            result['read_hits'] = int(parts[offset + 4])
            result['read_misses'] = int(parts[offset + 5])
            result['write_hits'] = int(parts[offset + 6])
            result['write_misses'] = int(parts[offset + 7])
            result['demotions'] = int(parts[offset + 8])
            result['promotions'] = int(parts[offset + 9])
            result['dirty'] = int(parts[offset + 10])

        return result
