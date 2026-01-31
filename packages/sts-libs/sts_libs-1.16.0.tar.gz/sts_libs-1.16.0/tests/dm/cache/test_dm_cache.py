"""Tests for Device Mapper cache target.

This module contains pytest tests for the DM cache target functionality.
dm-cache improves performance by caching data from a slow origin device
(e.g., HDD) on a faster cache device (e.g., SSD).
"""

# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging

import pytest

from sts.blockdevice import BlockDevice
from sts.dm import CacheDevice, DmDevice
from sts.utils.cmdline import run
from sts.utils.files import mkfs, write_data, write_zeroes


@pytest.mark.parametrize('loop_devices', [{'count': 3, 'size_mb': 256}], indirect=True)
class TestCacheDeviceCreation:
    """Test cases for cache device creation and basic operations."""

    def test_cache_device_creation_basic(self, cache_dm_device: CacheDevice) -> None:
        """Test basic cache device creation."""
        assert cache_dm_device is not None
        assert cache_dm_device.dm_name is not None

        # Verify device is listed
        dm_devices = DmDevice.ls()
        assert cache_dm_device.dm_name in dm_devices
        logging.info(f'DM devices: {dm_devices}')

        # Verify table contains cache target
        table = cache_dm_device.table
        assert table is not None
        assert 'cache' in table
        logging.info(f'Cache device table: {table}')

    def test_cache_device_info(self, cache_dm_device: CacheDevice) -> None:
        """Test cache device info retrieval."""
        info = cache_dm_device.info()
        assert info is not None
        assert isinstance(info, dict)
        assert 'State' in info
        assert info['State'] == 'ACTIVE'
        logging.info(f'Device info: {info}')

    def test_cache_device_status(self, cache_dm_device: CacheDevice) -> None:
        """Test cache device status retrieval."""
        status = cache_dm_device.get_status()
        assert status is not None
        logging.info(f'Cache status: {status}')

        # Parse status
        parsed = CacheDevice.parse_status(status)
        assert 'cache_block_size' in parsed
        logging.info(f'Parsed status: {parsed}')

    def test_cache_device_suspend_resume(self, cache_dm_device: CacheDevice) -> None:
        """Test suspend and resume operations on cache device."""
        assert cache_dm_device.suspend(), 'Failed to suspend cache device'
        logging.info('Cache device suspended')

        info = cache_dm_device.info()
        assert info is not None
        assert isinstance(info, dict)
        assert info.get('State') == 'SUSPENDED'

        assert cache_dm_device.resume(), 'Failed to resume cache device'
        logging.info('Cache device resumed')

        info = cache_dm_device.info()
        assert info is not None
        assert isinstance(info, dict)
        assert info.get('State') == 'ACTIVE'


