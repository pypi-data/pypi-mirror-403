"""Tests for Device Mapper zero target.

This module contains pytest tests for the DM zero target functionality.
The zero target returns blocks of zeros when read and discards all writes,
useful for creating sparse devices or testing.
"""

# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
import os
from pathlib import Path

import pytest

from sts.blockdevice import BlockDevice
from sts.dm import DmDevice, ZeroDevice


class TestZeroDeviceCreation:
    """Test cases for zero device creation and basic operations."""

    def test_zero_device_creation_basic(self, zero_dm_device: ZeroDevice) -> None:
        """Test basic zero device creation."""
        assert zero_dm_device is not None
        assert zero_dm_device.dm_name is not None

        # Verify device is listed
        dm_devices = DmDevice.ls()
        assert zero_dm_device.dm_name in dm_devices
        logging.info(f'DM devices: {dm_devices}')

        # Verify table contains zero target
        table = zero_dm_device.table
        assert table is not None
        assert 'zero' in table
        logging.info(f'Device table: {table}')

    def test_zero_device_string_format(self) -> None:
        """Test zero device string representation."""
        zero_dev = ZeroDevice.create_config(start=0, size=1000000)

        device_str = str(zero_dev)
        logging.info(f'Zero device string: {device_str!r}')

        # Format should be: "0 1000000 zero" (with possible trailing space from args)
        assert device_str.strip() == '0 1000000 zero'

    @pytest.mark.parametrize(
        'zero_dm_device',
        [{'size': 500000}],
        indirect=True,
        ids=['500k-sectors'],
    )
    def test_zero_device_custom_size(self, zero_dm_device: ZeroDevice) -> None:
        """Test zero device with custom size."""
        assert zero_dm_device is not None

        table = zero_dm_device.table
        assert table is not None
        assert 'zero' in table
        assert '500000' in table
        logging.info(f'Device table with custom size: {table}')

    def test_zero_device_info(self, zero_dm_device: ZeroDevice) -> None:
        """Test zero device info retrieval."""
        info = zero_dm_device.info()
        assert info is not None
        assert isinstance(info, dict)
        assert 'State' in info
        assert info['State'] == 'ACTIVE'
        logging.info(f'Device info: {info}')

    def test_zero_device_suspend_resume(self, zero_dm_device: ZeroDevice) -> None:
        """Test suspend and resume operations on zero device."""
        assert zero_dm_device.suspend(), 'Failed to suspend zero device'
        logging.info('Zero device suspended')

        info = zero_dm_device.info()
        assert info is not None
        assert isinstance(info, dict)
        assert info.get('State') == 'SUSPENDED'

        assert zero_dm_device.resume(), 'Failed to resume zero device'
        logging.info('Zero device resumed')

        info = zero_dm_device.info()
        assert info is not None
        assert isinstance(info, dict)
        assert info.get('State') == 'ACTIVE'


