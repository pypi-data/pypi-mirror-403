"""Tests for Device Mapper thin provisioning targets.

This module contains pytest tests for the DM thin-pool and thin target
functionality, including pool creation, thin volume provisioning,
snapshots, and I/O operations.

Thin provisioning allows allocating more virtual space than physical
storage, with actual allocation happening on-demand as data is written.
"""

# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging

import pytest

from sts.blockdevice import BlockDevice
from sts.dm import DmDevice, ThinDevice, ThinPoolDevice
from sts.utils.cmdline import run
from sts.utils.files import mkfs, write_data, write_zeroes


@pytest.mark.parametrize('loop_devices', [{'count': 2, 'size_mb': 512}], indirect=True)
class TestThinPoolCreation:
    """Test cases for thin-pool device creation and basic operations."""

    def test_thin_pool_creation_basic(self, thin_pool_dm_device: ThinPoolDevice) -> None:
        """Test basic thin-pool device creation."""
        assert thin_pool_dm_device is not None
        assert thin_pool_dm_device.dm_name is not None

        # Verify device is listed
        dm_devices = DmDevice.ls()
        assert thin_pool_dm_device.dm_name in dm_devices
        logging.info(f'DM devices: {dm_devices}')

        # Verify table contains thin-pool target
        table = thin_pool_dm_device.table
        assert table is not None
        assert 'thin-pool' in table
        logging.info(f'Thin-pool table: {table}')

    def test_thin_pool_info(self, thin_pool_dm_device: ThinPoolDevice) -> None:
        """Test thin-pool device info retrieval."""
        info = thin_pool_dm_device.info()
        assert info is not None
        assert isinstance(info, dict)
        assert 'State' in info
        assert info['State'] == 'ACTIVE'
        logging.info(f'Device info: {info}')

    def test_thin_pool_status(self, thin_pool_dm_device: ThinPoolDevice) -> None:
        """Test thin-pool status retrieval."""
        status = thin_pool_dm_device.get_status()
        assert status is not None
        logging.info(f'Thin-pool status: {status}')

        # Status format: <transaction id> <used meta>/<total meta> <used data>/<total data> ...
        parts = status.split()
        assert len(parts) >= 4, f'Unexpected status format: {status}'

    @pytest.mark.parametrize(
        'thin_pool_dm_device',
        [{'block_size_sectors': 256}],
        indirect=True,
        ids=['block-256'],
    )
    def test_thin_pool_custom_block_size(self, thin_pool_dm_device: ThinPoolDevice) -> None:
        """Test thin-pool with custom block size."""
        table = thin_pool_dm_device.table
        assert table is not None
        assert 'thin-pool' in table
        assert '256' in table  # Block size in table
        logging.info(f'Thin-pool table with block_size=256: {table}')

    def test_thin_pool_suspend_resume(self, thin_pool_dm_device: ThinPoolDevice) -> None:
        """Test suspend and resume operations on thin-pool device."""
        assert thin_pool_dm_device.suspend(), 'Failed to suspend thin-pool'
        logging.info('Thin-pool suspended')

        info = thin_pool_dm_device.info()
        assert info is not None
        assert isinstance(info, dict)
        assert info.get('State') == 'SUSPENDED'

        assert thin_pool_dm_device.resume(), 'Failed to resume thin-pool'
        logging.info('Thin-pool resumed')

        info = thin_pool_dm_device.info()
        assert info is not None
        assert isinstance(info, dict)
        assert info.get('State') == 'ACTIVE'


@pytest.mark.parametrize('loop_devices', [{'count': 2, 'size_mb': 512}], indirect=True)
class TestThinDeviceCreation:
    """Test cases for thin device creation and operations."""

    def test_thin_device_creation_basic(self, thin_dm_device: ThinDevice) -> None:
        """Test basic thin device creation from pool."""
        assert thin_dm_device is not None
        assert thin_dm_device.dm_name is not None

        # Verify device is listed
        dm_devices = DmDevice.ls()
        assert thin_dm_device.dm_name in dm_devices
        logging.info(f'DM devices: {dm_devices}')

        # Verify table contains thin target
        table = thin_dm_device.table
        assert table is not None
        assert 'thin' in table
        # Should NOT contain "thin-pool" (that's the pool, not the thin device)
        assert 'thin-pool' not in table
        logging.info(f'Thin device table: {table}')

    def test_thin_device_info(self, thin_dm_device: ThinDevice) -> None:
        """Test thin device info retrieval."""
        info = thin_dm_device.info()
        assert info is not None
        assert isinstance(info, dict)
        assert 'State' in info
        assert info['State'] == 'ACTIVE'
        logging.info(f'Device info: {info}')

    def test_thin_device_status(self, thin_dm_device: ThinDevice) -> None:
        """Test thin device status retrieval."""
        status = thin_dm_device.get_status()
        assert status is not None
        logging.info(f'Thin device status: {status}')

        # Status format: <nr mapped sectors> <highest mapped sector>
        # Initially may be "0 -" if no data written

    @pytest.mark.parametrize(
        'thin_dm_device',
        [{'size': 4194304}],  # 2 GB
        indirect=True,
        ids=['size-2gb'],
    )
    def test_thin_device_custom_size(self, thin_dm_device: ThinDevice) -> None:
        """Test thin device with custom size."""
        table = thin_dm_device.table
        assert table is not None
        assert 'thin' in table
        assert '4194304' in table  # Size in table
        logging.info(f'Thin device table with size=4194304: {table}')


