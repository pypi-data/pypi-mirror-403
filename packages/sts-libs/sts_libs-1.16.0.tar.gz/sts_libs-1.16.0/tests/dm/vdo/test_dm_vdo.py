#  Copyright: Contributors to the sts project
#  GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Tests for VDO (Virtual Data Optimizer) device mapper target.

VDO provides block-level deduplication, compression, and thin provisioning.
These tests create VDO devices on the system using dmsetup create.
Requires: vdo kernel module loaded, vdoformat tool available.
"""

from __future__ import annotations

import logging

import pytest

from sts.dm import DmDevice, VdoDevice
from sts.vdo import VdoFormat


@pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 8192}], indirect=True)
class TestVdoDeviceIntegration:
    """Integration tests for VDO device creation with dmsetup.

    These tests create VDO devices on the system using dmsetup create.
    Requires: vdo kernel module loaded, vdoformat tool available.
    Uses 10G logical on 8G physical to test thin provisioning.
    """

    logical_size_sectors: int = 20971520  # 10 GB = 20971520 sectors of 512 bytes

    def test_vdo_device_creation(self, vdo_dm_device: DmDevice) -> None:
        """Test that VDO device is created with dmsetup."""
        assert vdo_dm_device is not None
        assert vdo_dm_device.dm_name is not None

        # Verify device is listed
        dm_devices = DmDevice.ls()
        assert vdo_dm_device.dm_name in dm_devices
        logging.info(f'DM devices: {dm_devices}')

        assert vdo_dm_device.table is not None
        assert 'vdo' in vdo_dm_device.table
        logging.info(f'Device table: {vdo_dm_device.table}')

    def test_vdo_device_status(self, vdo_dm_device: DmDevice) -> None:
        """Test that VDO device status can be retrieved."""
        status = vdo_dm_device.get_status()
        assert status is not None
        logging.info(f'VDO device status: {status}')

        parsed = VdoDevice.parse_status(status)
        assert 'operating_mode' in parsed
        logging.info(f'Parsed status: {parsed}')

    def test_vdo_device_suspend_resume(self, vdo_dm_device: DmDevice) -> None:
        """Test suspend and resume operations on VDO device."""
        assert vdo_dm_device.suspend(), 'Failed to suspend VDO device'
        logging.info('VDO device suspended')

        info = vdo_dm_device.info()
        assert info is not None
        assert isinstance(info, dict)
        assert info.get('State') == 'SUSPENDED'

        assert vdo_dm_device.resume(), 'Failed to resume VDO device'
        logging.info('VDO device resumed')

        info = vdo_dm_device.info()
        assert info is not None
        assert isinstance(info, dict)
        assert info.get('State') == 'ACTIVE'


def test_vdoformat_version(load_vdo_module: str) -> None:
    """Test vdoformat version retrieval."""
    _ = load_vdo_module

    version = VdoFormat.get_version()
    if version is None:
        pytest.skip('vdoformat not installed')

    logging.info(f'vdoformat version: {version}')
    assert version


# Sparse UDS index requires ~26 GB minimum backing device (26130157568 bytes)
@pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 27648}], indirect=True)
@pytest.mark.parametrize(
    'vdo_formatted_device',
    [{'logical_size': '1G', 'uds_sparse': True}],
    indirect=True,
)
def test_vdoformat_with_uds_sparse(vdo_formatted_device: tuple[str, object]) -> None:
    """Test vdoformat with sparse UDS index.

    Sparse UDS index requires a larger backing device (~26 GB minimum).
    Uses vdo_formatted_device fixture which handles VdoFormat setup.
    """
    device_path, _ = vdo_formatted_device
    logging.info(f'Successfully formatted {device_path} with sparse UDS index')


@pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 8192}], indirect=True)
class TestVdoFormat:
    """Tests for VdoFormat class functionality.

    Uses vdo_formatted_device fixture which handles VdoFormat setup and cleanup.
    """

    @pytest.mark.parametrize(
        'vdo_formatted_device',
        [{'logical_size': '10G'}],
        indirect=True,
    )
    def test_vdoformat_basic(self, vdo_formatted_device: tuple[str, object]) -> None:
        """Test basic vdoformat functionality."""
        device_path, _ = vdo_formatted_device
        logging.info(f'Successfully formatted {device_path}')

    def test_vdoformat_with_slab_bits(self, load_vdo_module: str, loop_devices: list[str]) -> None:
        """Test vdoformat with different slab_bits values.

        Note: We test slab_size_mb property, so we need direct access to VdoFormat instance.
        """
        _ = load_vdo_module
        device_path = loop_devices[0]

        vdo_format = VdoFormat(
            device=device_path,
            logical_size='10G',
            slab_bits=17,
            force=True,
        )

        assert vdo_format.format(), f'Failed to format {device_path} with slab_bits=17'
        assert vdo_format.slab_size_mb == 512
        logging.info(f'Successfully formatted with slab_bits=17 (slab_size={vdo_format.slab_size_mb}MB)')


@pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 8192}], indirect=True)
class TestVdoDeviceCreation:
    """Tests for VdoDevice creation methods."""

    @pytest.mark.parametrize(
        'vdo_dm_device',
        [{'compression': True}],
        indirect=True,
        ids=['compression-on'],
    )
    def test_vdo_create_from_target(self, vdo_dm_device: DmDevice) -> None:
        """Test creating VDO device using VdoDevice.from_block_device() method."""
        assert vdo_dm_device is not None, 'VdoDevice.create() returned None'

        table = vdo_dm_device.table
        assert table is not None
        assert 'vdo' in table
        assert 'compression on' in table
        logging.info(f'Created VDO device via target.create(): {table}')


@pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 8192}], indirect=True)
class TestVdoOptions:
    """Test VDO device creation with various settings.

    Tests VDO device creation with different dm target options,
    similar to how vdo_sanity_test.py tests LVM VDO options.
    Uses vdo_dm_device fixture with indirect parametrization for cleanup.
    """

    @pytest.mark.parametrize(
        'vdo_dm_device',
        [{'minimum_io_size': 512}, {'minimum_io_size': 4096}],
        indirect=True,
        ids=['min-io-512', 'min-io-4096'],
    )
    def test_vdo_minimum_io_size(self, vdo_dm_device: DmDevice) -> None:
        """Test VDO device creation with various minimum_io_size values."""
        assert vdo_dm_device is not None
        assert vdo_dm_device.table is not None
        logging.info(f'Created VDO with minimum_io_size: {vdo_dm_device.table}')

    @pytest.mark.parametrize(
        'vdo_dm_device',
        [{'block_map_cache_size_mb': 128}, {'block_map_cache_size_mb': 4096}],
        indirect=True,
        ids=['bmcache-128', 'bmcache-4096'],
    )
    def test_vdo_block_map_cache_size(self, vdo_dm_device: DmDevice) -> None:
        """Test VDO device creation with various block_map_cache_size_mb values."""
        assert vdo_dm_device is not None
        assert vdo_dm_device.table is not None
        logging.info(f'Created VDO with block_map_cache_size: {vdo_dm_device.table}')

    @pytest.mark.parametrize(
        'vdo_dm_device',
        [{'block_map_period': 1}, {'block_map_period': 8192}, {'block_map_period': 16380}],
        indirect=True,
        ids=['bm-period-1', 'bm-period-8192', 'bm-period-16380'],
    )
    def test_vdo_block_map_period(self, vdo_dm_device: DmDevice) -> None:
        """Test VDO device creation with various block_map_period values."""
        assert vdo_dm_device is not None
        assert vdo_dm_device.table is not None
        logging.info(f'Created VDO with block_map_period: {vdo_dm_device.table}')

    @pytest.mark.parametrize(
        'vdo_dm_device',
        [{'ack': 0}, {'ack': 1}, {'ack': 50}, {'ack': 100}],
        indirect=True,
        ids=['ack-0', 'ack-1', 'ack-50', 'ack-100'],
    )
    def test_vdo_ack(self, vdo_dm_device: DmDevice, request: pytest.FixtureRequest) -> None:
        """Test VDO device creation with various ack values."""
        assert vdo_dm_device is not None
        assert vdo_dm_device.table is not None

        ack = request.node.callspec.params['vdo_dm_device']['ack']
        assert f'ack {ack}' in vdo_dm_device.table
        logging.info(f'Created VDO with ack={ack}: {vdo_dm_device.table}')

    @pytest.mark.parametrize(
        'vdo_dm_device',
        [{'bio': 1}, {'bio': 4}, {'bio': 50}, {'bio': 100}],
        indirect=True,
        ids=['bio-1', 'bio-4', 'bio-50', 'bio-100'],
    )
    def test_vdo_bio(self, vdo_dm_device: DmDevice, request: pytest.FixtureRequest) -> None:
        """Test VDO device creation with various bio values."""
        assert vdo_dm_device is not None
        assert vdo_dm_device.table is not None

        bio = request.node.callspec.params['vdo_dm_device']['bio']
        assert f'bio {bio}' in vdo_dm_device.table
        logging.info(f'Created VDO with bio={bio}: {vdo_dm_device.table}')

    @pytest.mark.parametrize(
        'vdo_dm_device',
        [{'bioRotationInterval': 1}, {'bioRotationInterval': 64}, {'bioRotationInterval': 1024}],
        indirect=True,
        ids=['bio-rot-1', 'bio-rot-64', 'bio-rot-1024'],
    )
    def test_vdo_bio_rotation_interval(self, vdo_dm_device: DmDevice) -> None:
        """Test VDO device creation with various bioRotationInterval values."""
        assert vdo_dm_device is not None
        assert vdo_dm_device.table is not None
        logging.info(f'Created VDO with bioRotationInterval: {vdo_dm_device.table}')

    @pytest.mark.parametrize(
        'vdo_dm_device',
        [{'cpu': 1}, {'cpu': 2}, {'cpu': 50}, {'cpu': 100}],
        indirect=True,
        ids=['cpu-1', 'cpu-2', 'cpu-50', 'cpu-100'],
    )
    def test_vdo_cpu(self, vdo_dm_device: DmDevice, request: pytest.FixtureRequest) -> None:
        """Test VDO device creation with various cpu values."""
        assert vdo_dm_device is not None
        assert vdo_dm_device.table is not None

        cpu = request.node.callspec.params['vdo_dm_device']['cpu']
        assert f'cpu {cpu}' in vdo_dm_device.table
        logging.info(f'Created VDO with cpu={cpu}: {vdo_dm_device.table}')

    @pytest.mark.parametrize(
        'vdo_dm_device',
        [
            # NOTE: dm-vdo constraints:
            # 1. If any of hash/logical/physical is non-zero, ALL THREE must be non-zero
            # 2. physical requires at least 1 slab per thread (default slab=2GB)
            #    With 8GB device, max ~4 slabs, so physical <= 4
            {'hash': 0, 'logical': 0, 'physical': 0},
            {'hash': 1, 'logical': 1, 'physical': 1},
            {'hash': 4, 'logical': 4, 'physical': 2},
        ],
        indirect=True,
        ids=['all-zero', 'all-one', 'hash-4-logical-4-physical-2'],
    )
    def test_vdo_hash_logical_physical(self, vdo_dm_device: DmDevice, request: pytest.FixtureRequest) -> None:
        """Test VDO device creation with hash/logical/physical thread combinations.

        dm-vdo constraints:
        - If any of hash, logical, or physical is non-zero, all three must be non-zero
        - physical requires at least 1 slab per thread (with 8GB device, max ~4 slabs)
        """
        assert vdo_dm_device is not None
        assert vdo_dm_device.table is not None

        params = request.node.callspec.params['vdo_dm_device']
        hash_val = params['hash']
        logical_val = params['logical']
        physical_val = params['physical']

        # Only non-zero values appear in table
        if hash_val != 0:
            assert f'hash {hash_val}' in vdo_dm_device.table
        if logical_val != 0:
            assert f'logical {logical_val}' in vdo_dm_device.table
        if physical_val != 0:
            assert f'physical {physical_val}' in vdo_dm_device.table

        logging.info(
            f'Created VDO with hash={hash_val}, logical={logical_val}, physical={physical_val}: {vdo_dm_device.table}'
        )

    @pytest.mark.parametrize(
        'vdo_dm_device',
        [{'maxDiscard': 1}, {'maxDiscard': 1500}, {'maxDiscard': (2**32 // 4096) - 1}],
        indirect=True,
        ids=['max-discard-1', 'max-discard-1500', 'max-discard-max'],
    )
    def test_vdo_max_discard(self, vdo_dm_device: DmDevice, request: pytest.FixtureRequest) -> None:
        """Test VDO device creation with various maxDiscard values."""
        assert vdo_dm_device is not None
        assert vdo_dm_device.table is not None

        max_discard_val = request.node.callspec.params['vdo_dm_device']['maxDiscard']
        assert f'maxDiscard {max_discard_val}' in vdo_dm_device.table
        logging.info(f'Created VDO with maxDiscard={max_discard_val}: {vdo_dm_device.table}')

    @pytest.mark.parametrize(
        'vdo_dm_device',
        [
            {'compression': True, 'deduplication': True},
            {'compression': True, 'deduplication': False},
            {'compression': False, 'deduplication': True},
            {'compression': False, 'deduplication': False},
        ],
        indirect=True,
        ids=['comp-on-dedup-on', 'comp-on-dedup-off', 'comp-off-dedup-on', 'comp-off-dedup-off'],
    )
    def test_vdo_compression_deduplication(self, vdo_dm_device: DmDevice, request: pytest.FixtureRequest) -> None:
        """Test VDO device creation with compression and deduplication options."""
        assert vdo_dm_device is not None
        assert vdo_dm_device.table is not None

        params = request.node.callspec.params['vdo_dm_device']
        compression = params['compression']
        deduplication = params['deduplication']

        # compression only appears in table if 'on'
        if compression:
            assert 'compression on' in vdo_dm_device.table
        # deduplication only appears in table if 'off'
        if not deduplication:
            assert 'deduplication off' in vdo_dm_device.table

        logging.info(
            f'Created VDO with compression={compression}, deduplication={deduplication}: {vdo_dm_device.table}'
        )

    @pytest.mark.parametrize(
        'vdo_dm_device',
        [
            {'logical': 0, 'hash': 0, 'physical': 0},
            # physical=2 to fit within 8GB device (~4 slabs with 2GB slab size)
            {'logical': 2, 'hash': 2, 'physical': 2},
            {'ack': 2, 'bio': 4, 'cpu': 2},
        ],
        indirect=True,
        ids=['all-zero-threads', 'all-two-threads', 'mixed-threads'],
    )
    def test_vdo_combined_thread_options(self, vdo_dm_device: DmDevice) -> None:
        """Test VDO device creation with combined thread option sets."""
        assert vdo_dm_device is not None
        assert vdo_dm_device.table is not None
        logging.info(f'Created VDO with combined thread options: {vdo_dm_device.table}')

    @pytest.mark.parametrize(
        'vdo_dm_device',
        [
            {
                'minimum_io_size': 4096,
                'block_map_cache_size_mb': 128,
                'block_map_period': 16380,
                'ack': 2,
                'bio': 4,
                'cpu': 2,
                'hash': 1,
                'logical': 1,
                'physical': 1,
                'deduplication': True,
                'compression': True,
            }
        ],
        indirect=True,
        ids=['full-options'],
    )
    def test_vdo_full_options(self, vdo_dm_device: DmDevice) -> None:
        """Test VDO device creation with all thread and feature options."""
        assert vdo_dm_device is not None

        table = vdo_dm_device.table
        assert table is not None
        assert 'vdo' in table
        assert 'compression on' in table
        assert 'ack 2' in table
        assert 'bio 4' in table
        logging.info(f'VDO device with full options: {table}')

        status = vdo_dm_device.get_status()
        assert status is not None
        logging.info(f'Status: {status}')
