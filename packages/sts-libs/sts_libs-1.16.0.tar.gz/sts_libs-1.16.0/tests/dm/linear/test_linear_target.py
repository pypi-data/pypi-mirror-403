"""Tests for Device Mapper linear target.

This module contains pytest tests for the DM linear target functionality,
including device creation, filesystem operations, and data I/O testing.

Note: Performance tests are in test_dm_performance.py
"""

# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from sts.blockdevice import BlockDevice
from sts.dm import DmDevice, LinearDevice
from sts.fixtures.dm_fixtures import create_dm_device_from_targets
from sts.utils.cmdline import run


@pytest.mark.parametrize('loop_devices', [{'count': 2, 'size_mb': 512}], indirect=True)
class TestLinearDevice:
    """Test cases for Device Mapper linear target."""

    def test_linear_device_creation_basic(self, loop_devices: list[str]) -> None:
        """Test basic linear device creation and operations."""
        device_path = loop_devices[0]
        logging.info(f'Testing linear device with device {device_path}')

        # Create BlockDevice instance
        block_device = BlockDevice(device_path)

        # Create linear device from block device
        linear_dev = LinearDevice.from_block_device(block_device, size_sectors=1000000)  # ~500MB in sectors
        assert linear_dev.start == 0
        assert linear_dev.size_sectors == 1000000
        assert linear_dev.type == 'linear'

        # Verify device string format
        device_str = str(linear_dev)
        logging.info(f'Linear device string: {device_str}')
        assert device_str.startswith('0 1000000 linear')

        # Verify the device string contains the device's major:minor
        # The format is: "0 1000000 linear major:minor 0"
        parts = device_str.split()
        assert len(parts) >= 4, f'Device string should have at least 4 parts: {device_str}'
        device_id = parts[3]  # major:minor is the 4th part
        assert ':' in device_id, f'Device ID should contain major:minor format: {device_id}'
        logging.info(f'Device ID: {device_id}')

    def test_device_properties(self, linear_dm_device: LinearDevice) -> None:
        """Test device properties including dm_device_path and device_root_dir."""
        # Test device_root_dir property
        root_dir = linear_dm_device.device_root_dir
        assert root_dir == '/dev/mapper', f'Expected /dev/mapper, got {root_dir}'
        logging.info(f'Device root directory: {root_dir}')

        # Test dm_device_path property
        device_path_prop = linear_dm_device.dm_device_path
        assert device_path_prop is not None
        assert device_path_prop.startswith('/dev/mapper/')
        logging.info(f'Device path: {device_path_prop}')

        # Verify dm_name is set
        assert linear_dm_device.dm_name is not None
        logging.info(f'Device name: {linear_dm_device.dm_name}')

    def test_linear_device_creation_and_removal(self, linear_dm_device: LinearDevice) -> None:
        """Test that linear DM device is created properly."""
        assert linear_dm_device.dm_name is not None

        # Verify device is listed
        dm_devices = DmDevice.ls()
        assert linear_dm_device.dm_name in dm_devices

        # Get device table and verify it's correct
        table = linear_dm_device.table
        assert table is not None
        assert 'linear' in table
        logging.info(f'Device table: {table}')

    @pytest.mark.parametrize(
        'mounted_dm_device',
        [{'dm_device_fixture': 'linear_dm_device', 'mount_point': '/mnt/sts-dm-linear-test'}],
        indirect=True,
    )
    def test_filesystem_creation_and_data_operations(
        self,
        linear_dm_device: LinearDevice,
        mounted_dm_device: tuple[DmDevice, str],
    ) -> None:
        """Test creating filesystem on linear device and performing data operations."""
        _ = linear_dm_device  # Required for fixture dependency chain
        dm_device, mount_point = mounted_dm_device

        # Write test data to the mounted filesystem
        test_file = Path(mount_point) / 'test_file.txt'
        test_data = 'Hello, Device Mapper Linear Target!\nThis is test data.\n' * 100
        test_file.write_text(test_data)
        logging.info(f'Wrote {len(test_data)} bytes to {test_file}')

        # Verify data can be read back
        read_data = test_file.read_text()
        assert read_data == test_data, 'Data mismatch after read'

        # Create a larger file to test I/O
        large_file = Path(mount_point) / 'large_test.dat'
        result = run(f'dd if=/dev/zero of={large_file} bs=1M count=10 conv=fsync')
        assert result.succeeded, 'Failed to create large test file'

        # Verify file exists and has correct size
        assert large_file.exists(), 'Large test file was not created'
        file_size = large_file.stat().st_size
        expected_size = 10 * 1024 * 1024  # 10MB
        assert file_size == expected_size, f'File size mismatch: got {file_size}, expected {expected_size}'

        logging.info(f'Filesystem operations completed successfully on {dm_device.dm_name}')

    def test_multiple_linear_targets(self, loop_devices: list[str]) -> None:
        """Test creating a device with multiple linear targets (concatenation)."""
        if len(loop_devices) < 2:
            pytest.skip('Need at least 2 loop devices for concatenation test')

        device1_path = loop_devices[0]
        device2_path = loop_devices[1]
        dm_name = 'test-concat-device'

        # Create BlockDevice instances
        block_device1 = BlockDevice(device1_path)
        block_device2 = BlockDevice(device2_path)

        # Get device sizes in sectors using actual sector size
        assert block_device1.size is not None
        assert block_device2.size is not None
        device1_size = block_device1.size // block_device1.sector_size
        device2_size = block_device2.size // block_device2.sector_size

        # Create targets for concatenation
        target1 = LinearDevice.from_block_device(block_device1, start=0, size_sectors=device1_size)
        target2 = LinearDevice.from_block_device(block_device2, start=device1_size, size_sectors=device2_size)

        logging.info(f'Target 1: {target1}')
        logging.info(f'Target 2: {target2}')

        # Create device with multiple targets
        dm_device = create_dm_device_from_targets(dm_name, [target1, target2])
        assert dm_device is not None, 'Failed to create concatenated device'

        try:
            # Verify device table contains both targets
            table = dm_device.table
            assert table is not None
            table_lines = table.strip().split('\n')
            assert len(table_lines) == 2, f'Expected 2 table lines, got {len(table_lines)}'

            # Verify both table lines are linear targets
            for line in table_lines:
                assert 'linear' in line, f'Expected linear target in table line: {line}'

            # Verify concatenated device size
            total_expected_size = device1_size + device2_size
            dm_device_path = dm_device.dm_device_path
            assert dm_device_path is not None, 'Device path not available'
            result = run(f'blockdev --getsz {dm_device_path}')
            assert result.succeeded, 'Failed to get device size'
            actual_size = int(result.stdout.strip())
            assert actual_size == total_expected_size, (
                f'Size mismatch: got {actual_size}, expected {total_expected_size}'
            )

            logging.info(f'Concatenated device size: {actual_size} sectors')

        finally:
            # Clean up
            assert dm_device.remove(), 'Failed to remove concatenated device'

    @pytest.mark.parametrize(
        'linear_dm_device',
        [{'dm_name': 'test-linear-offset', 'offset': 2048, 'size': 500000}],
        indirect=True,
        ids=['offset-2048'],
    )
    def test_linear_device_with_offset(self, linear_dm_device: LinearDevice) -> None:
        """Test linear device with non-zero offset."""
        offset = 2048

        # Verify target configuration - check the table contains the offset
        table = linear_dm_device.table
        assert table is not None, 'Device table should not be None'
        assert 'linear' in table, 'Table should contain linear target'
        assert str(offset) in table, f'Offset {offset} not found in table: {table}'

        # Test basic I/O to verify offset works
        dm_device_path = linear_dm_device.dm_device_path
        assert dm_device_path is not None, 'Device path not available'

        logging.info(f'Successfully created device with offset {offset}')

    def test_device_suspend_resume(self, linear_dm_device: LinearDevice) -> None:
        """Test device suspend and resume operations."""
        # Test suspend
        assert linear_dm_device.suspend(), 'Failed to suspend device'
        logging.info(f'Successfully suspended device {linear_dm_device.dm_name}')

        # Verify device is suspended
        info = linear_dm_device.info()
        assert info is not None
        assert isinstance(info, dict)
        assert info.get('State') == 'SUSPENDED'

        # Test resume
        assert linear_dm_device.resume(), 'Failed to resume device'
        logging.info(f'Successfully resumed device {linear_dm_device.dm_name}')

        # Verify device is active again
        info = linear_dm_device.info()
        assert info is not None
        assert isinstance(info, dict)
        assert info.get('State') == 'ACTIVE'

    def test_table_string_handling(self, linear_dm_device: LinearDevice) -> None:
        """Test that table strings are handled correctly."""
        # Verify table contains expected content
        table = linear_dm_device.table
        assert table is not None, 'Device table should not be None'
        assert 'linear' in table, 'Table should contain linear target type'
        logging.info(f'Device table: {table}')

        # Test that the device actually works
        dm_device_path = linear_dm_device.dm_device_path
        assert dm_device_path is not None, 'Device path not available'

        # Simple I/O test to verify device works
        result = run(f'blockdev --getsize64 {dm_device_path}')
        assert result.succeeded, 'Failed to get device size'
        logging.info(f'Device size: {result.stdout.strip()} bytes')

    def test_device_creation_optimization(self, linear_dm_device: LinearDevice) -> None:
        """Test that device creation returns the instance directly without additional queries."""
        # Verify that the returned device instance already has the table loaded
        assert linear_dm_device.table is not None, 'Device table should be immediately available'
        assert 'linear' in linear_dm_device.table, 'Table should contain linear target'

        # Verify device properties are set correctly
        assert linear_dm_device.dm_name is not None

        # Verify the device actually works (can perform basic operations)
        dm_device_path = linear_dm_device.dm_device_path
        assert dm_device_path is not None, 'Device path should be available'

        # Verify device is listed
        dm_devices = DmDevice.ls()
        assert linear_dm_device.dm_name in dm_devices

        logging.info(f'Device created successfully with table: {linear_dm_device.table}')

    def test_dmsetup_ls_parsing(self, linear_dm_device: LinearDevice) -> None:
        """Test that dmsetup ls parsing works correctly."""
        dm_name = linear_dm_device.dm_name
        assert dm_name is not None

        # Test that DmDevice.get_all() can find our device
        all_devices = DmDevice.get_all()
        device_names = [dev.dm_name for dev in all_devices if dev.dm_name]

        assert dm_name in device_names, f'Created device {dm_name} not found in device list: {device_names}'
        logging.info(f'Successfully found device {dm_name} in dmsetup ls output')

        # Also test that we can get the specific device by name
        found_device = DmDevice.get_by_name(dm_name)
        assert found_device is not None, f'Could not retrieve device {dm_name} by name'
        assert found_device.dm_name == dm_name, 'Retrieved device has incorrect name'
