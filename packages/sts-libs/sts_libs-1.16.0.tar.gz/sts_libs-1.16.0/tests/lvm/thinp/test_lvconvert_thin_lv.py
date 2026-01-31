# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for lvconvert operations to convert LV to thin LV.

This module contains pytest tests for converting regular logical volumes to thin LVs
while preserving data and creating origin snapshots.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from sts.lvm import LogicalVolume, ThinPool
from sts.utils.cmdline import run
from sts.utils.files import mkfs, mount, umount, write_data


@pytest.mark.parametrize('loop_devices', [{'count': 4, 'size_mb': 256}], indirect=True)
class TestLvconvertThinLv:
    """Test cases for converting LV to thin LV operations."""

    @pytest.mark.parametrize(
        'temp_mount_fixture',
        [{'mount_point': '/mnt/thin'}],
        indirect=True,
    )
    @pytest.mark.parametrize(
        ('regular_lv_fixture', 'thinpool_fixture', 'fs_type'),
        [
            ({'extents': '75', 'lv_name': 'thin'}, {'size': '150M', 'pool_name': 'pool'}, 'ext4'),
            ({'extents': '75', 'lv_name': 'thin'}, {'size': '150M', 'pool_name': 'pool'}, 'xfs'),
        ],
        indirect=['regular_lv_fixture', 'thinpool_fixture'],
        ids=['ext4', 'xfs'],
    )
    def test_convert_lv_to_thin(
        self,
        regular_lv_fixture: LogicalVolume,
        thinpool_fixture: ThinPool,
        temp_mount_fixture: dict[str, Any],
        fs_type: str,
    ) -> None:
        """Test converting regular LV to thin LV with data preservation.

        Tests the full workflow of converting a regular LV with data to a thin LV,
        including verification of data integrity, origin snapshot creation, and
        proper handling of data writes to the thin pool.

        Args:
            regular_lv_fixture: Regular LV fixture
            thinpool_fixture: Thin pool fixture
            temp_mount_fixture: Temporary mount fixture
            fs_type: Filesystem type to use
        """
        thin_lv = regular_lv_fixture
        pool = thinpool_fixture
        vg_name = pool.vg
        mount_point = temp_mount_fixture['mount_point']
        temp_files = temp_mount_fixture['temp_files']
        file_path = mount_point / '5m'

        # Track temp files for cleanup
        temp_files.extend(['/tmp/pre_md5', '/tmp/post_md5', '/tmp/origin_md5'])

        # Create filesystem on the regular LV
        thin_device = Path(f'/dev/mapper/{vg_name}-thin')
        assert mkfs(thin_device, fs_type, force='')
        assert mount(thin_device, mount_point)

        # Create test data and checksum
        assert write_data(source='/dev/urandom', target=file_path, bs='1M', count=5)
        run(f'md5sum {file_path!s} > /tmp/pre_md5')

        # Convert LV to thin LV with origin
        success, origin_lv = thin_lv.convert_originname(
            thinpool=f'{vg_name}/pool',
            originname='thin_origin',
        )

        assert success
        assert origin_lv

        run('sync')

        # Verify data integrity
        run(f'md5sum {file_path!s} > /tmp/post_md5')
        result = run('diff /tmp/pre_md5 /tmp/post_md5')
        assert result.succeeded, 'Data corruption detected after conversion'

        # Verify thin LV properties
        assert thin_lv.report
        assert thin_lv.report.lv_size == '300.00m'
        assert thin_lv.report.pool_lv == 'pool'
        assert thin_lv.report.lv_attr == 'Vwi-aotz--'
        assert thin_lv.report.origin == 'thin_origin'

        # Verify readonly origin LV was created
        assert origin_lv.report
        assert origin_lv.report.lv_attr == 'ori-------'

        # Test that new data goes to the pool
        pre_thin_dp = float(thin_lv.report.data_percent or '0') if thin_lv.report else 0.0
        pre_pool_dp = float(pool.report.data_percent or '0') if pool.report else 0.0

        assert write_data(source='/dev/urandom', target=mount_point / '10m', bs='1M', count=10)

        thin_lv.refresh_report()
        pool.refresh_report()
        post_thin_dp = float(thin_lv.report.data_percent or '0') if thin_lv.report else 0.0
        post_pool_dp = float(pool.report.data_percent or '0') if pool.report else 0.0

        assert post_thin_dp > pre_thin_dp, 'Thin LV data percentage should increase'
        assert post_pool_dp > pre_pool_dp, 'Pool data percentage should increase'

        # Test deleting the thin LV and checking origin integrity
        file_path.unlink()
        umount(mount_point)

        # Remove thin LV and activate origin
        assert thin_lv.remove()
        assert origin_lv
        assert origin_lv.activate()

        # For XFS, we need writable device for journal
        if fs_type == 'xfs':
            assert origin_lv.change(f'{vg_name}/thin_origin', permission='rw')

        # Mount origin and verify original data
        thin_origin_device = Path(f'/dev/mapper/{vg_name}-thin_origin')
        assert mount(thin_origin_device, mount_point)

        # Re-create file path for origin check
        file_path = mount_point / '5m'
        run(f'md5sum {file_path!s} > /tmp/origin_md5')
        result = run('diff /tmp/pre_md5 /tmp/origin_md5')
        assert result.succeeded, 'Original data not preserved in origin'

        # Cleanup will be handled by fixtures

    @pytest.mark.parametrize(
        'temp_mount_fixture',
        [{'mount_point': '/mnt/thin_test'}],
        indirect=True,
    )
    @pytest.mark.parametrize(
        ('regular_lv_fixture', 'thinpool_fixture'),
        [
            ({'extents': '75', 'lv_name': 'thin'}, {'size': '150M', 'pool_name': 'pool'}),
        ],
        indirect=True,
    )
    @pytest.mark.parametrize('data_size_mb', [5, 10], ids=['5MB-write', '10MB-write'])
    def test_thin_lv_data_allocation(
        self,
        regular_lv_fixture: LogicalVolume,
        thinpool_fixture: ThinPool,
        temp_mount_fixture: dict[str, Any],
        data_size_mb: int,
    ) -> None:
        """Test that data written to thin LV correctly allocates space in the pool.

        Verifies that writes to a converted thin LV properly consume space from
        the thin pool and that data percentages increase as expected.

        Args:
            regular_lv_fixture: Regular LV fixture
            thinpool_fixture: Thin pool fixture
            temp_mount_fixture: Temporary mount fixture
            data_size_mb: Amount of data to write in MB
        """
        thin_lv = regular_lv_fixture
        pool = thinpool_fixture
        vg_name = pool.vg
        mount_point = temp_mount_fixture['mount_point']

        # Create filesystem on the regular LV
        thin_device = Path(f'/dev/mapper/{vg_name}-thin')
        assert mkfs(thin_device, 'ext4', force='')
        assert mount(thin_device, mount_point)

        # Convert to thin LV
        success, origin_lv = thin_lv.convert_originname(
            thinpool=f'{vg_name}/pool',
            originname='thin_origin',
        )
        assert success
        assert origin_lv

        # Get initial data percentages
        pre_thin_dp = float(thin_lv.report.data_percent or '0') if thin_lv.report else 0.0
        pre_pool_dp = float(pool.report.data_percent or '0') if pool.report else 0.0

        # Write data
        test_file = mount_point / f'{data_size_mb}m'
        assert write_data(source='/dev/urandom', target=test_file, bs='1M', count=data_size_mb)
        run('sync')

        # Get post-write data percentages
        thin_lv.refresh_report()
        pool.refresh_report()
        post_thin_dp = float(thin_lv.report.data_percent or '0') if thin_lv.report else 0.0
        post_pool_dp = float(pool.report.data_percent or '0') if pool.report else 0.0

        # Verify data allocation - should always increase with writes
        assert post_thin_dp > pre_thin_dp, f'Thin LV usage should increase after {data_size_mb}MB write'
        assert post_pool_dp > pre_pool_dp, f'Pool usage should increase after {data_size_mb}MB write'

        # Cleanup - unmount before fixture cleanup
        umount(mount_point)

    @pytest.mark.parametrize(
        ('regular_lv_fixture', 'thinpool_fixture'),
        [
            ({'size': '50M', 'lv_name': 'data_lv'}, {'size': '100M', 'pool_name': 'mypool'}),
        ],
        indirect=True,
    )
    def test_convert_with_custom_origin_name(
        self,
        regular_lv_fixture: LogicalVolume,
        thinpool_fixture: ThinPool,
    ) -> None:
        """Test converting LV to thin with custom origin name.

        Verifies that the --originname option correctly creates an origin
        snapshot with the specified custom name.

        Args:
            regular_lv_fixture: Regular LV fixture
            thinpool_fixture: Thin pool fixture
        """
        lv = regular_lv_fixture
        pool = thinpool_fixture
        vg_name = pool.vg

        # Convert with custom origin name
        custom_origin = 'my_custom_origin'
        success, origin_lv = lv.convert_originname(
            thinpool=f'{vg_name}/mypool',
            originname=custom_origin,
        )

        assert success
        assert origin_lv
        assert origin_lv.name == custom_origin

        # Verify the origin exists and has correct properties
        assert origin_lv.report
        assert origin_lv.report.lv_attr == 'ori-------'

        # Verify the converted LV points to the origin
        assert lv.report
        assert lv.report.origin == custom_origin
        assert lv.report.pool_lv == 'mypool'

        # Cleanup handled by fixtures

    @pytest.mark.parametrize(
        'origin_suffix',
        ['snap1', 'backup', 'orig'],
        ids=['snap1', 'backup', 'orig'],
    )
    def test_multiple_conversions_different_origins(self, setup_loopdev_vg: str, origin_suffix: str) -> None:
        """Test converting multiple LVs with different origin names.

        Ensures that multiple LVs can be converted to thin LVs in the same pool,
        each with their own unique origin snapshot names.

        Note: This test creates pool and LV inline because each iteration needs
        unique names based on origin_suffix, which is not easily parameterizable
        through fixtures.

        Args:
            setup_loopdev_vg: Volume group fixture
            origin_suffix: Suffix for unique naming
        """
        vg_name = setup_loopdev_vg

        # Create thin pool (unique per test iteration)
        pool_name = f'tpool_{origin_suffix}'
        pool = ThinPool.create_thin_pool(pool_name, vg_name, size='200M')

        try:
            # Create and convert LV with distinct naming
            lv_name = f'data_{origin_suffix}'
            origin_name = f'origin_{origin_suffix}'

            lv = LogicalVolume(name=lv_name, vg=vg_name)
            assert lv.create(size='30M')

            success, origin_lv = lv.convert_originname(
                thinpool=f'{vg_name}/{pool_name}',
                originname=origin_name,
            )

            assert success, f'Failed to convert {lv_name} to thin LV with origin {origin_name}'
            assert origin_lv
            assert origin_lv.name == origin_name

            # Verify conversion
            assert lv.report
            assert lv.report.origin == origin_name
            assert lv.report.pool_lv == pool_name
        finally:
            # Cleanup
            pool.remove_with_thin_volumes()
