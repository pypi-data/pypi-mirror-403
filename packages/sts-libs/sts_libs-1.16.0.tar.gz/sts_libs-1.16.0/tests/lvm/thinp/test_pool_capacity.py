# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for thin pool capacity management.

This module contains pytest tests for thin pool capacity management,
focusing on behavior when pool capacity is exceeded with different filesystems.
"""

from __future__ import annotations

import contextlib
import logging
from pathlib import Path

import pytest

from sts.lvm import ThinPool
from sts.utils.cmdline import run
from sts.utils.files import Directory, mkfs, mount, umount


@pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 1024}], indirect=True)
class TestPoolCapacity:
    """Test cases for thin pool capacity management."""

    @pytest.mark.parametrize('filesystem', ['ext4', 'xfs'])
    def test_exceed_pool_capacity(self, setup_loopdev_vg: str, filesystem: str) -> None:
        """Test exceeding thin pool capacity with different filesystems.

        Args:
            setup_loopdev_vg: Volume group setup fixture
            filesystem: Filesystem type to test (ext4, xfs)
        """
        vg_name = setup_loopdev_vg
        mnt_point_thin1 = Path('/mnt/thin1')
        mnt_point_thin2 = Path('/mnt/thin2')

        logging.info(f'Testing filesystem={filesystem}')

        pool: ThinPool | None = None
        mnt_dir1: Directory | None = None
        mnt_dir2: Directory | None = None
        mounted_thin1 = False
        mounted_thin2 = False

        try:
            # Create thin pool with 800M size (from 1G VG)
            pool = ThinPool.create_thin_pool('test_pool', vg_name, size='800M')

            # Create two 1G thin volumes (overprovisioned)
            pool.create_thin_volume('thin1', virtualsize='1G')
            pool.create_thin_volume('thin2', virtualsize='1G')

            # Display LVs for debugging
            assert run('lvs -a -o +devices').succeeded

            # Check device mapper table
            assert run('dmsetup table').succeeded

            # Create mount directories
            mnt_dir1 = Directory(mnt_point_thin1, create=True)
            mnt_dir2 = Directory(mnt_point_thin2, create=True)

            # Create filesystem on first thin volume
            thin1_device = Path(f'/dev/mapper/{vg_name}-thin1')
            logging.info(f'Creating {filesystem} filesystem on {thin1_device}')
            assert mkfs(thin1_device, filesystem)

            # Mount first thin volume
            assert mount(thin1_device, mnt_point_thin1)
            mounted_thin1 = True

            # Create filesystem on second thin volume
            thin2_device = Path(f'/dev/mapper/{vg_name}-thin2')
            logging.info(f'Creating {filesystem} filesystem on {thin2_device}')
            assert mkfs(thin2_device, filesystem)

            # Mount second thin volume
            assert mount(thin2_device, mnt_point_thin2)
            mounted_thin2 = True

            # Fill up the thin volumes to exceed pool capacity
            logging.info('Starting to fill thin volumes to exceed pool capacity...')

            # Write data to both thin volumes
            # Start writing to first volume (400M should be safe)
            dd_cmd1 = f'dd if=/dev/zero of={mnt_point_thin1!s}/testfile bs=1M count=400 oflag=sync'
            result1 = run(dd_cmd1)
            logging.info(f'Write to thin1 result: {result1.rc}')

            # Try to write to second volume to exceed pool capacity
            dd_cmd2 = f'dd if=/dev/zero of={mnt_point_thin2!s}/testfile bs=1M count=400 oflag=sync'
            result2 = run(dd_cmd2)
            logging.info(f'Write to thin2 result: {result2.rc}')

            # Check pool status
            pool.refresh_report()
            assert pool.report is not None
            if pool.report.data_percent:
                logging.info(f'Pool data usage: {pool.report.data_percent}')

            # Verify filesystem behavior after pool stress
            df_result1 = run(f'df {mnt_point_thin1!s}')
            logging.info(f'df result for thin1: {df_result1.rc}')

            df_result2 = run(f'df {mnt_point_thin2!s}')
            logging.info(f'df result for thin2: {df_result2.rc}')

        finally:
            # Cleanup - ensure unmounting even if test fails
            if mounted_thin1:
                umount_result1 = umount(mnt_point_thin1)
                logging.info(f'Unmount result thin1: {umount_result1}')
            if mounted_thin2:
                umount_result2 = umount(mnt_point_thin2)
                logging.info(f'Unmount result thin2: {umount_result2}')

            # Remove mount point directories
            if mnt_dir1 and mnt_dir1.exists:
                mnt_dir1.remove_dir()
            if mnt_dir2 and mnt_dir2.exists:
                mnt_dir2.remove_dir()

            # Clean up LVM volumes
            if pool:
                with contextlib.suppress(RuntimeError):
                    pool.remove_with_thin_volumes()

    @pytest.mark.parametrize(
        ('pool_size', 'write_size', 'write_count'),
        [
            ('500M', 100, 5),  # 5 x 100M = 500M (fills pool exactly)
            ('600M', 100, 6),  # 6 x 100M = 600M (fills pool exactly)
        ],
        ids=['500M-pool', '600M-pool'],
    )
    def test_pool_data_usage_monitoring(
        self, setup_loopdev_vg: str, pool_size: str, write_size: int, write_count: int
    ) -> None:
        """Test monitoring pool data usage during filling.

        Args:
            setup_loopdev_vg: Volume group setup fixture
            pool_size: Size of the thin pool
            write_size: Size of each write in MB
            write_count: Number of writes to perform
        """
        vg_name = setup_loopdev_vg
        mnt_point = Path('/mnt/monitor_test')

        pool: ThinPool | None = None
        mnt_dir: Directory | None = None
        mounted = False

        try:
            # Create thin pool and volume
            pool = ThinPool.create_thin_pool('monitor_pool', vg_name, size=pool_size)
            pool.create_thin_volume('monitor_thin', virtualsize='1G')

            # Create filesystem and mount
            thin_device = Path(f'/dev/mapper/{vg_name}-monitor_thin')
            assert mkfs(thin_device, 'ext4')

            mnt_dir = Directory(mnt_point, create=True)

            assert mount(thin_device, mnt_point)
            mounted = True

            # Write data in increments and monitor usage
            for i in range(1, write_count + 1):
                dd_cmd = f'dd if=/dev/zero of={mnt_point!s}/testfile{i} bs=1M count={write_size} oflag=sync'
                result = run(dd_cmd)

                # Check pool usage after each write
                pool.refresh_report()
                assert pool.report is not None
                if pool.report.data_percent:
                    logging.info(f'After writing {i * write_size}M: Pool usage {pool.report.data_percent}')

                # If pool is getting full, writes may start failing
                if not result.succeeded:
                    logging.info(f'Write {i} failed, pool likely full')
                    break

        finally:
            if mounted:
                umount(mnt_point)
            if mnt_dir and mnt_dir.exists:
                mnt_dir.remove_dir()
            if pool:
                with contextlib.suppress(RuntimeError):
                    pool.remove_with_thin_volumes()

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'size': '800M', 'pool_name': 'meta_pool'}],
        indirect=True,
    )
    @pytest.mark.parametrize(
        ('volume_count', 'check_interval'),
        [
            (20, 5),  # Check every 5 volumes
            (15, 3),  # Check every 3 volumes
        ],
        ids=['20-volumes', '15-volumes'],
    )
    def test_metadata_usage_monitoring(
        self, thinpool_fixture: ThinPool, volume_count: int, check_interval: int
    ) -> None:
        """Test monitoring pool metadata usage.

        Args:
            thinpool_fixture: Thin pool fixture
            volume_count: Number of thin volumes to create
            check_interval: How often to check metadata usage
        """
        pool = thinpool_fixture

        # Create many small thin volumes to consume metadata
        for i in range(volume_count):
            pool.create_thin_volume(f'thin{i}', virtualsize='100M')

            # Check metadata usage periodically
            if i % check_interval == 0:
                pool.refresh_report()
                assert pool.report is not None
                if pool.report.metadata_percent:
                    logging.info(f'After creating {i + 1} thin volumes: Metadata usage {pool.report.metadata_percent}')

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        ('pool_size', 'write_size'),
        [
            ('400M', 200),  # Write 200M to 400M pool
            ('600M', 300),  # Write 300M to 600M pool
        ],
        ids=['400M-pool', '600M-pool'],
    )
    def test_pool_autoextend_behavior(self, setup_loopdev_vg: str, pool_size: str, write_size: int) -> None:
        """Test thin pool autoextend configuration behavior.

        Args:
            setup_loopdev_vg: Volume group setup fixture
            pool_size: Size of the thin pool
            write_size: Size of data to write in MB
        """
        vg_name = setup_loopdev_vg
        mnt_point = Path('/mnt/autoextend_test')

        pool: ThinPool | None = None
        mnt_dir: Directory | None = None
        mounted = False

        try:
            # Create thin pool and volume
            pool = ThinPool.create_thin_pool('autoextend_pool', vg_name, size=pool_size)
            pool.create_thin_volume('autoextend_thin', virtualsize='1G')

            # Check initial pool size
            assert pool.report is not None
            initial_size = pool.report.lv_size
            logging.info(f'Initial pool size: {initial_size}')

            # Create filesystem and write data
            thin_device = Path(f'/dev/mapper/{vg_name}-autoextend_thin')
            assert mkfs(thin_device, 'ext4')

            mnt_dir = Directory(mnt_point, create=True)

            assert mount(thin_device, mnt_point)
            mounted = True

            # Write data that should fit in the pool
            dd_cmd = f'dd if=/dev/zero of={mnt_point!s}/testfile bs=1M count={write_size} oflag=sync'
            result = run(dd_cmd)
            assert result.succeeded

            # Check pool size after write (should be same unless autoextend is configured)
            pool.refresh_report()
            assert pool.report is not None
            final_size = pool.report.lv_size
            logging.info(f'Final pool size: {final_size}')

            # Verify size hasn't changed (no autoextend configured)
            assert initial_size == final_size

        finally:
            if mounted:
                umount(mnt_point)
            if mnt_dir and mnt_dir.exists:
                mnt_dir.remove_dir()
            if pool:
                with contextlib.suppress(RuntimeError):
                    pool.remove_with_thin_volumes()

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'size': '600M', 'pool_name': 'multi_pool'}],
        indirect=True,
    )
    @pytest.mark.parametrize(
        'volume_count',
        [2, 3],
        ids=['two-volumes', 'three-volumes'],
    )
    def test_pool_with_multiple_volumes_capacity(self, thinpool_fixture: ThinPool, volume_count: int) -> None:
        """Test pool capacity with multiple thin volumes.

        Args:
            thinpool_fixture: Thin pool fixture
            volume_count: Number of thin volumes to create
        """
        pool = thinpool_fixture

        # Create multiple overprovisioned volumes
        for i in range(volume_count):
            pool.create_thin_volume(f'thin{i}', virtualsize='1G')

        # Verify all volumes were created
        pool.refresh_report()
        assert pool.report is not None
        assert pool.report.thin_count == str(volume_count)

        # Check initial pool usage
        initial_usage = pool.report.data_percent
        logging.info(f'Initial pool data usage with {volume_count} volumes: {initial_usage}')

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'size': '500M', 'pool_name': 'snap_pool'}],
        indirect=True,
    )
    def test_pool_capacity_with_snapshots(self, thinpool_fixture: ThinPool) -> None:
        """Test pool capacity behavior with snapshots.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture
        vg_name = pool.vg
        mnt_point = Path('/mnt/snapshot_test')

        # Create thin volume
        thin = pool.create_thin_volume('origin', virtualsize='1G')

        # Create filesystem and write initial data
        thin_device = Path(f'/dev/mapper/{vg_name}-origin')
        assert mkfs(thin_device, 'ext4')

        mnt_dir = Directory(mnt_point, create=True)
        mounted = False

        try:
            assert mount(thin_device, mnt_point)
            mounted = True

            # Write initial data
            dd_cmd = f'dd if=/dev/zero of={mnt_point!s}/testfile bs=1M count=100 oflag=sync'
            result = run(dd_cmd)
            assert result.succeeded

            # Check pool usage after initial write
            pool.refresh_report()
            assert pool.report is not None
            usage_before_snap = pool.report.data_percent
            logging.info(f'Pool usage before snapshot: {usage_before_snap}')

            # Create snapshots
            snap1 = thin.create_snapshot('snap1')
            snap2 = thin.create_snapshot('snap2')
            assert snap1 is not None
            assert snap2 is not None

            # Write more data to origin
            dd_cmd = f'dd if=/dev/zero of={mnt_point!s}/testfile2 bs=1M count=100 oflag=sync'
            result = run(dd_cmd)
            assert result.succeeded

            # Check pool usage after writes with snapshots
            pool.refresh_report()
            assert pool.report is not None
            usage_after_snap = pool.report.data_percent
            logging.info(f'Pool usage after snapshot and writes: {usage_after_snap}')

            # Verify thin count includes snapshots
            assert pool.report.thin_count == '3'  # origin + 2 snapshots

        finally:
            if mounted:
                umount(mnt_point)
            if mnt_dir.exists:
                mnt_dir.remove_dir()
            # Pool cleanup handled by fixture