@pytest.mark.parametrize('loop_devices', [{'count': 2, 'size_mb': 512}], indirect=True)
class TestThinDeviceIO:
    """Test I/O operations on thin devices."""

    def test_thin_device_read_write(self, thin_dm_device: ThinDevice) -> None:
        """Test basic read/write operations on thin device."""
        dm_device_path = thin_dm_device.dm_device_path
        assert dm_device_path is not None

        # Write some data
        assert write_data(dm_device_path, '/dev/urandom', bs='1M', count=10, conv='fsync'), 'Write failed'
        logging.info('Wrote 10 MB to thin device')

        # Read back and verify
        result = run(f'dd if={dm_device_path} of=/dev/null bs=1M count=10 2>&1')
        assert result.succeeded, f'Read failed: {result.stderr}'
        logging.info('Read 10 MB from thin device')

    def test_thin_device_filesystem(self, thin_dm_device: ThinDevice) -> None:
        """Test creating filesystem on thin device."""
        dm_device_path = thin_dm_device.dm_device_path
        assert dm_device_path is not None

        # Create ext4 filesystem
        assert mkfs(dm_device_path, 'ext4', force=True), 'Failed to create filesystem'
        logging.info(f'Created ext4 filesystem on {dm_device_path}')

        # Verify filesystem
        result = run(f'blkid {dm_device_path}')
        assert result.succeeded
        assert 'ext4' in result.stdout
        logging.info(f'Filesystem info: {result.stdout}')

    def test_thin_provisioning_on_demand(self, thin_pool_dm_device: ThinPoolDevice, thin_dm_device: ThinDevice) -> None:
        """Test that space is allocated on-demand (thin provisioning)."""
        pool_path = thin_pool_dm_device.dm_device_path
        thin_path = thin_dm_device.dm_device_path
        assert pool_path is not None
        assert thin_path is not None

        # Get initial pool usage
        initial_status = thin_pool_dm_device.get_status()
        assert initial_status is not None
        logging.info(f'Initial pool status: {initial_status}')

        # Write data to thin device
        assert write_zeroes(thin_path, bs='1M', count=50, conv='fsync'), 'Write failed'

        # Get pool usage after write
        after_status = thin_pool_dm_device.get_status()
        assert after_status is not None
        logging.info(f'After write pool status: {after_status}')

        # Pool should show more data used
        # Status format: <start> <size> thin-pool <txn> <meta used/total> <data used/total> ...
        # Example: 0 1048576 thin-pool 0 4114/131072 0/8192 - rw ...
        initial_parts = initial_status.split()
        after_parts = after_status.split()

        # Find data usage field (format: used/total, after "thin-pool" and transaction ID)
        # It's the 6th field (index 5): start, size, thin-pool, txn, meta, data
        if len(initial_parts) >= 6 and len(after_parts) >= 6:
            # Parse data usage (6th field: used/total)
            initial_data = initial_parts[5].split('/')[0]
            after_data = after_parts[5].split('/')[0]
            logging.info(f'Data usage: {initial_data} -> {after_data}')
            assert int(after_data) > int(initial_data), 'Pool data usage should increase after write'


@pytest.mark.parametrize('loop_devices', [{'count': 2, 'size_mb': 512}], indirect=True)
class TestThinPoolConfig:
    """Test thin pool configuration and validation."""

    def test_thin_pool_string_format(self, loop_devices: list[str]) -> None:
        """Test thin pool string representation."""
        data_device = BlockDevice(loop_devices[0])
        metadata_device = BlockDevice(loop_devices[1])

        pool_dev = ThinPoolDevice.from_block_devices(
            metadata_device=metadata_device,
            data_device=data_device,
            block_size_sectors=128,
            low_water_mark=100,
            features=['skip_block_zeroing'],
        )

        device_str = str(pool_dev)
        logging.info(f'Thin pool string: {device_str!r}')

        # Should contain: start size thin-pool metadata_id data_id block_size lwm features
        assert 'thin-pool' in device_str
        assert '128' in device_str  # block size
        assert '100' in device_str  # low water mark
        assert 'skip_block_zeroing' in device_str


