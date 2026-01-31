# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for thin pool metadata spare creation.

This module contains pytest tests for creating thin pools with and without
pool metadata spare volumes and managing their sizes.
"""

from __future__ import annotations

import contextlib
import logging

import pytest

from sts.lvm import LogicalVolume, ThinPool


def _cleanup_spare_lv(vg_name: str, spare_name: str = 'lvol0_pmspare') -> None:
    """Clean up pool metadata spare LV if it exists.

    Args:
        vg_name: Volume group name
        spare_name: Name of the spare LV (default: 'lvol0_pmspare')
    """
    spare_lv = LogicalVolume(name=spare_name, vg=vg_name)
    with contextlib.suppress(RuntimeError):
        spare_lv.remove(force='', yes='')


@pytest.mark.parametrize('loop_devices', [{'count': 4, 'size_mb': 128}], indirect=True)
class TestLvcreatePoolmetadataspare:
    """Test cases for thin pool metadata spare operations."""

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'extents': '10', 'pool_name': 'pool0', 'poolmetadataspare': 'n'}],
        indirect=True,
    )
    def test_poolmetadataspare_disabled(self, thinpool_fixture: ThinPool, setup_loopdev_vg: str) -> None:
        """Test creating pool without metadata spare.

        Args:
            thinpool_fixture: Thin pool fixture with spare disabled
            setup_loopdev_vg: Volume group name for verification
        """
        _ = thinpool_fixture  # Fixture needed to create pool, value unused
        pmspare_name = 'lvol0_pmspare'

        # Verify spare doesn't exist
        all_lvs = LogicalVolume.get_all(setup_loopdev_vg)
        assert not any(lv.name == pmspare_name for lv in all_lvs), 'lvol0_pmspare should not exist'

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'extents': '10', 'pool_name': 'pool', 'poolmetadataspare': 'y'}],
        indirect=True,
    )
    def test_poolmetadataspare_enabled(self, thinpool_fixture: ThinPool, setup_loopdev_vg: str) -> None:
        """Test creating pool with metadata spare explicitly enabled.

        Args:
            thinpool_fixture: Thin pool fixture with spare enabled
            setup_loopdev_vg: Volume group name for verification
        """
        _ = thinpool_fixture  # Fixture needed to create pool, value unused
        pmspare_name = 'lvol0_pmspare'

        try:
            # Verify spare exists with default size (4M)
            spare_lv = LogicalVolume(name=pmspare_name, vg=setup_loopdev_vg)
            assert spare_lv.refresh_report(), 'lvol0_pmspare should exist'
            assert spare_lv.report
            assert spare_lv.report.lv_size == '4.00m', f'Expected 4.00m, got {spare_lv.report.lv_size}'
        finally:
            # Clean up spare LV (fixture handles pool cleanup)
            _cleanup_spare_lv(setup_loopdev_vg)

    @pytest.mark.parametrize(
        ('thinpool_fixture', 'expected_spare_size'),
        [
            ({'extents': '10', 'pool_name': 'pool_4M', 'poolmetadatasize': '4M'}, '4.00m'),
            ({'extents': '10', 'pool_name': 'pool_8M', 'poolmetadatasize': '8M'}, '8.00m'),
            ({'extents': '10', 'pool_name': 'pool_16M', 'poolmetadatasize': '16M'}, '16.00m'),
        ],
        indirect=['thinpool_fixture'],
        ids=['4M-metadata', '8M-metadata', '16M-metadata'],
    )
    def test_poolmetadataspare_with_custom_metadata_size(
        self, thinpool_fixture: ThinPool, expected_spare_size: str, setup_loopdev_vg: str
    ) -> None:
        """Test that spare size matches the pool metadata size.

        Args:
            thinpool_fixture: Thin pool fixture with custom metadata size
            expected_spare_size: Expected spare LV size
            setup_loopdev_vg: Volume group name for verification
        """
        _ = thinpool_fixture  # Fixture needed to create pool, value unused
        pmspare_name = 'lvol0_pmspare'

        try:
            # Verify spare exists and has matching size
            spare_lv = LogicalVolume(name=pmspare_name, vg=setup_loopdev_vg)
            assert spare_lv.refresh_report(), 'lvol0_pmspare should exist'
            assert spare_lv.report
            assert spare_lv.report.lv_size == expected_spare_size, (
                f'Expected {expected_spare_size}, got {spare_lv.report.lv_size}'
            )
        finally:
            _cleanup_spare_lv(setup_loopdev_vg)

    def test_poolmetadataspare_size_updates_with_larger_pool(self, setup_loopdev_vg: str) -> None:
        """Test that metadata spare size gets updated when larger pools are created.

        Args:
            setup_loopdev_vg: Volume group fixture
        """
        vg_name = setup_loopdev_vg
        pmspare_name = 'lvol0_pmspare'

        pool1: ThinPool | None = None
        pool2: ThinPool | None = None

        try:
            # Step 1: Create pool with 4M metadata
            pool1 = ThinPool(name='pool1', vg=vg_name)
            assert pool1.create(extents='10', poolmetadatasize='4M')

            # Verify spare exists and has 4M size
            spare_lv = LogicalVolume(name=pmspare_name, vg=vg_name)
            assert spare_lv.refresh_report(), 'lvol0_pmspare should exist'
            assert spare_lv.report
            assert spare_lv.report.lv_size == '4.00m', f'Expected 4.00m, got {spare_lv.report.lv_size}'

            # Step 2: Create pool with 8M metadata - should update spare size to 8M
            pool2 = ThinPool(name='pool2', vg=vg_name)
            assert pool2.create(extents='10', poolmetadatasize='8M')

            # Verify spare size updated to 8M
            spare_lv.refresh_report()
            assert spare_lv.report.lv_size == '8.00m', f'Expected 8.00m, got {spare_lv.report.lv_size}'
        finally:
            if pool2:
                pool2.remove(force='', yes='')
            if pool1:
                pool1.remove(force='', yes='')
            _cleanup_spare_lv(vg_name)

    def test_poolmetadataspare_multiple_pools_management(self, setup_loopdev_vg: str) -> None:
        """Test managing metadata spare with multiple pools.

        Args:
            setup_loopdev_vg: Volume group fixture
        """
        vg_name = setup_loopdev_vg
        pmspare_name = 'lvol0_pmspare'

        pool1: ThinPool | None = None
        pool2: ThinPool | None = None

        try:
            # Step 1: Create pool without spare
            pool1 = ThinPool(name='pool1', vg=vg_name)
            assert pool1.create(extents='10', poolmetadataspare='n')

            # Verify spare doesn't exist
            all_lvs = LogicalVolume.get_all(vg_name)
            assert not any(lv.name == pmspare_name for lv in all_lvs), 'lvol0_pmspare should not exist'

            # Step 2: Create pool with spare
            pool2 = ThinPool(name='pool2', vg=vg_name)
            assert pool2.create(extents='10', poolmetadataspare='y')

            # Verify spare now exists
            spare_lv = LogicalVolume(name=pmspare_name, vg=vg_name)
            assert spare_lv.refresh_report(), 'lvol0_pmspare should exist after pool2 creation'
        finally:
            if pool2:
                pool2.remove(force='', yes='')
            if pool1:
                pool1.remove(force='', yes='')
            _cleanup_spare_lv(vg_name)

    def test_poolmetadataspare_with_thin_volumes(self, setup_loopdev_vg: str) -> None:
        """Test that pools with and without spare can create thin volumes.

        Args:
            setup_loopdev_vg: Volume group fixture
        """
        vg_name = setup_loopdev_vg

        pool1: ThinPool | None = None
        pool2: ThinPool | None = None

        try:
            # Create pool without spare
            pool1 = ThinPool.create_thin_pool('pool1', vg_name, extents='10', poolmetadataspare='n')

            # Create pool with spare
            pool2 = ThinPool.create_thin_pool('pool2', vg_name, extents='10', poolmetadataspare='y')

            # Create thin volumes in both pools to verify they work
            pool1.create_thin_volume('thin1', virtualsize='100M')
            pool2.create_thin_volume('thin2', virtualsize='100M')

            # Verify both pools have their thin volumes
            assert pool1.get_thin_volume_count() == 1
            assert pool2.get_thin_volume_count() == 1

            # Log all LVs for debugging
            for lv in LogicalVolume.get_all(vg_name):
                logging.info(f'LV: {lv.name}')
        finally:
            if pool1:
                pool1.remove_with_thin_volumes()
            if pool2:
                pool2.remove_with_thin_volumes()
            _cleanup_spare_lv(vg_name)

    @pytest.mark.parametrize(
        ('pool1_meta_size', 'pool2_meta_size', 'expected_spare_size'),
        [
            ('4M', '4M', '4.00m'),  # Same size - spare should be 4M
            ('4M', '8M', '8.00m'),  # Increasing size - spare should grow to 8M
            ('8M', '4M', '8.00m'),  # Decreasing size - spare stays at 8M (max)
        ],
        ids=['same-4M', 'increasing-4M-to-8M', 'decreasing-8M-to-4M'],
    )
    def test_poolmetadataspare_size_behavior(
        self,
        setup_loopdev_vg: str,
        pool1_meta_size: str,
        pool2_meta_size: str,
        expected_spare_size: str,
    ) -> None:
        """Test spare size behavior with different pool metadata sizes.

        Args:
            setup_loopdev_vg: Volume group fixture
            pool1_meta_size: Metadata size for first pool
            pool2_meta_size: Metadata size for second pool
            expected_spare_size: Expected final spare size
        """
        vg_name = setup_loopdev_vg
        pmspare_name = 'lvol0_pmspare'

        pool1: ThinPool | None = None
        pool2: ThinPool | None = None

        try:
            # Create first pool
            pool1 = ThinPool(name='pool1', vg=vg_name)
            assert pool1.create(extents='10', poolmetadatasize=pool1_meta_size)

            # Create second pool
            pool2 = ThinPool(name='pool2', vg=vg_name)
            assert pool2.create(extents='10', poolmetadatasize=pool2_meta_size)

            # Verify spare size matches expected (should be the max of all pools)
            spare_lv = LogicalVolume(name=pmspare_name, vg=vg_name)
            assert spare_lv.refresh_report(), 'lvol0_pmspare should exist'
            assert spare_lv.report
            assert spare_lv.report.lv_size == expected_spare_size, (
                f'Expected {expected_spare_size}, got {spare_lv.report.lv_size}'
            )
        finally:
            if pool2:
                pool2.remove(force='', yes='')
            if pool1:
                pool1.remove(force='', yes='')
            _cleanup_spare_lv(vg_name)
