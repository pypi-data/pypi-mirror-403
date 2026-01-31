"""Tests for Device Mapper error target.

This module contains pytest tests for the DM error target functionality.
The error target returns I/O errors for all read and write operations,
useful for testing error handling in applications and filesystems.
"""

# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging

import pytest

from sts.dm import DmDevice, ErrorDevice
from sts.utils.cmdline import run


class TestErrorDeviceCreation:
    """Test cases for error device creation and basic operations."""

    def test_error_device_creation_basic(self, error_dm_device: ErrorDevice) -> None:
        """Test basic error device creation."""
        assert error_dm_device is not None
        assert error_dm_device.dm_name is not None

        # Verify device is listed
        dm_devices = DmDevice.ls()
        assert error_dm_device.dm_name in dm_devices
        logging.info(f'DM devices: {dm_devices}')

        # Verify table contains error target
        table = error_dm_device.table
        assert table is not None
        assert 'error' in table
        logging.info(f'Device table: {table}')

    def test_error_device_string_format(self) -> None:
        """Test error device string representation."""
        error_dev = ErrorDevice.create_config(start=0, size=1000000)

        device_str = str(error_dev)
        logging.info(f'Error device string: {device_str!r}')

        # Format should be: "0 1000000 error" (with possible trailing space from args)
        assert device_str.strip() == '0 1000000 error'

    @pytest.mark.parametrize(
        'error_dm_device',
        [{'size': 500000}],
        indirect=True,
        ids=['500k-sectors'],
    )
    def test_error_device_custom_size(self, error_dm_device: ErrorDevice) -> None:
        """Test error device with custom size."""
        assert error_dm_device is not None

        table = error_dm_device.table
        assert table is not None
        assert 'error' in table
        assert '500000' in table
        logging.info(f'Device table with custom size: {table}')

    def test_error_device_info(self, error_dm_device: ErrorDevice) -> None:
        """Test error device info retrieval."""
        info = error_dm_device.info()
        assert info is not None
        assert isinstance(info, dict)
        assert 'State' in info
        assert info['State'] == 'ACTIVE'
        logging.info(f'Device info: {info}')

    def test_error_device_suspend_resume(self, error_dm_device: ErrorDevice) -> None:
        """Test suspend and resume operations on error device."""
        assert error_dm_device.suspend(), 'Failed to suspend error device'
        logging.info('Error device suspended')

        info = error_dm_device.info()
        assert info is not None
        assert isinstance(info, dict)
        assert info.get('State') == 'SUSPENDED'

        assert error_dm_device.resume(), 'Failed to resume error device'
        logging.info('Error device resumed')

        info = error_dm_device.info()
        assert info is not None
        assert isinstance(info, dict)
        assert info.get('State') == 'ACTIVE'


class TestErrorDeviceIO:
    """Test I/O operations on error devices (expecting failures)."""

    def test_read_returns_error(self, error_dm_device: ErrorDevice) -> None:
        """Test that reading from error device returns I/O error."""
        dm_device_path = error_dm_device.dm_device_path
        assert dm_device_path is not None

        # Reading should fail with I/O error
        result = run(f'dd if={dm_device_path} of=/dev/null bs=512 count=1 2>&1')
        assert result.failed, 'Read from error device should fail'
        logging.info(f'Expected read failure: {result.stderr or result.stdout}')

    def test_write_returns_error(self, error_dm_device: ErrorDevice) -> None:
        """Test that writing to error device returns I/O error."""
        dm_device_path = error_dm_device.dm_device_path
        assert dm_device_path is not None

        # Writing should fail with I/O error
        result = run(f'dd if=/dev/zero of={dm_device_path} bs=512 count=1 conv=fsync 2>&1')
        assert result.failed, 'Write to error device should fail'
        logging.info(f'Expected write failure: {result.stderr or result.stdout}')

    def test_filesystem_creation_fails(self, error_dm_device: ErrorDevice) -> None:
        """Test that creating filesystem on error device fails."""
        dm_device_path = error_dm_device.dm_device_path
        assert dm_device_path is not None

        # mkfs should fail due to I/O errors
        result = run(f'mkfs.ext4 -F {dm_device_path} 2>&1')
        assert result.failed, 'Filesystem creation on error device should fail'
        logging.info(f'Expected mkfs failure: {result.stderr or result.stdout}')


class TestErrorDeviceConfig:
    """Test ErrorDevice configuration and validation."""

    def test_create_config_requires_size(self) -> None:
        """Test that create_config requires size parameter."""
        with pytest.raises(ValueError, match='Size must be specified'):
            ErrorDevice.create_config(size=None)

    def test_create_config_default_start(self) -> None:
        """Test create_config with default start value."""
        error_dev = ErrorDevice.create_config(size=1000000)
        assert error_dev.start == 0
        assert error_dev.size_sectors == 1000000
        assert error_dev.args == ''

    def test_target_type_is_error(self) -> None:
        """Test that target_type is correctly set to 'error'."""
        error_dev = ErrorDevice.create_config(size=1000000)
        assert error_dev.target_type == 'error'
        assert error_dev.type == 'error'