@pytest.mark.parametrize('loop_devices', [{'count': 3, 'size_mb': 256}], indirect=True)
class TestCacheDeviceIO:
    """Test I/O operations on cache devices."""

    def test_cache_read_write(self, cache_dm_device: CacheDevice) -> None:
        """Test read/write operations on cache device."""
        dm_device_path = cache_dm_device.dm_device_path
        assert dm_device_path is not None

        # Write data
        assert write_data(dm_device_path, '/dev/urandom', bs='1M', count=10, conv='fsync'), 'Write failed'
        logging.info('Wrote 10 MB to cache device')

        # Read back
        result = run(f'dd if={dm_device_path} of=/dev/null bs=1M count=10 2>&1')
        assert result.succeeded, f'Read failed: {result.stderr}'
        logging.info('Read 10 MB from cache device')

    def test_cache_filesystem(self, cache_dm_device: CacheDevice) -> None:
        """Test creating filesystem on cache device."""
        dm_device_path = cache_dm_device.dm_device_path
        assert dm_device_path is not None

        # Create ext4 filesystem
        assert mkfs(dm_device_path, 'ext4', force=True), 'Failed to create filesystem'
        logging.info(f'Created ext4 filesystem on {dm_device_path}')

        # Verify filesystem
        result = run(f'blkid {dm_device_path}')
        assert result.succeeded
        assert 'ext4' in result.stdout
        logging.info(f'Filesystem info: {result.stdout}')

    def test_cache_statistics(self, cache_dm_device: CacheDevice) -> None:
        """Test cache statistics after I/O."""
        dm_device_path = cache_dm_device.dm_device_path
        assert dm_device_path is not None

        # Get initial stats
        initial_status = cache_dm_device.get_status()
        assert initial_status is not None
        initial_parsed = CacheDevice.parse_status(initial_status)
        logging.info(f'Initial stats: {initial_parsed}')

        # Perform some I/O
        assert write_zeroes(dm_device_path, bs='1M', count=5, conv='fsync')

        # Read back (should hit cache after first miss)
        result = run(f'dd if={dm_device_path} of=/dev/null bs=1M count=5 2>&1')
        assert result.succeeded

        # Get stats after I/O
        after_status = cache_dm_device.get_status()
        assert after_status is not None
        after_parsed = CacheDevice.parse_status(after_status)
        logging.info(f'After I/O stats: {after_parsed}')

        # Should have some hits or misses recorded
        read_hits = int(after_parsed.get('read_hits', 0))
        read_misses = int(after_parsed.get('read_misses', 0))
        write_hits = int(after_parsed.get('write_hits', 0))
        write_misses = int(after_parsed.get('write_misses', 0))
        total_reads = read_hits + read_misses
        total_writes = write_hits + write_misses
        assert total_reads > 0 or total_writes > 0, 'Should have recorded some I/O'


@pytest.mark.parametrize('loop_devices', [{'count': 3, 'size_mb': 256}], indirect=True)
class TestCacheDeviceModes:
    """Test cache device with different modes."""

    @pytest.mark.parametrize(
        'cache_dm_device',
        [{'writethrough': True}],
        indirect=True,
        ids=['writethrough'],
    )
    def test_cache_writethrough_mode(self, cache_dm_device: CacheDevice) -> None:
        """Test cache device in writethrough mode."""
        table = cache_dm_device.table
        assert table is not None
        assert 'cache' in table
        assert 'writethrough' in table
        logging.info(f'Writethrough cache table: {table}')

        # Writethrough should work - writes go to both cache and origin
        dm_device_path = cache_dm_device.dm_device_path
        assert dm_device_path is not None
        assert write_zeroes(dm_device_path, bs='1M', count=1, conv='fsync')

    @pytest.mark.parametrize(
        'cache_dm_device',
        [{'block_size_sectors': 1024}],
        indirect=True,
        ids=['block-1024'],
    )
    def test_cache_custom_block_size(self, cache_dm_device: CacheDevice) -> None:
        """Test cache device with custom block size."""
        table = cache_dm_device.table
        assert table is not None
        assert 'cache' in table
        assert '1024' in table  # Block size in table
        logging.info(f'Cache with block_size=1024: {table}')

    @pytest.mark.parametrize(
        'cache_dm_device',
        [{'policy': 'smq'}],
        indirect=True,
        ids=['policy-smq'],
    )
    def test_cache_smq_policy(self, cache_dm_device: CacheDevice) -> None:
        """Test cache device with SMQ policy."""
        table = cache_dm_device.table
        assert table is not None
        assert 'cache' in table
        assert 'smq' in table
        logging.info(f'Cache with SMQ policy: {table}')


