"""Tests for Device Mapper flakey target.

This module contains pytest tests for the DM flakey target functionality.
The flakey target is similar to linear but exhibits unreliable behavior
periodically, useful for testing error handling and recovery.
"""

# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging

import pytest

from sts.blockdevice import BlockDevice
from sts.dm import DmDevice, FlakeyDevice
from sts.utils.cmdline import run
from sts.utils.files import mkfs


@pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 512}], indirect=True)
class TestFlakeyDeviceCreation:
    """Test cases for flakey device creation and basic operations."""

    def test_flakey_device_creation_basic(self, flakey_dm_device: FlakeyDevice) -> None:
        """Test basic flakey device creation."""
        assert flakey_dm_device is not None
        assert flakey_dm_device.dm_name is not None

        # Verify device is listed
        dm_devices = DmDevice.ls()
        assert flakey_dm_device.dm_name in dm_devices
        logging.info(f'DM devices: {dm_devices}')

        # Verify table contains flakey target
        table = flakey_dm_device.table
        assert table is not None
        assert 'flakey' in table
        logging.info(f'Flakey device table: {table}')

    def test_flakey_device_info(self, flakey_dm_device: FlakeyDevice) -> None:
        """Test flakey device info retrieval."""
        info = flakey_dm_device.info()
        assert info is not None
        assert isinstance(info, dict)
        assert 'State' in info
        assert info['State'] == 'ACTIVE'
        logging.info(f'Device info: {info}')

    def test_flakey_device_suspend_resume(self, flakey_dm_device: FlakeyDevice) -> None:
        """Test suspend and resume operations on flakey device."""
        assert flakey_dm_device.suspend(), 'Failed to suspend flakey device'
        logging.info('Flakey device suspended')

        info = flakey_dm_device.info()
        assert info is not None
        assert isinstance(info, dict)
        assert info.get('State') == 'SUSPENDED'

        assert flakey_dm_device.resume(), 'Failed to resume flakey device'
        logging.info('Flakey device resumed')

        info = flakey_dm_device.info()
        assert info is not None
        assert isinstance(info, dict)
        assert info.get('State') == 'ACTIVE'


@pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 512}], indirect=True)
class TestFlakeyDeviceIO:
    """Test I/O operations on flakey devices during up interval."""

    def test_flakey_read_write_during_up(self, flakey_dm_device: FlakeyDevice) -> None:
        """Test read/write during up interval (reliable period)."""
        dm_device_path = flakey_dm_device.dm_device_path
        assert dm_device_path is not None

        # Write data
        result = run(f'dd if=/dev/urandom of={dm_device_path} bs=1M count=10 conv=fsync 2>&1')
        assert result.succeeded, f'Write failed: {result.stderr}'
        logging.info('Wrote 10 MB to flakey device')

        # Read back
        result = run(f'dd if={dm_device_path} of=/dev/null bs=1M count=10 2>&1')
        assert result.succeeded, f'Read failed: {result.stderr}'
        logging.info('Read 10 MB from flakey device')

    def test_flakey_filesystem(self, flakey_dm_device: FlakeyDevice) -> None:
        """Test creating filesystem on flakey device."""
        dm_device_path = flakey_dm_device.dm_device_path
        assert dm_device_path is not None

        # Create ext4 filesystem
        assert mkfs(dm_device_path, 'ext4', force=True), 'Failed to create filesystem'
        logging.info(f'Created ext4 filesystem on {dm_device_path}')

        # Verify filesystem
        result = run(f'blkid {dm_device_path}')
        assert result.succeeded
        assert 'ext4' in result.stdout
        logging.info(f'Filesystem info: {result.stdout}')

    def test_flakey_blockdev_operations(self, flakey_dm_device: FlakeyDevice) -> None:
        """Test blockdev operations on flakey device."""
        dm_device_path = flakey_dm_device.dm_device_path
        assert dm_device_path is not None

        # Get device size
        result = run(f'blockdev --getsize64 {dm_device_path}')
        assert result.succeeded
        size_bytes = int(result.stdout.strip())
        assert size_bytes > 0
        logging.info(f'Device size: {size_bytes} bytes')


@pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 512}], indirect=True)
class TestFlakeyDeviceConfig:
    """Test FlakeyDevice configuration and string format."""

    def test_flakey_string_format_basic(self, loop_devices: list[str]) -> None:
        """Test basic flakey device string representation."""
        device = BlockDevice(loop_devices[0])
        flakey_dev = FlakeyDevice.from_block_device(
            device=device,
            up_interval=60,
            down_interval=10,
        )

        device_str = str(flakey_dev)
        logging.info(f'Flakey device string: {device_str!r}')

        assert 'flakey' in device_str
        assert '60' in device_str  # up interval
        assert '10' in device_str  # down interval

    def test_flakey_string_format_with_drop_writes(self, loop_devices: list[str]) -> None:
        """Test flakey device string with drop_writes feature."""
        device = BlockDevice(loop_devices[0])
        flakey_dev = FlakeyDevice.from_block_device(
            device=device,
            up_interval=30,
            down_interval=5,
            drop_writes=True,
        )

        device_str = str(flakey_dev)
        logging.info(f'Flakey device string with drop_writes: {device_str!r}')

        assert 'flakey' in device_str
        assert 'drop_writes' in device_str
        assert '1' in device_str  # num_features

    def test_flakey_string_format_with_error_writes(self, loop_devices: list[str]) -> None:
        """Test flakey device string with error_writes feature."""
        device = BlockDevice(loop_devices[0])
        flakey_dev = FlakeyDevice.from_block_device(
            device=device,
            up_interval=30,
            down_interval=5,
            error_writes=True,
        )

        device_str = str(flakey_dev)
        logging.info(f'Flakey device string with error_writes: {device_str!r}')

        assert 'flakey' in device_str
        assert 'error_writes' in device_str

    def test_flakey_string_format_with_corrupt_bio(self, loop_devices: list[str]) -> None:
        """Test flakey device string with corrupt_bio_byte feature."""
        device = BlockDevice(loop_devices[0])
        flakey_dev = FlakeyDevice.from_block_device(
            device=device,
            up_interval=30,
            down_interval=5,
            corrupt_bio_byte=(32, 'r', 1, 0),
        )

        device_str = str(flakey_dev)
        logging.info(f'Flakey device string with corrupt_bio_byte: {device_str!r}')

        assert 'flakey' in device_str
        assert 'corrupt_bio_byte' in device_str
        assert '32' in device_str  # nth_byte
        assert 'r' in device_str  # direction

    def test_flakey_string_format_multiple_features(self, loop_devices: list[str]) -> None:
        """Test flakey device string with multiple features."""
        device = BlockDevice(loop_devices[0])
        flakey_dev = FlakeyDevice.from_block_device(
            device=device,
            up_interval=30,
            down_interval=5,
            drop_writes=True,
            corrupt_bio_byte=(224, 'w', 0, 32),
        )

        device_str = str(flakey_dev)
        logging.info(f'Flakey device string with multiple features: {device_str!r}')

        assert 'flakey' in device_str
        assert 'drop_writes' in device_str
        assert 'corrupt_bio_byte' in device_str
        assert '2' in device_str  # num_features (drop_writes + corrupt_bio_byte)


@pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 512}], indirect=True)
class TestFlakeyDeviceFeatures:
    """Test flakey device with different feature configurations."""

    @pytest.mark.parametrize(
        'flakey_dm_device',
        [{'up_interval': 60, 'down_interval': 0, 'drop_writes': True}],
        indirect=True,
        ids=['drop-writes'],
    )
    def test_flakey_with_drop_writes_feature(self, flakey_dm_device: FlakeyDevice) -> None:
        """Test flakey device configured with drop_writes feature."""
        table = flakey_dm_device.table
        assert table is not None
        assert 'flakey' in table
        assert 'drop_writes' in table
        logging.info(f'Flakey table with drop_writes: {table}')

    @pytest.mark.parametrize(
        'flakey_dm_device',
        [{'up_interval': 60, 'down_interval': 0, 'error_writes': True}],
        indirect=True,
        ids=['error-writes'],
    )
    def test_flakey_with_error_writes_feature(self, flakey_dm_device: FlakeyDevice) -> None:
        """Test flakey device configured with error_writes feature."""
        table = flakey_dm_device.table
        assert table is not None
        assert 'flakey' in table
        assert 'error_writes' in table
        logging.info(f'Flakey table with error_writes: {table}')

    @pytest.mark.parametrize(
        'flakey_dm_device',
        [{'up_interval': 30, 'down_interval': 10}],
        indirect=True,
        ids=['30-up-10-down'],
    )
    def test_flakey_custom_intervals(self, flakey_dm_device: FlakeyDevice) -> None:
        """Test flakey device with custom up/down intervals."""
        table = flakey_dm_device.table
        assert table is not None
        assert 'flakey' in table
        assert '30' in table  # up interval
        assert '10' in table  # down interval
        logging.info(f'Flakey table with custom intervals: {table}')