class TestZeroDeviceIO:
    """Test I/O operations on zero devices."""

    def test_read_returns_zeros(self, zero_dm_device: ZeroDevice) -> None:
        """Test that reading from zero device returns all zeros."""
        dm_device_path = zero_dm_device.dm_device_path
        assert dm_device_path is not None

        # Read 1KB from the device using Python
        block_size = 1024
        with Path(dm_device_path).open('rb') as f:
            data = f.read(block_size)

        assert len(data) == block_size, f'Expected {block_size} bytes, got {len(data)}'
        assert data == b'\x00' * block_size, 'Read data is not all zeros'
        logging.info(f'Read {block_size} bytes, verified all zeros')

    def test_read_large_block_zeros(self, zero_dm_device: ZeroDevice) -> None:
        """Test reading larger block returns all zeros."""
        dm_device_path = zero_dm_device.dm_device_path
        assert dm_device_path is not None

        # Read 1MB and verify it's all zeros using Python
        block_size = 1024 * 1024  # 1MB
        with Path(dm_device_path).open('rb') as f:
            data = f.read(block_size)

        assert len(data) == block_size, f'Expected {block_size} bytes, got {len(data)}'
        assert data == b'\x00' * block_size, 'Read data is not all zeros'
        logging.info('1MB read block verified as all zeros')

    def test_write_succeeds_but_discarded(self, zero_dm_device: ZeroDevice) -> None:
        """Test that writes succeed but data is discarded."""
        dm_device_path = zero_dm_device.dm_device_path
        assert dm_device_path is not None

        # Write random data using Python
        write_size = 512 * 10  # 10 sectors
        random_data = os.urandom(write_size)
        with Path(dm_device_path).open('wb') as f:
            bytes_written = f.write(random_data)
            f.flush()
            os.fsync(f.fileno())
        assert bytes_written == write_size, f'Expected to write {write_size} bytes, wrote {bytes_written}'
        logging.info(f'Wrote {bytes_written} bytes of random data')

        # Read back - should still be zeros (writes are discarded)
        with Path(dm_device_path).open('rb') as f:
            data = f.read(512)
        assert data == b'\x00' * 512, 'Read data is not all zeros after write'
        logging.info('Verified write was discarded - read still returns zeros')

    def test_blockdev_operations(self, zero_dm_device: ZeroDevice) -> None:
        """Test blockdev operations on zero device."""
        dm_device_path = zero_dm_device.dm_device_path
        assert dm_device_path is not None

        # Get device properties using BlockDevice
        block_dev = BlockDevice(path=dm_device_path)

        # Get device size
        size_bytes = block_dev.size
        assert size_bytes is not None
        assert size_bytes > 0
        logging.info(f'Device size: {size_bytes} bytes')

        # Get sector size
        sector_size = block_dev.sector_size
        assert sector_size in [512, 4096]
        logging.info(f'Sector size: {sector_size} bytes')


class TestZeroDeviceConfig:
    """Test ZeroDevice configuration and validation."""

    def test_create_config_requires_size(self) -> None:
        """Test that create_config requires size parameter."""
        with pytest.raises(ValueError, match='Size must be specified'):
            ZeroDevice.create_config(size=None)

    def test_create_config_default_start(self) -> None:
        """Test create_config with default start value."""
        zero_dev = ZeroDevice.create_config(size=1000000)
        assert zero_dev.start == 0
        assert zero_dev.size_sectors == 1000000
        assert zero_dev.args == ''

    def test_target_type_is_zero(self) -> None:
        """Test that target_type is correctly set to 'zero'."""
        zero_dev = ZeroDevice.create_config(size=1000000)
        assert zero_dev.target_type == 'zero'
        assert zero_dev.type == 'zero'


class TestZeroDeviceUseCases:
    """Test common use cases for zero devices."""

    def test_zero_as_sparse_backing(self, zero_dm_device: ZeroDevice) -> None:
        """Test zero device can be used as sparse backing store placeholder."""
        dm_device_path = zero_dm_device.dm_device_path
        assert dm_device_path is not None

        # Verify we can read from the device (sparse read)
        # Just read first sector to verify accessibility
        with Path(dm_device_path).open('rb') as f:
            data = f.read(512)

        assert len(data) == 512, f'Expected 512 bytes, got {len(data)}'
        logging.info('Zero device works as sparse backing store')

    def test_zero_device_size_matches_config(self, zero_dm_device: ZeroDevice) -> None:
        """Test that actual device size matches configuration."""
        dm_device_path = zero_dm_device.dm_device_path
        assert dm_device_path is not None

        # Get actual size using BlockDevice
        block_dev = BlockDevice(path=dm_device_path)
        assert block_dev.size is not None

        # Calculate sectors from size (size is in bytes, sector is typically 512)
        actual_sectors = block_dev.size // block_dev.sector_size

        # Should match configured size
        assert actual_sectors == zero_dm_device.size_sectors
        logging.info(f'Device size matches: {actual_sectors} sectors')