def test_thin_device_requires_size() -> None:
    """Test that thin device creation requires size."""
    # Create a mock pool device
    pool = DmDevice(dm_name='fake-pool', path='/dev/dm-0')

    with pytest.raises(ValueError, match='Size must be specified'):
        ThinDevice.from_thin_pool(pool_device=pool, thin_id=0, size=None)


@pytest.mark.parametrize('loop_devices', [{'count': 2, 'size_mb': 512}], indirect=True)
class TestThinSnapshot:
    """Test thin snapshot operations."""

    def test_create_internal_snapshot(self, thin_pool_dm_device: ThinPoolDevice, thin_dm_device: ThinDevice) -> None:
        """Test creating internal snapshot of thin device using pool methods."""
        thin_path = thin_dm_device.dm_device_path
        assert thin_path is not None

        # Verify thin device has correct parent reference
        assert thin_dm_device.pool is thin_pool_dm_device
        assert thin_dm_device.thin_id == 0

        # Write some data to origin
        assert write_data(thin_path, '/dev/urandom', bs='1M', count=5, conv='fsync')

        # Suspend origin before snapshot (required to avoid corruption)
        assert thin_dm_device.suspend(), 'Failed to suspend thin device'

        # Create snapshot using pool method (ID 1 from origin ID 0)
        snap_name = 'test-snap'
        snap_dev = thin_pool_dm_device.create_snapshot(
            origin_id=0,
            snap_id=1,
            dm_name=snap_name,
        )
        assert snap_dev is not None, 'Failed to create snapshot'
        logging.info('Created internal snapshot using pool.create_snapshot()')

        # Resume origin
        assert thin_dm_device.resume(), 'Failed to resume thin device'

        try:
            # Verify snapshot is active and tracked by pool
            dm_devices = DmDevice.ls()
            assert snap_name in dm_devices
            assert 1 in thin_pool_dm_device.thin_devices

            snap_path = snap_dev.dm_device_path
            assert snap_path is not None

            # Verify snapshot has correct parent reference
            assert snap_dev.pool is thin_pool_dm_device
            assert snap_dev.thin_id == 1

            # Read from snapshot should work
            result = run(f'dd if={snap_path} of=/dev/null bs=1M count=1 2>&1')
            assert result.succeeded, 'Failed to read from snapshot'
            logging.info('Successfully read from snapshot')

        finally:
            # Cleanup snapshot using pool method
            thin_pool_dm_device.delete_thin(1, force=True)


@pytest.mark.parametrize('loop_devices', [{'count': 2, 'size_mb': 512}], indirect=True)
class TestMultipleThinDevices:
    """Test multiple thin devices from same pool."""

    def test_multiple_thin_devices(self, thin_pool_dm_device: ThinPoolDevice) -> None:
        """Test creating multiple thin devices from same pool using pool methods."""
        try:
            # Create 3 thin devices using pool.create_thin()
            for i in range(3):
                dm_name = f'test-thin-multi-{i}'
                thin_dev = thin_pool_dm_device.create_thin(
                    thin_id=i,
                    size=1048576,  # 512 MB each
                    dm_name=dm_name,
                )
                assert thin_dev is not None, f'Failed to create thin {dm_name}'
                logging.info(f'Created thin device {dm_name}')

            # Verify all devices are active and tracked
            dm_list = DmDevice.ls()
            for i in range(3):
                assert f'test-thin-multi-{i}' in dm_list
                assert i in thin_pool_dm_device.thin_devices

            # Verify pool tracks all 3 devices
            assert len(thin_pool_dm_device.thin_devices) == 3

            # Write to each device
            for thin_id, thin_dev in thin_pool_dm_device.thin_devices.items():
                thin_path = thin_dev.dm_device_path
                assert thin_path is not None
                assert write_zeroes(thin_path, bs='1M', count=1, conv='fsync')
                logging.info(f'Wrote to thin device ID {thin_id}')

            logging.info('Successfully created and used 3 thin devices from same pool')

        finally:
            # Cleanup using pool.delete_thin()
            for thin_id in list(thin_pool_dm_device.thin_devices.keys()):
                thin_pool_dm_device.delete_thin(thin_id, force=True)
