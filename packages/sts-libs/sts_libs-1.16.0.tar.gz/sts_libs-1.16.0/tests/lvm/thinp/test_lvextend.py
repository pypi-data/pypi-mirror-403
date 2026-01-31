# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for lvextend thin provisioning operations.

This module contains pytest tests for lvextend command with thin provisioning,
focusing on extending thin pools and thin volumes.
"""

from __future__ import annotations

import pytest

from sts.lvm import ThinPool


@pytest.mark.parametrize('loop_devices', [{'count': 4, 'size_mb': 512}], indirect=True)
class TestLvextendThin:
    """Test cases for lvextend thin provisioning operations."""

    @pytest.mark.parametrize(
        'stripes',
        [None, '2'],
        ids=['single-stripe', 'two-stripes'],
    )
    def test_extend_thin_pool_by_extents(self, setup_loopdev_vg: str, stripes: str | None) -> None:
        """Test extending thin pool by extents.

        Args:
            setup_loopdev_vg: Volume group fixture
            stripes: Number of stripes (None for single stripe)
        """
        vg_name = setup_loopdev_vg

        pool_name = f'pool_{"single" if stripes is None else "striped"}'
        pool: ThinPool | None = None

        try:
            # Create thin pool
            if stripes:
                pool = ThinPool.create_thin_pool(pool_name, vg_name, stripes=stripes, extents='2')
            else:
                pool = ThinPool.create_thin_pool(pool_name, vg_name, extents='2')

            # Extend by 2 extents
            assert pool.extend(extents='+2')
            assert pool.report
            assert pool.report.lv_size == '16.00m'
        finally:
            if pool:
                pool.remove(force='', yes='')

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'extents': '2', 'pool_name': 'pool'}],
        indirect=True,
    )
    @pytest.mark.parametrize(
        ('extend_size', 'expected_size'),
        [
            ('+8', '24.00m'),  # Relative size (default unit is m): 16m + 8m = 24m
            ('+8M', '24.00m'),  # Relative size with explicit unit: 16m + 8M = 24m
        ],
        ids=['relative-default-unit', 'relative-explicit-unit'],
    )
    def test_extend_thin_pool_by_size(self, thinpool_fixture: ThinPool, extend_size: str, expected_size: str) -> None:
        """Test extending thin pool by size with different formats.

        Args:
            thinpool_fixture: Thin pool fixture
            extend_size: Size to extend by
            expected_size: Expected final size
        """
        pool = thinpool_fixture

        # First extend to 16m (pool starts at 8m = 2 extents * 4m)
        assert pool.extend(extents='+2')
        assert pool.report is not None
        assert pool.report.lv_size == '16.00m'

        # Then extend by specified size
        assert pool.extend(size=extend_size)
        assert pool.report is not None
        assert pool.report.lv_size == expected_size

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'stripes',
        [None, '2'],
        ids=['single-stripe', 'two-stripes'],
    )
    def test_extend_thin_pool_to_absolute_size_by_extents(self, setup_loopdev_vg: str, stripes: str | None) -> None:
        """Test extending thin pool to absolute size using extents.

        Args:
            setup_loopdev_vg: Volume group fixture
            stripes: Number of stripes (None for single stripe)
        """
        vg_name = setup_loopdev_vg

        pool_name = f'pool_{"single" if stripes is None else "striped"}'
        pool: ThinPool | None = None

        try:
            # Create thin pool
            if stripes:
                pool = ThinPool.create_thin_pool(pool_name, vg_name, stripes=stripes, extents='2')
            else:
                pool = ThinPool.create_thin_pool(pool_name, vg_name, extents='2')

            # Set specific size by extents (6 extents = 24m)
            assert pool.extend(extents='6')
            assert pool.report
            assert pool.report.lv_size == '24.00m'
        finally:
            if pool:
                pool.remove(force='', yes='')

    @pytest.mark.parametrize(
        'stripes',
        [None, '2'],
        ids=['single-stripe', 'two-stripes'],
    )
    def test_extend_thin_pool_to_absolute_size_by_size(self, setup_loopdev_vg: str, stripes: str | None) -> None:
        """Test extending thin pool to absolute size using size.

        Args:
            setup_loopdev_vg: Volume group fixture
            stripes: Number of stripes (None for single stripe)
        """
        vg_name = setup_loopdev_vg

        pool_name = f'pool_{"single" if stripes is None else "striped"}'
        pool: ThinPool | None = None

        try:
            # Create thin pool
            if stripes:
                pool = ThinPool.create_thin_pool(pool_name, vg_name, stripes=stripes, extents='2')
            else:
                pool = ThinPool.create_thin_pool(pool_name, vg_name, extents='2')

            # Set specific size (40m)
            assert pool.extend(size='40m')
            assert pool.report
            assert pool.report.lv_size == '40.00m'
        finally:
            if pool:
                pool.remove(force='', yes='')

    @pytest.mark.parametrize(
        ('thinpool_fixture', 'initial_size', 'extend_amount', 'expected_size'),
        [
            ({'extents': '50', 'pool_name': 'pool'}, '100m', '+100m', '200.00m'),
            ({'extents': '50', 'pool_name': 'pool'}, '200m', '+200m', '400.00m'),
        ],
        indirect=['thinpool_fixture'],
        ids=['100m-to-200m', '200m-to-400m'],
    )
    def test_extend_thin_lv_by_relative_size(
        self, thinpool_fixture: ThinPool, initial_size: str, extend_amount: str, expected_size: str
    ) -> None:
        """Test extending thin LV virtual size by relative amount.

        Args:
            thinpool_fixture: Thin pool fixture
            initial_size: Initial size for thin LV
            extend_amount: Amount to extend by
            expected_size: Expected final size
        """
        pool = thinpool_fixture

        # Create thin LV inline to get direct reference
        thin_lv = pool.create_thin_volume('lv1', virtualsize=initial_size)

        assert thin_lv.report
        assert thin_lv.report.lv_size == initial_size.replace('m', '.00m')

        # Extend thin LV virtual size
        assert thin_lv.extend(size=extend_amount)
        assert thin_lv.report.lv_size == expected_size

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'extents': '50', 'pool_name': 'pool'}],
        indirect=True,
    )
    def test_extend_thin_lv_to_absolute_size(self, thinpool_fixture: ThinPool) -> None:
        """Test extending thin LV to absolute size.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture

        # Create thin LV inline to get direct reference
        thin_lv = pool.create_thin_volume('lv1', virtualsize='100m')

        assert thin_lv.report
        assert thin_lv.report.lv_size == '100.00m'

        # Extend to specific absolute size
        assert thin_lv.extend(size='300m')
        assert thin_lv.report.lv_size == '300.00m'

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'extents': '50', 'pool_name': 'pool'}],
        indirect=True,
    )
    def test_extend_thin_lv_by_extents(self, thinpool_fixture: ThinPool) -> None:
        """Test extending thin LV by extents.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture

        # Create thin LV inline to get direct reference
        thin_lv = pool.create_thin_volume('lv1', virtualsize='300m')

        assert thin_lv.report
        assert thin_lv.report.lv_size == '300.00m'

        # Extend by extents (assuming 4M extent size, +25 extents = +100m)
        assert thin_lv.extend(extents='+25')
        assert thin_lv.report.lv_size == '400.00m'

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        ('thinpool_fixture', 'size_spec', 'expected_size'),
        [
            ({'extents': '50', 'pool_name': 'pool'}, '+50m', '156.00m'),
            ({'extents': '50', 'pool_name': 'pool'}, '+1g', '1.10g'),
        ],
        indirect=['thinpool_fixture'],
        ids=['extend-megabytes', 'extend-gigabytes'],
    )
    def test_extend_thin_lv_different_units(
        self, thinpool_fixture: ThinPool, size_spec: str, expected_size: str
    ) -> None:
        """Test extending thin LV with different size units.

        Args:
            thinpool_fixture: Thin pool fixture
            size_spec: Size specification for extend
            expected_size: Expected final size
        """
        pool = thinpool_fixture

        # Create thin LV inline to get direct reference
        thin_lv = pool.create_thin_volume('lv1', virtualsize='100m')

        # First extend by 2m to get to 102m
        assert thin_lv.extend(size='+2m')

        # Then perform the parametrized extend
        assert thin_lv.extend(size=size_spec)
        assert thin_lv.report is not None
        assert thin_lv.report.lv_size == expected_size

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'extents': '50', 'pool_name': 'pool'}],
        indirect=True,
    )
    def test_extend_thin_lv_to_large_absolute_size(self, thinpool_fixture: ThinPool) -> None:
        """Test extending thin LV to large absolute size.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture

        # Create thin LV inline to get direct reference
        thin_lv = pool.create_thin_volume('lv1', virtualsize='100m')

        # Extend to 2g absolute
        assert thin_lv.extend(size='2g')
        assert thin_lv.report is not None
        assert thin_lv.report.lv_size == '2.00g'

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'extents': '10', 'pool_name': 'pool'}],
        indirect=True,
    )
    def test_extend_beyond_vg_capacity_fails(self, thinpool_fixture: ThinPool) -> None:
        """Test that extending beyond VG capacity fails.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture

        # Try to extend beyond VG capacity - should fail
        assert not pool.extend(extents='+1000')

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        ('thinpool_fixture', 'metadata_size'),
        [
            ({'size': '100m', 'pool_name': 'pool_8m', 'poolmetadatasize': '8m'}, '8m'),
            ({'size': '100m', 'pool_name': 'pool_16m', 'poolmetadatasize': '16m'}, '16m'),
        ],
        indirect=['thinpool_fixture'],
        ids=['8m-metadata', '16m-metadata'],
    )
    def test_extend_thin_pool_with_metadata(self, thinpool_fixture: ThinPool, metadata_size: str) -> None:
        """Test creating thin pool with specific metadata size.

        Args:
            thinpool_fixture: Thin pool fixture with specific metadata size
            metadata_size: Expected metadata size
        """
        pool = thinpool_fixture

        # Verify pool is functional and metadata size matches expected
        assert pool.report
        assert pool.report.lv_size == '100.00m'

        expected_meta = metadata_size.replace('m', '.00m')
        assert pool.report.lv_metadata_size == expected_meta

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        ('thinpool_fixture', 'pool_extend', 'expected_pool_size'),
        [
            ({'extents': '2', 'pool_name': 'pool'}, '+2', '16.00m'),  # Extend by 2 extents: 8m + 8m = 16m
            ({'extents': '2', 'pool_name': 'pool'}, '+8m', '16.00m'),  # Extend by 8m size: 8m + 8m = 16m
        ],
        indirect=['thinpool_fixture'],
        ids=['extend-by-extents', 'extend-by-size'],
    )
    def test_extend_thin_pool_with_multiple_operations(
        self, thinpool_fixture: ThinPool, pool_extend: str, expected_pool_size: str
    ) -> None:
        """Test extending thin pool with multiple operations.

        Args:
            thinpool_fixture: Thin pool fixture
            pool_extend: Extend specification (extents or size)
            expected_pool_size: Expected pool size after extend
        """
        pool = thinpool_fixture

        # Extend the pool
        if pool_extend.startswith('+') and pool_extend[1:].isdigit():
            # It's an extent specification
            assert pool.extend(extents=pool_extend)
        else:
            # It's a size specification
            assert pool.extend(size=pool_extend)

        assert pool.report is not None
        assert pool.report.lv_size == expected_pool_size

        # Create thin volume to verify pool works
        thin_lv = pool.create_thin_volume('thin1', virtualsize='100m')
        assert thin_lv.report

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'extents': '50', 'pool_name': 'pool'}],
        indirect=True,
    )
    def test_extend_thin_pool_and_thin_volumes(self, thinpool_fixture: ThinPool) -> None:
        """Test extending both pool and thin volumes.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture

        # Create multiple thin volumes
        thin1 = pool.create_thin_volume('thin1', virtualsize='100m')
        thin2 = pool.create_thin_volume('thin2', virtualsize='200m')

        # Extend pool
        assert pool.extend(size='+100m')
        assert pool.report

        # Extend thin volumes
        assert thin1.extend(size='+100m')
        assert thin1.report is not None
        assert thin1.report.lv_size == '200.00m'

        assert thin2.extend(size='+100m')
        assert thin2.report is not None
        assert thin2.report.lv_size == '300.00m'

        # Verify pool has both volumes
        assert pool.get_thin_volume_count() == 2

        # Cleanup handled by fixture
