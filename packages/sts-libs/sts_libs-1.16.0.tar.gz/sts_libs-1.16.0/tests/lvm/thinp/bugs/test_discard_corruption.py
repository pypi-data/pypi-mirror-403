# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Test for BZ918647 - discard corruption with thin provisioning snapshots.

This module contains pytest tests for verifying that discard operations on
thin snapshots work correctly and don't cause data corruption.

Bug Reference: BZ918647
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from sts.utils.cmdline import run
from sts.utils.files import Directory, mkfs, mount, umount

if TYPE_CHECKING:
    from sts.lvm import ThinPool


@pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 512}], indirect=True)
class TestDiscardCorruptionBz918647:
    """Test cases for BZ918647 - discard corruption with thin snapshots."""

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'size': '500M', 'pool_name': 'POOL'}],
        indirect=True,
    )
    def test_discard_corruption_snapshot(self, thinpool_fixture: ThinPool) -> None:
        """Test that discard operations on snapshots work correctly without corruption.

        This test verifies that:
        1. Discarding data from origin affects only origin data percentage
        2. Discarding data from snapshot affects snapshot and pool data percentage
        3. Data percentages behave correctly with nopassdown discard mode

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture
        vg_name = pool.vg
        origin_mnt = Path('/var/tmp/origin_mnt')
        snap_mnt = Path('/var/tmp/snap_mnt')

        # Create mount directories
        origin_dir = Directory(origin_mnt, create=True)
        snap_dir: Directory | None = None
        origin_mounted = False
        snap_mounted = False

        try:
            # Create thin volume using ThinPool helper
            logging.info('Creating thin LV')
            origin_lv = pool.create_thin_volume('origin', virtualsize='100M')
            assert origin_lv is not None, 'Failed to create origin thin volume'

            # Set discard mode to nopassdown
            assert pool.change_discards(discards='nopassdown'), 'Failed to set discard mode'

            # Create filesystem and mount
            origin_device = Path(f'/dev/{vg_name}/origin')
            assert mkfs(origin_device, 'ext4', force=True), 'Failed to create filesystem'

            assert mount(origin_device, origin_mnt), 'Failed to mount origin'
            origin_mounted = True

            # Create test file
            logging.info('Creating test file')
            result = run(f'sync; dd if=/dev/zero of={origin_mnt}/file1 bs=1M count=60; sync')
            assert result.succeeded, 'Failed to create test file'

            # Create snapshot (use -K to ignore activation skip and create active)
            logging.info('Creating snapshot')
            snap1_lv = origin_lv.create_snapshot('snap1', '-K')
            assert snap1_lv is not None, 'Failed to create snapshot'
            time.sleep(5)

            # Show discard information
            run(f'lvs {vg_name} -o+discards')

            # Get initial data percentages
            assert pool.report is not None
            assert origin_lv.report is not None
            assert snap1_lv.report is not None
            pre_dp_pool = float(pool.report.data_percent or '0')
            pre_dp_origin = float(origin_lv.report.data_percent or '0')
            pre_dp_snap = float(snap1_lv.report.data_percent or '0')

            logging.info(
                f'Initial data percentages - Pool: {pre_dp_pool}%, Origin: {pre_dp_origin}%, Snap: {pre_dp_snap}%'
            )

            # Remove file from origin and perform discard
            result = run(f'rm -rf {origin_mnt}/file1; sync')
            assert result.succeeded, 'Failed to remove file'

            result = run(f'fstrim -vvv {origin_mnt}; sync')
            assert result.succeeded, 'fstrim failed on origin'

            umount(origin_mnt)
            origin_mounted = False
            time.sleep(5)

            logging.info('Checking if data percentage got reduced only on origin')
            run(f'lvs {vg_name} -o+discards')

            # Refresh reports to get updated data percentages
            pool.refresh_report()
            origin_lv.refresh_report()
            snap1_lv.refresh_report()

            # Get data percentages after origin discard
            assert pool.report is not None
            assert origin_lv.report is not None
            assert snap1_lv.report is not None
            now_dp_pool = float(pool.report.data_percent or '0')
            now_dp_origin = float(origin_lv.report.data_percent or '0')
            now_dp_snap = float(snap1_lv.report.data_percent or '0')

            logging.info(f'After origin discard - Pool: {now_dp_pool}%, Origin: {now_dp_origin}%, Snap: {now_dp_snap}%')

            # Verify pool data percentage is relatively unchanged (within 2% tolerance)
            if pre_dp_pool > 0:
                pool_diff = pre_dp_pool / now_dp_pool if now_dp_pool > 0 else float('inf')
                assert 0.98 <= pool_diff <= 1.02, (
                    f'Pool data percentage changed too much: {pre_dp_pool}% -> {now_dp_pool}% (ratio: {pool_diff})'
                )

            # Verify snapshot data percentage unchanged
            assert now_dp_snap == pre_dp_snap, (
                f'Snapshot data percentage should not change: {pre_dp_snap}% -> {now_dp_snap}%'
            )

            # Verify origin data percentage reduced
            assert now_dp_origin < pre_dp_origin, (
                f'Origin data percentage should reduce: {pre_dp_origin}% -> {now_dp_origin}%'
            )

            # Test discard on snapshot
            logging.info('Deleting data from snapshot')
            snap_dir = Directory(snap_mnt, create=True)
            snap_device = Path(f'/dev/{vg_name}/snap1')
            assert mount(snap_device, snap_mnt), 'Failed to mount snapshot'
            snap_mounted = True

            result = run(f'rm -rf {snap_mnt}/file1; sync')
            assert result.succeeded, 'Failed to remove file from snapshot'

            result = run(f'fstrim -vvv {snap_mnt}; sync')
            assert result.succeeded, 'fstrim failed on snapshot'

            time.sleep(5)

            logging.info('Checking if data percentage got reduced on snapshot and pool')
            run(f'lvs {vg_name} -o+discards')

            # Refresh reports for final check
            pool.refresh_report()
            origin_lv.refresh_report()
            snap1_lv.refresh_report()

            # Get final data percentages
            assert pool.report is not None
            assert origin_lv.report is not None
            assert snap1_lv.report is not None
            post_dp_pool = float(pool.report.data_percent or '0')
            post_dp_origin = float(origin_lv.report.data_percent or '0')
            post_dp_snap = float(snap1_lv.report.data_percent or '0')

            logging.info(
                f'After snapshot discard - Pool: {post_dp_pool}%, Origin: {post_dp_origin}%, Snap: {post_dp_snap}%'
            )

            # Verify pool data percentage reduced
            assert post_dp_pool < now_dp_pool, f'Pool data percentage should reduce: {now_dp_pool}% -> {post_dp_pool}%'

            # Verify snapshot data percentage reduced
            assert post_dp_snap < now_dp_snap, (
                f'Snapshot data percentage should reduce: {now_dp_snap}% -> {post_dp_snap}%'
            )

            # Verify origin data percentage unchanged
            assert post_dp_origin == now_dp_origin, (
                f'Origin data percentage should not change: {now_dp_origin}% -> {post_dp_origin}%'
            )

            umount(snap_mnt)
            snap_mounted = False

        finally:
            # Cleanup mounts (only if still mounted)
            if origin_mounted:
                umount(mountpoint=origin_mnt)
            if snap_mounted:
                umount(mountpoint=snap_mnt)

            # Remove directories if they exist
            if origin_dir.exists:
                origin_dir.remove_dir()
            if snap_dir is not None and snap_dir.exists:
                snap_dir.remove_dir()
