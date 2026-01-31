# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for resizing thin provisioning logical volumes.

This module contains pytest tests for resizing thin pools and thin volumes,
including extending pools, extending thin volumes, and filesystem operations.
"""

from __future__ import annotations

import contextlib
from pathlib import Path

import pytest

from sts.lvm import ThinPool
from sts.utils.cmdline import run
from sts.utils.files import Directory, mkfs, mount, umount


@pytest.mark.parametrize('loop_devices', [{'count': 4, 'size_mb': 256}], indirect=True)
class TestLvresizeThinp:
    """Test cases for resizing thin provisioning volumes."""

    @pytest.mark.parametrize(
        'stripes',
        [None, '2'],
        ids=['single-stripe', 'two-stripes'],
    )
    def test_extend_pool_by_extents(self, setup_loopdev_vg: str, stripes: str | None) -> None:
        """Test extending thin pools by extents.

        Args:
            setup_loopdev_vg: Volume group fixture
            stripes: Number of stripes (None for single stripe)
        """
        vg_name = setup_loopdev_vg

        pool: ThinPool | None = None
        try:
            # Create thin pool
            if stripes:
                pool = ThinPool.create_thin_pool('pool', vg_name, extents='2', stripes=stripes)
            else:
                pool = ThinPool.create_thin_pool('pool', vg_name, extents='2')

            # Extend by extents
            assert pool.extend(extents='+2')
            assert pool.report is not None
            assert pool.report.lv_size == '16.00m'

            # Cleanup
            assert pool.remove('-f')
            pool = None
        finally:
            if pool:
                with contextlib.suppress(RuntimeError):
                    pool.remove_with_thin_volumes()

    @pytest.mark.parametrize(
        ('size_spec', 'expected_size'),
        [
            ('+8', '24.00m'),  # Default unit (m)
            ('+8M', '24.00m'),  # Explicit unit
        ],
        ids=['default-unit', 'explicit-unit'],
    )
    def test_extend_pool_by_size(self, setup_loopdev_vg: str, size_spec: str, expected_size: str) -> None:
        """Test extending thin pools by size.

        Args:
            setup_loopdev_vg: Volume group fixture
            size_spec: Size specification for extension
            expected_size: Expected final size
        """
        vg_name = setup_loopdev_vg

        pool: ThinPool | None = None
        try:
            # Create thin pool and extend to 16m first
            pool = ThinPool.create_thin_pool('pool', vg_name, extents='2')
            assert pool.extend(extents='+2')
            assert pool.report is not None
            assert pool.report.lv_size == '16.00m'

            # Extend by size
            assert pool.extend(size=size_spec)
            assert pool.report is not None
            assert pool.report.lv_size == expected_size

            # Cleanup
            assert pool.remove('-f')
            pool = None
        finally:
            if pool:
                with contextlib.suppress(RuntimeError):
                    pool.remove_with_thin_volumes()

    @pytest.mark.parametrize(
        ('resize_spec', 'expected_size'),
        [
            ('16', '64.00m'),  # Absolute extents: resize to 16 extents
            ('72m', '72.00m'),  # Absolute size: resize to 72m
        ],
        ids=['absolute-extents', 'absolute-size'],
    )
    def test_resize_pool_to_absolute_size(self, setup_loopdev_vg: str, resize_spec: str, expected_size: str) -> None:
        """Test resizing thin pools to absolute sizes (extending only, as reduction not allowed).

        Args:
            setup_loopdev_vg: Volume group fixture
            resize_spec: Resize specification (extents or size with unit)
            expected_size: Expected final size
        """
        vg_name = setup_loopdev_vg

        pool: ThinPool | None = None
        try:
            # Create pool with small initial size
            pool = ThinPool.create_thin_pool('pool', vg_name, extents='2')

            # Resize to specific size (extending)
            if resize_spec.endswith('m'):
                assert pool.resize(size=resize_spec)
            else:
                assert pool.resize(extents=resize_spec)
            assert pool.report is not None
            assert pool.report.lv_size == expected_size

            # Cleanup
            assert pool.remove('-f')
            pool = None
        finally:
            if pool:
                with contextlib.suppress(RuntimeError):
                    pool.remove_with_thin_volumes()

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'extents': '18', 'pool_name': 'pool'}],
        indirect=True,
    )
    @pytest.mark.parametrize(
        'test_option',
        ['--test', '-t'],
        ids=['long-form', 'short-form'],
    )
    def test_resize_pool_test_mode(self, thinpool_fixture: ThinPool, test_option: str) -> None:
        """Test resizing pools in test mode (dry-run).

        Args:
            thinpool_fixture: Thin pool fixture
            test_option: Test mode option (--test or -t)
        """
        pool = thinpool_fixture
        assert pool.report is not None
        original_size = pool.report.lv_size

        # Test mode resize (should not change size)
        assert pool.resize('-l+100%FREE', test_option)
        pool.refresh_report()
        assert pool.report is not None
        assert pool.report.lv_size == original_size

        # Cleanup handled by fixture

    def test_resize_pool_with_specific_devices(self, setup_loopdev_vg: str, loop_devices: list) -> None:
        """Test resizing pool using specific devices.

        Args:
            setup_loopdev_vg: Volume group fixture
            loop_devices: List of loop devices
        """
        vg_name = setup_loopdev_vg
        pvs = loop_devices

        pool: ThinPool | None = None
        try:
            # Create thin pool
            pool = ThinPool.create_thin_pool('pool', vg_name, extents='8')

            # Extend using specific device
            assert pool.resize('-l+2', pvs[3])
            assert pool.report is not None
            assert pool.report.lv_size == '40.00m'

            # Extend using specific PE range
            assert pool.resize('-l+2', f'{pvs[2]}:40:41')
            assert pool.report is not None
            assert pool.report.lv_size == '48.00m'

            # Verify device allocation
            result = run(f'pvs -ovg_name,lv_name,devices {pvs[2]} | grep "{pvs[2]}(40)"')
            assert result.succeeded

            # Cleanup
            assert pool.remove('-f')
            pool = None
        finally:
            if pool:
                with contextlib.suppress(RuntimeError):
                    pool.remove_with_thin_volumes()

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'extents': '85', 'pool_name': 'pool'}],
        indirect=True,
    )
    def test_extend_thin_volume_by_extents(self, thinpool_fixture: ThinPool) -> None:
        """Test extending thin volumes by extents.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture

        # Create thin volume
        thin_lv = pool.create_thin_volume('lv1', virtualsize='308M')

        # Extend to 79 extents (316m)
        assert thin_lv.extend(extents='79')
        assert thin_lv.report is not None
        assert thin_lv.report.lv_size == '316.00m'

        # Extend by +2 extents (should add 8m: 316m + 8m = 324m)
        assert thin_lv.extend(extents='+2')
        assert thin_lv.report is not None
        assert thin_lv.report.lv_size == '324.00m'

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'extents': '85', 'pool_name': 'pool'}],
        indirect=True,
    )
    @pytest.mark.parametrize(
        ('size_spec', 'expected_size'),
        [
            ('324', '324.00m'),  # Absolute size (default unit m)
            ('340m', '340.00m'),  # Absolute size with unit
            ('348m', '348.00m'),  # Another absolute size
        ],
        ids=['absolute-default', 'absolute-340m', 'absolute-348m'],
    )
    def test_extend_thin_volume_by_size(self, thinpool_fixture: ThinPool, size_spec: str, expected_size: str) -> None:
        """Test extending thin volumes by size.

        Args:
            thinpool_fixture: Thin pool fixture
            size_spec: Size specification for extension
            expected_size: Expected final size
        """
        pool = thinpool_fixture

        # Create thin volume
        thin_lv = pool.create_thin_volume('lv1', virtualsize='308M')

        # Extend to specified size
        if size_spec.endswith('m'):
            assert thin_lv.resize(size=size_spec)
        else:
            assert thin_lv.extend(size=size_spec)
        assert thin_lv.report is not None
        assert thin_lv.report.lv_size == expected_size

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'extents': '85', 'pool_name': 'pool'}],
        indirect=True,
    )
    def test_extend_thin_volume_test_mode(self, thinpool_fixture: ThinPool) -> None:
        """Test extending thin volumes in test mode.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture

        # Create thin volume
        thin_lv = pool.create_thin_volume('lv1', virtualsize='308M')

        assert thin_lv.report is not None
        original_size = thin_lv.report.lv_size

        # Test mode resize (should not change size)
        assert thin_lv.resize('-l+100%FREE', '--test')
        thin_lv.refresh_report()
        assert thin_lv.report is not None
        assert thin_lv.report.lv_size == original_size

        assert thin_lv.resize('-l+100%PVS', '--test')
        thin_lv.refresh_report()
        assert thin_lv.report is not None
        assert thin_lv.report.lv_size == original_size

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'size': '200M', 'pool_name': 'pool'}],
        indirect=True,
    )
    @pytest.mark.parametrize(
        'fs_type',
        ['ext4'],  # XFS can extend but not reduce easily
        ids=['ext4-filesystem'],
    )
    def test_resize_thin_volume_with_filesystem(self, thinpool_fixture: ThinPool, fs_type: str) -> None:
        """Test resizing thin volumes with filesystems.

        Args:
            thinpool_fixture: Thin pool fixture
            fs_type: Filesystem type to use
        """
        pool = thinpool_fixture
        vg_name = pool.vg
        lv_mnt = Path('/mnt/lv_resize_test')
        lv_dir = Directory(lv_mnt, create=True)

        # Create thin volume
        thin_lv = pool.create_thin_volume('lv1', virtualsize='100M')

        lv_device = Path(f'/dev/mapper/{vg_name}-lv1')

        try:
            # Create and mount filesystem
            assert mkfs(lv_device, fs_type, force='')
            assert mount(lv_device, lv_mnt)

            # Add some data
            run(f'dd if=/dev/urandom of={lv_mnt!s}/testfile bs=1M count=5')

            # Extend with filesystem resize
            assert thin_lv.resize('-rf', '-l+2')
            assert thin_lv.report is not None
            assert thin_lv.report.lv_size == '108.00m'

            # Verify filesystem is accessible
            result = run(f'df -h {lv_mnt!s}')
            assert result.succeeded

        finally:
            # Cleanup
            umount(lv_mnt)
            lv_dir.remove_dir()
            # Pool cleanup handled by fixture

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'size': '200M', 'pool_name': 'pool'}],
        indirect=True,
    )
    def test_resize_thin_volume_with_snapshot(self, thinpool_fixture: ThinPool) -> None:
        """Test resizing thin volume and its snapshot with filesystem.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture
        vg_name = pool.vg
        lv_mnt = Path('/mnt/lv')
        snap_mnt = Path('/mnt/snap')
        lv_dir = Directory(lv_mnt, create=True)
        snap_dir = Directory(snap_mnt, create=True)

        # Create thin volume
        thin_lv = pool.create_thin_volume('lv1', virtualsize='100M')

        lv_device = Path(f'/dev/mapper/{vg_name}-lv1')
        fs_type = 'ext4'

        snap1 = None
        try:
            # Create and mount filesystem
            assert mkfs(lv_device, fs_type, force='')
            assert mount(lv_device, lv_mnt)

            # Add data
            run(f'dd if=/dev/urandom of={lv_mnt!s}/lv1 bs=1M count=5')

            # Extend with filesystem resize
            assert thin_lv.resize('-rf', '-l+2')
            assert thin_lv.report is not None
            assert thin_lv.report.lv_size == '108.00m'

            # Create snapshot
            snap1 = thin_lv.create_snapshot('snap1', '-K')
            assert snap1 is not None

            snap_device = Path(f'/dev/mapper/{vg_name}-snap1')

            assert mkfs(snap_device, fs_type, force='')
            assert mount(snap_device, snap_mnt)

            # Add data to snapshot
            run(f'dd if=/dev/urandom of={snap_mnt!s}/lv1 bs=1M count=5')

            # Extend snapshot with filesystem resize
            assert snap1.resize('-rf', '-l+2')
            assert snap1.report is not None
            assert snap1.report.lv_size == '116.00m'

            run(f'df -h {snap_mnt!s}')

            # Extend snapshot to specific size
            assert snap1.resize('-rf', '-L120')
            assert snap1.report is not None
            assert snap1.report.lv_size == '120.00m'

            run(f'df -h {snap_mnt!s}')

        finally:
            # Cleanup
            umount(lv_mnt)
            umount(snap_mnt)
            lv_dir.remove_dir()
            snap_dir.remove_dir()
            # Note: snap1 cleanup handled by fixture's remove_with_thin_volumes()

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [
            {'size': '40M', 'pool_name': 'pool', 'poolmetadatasize': '8M'},
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        ('extend_size', 'expected_size'),
        [
            ('+4M', '12.00m'),
            ('16M', '16.00m'),
        ],
        ids=['relative-extend', 'absolute-resize'],
    )
    def test_resize_pool_metadata(self, thinpool_fixture: ThinPool, extend_size: str, expected_size: str) -> None:
        """Test resizing thin pool metadata.

        Args:
            thinpool_fixture: Thin pool fixture with custom metadata size
            extend_size: Size to extend/resize metadata to
            expected_size: Expected final metadata size
        """
        pool = thinpool_fixture

        # Verify initial metadata size
        assert pool.report is not None
        assert pool.report.lv_metadata_size == '8.00m'

        # Resize metadata
        assert pool.resize(poolmetadatasize=extend_size)
        assert pool.report is not None
        assert pool.report.lv_metadata_size == expected_size

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'stripes',
        [None, '2'],
        ids=['single-stripe', 'two-stripes'],
    )
    def test_resize_pool_multiple_operations(self, setup_loopdev_vg: str, stripes: str | None) -> None:
        """Test multiple resize operations on same pool.

        Args:
            setup_loopdev_vg: Volume group fixture
            stripes: Number of stripes (None for single stripe)
        """
        vg_name = setup_loopdev_vg

        pool: ThinPool | None = None
        try:
            # Create pool
            if stripes:
                pool = ThinPool.create_thin_pool('pool', vg_name, extents='2', stripes=stripes)
            else:
                pool = ThinPool.create_thin_pool('pool', vg_name, extents='2')

            # Perform multiple resize operations
            assert pool.extend(extents='+2')
            assert pool.report is not None
            assert pool.report.lv_size == '16.00m'

            assert pool.extend(size='+8')
            assert pool.report is not None
            assert pool.report.lv_size == '24.00m'

            assert pool.extend(size='+8M')
            assert pool.report is not None
            assert pool.report.lv_size == '32.00m'

            assert pool.resize(extents='16')
            assert pool.report is not None
            assert pool.report.lv_size == '64.00m'

            assert pool.resize(size='72m')
            assert pool.report is not None
            assert pool.report.lv_size == '72.00m'

            # Cleanup
            assert pool.remove('-f')
            pool = None
        finally:
            if pool:
                with contextlib.suppress(RuntimeError):
                    pool.remove_with_thin_volumes()

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'extents': '85', 'pool_name': 'pool'}],
        indirect=True,
    )
    def test_resize_multiple_thin_volumes(self, thinpool_fixture: ThinPool) -> None:
        """Test resizing multiple thin volumes in same pool.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture

        # Create multiple thin volumes
        thin1 = pool.create_thin_volume('lv1', virtualsize='100M')
        thin2 = pool.create_thin_volume('lv2', virtualsize='100M')
        thin3 = pool.create_thin_volume('lv3', virtualsize='100M')

        # Resize all volumes
        assert thin1.extend(size='+50m')
        # LVM may round to extent boundary: 100m + 50m = 150m, rounded to 152m
        assert thin1.report is not None
        assert thin1.report.lv_size in ['150.00m', '152.00m']

        assert thin2.extend(size='+100m')
        # 100m + 100m = 200m
        assert thin2.report is not None
        assert thin2.report.lv_size == '200.00m'

        assert thin3.resize(size='250m')
        # 250m may round to 252m
        assert thin3.report is not None
        assert thin3.report.lv_size in ['250.00m', '252.00m']

        # Verify all volumes are in pool
        assert pool.get_thin_volume_count() == 3