@pytest.mark.parametrize('loop_devices', [{'count': 3, 'size_mb': 256}], indirect=True)
class TestCacheDeviceConfig:
    """Test CacheDevice configuration and string format."""

    def test_cache_string_format_basic(self, loop_devices: list[str]) -> None:
        """Test basic cache device string representation."""
        metadata = BlockDevice(loop_devices[2])
        cache = BlockDevice(loop_devices[1])
        origin = BlockDevice(loop_devices[0])

        cache_dev = CacheDevice.from_block_devices(
            metadata_device=metadata,
            cache_device=cache,
            origin_device=origin,
            block_size_sectors=512,
            policy='default',
        )

        device_str = str(cache_dev)
        logging.info(f'Cache device string: {device_str!r}')

        assert 'cache' in device_str
        assert '512' in device_str  # block size
        assert 'default' in device_str  # policy

    def test_cache_string_format_with_writethrough(self, loop_devices: list[str]) -> None:
        """Test cache device string with writethrough mode."""
        metadata = BlockDevice(loop_devices[2])
        cache = BlockDevice(loop_devices[1])
        origin = BlockDevice(loop_devices[0])

        cache_dev = CacheDevice.from_block_devices(
            metadata_device=metadata,
            cache_device=cache,
            origin_device=origin,
            writethrough=True,
        )

        device_str = str(cache_dev)
        logging.info(f'Cache device string with writethrough: {device_str!r}')

        assert 'cache' in device_str
        assert 'writethrough' in device_str

    def test_cache_string_format_with_metadata2(self, loop_devices: list[str]) -> None:
        """Test cache device string with metadata2 feature."""
        metadata = BlockDevice(loop_devices[2])
        cache = BlockDevice(loop_devices[1])
        origin = BlockDevice(loop_devices[0])

        cache_dev = CacheDevice.from_block_devices(
            metadata_device=metadata,
            cache_device=cache,
            origin_device=origin,
            metadata2=True,
        )

        device_str = str(cache_dev)
        logging.info(f'Cache device string with metadata2: {device_str!r}')

        assert 'cache' in device_str
        assert 'metadata2' in device_str


@pytest.mark.parametrize('loop_devices', [{'count': 3, 'size_mb': 256}], indirect=True)
class TestCacheDeviceRemoval:
    """Test cache device removal scenarios."""

    def test_device_removal(self, loop_devices: list[str]) -> None:
        """Test creating and removing a cache device manually."""
        origin = BlockDevice(loop_devices[0])
        cache = BlockDevice(loop_devices[1])
        metadata = BlockDevice(loop_devices[2])
        dm_name = 'test-cache-removal'

        # Zero metadata
        write_zeroes(loop_devices[2], bs=4096, count=1, conv='fsync')

        # Create cache device
        cache_dev = CacheDevice.from_block_devices(
            metadata_device=metadata,
            cache_device=cache,
            origin_device=origin,
        )
        assert cache_dev.create(dm_name), 'Failed to create cache device'

        # Verify device exists
        dm_devices = DmDevice.ls()
        assert dm_name in dm_devices

        # Remove device
        assert cache_dev.remove(), 'Failed to remove cache device'

        # Verify device is gone
        dm_devices = DmDevice.ls()
        assert dm_name not in dm_devices
        logging.info(f'Successfully created and removed cache device {dm_name}')

    def test_force_removal(self, loop_devices: list[str]) -> None:
        """Test force removal of cache device."""
        origin = BlockDevice(loop_devices[0])
        cache = BlockDevice(loop_devices[1])
        metadata = BlockDevice(loop_devices[2])
        dm_name = 'test-cache-force-remove'

        # Zero metadata
        write_zeroes(loop_devices[2], bs=4096, count=1, conv='fsync')

        # Create cache device
        cache_dev = CacheDevice.from_block_devices(
            metadata_device=metadata,
            cache_device=cache,
            origin_device=origin,
        )
        assert cache_dev.create(dm_name), 'Failed to create cache device'

        try:
            # Force remove
            assert cache_dev.remove(force=True), 'Failed to force remove cache device'

            # Verify device is gone
            dm_devices = DmDevice.ls()
            assert dm_name not in dm_devices
        finally:
            # Cleanup in case of failure
            existing = DmDevice.get_by_name(dm_name)
            if existing:
                existing.remove(force=True)


@pytest.mark.parametrize('loop_devices', [{'count': 3, 'size_mb': 256}], indirect=True)
class TestCacheStatusParsing:
    """Test cache status parsing."""

    def test_parse_status(self, cache_dm_device: CacheDevice) -> None:
        """Test parsing cache status."""
        status = cache_dm_device.get_status()
        assert status is not None

        parsed = CacheDevice.parse_status(status)

        # Check expected fields
        assert 'cache_block_size' in parsed
        assert 'read_hits' in parsed
        assert 'read_misses' in parsed
        assert 'write_hits' in parsed
        assert 'write_misses' in parsed
        assert 'dirty' in parsed

        logging.info(f'Parsed cache status: {parsed}')
