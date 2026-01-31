# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for renaming thin provisioning logical volumes.

This module contains pytest tests for renaming thin pools and thin volumes,
verifying that relationships are maintained correctly.
"""

from __future__ import annotations

import contextlib

import pytest

from sts.lvm import LogicalVolume, ThinPool


@pytest.mark.parametrize('loop_devices', [{'count': 4, 'size_mb': 128}], indirect=True)
class TestLvrenameThinp:
    """Test cases for renaming thin provisioning volumes."""

    def test_rename_empty_thin_pool(self, setup_loopdev_vg: str) -> None:
        """Test renaming an empty thin pool.

        Args:
            setup_loopdev_vg: Volume group fixture
        """
        vg_name = setup_loopdev_vg

        pool: ThinPool | None = None
        renamed_pool: ThinPool | None = None

        try:
            # Create empty thin pool
            pool = ThinPool.create_thin_pool('pool1', vg_name, extents='20')

            # Rename pool
            assert pool.rename('renamed_pool')
            renamed_pool = ThinPool(name='renamed_pool', vg=vg_name)
            pool = None  # Original name no longer valid

            # Verify new pool exists
            all_lvs = LogicalVolume.get_all(vg=vg_name)
            assert any(lv.name == 'renamed_pool' for lv in all_lvs), 'renamed_pool should exist'
            assert not any(lv.name == 'pool1' for lv in all_lvs), 'pool1 should not exist'

            # Cleanup
            assert renamed_pool.remove('-f')
            renamed_pool = None
        finally:
            if pool:
                with contextlib.suppress(RuntimeError):
                    pool.remove_with_thin_volumes()
            if renamed_pool:
                with contextlib.suppress(RuntimeError):
                    renamed_pool.remove_with_thin_volumes()

    def test_rename_thin_pool_with_volume(self, setup_loopdev_vg: str) -> None:
        """Test renaming thin pool that contains volumes.

        Args:
            setup_loopdev_vg: Volume group fixture
        """
        vg_name = setup_loopdev_vg

        pool: ThinPool | None = None
        renamed_pool: ThinPool | None = None

        try:
            # Create thin pool with volume
            pool = ThinPool.create_thin_pool('pool1', vg_name, extents='20')
            pool.create_thin_volume('lv1', virtualsize='100M')

            # Rename pool
            assert pool.rename('bakpool1')
            renamed_pool = ThinPool(name='bakpool1', vg=vg_name)
            pool = None

            # Verify new pool exists and old doesn't
            all_lvs = LogicalVolume.get_all(vg=vg_name)
            assert any(lv.name == 'bakpool1' for lv in all_lvs), 'bakpool1 should exist'
            assert not any(lv.name == 'pool1' for lv in all_lvs), 'pool1 should not exist'

            # Verify thin LV still points to renamed pool
            thin_lv_check = next(lv for lv in all_lvs if lv.name == 'lv1')
            assert thin_lv_check.report
            assert thin_lv_check.report.pool_lv == 'bakpool1', 'lv1 should point to bakpool1'

            # Cleanup
            assert renamed_pool.remove_with_thin_volumes()
            renamed_pool = None
        finally:
            if pool:
                with contextlib.suppress(RuntimeError):
                    pool.remove_with_thin_volumes()
            if renamed_pool:
                with contextlib.suppress(RuntimeError):
                    renamed_pool.remove_with_thin_volumes()

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'extents': '20', 'pool_name': 'pool1'}],
        indirect=True,
    )
    def test_rename_thin_volume(self, thinpool_fixture: ThinPool) -> None:
        """Test renaming a thin volume.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture
        vg_name = pool.vg

        # Create thin volume
        thin_lv = pool.create_thin_volume('lv1', virtualsize='100M')

        # Rename thin volume
        assert thin_lv.rename('renamed_lv')

        # Verify new LV exists and old doesn't
        all_lvs = LogicalVolume.get_all(vg=vg_name)
        assert any(lv.name == 'renamed_lv' for lv in all_lvs), 'renamed_lv should exist'
        assert not any(lv.name == 'lv1' for lv in all_lvs), 'lv1 should not exist'

        # Verify renamed LV still points to pool
        renamed_lv = next(lv for lv in all_lvs if lv.name == 'renamed_lv')
        assert renamed_lv.report
        assert renamed_lv.report.pool_lv == 'pool1', 'renamed_lv should point to pool1'

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'stripes',
        [None, '2'],
        ids=['single-stripe', 'two-stripes'],
    )
    def test_rename_pool_and_volume(self, setup_loopdev_vg: str, stripes: str | None) -> None:
        """Test renaming both pool and volume.

        Args:
            setup_loopdev_vg: Volume group fixture
            stripes: Number of stripes (None for single stripe)
        """
        vg_name = setup_loopdev_vg

        pool: ThinPool | None = None
        renamed_pool: ThinPool | None = None

        try:
            # Create thin pool with volume
            if stripes:
                pool = ThinPool.create_thin_pool('pool1', vg_name, extents='20', stripes=stripes)
            else:
                pool = ThinPool.create_thin_pool('pool1', vg_name, extents='20')

            thin_lv = pool.create_thin_volume('lv1', virtualsize='100M')

            # Rename pool
            assert pool.rename('bakpool1')
            renamed_pool = ThinPool(name='bakpool1', vg=vg_name)
            pool = None

            # Verify thin LV now points to renamed pool
            all_lvs = LogicalVolume.get_all(vg=vg_name)
            thin_lv_check = next(lv for lv in all_lvs if lv.name == 'lv1')
            assert thin_lv_check.report
            assert thin_lv_check.report.pool_lv == 'bakpool1', 'lv1 should point to bakpool1'

            # Rename thin LV
            assert thin_lv.rename('baklv1')

            # Verify renamed LV still points to renamed pool
            all_lvs = LogicalVolume.get_all(vg=vg_name)
            renamed_lv = next(lv for lv in all_lvs if lv.name == 'baklv1')
            assert renamed_lv.report
            assert renamed_lv.report.pool_lv == 'bakpool1', 'baklv1 should point to bakpool1'

            # Cleanup
            assert renamed_pool.remove_with_thin_volumes()
            renamed_pool = None
        finally:
            if pool:
                with contextlib.suppress(RuntimeError):
                    pool.remove_with_thin_volumes()
            if renamed_pool:
                with contextlib.suppress(RuntimeError):
                    renamed_pool.remove_with_thin_volumes()

    def test_rename_pool_with_multiple_volumes(self, setup_loopdev_vg: str) -> None:
        """Test renaming pool with multiple volumes.

        Args:
            setup_loopdev_vg: Volume group fixture
        """
        vg_name = setup_loopdev_vg

        pool: ThinPool | None = None
        renamed_pool: ThinPool | None = None
        volume_count = 3

        try:
            # Create thin pool with multiple volumes
            pool = ThinPool.create_thin_pool('pool1', vg_name, extents='20')
            for i in range(volume_count):
                pool.create_thin_volume(f'lv{i + 1}', virtualsize='100M')

            # Rename pool
            assert pool.rename('bakpool1')
            renamed_pool = ThinPool(name='bakpool1', vg=vg_name)
            pool = None

            # Verify all volumes point to renamed pool
            all_lvs = LogicalVolume.get_all(vg=vg_name)
            for i in range(volume_count):
                lv = next(lv for lv in all_lvs if lv.name == f'lv{i + 1}')
                assert lv.report
                assert lv.report.pool_lv == 'bakpool1', f'lv{i + 1} should point to bakpool1'

            # Cleanup
            assert renamed_pool.remove_with_thin_volumes()
            renamed_pool = None
        finally:
            if pool:
                with contextlib.suppress(RuntimeError):
                    pool.remove_with_thin_volumes()
            if renamed_pool:
                with contextlib.suppress(RuntimeError):
                    renamed_pool.remove_with_thin_volumes()

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'extents': '20', 'pool_name': 'pool1'}],
        indirect=True,
    )
    def test_rename_multiple_volumes_in_same_pool(self, thinpool_fixture: ThinPool) -> None:
        """Test renaming multiple volumes in the same pool.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture
        vg_name = pool.vg

        # Create multiple thin volumes
        lv1 = pool.create_thin_volume('lv1', virtualsize='100M')
        lv2 = pool.create_thin_volume('lv2', virtualsize='100M')
        lv3 = pool.create_thin_volume('lv3', virtualsize='100M')

        # Rename all volumes
        assert lv1.rename('renamed_lv1')
        assert lv2.rename('renamed_lv2')
        assert lv3.rename('renamed_lv3')

        # Verify all renamed volumes point to same pool
        all_lvs = LogicalVolume.get_all(vg=vg_name)
        for new_name in ['renamed_lv1', 'renamed_lv2', 'renamed_lv3']:
            lv = next(lv for lv in all_lvs if lv.name == new_name)
            assert lv.report
            assert lv.report.pool_lv == 'pool1', f'{new_name} should point to pool1'

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'extents': '20', 'pool_name': 'pool1'}],
        indirect=True,
    )
    def test_rename_snapshot(self, thinpool_fixture: ThinPool) -> None:
        """Test renaming a thin snapshot.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture
        vg_name = pool.vg

        # Create thin volume and snapshot
        thin_lv = pool.create_thin_volume('lv1', virtualsize='100M')
        snap = thin_lv.create_snapshot('snap1')
        assert snap is not None

        # Rename snapshot
        assert snap.rename('renamed_snap')

        # Verify new snapshot exists
        all_lvs = LogicalVolume.get_all(vg=vg_name)
        assert any(lv.name == 'renamed_snap' for lv in all_lvs), 'renamed_snap should exist'
        assert not any(lv.name == 'snap1' for lv in all_lvs), 'snap1 should not exist'

        # Verify renamed snapshot points to pool
        renamed_snap = next(lv for lv in all_lvs if lv.name == 'renamed_snap')
        assert renamed_snap.report
        assert renamed_snap.report.pool_lv == 'pool1'

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'extents': '20', 'pool_name': 'pool1'}],
        indirect=True,
    )
    def test_rename_snapshot_chain(self, thinpool_fixture: ThinPool) -> None:
        """Test renaming snapshots in a chain.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture
        vg_name = pool.vg

        # Create thin volume and snapshot chain
        thin_lv = pool.create_thin_volume('lv1', virtualsize='100M')
        snap1 = thin_lv.create_snapshot('snap1')
        assert snap1 is not None
        snap2 = snap1.create_snapshot('snap2')
        assert snap2 is not None

        # Rename snapshots
        assert snap1.rename('renamed_snap1')
        assert snap2.rename('renamed_snap2')

        # Verify renamed snapshots exist
        all_lvs = LogicalVolume.get_all(vg=vg_name)
        assert any(lv.name == 'renamed_snap1' for lv in all_lvs)
        assert any(lv.name == 'renamed_snap2' for lv in all_lvs)

        # Cleanup handled by fixture

    def test_rename_pool_multiple_times(self, setup_loopdev_vg: str) -> None:
        """Test renaming a pool multiple times.

        Args:
            setup_loopdev_vg: Volume group fixture
        """
        vg_name = setup_loopdev_vg

        pool: ThinPool | None = None
        final_pool: ThinPool | None = None

        try:
            # Create thin pool
            pool = ThinPool.create_thin_pool('pool1', vg_name, extents='20')
            pool.create_thin_volume('lv1', virtualsize='100M')

            # Rename pool multiple times
            assert pool.rename('pool2')
            assert pool.rename('pool3')
            assert pool.rename('final_pool')
            final_pool = ThinPool(name='final_pool', vg=vg_name)
            pool = None

            # Verify final name exists
            all_lvs = LogicalVolume.get_all(vg=vg_name)
            assert any(lv.name == 'final_pool' for lv in all_lvs)

            # Verify volume still points to renamed pool
            lv = next(lv for lv in all_lvs if lv.name == 'lv1')
            assert lv.report
            assert lv.report.pool_lv == 'final_pool'

            # Cleanup
            assert final_pool.remove_with_thin_volumes()
            final_pool = None
        finally:
            if pool:
                with contextlib.suppress(RuntimeError):
                    pool.remove_with_thin_volumes()
            if final_pool:
                with contextlib.suppress(RuntimeError):
                    final_pool.remove_with_thin_volumes()

    @pytest.mark.parametrize(
        ('old_name', 'new_name'),
        [
            ('pool', 'renamed_pool'),
            ('mypool', 'backup_pool'),
            ('test_pool', 'prod_pool'),
        ],
        ids=['simple-rename', 'backup-naming', 'test-to-prod'],
    )
    def test_rename_pool_various_names(self, setup_loopdev_vg: str, old_name: str, new_name: str) -> None:
        """Test renaming pools with various naming patterns.

        Args:
            setup_loopdev_vg: Volume group fixture
            old_name: Original pool name
            new_name: New pool name
        """
        vg_name = setup_loopdev_vg

        pool: ThinPool | None = None
        renamed_pool: ThinPool | None = None

        try:
            # Create thin pool with original name
            pool = ThinPool.create_thin_pool(old_name, vg_name, extents='20')
            pool.create_thin_volume('lv1', virtualsize='100M')

            # Rename pool
            assert pool.rename(new_name)
            renamed_pool = ThinPool(name=new_name, vg=vg_name)
            pool = None

            # Verify new name exists
            all_lvs = LogicalVolume.get_all(vg=vg_name)
            assert any(lv.name == new_name for lv in all_lvs)
            assert not any(lv.name == old_name for lv in all_lvs)

            # Cleanup
            assert renamed_pool.remove_with_thin_volumes()
            renamed_pool = None
        finally:
            if pool:
                with contextlib.suppress(RuntimeError):
                    pool.remove_with_thin_volumes()
            if renamed_pool:
                with contextlib.suppress(RuntimeError):
                    renamed_pool.remove_with_thin_volumes()
