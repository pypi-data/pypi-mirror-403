# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for reducing thin provisioning logical volumes.

This module contains pytest tests for reducing thin pools and thin volumes,
including filesystem reduction and snapshot handling.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sts.lvm import ThinPool
from sts.utils.cmdline import run
from sts.utils.files import Directory, mkfs, mount, umount


@pytest.mark.parametrize('loop_devices', [{'count': 4, 'size_mb': 256}], indirect=True)
class TestLvreduceThinp:
    """Test cases for reducing thin provisioning volumes."""

    @pytest.mark.parametrize(
        'stripes',
        [None, '2'],
        ids=['single-stripe', 'two-stripes'],
    )
    def test_reduce_pool_not_allowed(self, setup_loopdev_vg: str, stripes: str | None) -> None:
        """Test that reducing thin pools is not allowed.

        Args:
            setup_loopdev_vg: Volume group fixture
            stripes: Number of stripes (None for single stripe)
        """
        vg_name = setup_loopdev_vg

        pool: ThinPool | None = None
        pool_name = f'pool_{"single" if stripes is None else "striped"}'

        try:
            # Create thin pool with thin volume
            if stripes:
                pool = ThinPool.create_thin_pool(pool_name, vg_name, size='100M', stripes=stripes)
            else:
                pool = ThinPool.create_thin_pool(pool_name, vg_name, size='100M')

            # Create thin volume in pool
            pool.create_thin_volume('lv1', virtualsize='100M')

            # Try to reduce pool - should fail
            reduce_success = pool.reduce(extents='-1', force='')
            assert not reduce_success, 'Reducing thin pool should fail'
        finally:
            if pool:
                pool.remove_with_thin_volumes()

    @pytest.mark.parametrize(
        ('thinpool_fixture', 'reduce_spec', 'expected_size'),
        [
            ({'size': '100M', 'pool_name': 'pool'}, '-2', '92.00m'),
            ({'size': '100M', 'pool_name': 'pool'}, '-8m', '92.00m'),
        ],
        indirect=['thinpool_fixture'],
        ids=['by-extents', 'by-size'],
    )
    def test_reduce_thin_volume_relative(
        self, thinpool_fixture: ThinPool, reduce_spec: str, expected_size: str
    ) -> None:
        """Test reducing thin volumes by relative amounts.

        Args:
            thinpool_fixture: Thin pool fixture
            reduce_spec: Reduction specification (extents or size)
            expected_size: Expected size after reduction
        """
        pool = thinpool_fixture

        # Create thin LV inline to get direct reference
        thin_lv = pool.create_thin_volume('lv1', virtualsize='100M')

        # Reduce by specified amount
        if reduce_spec.startswith('-') and reduce_spec[1:].isdigit():
            # Extent-based reduction
            assert thin_lv.reduce(extents=reduce_spec, force='')
        else:
            # Size-based reduction
            assert thin_lv.reduce(size=reduce_spec, force='')

        assert thin_lv.report is not None
        assert thin_lv.report.lv_size == expected_size

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        ('thinpool_fixture', 'target_size', 'expected_size'),
        [
            ({'size': '100M', 'pool_name': 'pool'}, '72m', '72.00m'),
            ({'size': '100M', 'pool_name': 'pool'}, '64m', '64.00m'),
            ({'size': '100M', 'pool_name': 'pool'}, '48m', '48.00m'),
        ],
        indirect=['thinpool_fixture'],
        ids=['to-72m', 'to-64m', 'to-48m'],
    )
    def test_reduce_thin_volume_to_absolute_size(
        self, thinpool_fixture: ThinPool, target_size: str, expected_size: str
    ) -> None:
        """Test reducing thin volumes to absolute sizes.

        Args:
            thinpool_fixture: Thin pool fixture
            target_size: Target size for reduction
            expected_size: Expected size after reduction
        """
        pool = thinpool_fixture

        # Create thin LV inline to get direct reference
        thin_lv = pool.create_thin_volume('lv1', virtualsize='100M')

        # Reduce to target size
        assert thin_lv.reduce(size=target_size, force='')
        assert thin_lv.report is not None
        assert thin_lv.report.lv_size == expected_size

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'stripes',
        [None, '2'],
        ids=['single-stripe', 'two-stripes'],
    )
    def test_reduce_thin_volume_multiple_operations(self, setup_loopdev_vg: str, stripes: str | None) -> None:
        """Test multiple reduction operations on thin volumes.

        Args:
            setup_loopdev_vg: Volume group fixture
            stripes: Number of stripes (None for single stripe)
        """
        vg_name = setup_loopdev_vg

        pool: ThinPool | None = None
        pool_name = f'pool_{"single" if stripes is None else "striped"}'

        try:
            # Create thin pool with thin volume
            if stripes:
                pool = ThinPool.create_thin_pool(pool_name, vg_name, size='100M', stripes=stripes)
            else:
                pool = ThinPool.create_thin_pool(pool_name, vg_name, size='100M')

            thin_lv = pool.create_thin_volume('lv1', virtualsize='100M')

            # Reduce by extents
            assert thin_lv.reduce(extents='-2', force='')
            assert thin_lv.report is not None
            assert thin_lv.report.lv_size == '92.00m'

            # Reduce by size (default unit is m)
            assert thin_lv.reduce(size='-8m', force='')
            assert thin_lv.report is not None
            assert thin_lv.report.lv_size == '84.00m'

            # Reduce by size with explicit unit
            assert thin_lv.reduce(size='-8m', force='')
            assert thin_lv.report is not None
            assert thin_lv.report.lv_size == '76.00m'

            # Set specific size
            assert thin_lv.reduce(size='72m', force='')
            assert thin_lv.report is not None
            assert thin_lv.report.lv_size == '72.00m'

            # Set another specific size
            assert thin_lv.reduce(size='64m', force='')
            assert thin_lv.report is not None
            assert thin_lv.report.lv_size == '64.00m'
        finally:
            if pool:
                pool.remove_with_thin_volumes()

    @pytest.mark.parametrize(
        ('thinpool_fixture', 'test_option'),
        [
            ({'size': '100M', 'pool_name': 'pool'}, '--test'),
            ({'size': '100M', 'pool_name': 'pool'}, '-t'),
        ],
        indirect=['thinpool_fixture'],
        ids=['long-form', 'short-form'],
    )
    def test_reduce_thin_volume_test_mode(self, thinpool_fixture: ThinPool, test_option: str) -> None:
        """Test reducing thin volumes in test mode (dry-run).

        Args:
            thinpool_fixture: Thin pool fixture
            test_option: Test mode option (--test or -t)
        """
        pool = thinpool_fixture

        # Create thin LV inline to get direct reference
        thin_lv = pool.create_thin_volume('lv1', virtualsize='100M')

        # First reduce to a smaller size
        assert thin_lv.reduce(size='64m', force='')
        assert thin_lv.report is not None
        original_size = thin_lv.report.lv_size
        assert original_size == '64.00m'

        # Test dry-run with extent reduction (should not change size)
        assert thin_lv.reduce(test_option, extents='-1', force='')
        thin_lv.refresh_report()  # Need manual refresh for test mode
        assert thin_lv.report is not None
        assert thin_lv.report.lv_size == original_size

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        ('thinpool_fixture', 'percent_spec'),
        [
            ({'size': '100M', 'pool_name': 'pool'}, '-1%FREE'),
            ({'size': '100M', 'pool_name': 'pool'}, '-1%PVS'),
            ({'size': '100M', 'pool_name': 'pool'}, '-1%VG'),
        ],
        indirect=['thinpool_fixture'],
        ids=['percent-FREE', 'percent-PVS', 'percent-VG'],
    )
    def test_reduce_thin_volume_test_mode_with_percentages(self, thinpool_fixture: ThinPool, percent_spec: str) -> None:
        """Test reducing thin volumes in test mode with percentage specifications.

        Args:
            thinpool_fixture: Thin pool fixture
            percent_spec: Percentage specification for reduction
        """
        pool = thinpool_fixture

        # Create thin LV inline to get direct reference
        thin_lv = pool.create_thin_volume('lv1', virtualsize='100M')

        # First reduce to a smaller size
        assert thin_lv.reduce(size='64m', force='')
        assert thin_lv.report is not None
        original_size = thin_lv.report.lv_size
        assert original_size == '64.00m'

        # Test dry-run with percentage (should not change size)
        assert thin_lv.reduce('--test', extents=percent_spec, force='')
        thin_lv.refresh_report()  # Need manual refresh for test mode
        assert thin_lv.report is not None
        assert thin_lv.report.lv_size == original_size

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'fs_type',
        ['ext4'],  # XFS doesn't support reduction
        ids=['ext4-filesystem'],
    )
    def test_reduce_thin_volume_with_filesystem(self, setup_loopdev_vg: str, fs_type: str) -> None:
        """Test reducing thin volumes with filesystems.

        Args:
            setup_loopdev_vg: Volume group fixture
            fs_type: Filesystem type to test
        """
        vg_name = setup_loopdev_vg
        lv_mnt = Path('/mnt/lv_reduce_test')
        lv_dir = Directory(lv_mnt, create=True)

        pool: ThinPool | None = None

        try:
            # Create thin pool with thin volume
            pool = ThinPool.create_thin_pool('pool', vg_name, size='200M')
            thin_lv = pool.create_thin_volume('lv1', virtualsize='100M')

            lv_device = Path(f'/dev/mapper/{vg_name}-lv1')

            # Create filesystem
            assert mkfs(lv_device, fs_type, force='')
            assert mount(lv_device, lv_mnt)

            # Add some data
            run(f'dd if=/dev/urandom of={lv_mnt!s}/testfile bs=1M count=5')

            # Reduce with filesystem
            assert thin_lv.reduce('-f', '--resizefs', extents='-2')
            assert thin_lv.report is not None
            assert thin_lv.report.lv_size == '92.00m'

            # Verify filesystem is still accessible
            result = run(f'df -h {lv_mnt!s}')
            assert result.succeeded

        finally:
            # Cleanup
            umount(lv_mnt)
            lv_dir.remove_dir()
            if pool:
                pool.remove_with_thin_volumes()

    def test_reduce_thin_volume_with_snapshot(self, setup_loopdev_vg: str) -> None:
        """Test reducing thin volumes with snapshots.

        Args:
            setup_loopdev_vg: Volume group fixture
        """
        vg_name = setup_loopdev_vg
        lv_mnt = Path('/mnt/lv')
        snap_mnt = Path('/mnt/snap')
        lv_dir = Directory(lv_mnt, create=True)
        snap_dir = Directory(snap_mnt, create=True)

        pool: ThinPool | None = None
        snap1 = None

        try:
            # Create thin pool with thin volume
            pool = ThinPool.create_thin_pool('pool', vg_name, size='200M')
            thin_lv = pool.create_thin_volume('lv1', virtualsize='100M')

            # Create filesystem (use ext4 since xfs doesn't support reduction)
            fs_type = 'ext4'
            lv_device = Path(f'/dev/mapper/{vg_name}-lv1')

            assert mkfs(lv_device, fs_type, force='')
            assert mount(lv_device, lv_mnt)

            # Add some data
            run(f'dd if=/dev/urandom of={lv_mnt!s}/lv1 bs=1M count=5')

            # Reduce with filesystem
            assert thin_lv.reduce('-f', '--resizefs', extents='-2')
            assert thin_lv.report is not None
            assert thin_lv.report.lv_size == '92.00m'

            # Create snapshot
            snap1 = thin_lv.create_snapshot('snap1', '-K')
            assert snap1 is not None

            snap_device = Path(f'/dev/mapper/{vg_name}-snap1')

            assert mkfs(snap_device, fs_type, force='')
            assert mount(snap_device, snap_mnt)

            # Add data to snapshot
            run(f'dd if=/dev/urandom of={snap_mnt!s}/lv1 bs=1M count=5')

            # Reduce snapshot with filesystem
            assert snap1.reduce('-f', '--resizefs', extents='-2')
            assert snap1.report
            assert snap1.report.lv_size == '84.00m'

            run(f'df -h {snap_mnt!s}')

            # Reduce to specific size
            assert snap1.reduce('-f', '--resizefs', size='40m')
            assert snap1.report.lv_size == '40.00m'

            run(f'df -h {snap_mnt!s}')

        finally:
            # Cleanup
            umount(lv_mnt)
            umount(snap_mnt)
            lv_dir.remove_dir()
            snap_dir.remove_dir()
            if snap1:
                snap1.remove()
            if pool:
                pool.remove_with_thin_volumes()

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'size': '200M', 'pool_name': 'pool'}],
        indirect=True,
    )
    def test_reduce_multiple_thin_volumes(self, thinpool_fixture: ThinPool) -> None:
        """Test reducing multiple thin volumes in the same pool.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture

        # Create multiple thin volumes inline
        thin1 = pool.create_thin_volume('lv1', virtualsize='100M')
        thin2 = pool.create_thin_volume('lv2', virtualsize='100M')
        thin3 = pool.create_thin_volume('lv3', virtualsize='100M')

        # Reduce all thin volumes
        assert thin1.reduce(size='80m', force='')
        assert thin1.report is not None
        assert thin1.report.lv_size == '80.00m'

        assert thin2.reduce(size='60m', force='')
        assert thin2.report is not None
        assert thin2.report.lv_size == '60.00m'

        assert thin3.reduce(size='40m', force='')
        assert thin3.report is not None
        assert thin3.report.lv_size == '40.00m'

        # Verify all volumes are in the pool
        assert pool.get_thin_volume_count() == 3

        # Cleanup handled by fixture
