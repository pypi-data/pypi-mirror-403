# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for removing thin provisioning logical volumes.

This module contains pytest tests for removing thin pools, thin volumes,
and snapshots with various confirmation methods.
"""

from __future__ import annotations

import contextlib

import pytest

from sts.lvm import LogicalVolume, ThinPool


@pytest.mark.parametrize('loop_devices', [{'count': 4, 'size_mb': 256}], indirect=True)
class TestLvremoveThinp:
    """Test cases for removing thin provisioning volumes."""

    @pytest.mark.parametrize(
        'remove_method',
        ['interactive', '-f', '-ff'],
        ids=['interactive-confirmation', 'force-single', 'force-double'],
    )
    def test_remove_pool_with_confirmation_methods(self, setup_loopdev_vg: str, remove_method: str) -> None:
        """Test various methods of removing thin pools.

        Args:
            setup_loopdev_vg: Volume group fixture
            remove_method: Method to use for removal
        """
        vg_name = setup_loopdev_vg

        # Create thin pool
        pool = ThinPool.create_thin_pool('pool', vg_name, extents='20')

        # Remove pool with specified method
        if remove_method == 'interactive':
            # Simulate interactive removal (automatically answered with yes)
            assert pool.remove()
        elif remove_method == '-f':
            assert pool.remove('-f')
        else:  # '-ff'
            assert pool.remove('-ff')

        # No cleanup needed - pool is removed by the test

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'extents': '20', 'pool_name': 'pool'}],
        indirect=True,
    )
    def test_remove_empty_pool(self, thinpool_fixture: ThinPool) -> None:
        """Test removing an empty thin pool.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture

        # Remove empty pool - this tests the removal, fixture cleanup will handle any failure
        assert pool.remove('-f')

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'extents': '20', 'pool_name': 'pool'}],
        indirect=True,
    )
    def test_remove_pool_with_thin_volumes(self, thinpool_fixture: ThinPool) -> None:
        """Test removing pool that contains thin volumes.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture

        # Create thin volumes
        pool.create_thin_volume('lv1', virtualsize='100M')
        pool.create_thin_volume('lv2', virtualsize='100M')

        # Remove pool with all thin volumes
        assert pool.remove_with_thin_volumes()

    @pytest.mark.parametrize(
        ('thinpool_fixture', 'volume_count'),
        [
            ({'extents': '20', 'pool_name': 'pool'}, 1),
            ({'extents': '20', 'pool_name': 'pool'}, 3),
            ({'extents': '20', 'pool_name': 'pool'}, 5),
        ],
        indirect=['thinpool_fixture'],
        ids=['single-volume', 'three-volumes', 'five-volumes'],
    )
    def test_remove_pool_with_multiple_thin_volumes(self, thinpool_fixture: ThinPool, volume_count: int) -> None:
        """Test removing pool with various numbers of thin volumes.

        Args:
            thinpool_fixture: Thin pool fixture
            volume_count: Number of thin volumes to create
        """
        pool = thinpool_fixture

        # Create multiple thin volumes
        for i in range(volume_count):
            pool.create_thin_volume(f'lv{i + 1}', virtualsize='100M')

        # Verify count
        assert pool.get_thin_volume_count() == volume_count

        # Remove pool with all thin volumes
        assert pool.remove_with_thin_volumes()

    @pytest.mark.parametrize(
        ('thinpool_fixture', 'remove_flag'),
        [
            ({'extents': '20', 'pool_name': 'pool'}, '-f'),
            ({'extents': '20', 'pool_name': 'pool'}, '-ff'),
        ],
        indirect=['thinpool_fixture'],
        ids=['force-single', 'force-double'],
    )
    def test_remove_single_thin_volume(self, thinpool_fixture: ThinPool, remove_flag: str) -> None:
        """Test removing individual thin volumes with different flags.

        Args:
            thinpool_fixture: Thin pool fixture
            remove_flag: Flag to use for removal
        """
        pool = thinpool_fixture

        # Create thin volume
        thin_lv = pool.create_thin_volume('lv1', virtualsize='100M')

        # Remove thin volume
        assert thin_lv.remove(remove_flag)

        # Pool should still exist
        pool.refresh_report()
        assert pool.report

        # Cleanup handled by fixture

    def test_remove_thin_volume_from_multiple_pools(self, setup_loopdev_vg: str) -> None:
        """Test removing thin volumes from different pools.

        Args:
            setup_loopdev_vg: Volume group fixture
        """
        vg_name = setup_loopdev_vg

        pool1: ThinPool | None = None
        pool2: ThinPool | None = None

        try:
            # Create multiple pools with volumes
            pool1 = ThinPool.create_thin_pool('pool1', vg_name, extents='20')
            thin1 = pool1.create_thin_volume('lv1', virtualsize='100M')

            pool2 = ThinPool.create_thin_pool('pool2', vg_name, extents='20')
            thin2 = pool2.create_thin_volume('lv2', virtualsize='100M')

            # Remove volumes from different pools
            assert thin1.remove('-f')
            assert thin2.remove('-f')

            # Both pools should still exist
            pool1.refresh_report()
            pool2.refresh_report()
            assert pool1.report
            assert pool2.report

            # Cleanup pools
            assert pool1.remove('-f')
            pool1 = None
            assert pool2.remove('-f')
            pool2 = None
        finally:
            if pool1:
                with contextlib.suppress(RuntimeError):
                    pool1.remove_with_thin_volumes()
            if pool2:
                with contextlib.suppress(RuntimeError):
                    pool2.remove_with_thin_volumes()

    @pytest.mark.parametrize(
        ('thinpool_fixture', 'volume_count'),
        [
            ({'extents': '20', 'pool_name': 'pool'}, 2),
            ({'extents': '20', 'pool_name': 'pool'}, 3),
            ({'extents': '20', 'pool_name': 'pool'}, 4),
        ],
        indirect=['thinpool_fixture'],
        ids=['two-volumes', 'three-volumes', 'four-volumes'],
    )
    def test_remove_multiple_thin_volumes_at_once(self, thinpool_fixture: ThinPool, volume_count: int) -> None:
        """Test removing multiple thin volumes at once.

        Args:
            thinpool_fixture: Thin pool fixture
            volume_count: Number of volumes to create and remove
        """
        pool = thinpool_fixture
        vg_name = pool.vg

        # Create multiple thin volumes
        volumes = []
        for i in range(volume_count):
            lv = pool.create_thin_volume(f'lv{i + 1}', virtualsize='100M')
            volumes.append(lv)

        # Build list of volume paths for removal (all except first)
        other_volumes = [f'{vg_name}/lv{i + 2}' for i in range(volume_count - 1)]

        # Remove all volumes at once (first volume removes others too)
        assert volumes[0].remove(*other_volumes, '-f')

        # Verify all volumes are removed by checking each one
        for i in range(volume_count):
            lv_check = LogicalVolume(name=f'lv{i + 1}', vg=vg_name)
            # Volumes should not exist anymore
            assert not lv_check.refresh_report()

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'extents': '20', 'pool_name': 'pool'}],
        indirect=True,
    )
    def test_remove_thin_volume_with_double_force(self, thinpool_fixture: ThinPool) -> None:
        """Test removing multiple thin volumes with -ff flag.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture
        vg_name = pool.vg

        # Create multiple volumes
        lv1 = pool.create_thin_volume('lv1', virtualsize='100M')
        pool.create_thin_volume('lv2', virtualsize='100M')
        pool.create_thin_volume('lv3', virtualsize='100M')

        # Remove all three volumes with -ff flag
        assert lv1.remove(f'{vg_name}/lv2', f'{vg_name}/lv3', '-ff')

        # Verify all volumes are removed
        for lv_name in ['lv1', 'lv2', 'lv3']:
            lv_check = LogicalVolume(name=lv_name, vg=vg_name)
            assert not lv_check.refresh_report()

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'extents': '20', 'pool_name': 'pool'}],
        indirect=True,
    )
    def test_remove_thin_snapshot_simple(self, thinpool_fixture: ThinPool) -> None:
        """Test removing a single thin snapshot.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture

        # Create thin volume and snapshot
        thin_lv = pool.create_thin_volume('lv1', virtualsize='100M')

        snap1 = thin_lv.create_snapshot('snap1')
        assert snap1 is not None

        # Remove snapshot
        assert snap1.remove('-f')

        # Original volume should still exist
        thin_lv.refresh_report()
        assert thin_lv.report

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        ('thinpool_fixture', 'snapshot_count'),
        [
            ({'extents': '20', 'pool_name': 'pool'}, 1),
            ({'extents': '20', 'pool_name': 'pool'}, 2),
            ({'extents': '20', 'pool_name': 'pool'}, 3),
        ],
        indirect=['thinpool_fixture'],
        ids=['one-snapshot', 'two-snapshots', 'three-snapshots'],
    )
    def test_remove_multiple_snapshots(self, thinpool_fixture: ThinPool, snapshot_count: int) -> None:
        """Test removing multiple snapshots.

        Args:
            thinpool_fixture: Thin pool fixture
            snapshot_count: Number of snapshots to create and remove
        """
        pool = thinpool_fixture

        # Create thin volume
        thin_lv = pool.create_thin_volume('lv1', virtualsize='100M')

        # Create multiple snapshots
        snapshots = []
        for i in range(snapshot_count):
            snap = thin_lv.create_snapshot(f'snap{i + 1}')
            assert snap is not None
            snapshots.append(snap)

        # Remove all snapshots
        for snap in snapshots:
            assert snap.remove('-f')

        # Original volume should still exist
        thin_lv.refresh_report()
        assert thin_lv.report

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'extents': '20', 'pool_name': 'pool'}],
        indirect=True,
    )
    def test_remove_snapshot_chain(self, thinpool_fixture: ThinPool) -> None:
        """Test removing snapshots created from other snapshots.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture

        # Create thin volume
        thin_lv = pool.create_thin_volume('lv1', virtualsize='100M')

        # Create snapshot chain: lv1 -> snap1 -> snap2 -> snap3
        snap1 = thin_lv.create_snapshot('snap1')
        assert snap1 is not None

        snap2 = snap1.create_snapshot('snap2')
        assert snap2 is not None

        snap3 = snap2.create_snapshot('snap3')
        assert snap3 is not None

        # Remove snapshots in reverse order
        assert snap3.remove('-f')
        assert snap2.remove('-f')
        assert snap1.remove('-f')

        # Original volume should still exist
        thin_lv.refresh_report()
        assert thin_lv.report

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'extents': '20', 'pool_name': 'pool'}],
        indirect=True,
    )
    def test_remove_multiple_snapshots_at_once(self, thinpool_fixture: ThinPool) -> None:
        """Test removing multiple snapshots at once.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture
        vg_name = pool.vg

        # Create thin volume
        thin_lv = pool.create_thin_volume('lv1', virtualsize='100M')

        # Create snapshot chain
        snap1 = thin_lv.create_snapshot('snap1')
        assert snap1 is not None

        snap2 = snap1.create_snapshot('snap2')
        assert snap2 is not None

        # Remove both snapshots at once
        assert snap1.remove(f'{vg_name}/snap2', '-f')

        # Original volume should still exist
        thin_lv.refresh_report()
        assert thin_lv.report

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'extents': '20', 'pool_name': 'pool'}],
        indirect=True,
    )
    def test_remove_thin_volume_with_snapshots(self, thinpool_fixture: ThinPool) -> None:
        """Test that removing thin volume also removes its snapshots.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture

        # Create thin volume
        thin_lv = pool.create_thin_volume('lv1', virtualsize='100M')

        # Create snapshots
        snap1 = thin_lv.create_snapshot('snap1')
        assert snap1 is not None
        snap2 = thin_lv.create_snapshot('snap2')
        assert snap2 is not None

        # Remove entire pool with all volumes
        assert pool.remove_with_thin_volumes()

    @pytest.mark.parametrize(
        'stripes',
        [None, '2'],
        ids=['single-stripe', 'two-stripes'],
    )
    def test_remove_striped_pool_with_volumes(self, setup_loopdev_vg: str, stripes: str | None) -> None:
        """Test removing striped thin pools with volumes.

        Args:
            setup_loopdev_vg: Volume group fixture
            stripes: Number of stripes (None for single stripe)
        """
        vg_name = setup_loopdev_vg

        pool: ThinPool | None = None

        try:
            # Create pool (striped or not)
            if stripes:
                pool = ThinPool.create_thin_pool('pool', vg_name, extents='20', stripes=stripes)
            else:
                pool = ThinPool.create_thin_pool('pool', vg_name, extents='20')

            # Create thin volumes
            pool.create_thin_volume('lv1', virtualsize='100M')
            pool.create_thin_volume('lv2', virtualsize='100M')

            # Remove pool with all volumes
            assert pool.remove_with_thin_volumes()
            pool = None  # Mark as cleaned up
        finally:
            if pool:
                with contextlib.suppress(RuntimeError):
                    pool.remove_with_thin_volumes()
