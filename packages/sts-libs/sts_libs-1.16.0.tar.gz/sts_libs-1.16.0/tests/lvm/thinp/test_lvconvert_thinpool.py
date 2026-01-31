# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for lvconvert operations to create thin pools.

This module contains pytest tests for converting logical volumes to thin pools
with various parameters and configurations.
"""

from __future__ import annotations

import pytest

from sts.lvm import LogicalVolume


@pytest.mark.parametrize('loop_devices', [{'count': 4, 'size_mb': 128}], indirect=True)
class TestLvconvertThinpool:
    """Test cases for lvconvert to thin pool operations."""

    @pytest.mark.parametrize(
        ('regular_lv_fixture', 'expected_attr_prefix'),
        [
            ({'extents': '20', 'lv_name': 'pool', 'skip_cleanup': True}, 'twi-a-tz'),
            ({'extents': '30', 'lv_name': 'pool', 'skip_cleanup': True}, 'twi-a-tz'),
        ],
        indirect=['regular_lv_fixture'],
        ids=['20-extents', '30-extents'],
    )
    def test_convert_to_thinpool(self, regular_lv_fixture: LogicalVolume, expected_attr_prefix: str) -> None:
        """Test converting regular LV to thin pool with different sizes.

        Args:
            regular_lv_fixture: Regular LV fixture (skip_cleanup=True since we convert it)
            expected_attr_prefix: Expected attribute prefix after conversion
        """
        lv = regular_lv_fixture

        # Convert to thin pool
        pool = lv.convert_to_thinpool()
        assert pool is not None

        try:
            # Verify it's a thin pool
            assert pool.report
            assert pool.report.lv_attr
            assert pool.report.lv_attr.startswith(expected_attr_prefix)
        finally:
            # Cleanup the pool (not the original LV since it's now a pool)
            pool.remove(force='', yes='')

    @pytest.mark.parametrize(
        ('regular_lv_fixture', 'discards_mode'),
        [
            (
                {'extents': '20', 'lv_name': 'pool_passdown', 'inactive': True, 'zero': 'n', 'skip_cleanup': True},
                'passdown',
            ),
            (
                {'extents': '20', 'lv_name': 'pool_nopassdown', 'inactive': True, 'zero': 'n', 'skip_cleanup': True},
                'nopassdown',
            ),
            (
                {'extents': '20', 'lv_name': 'pool_ignore', 'inactive': True, 'zero': 'n', 'skip_cleanup': True},
                'ignore',
            ),
        ],
        indirect=['regular_lv_fixture'],
        ids=['passdown', 'nopassdown', 'ignore'],
    )
    def test_convert_inactive_to_thinpool(self, regular_lv_fixture: LogicalVolume, discards_mode: str) -> None:
        """Test converting inactive LV to thin pool with different discard modes.

        Args:
            regular_lv_fixture: Inactive regular LV fixture
            discards_mode: Discard mode to use for conversion
        """
        lv = regular_lv_fixture

        # Convert to thin pool with specific discard mode
        pool = lv.convert_to_thinpool(discards=discards_mode)
        assert pool is not None

        try:
            # Verify it's an inactive thin pool with correct discards
            assert pool.report
            assert pool.report.lv_attr
            assert pool.report.lv_attr.startswith('twi---tz')
            assert pool.report.discards == discards_mode
        finally:
            pool.remove(force='', yes='')

    @pytest.mark.parametrize(
        (
            'regular_lv_fixture',
            'chunksize',
            'zero',
            'discards',
            'poolmetadatasize',
            'expected_chunk',
            'expected_meta_size',
        ),
        [
            (
                {'extents': '20', 'lv_name': 'pool_256k', 'skip_cleanup': True},
                '256k',
                'y',
                'nopassdown',
                '4M',
                '256.00k',
                '4.00m',
            ),
            (
                {'extents': '20', 'lv_name': 'pool_128k', 'skip_cleanup': True},
                '128k',
                'n',
                'passdown',
                '8M',
                '128.00k',
                '8.00m',
            ),
            (
                {'extents': '20', 'lv_name': 'pool_512k', 'skip_cleanup': True},
                '512k',
                'y',
                'ignore',
                '4M',
                '512.00k',
                '4.00m',
            ),
        ],
        indirect=['regular_lv_fixture'],
        ids=['256k-nopassdown', '128k-passdown', '512k-ignore'],
    )
    def test_convert_with_parameters(
        self,
        regular_lv_fixture: LogicalVolume,
        chunksize: str,
        zero: str,
        discards: str,
        poolmetadatasize: str,
        expected_chunk: str,
        expected_meta_size: str,
    ) -> None:
        """Test converting to thin pool with various specific parameters.

        Args:
            regular_lv_fixture: Regular LV fixture
            chunksize: Chunk size for the pool
            zero: Zero option
            discards: Discards mode
            poolmetadatasize: Pool metadata size
            expected_chunk: Expected chunk size in output
            expected_meta_size: Expected metadata size in output
        """
        lv = regular_lv_fixture

        # Convert with specific parameters
        pool = lv.convert_to_thinpool(
            chunksize=chunksize,
            zero=zero,
            discards=discards,
            poolmetadatasize=poolmetadatasize,
            readahead='16',
        )
        assert pool is not None

        try:
            # Verify parameters
            assert pool.report
            assert pool.report.chunk_size == expected_chunk
            assert pool.report.discards == discards
            assert pool.report.lv_metadata_size == expected_meta_size
            assert pool.report.lv_size == '80.00m'
        finally:
            pool.remove(force='', yes='')

    def test_convert_with_separate_metadata(self, setup_loopdev_vg: str) -> None:
        """Test converting with separate metadata LV.

        This test creates both data and metadata LVs inline since they need to be
        combined during conversion.

        Args:
            setup_loopdev_vg: Volume group fixture
        """
        vg_name = setup_loopdev_vg

        # Create data and metadata LVs
        data_lv = LogicalVolume(name='pool_data', vg=vg_name)
        assert data_lv.create(extents='20')

        metadata_lv = LogicalVolume(name='pool_metadata', vg=vg_name)
        assert metadata_lv.create(extents='10')

        # Convert with separate metadata
        assert metadata_lv.name
        pool = data_lv.convert_to_thinpool(poolmetadata=metadata_lv.name)
        assert pool is not None

        try:
            # Verify sizes
            assert pool.report
            assert pool.report.lv_size == '80.00m'
            assert pool.report.lv_metadata_size == '40.00m'
        finally:
            # Cleanup - pool conversion consumes metadata LV
            pool.remove(force='', yes='')

    @pytest.mark.parametrize(
        ('data_extents', 'metadata_extents', 'expected_data_size', 'expected_meta_size'),
        [
            ('15', '5', '60.00m', '20.00m'),
            ('20', '10', '80.00m', '40.00m'),
            ('25', '8', '100.00m', '32.00m'),
        ],
        ids=['15-5', '20-10', '25-8'],
    )
    def test_convert_various_metadata_sizes(
        self,
        setup_loopdev_vg: str,
        data_extents: str,
        metadata_extents: str,
        expected_data_size: str,
        expected_meta_size: str,
    ) -> None:
        """Test converting with various data and metadata size combinations.

        This test creates both data and metadata LVs inline since they need to be
        combined during conversion with specific sizes.

        Args:
            setup_loopdev_vg: Volume group fixture
            data_extents: Extents for data LV
            metadata_extents: Extents for metadata LV
            expected_data_size: Expected data size after conversion
            expected_meta_size: Expected metadata size after conversion
        """
        vg_name = setup_loopdev_vg

        # Create data and metadata LVs with specific sizes
        data_lv = LogicalVolume(name=f'pool_d{data_extents}', vg=vg_name)
        assert data_lv.create(extents=data_extents)

        metadata_lv = LogicalVolume(name=f'pool_m{metadata_extents}', vg=vg_name)
        assert metadata_lv.create(extents=metadata_extents)

        # Convert with separate metadata
        assert metadata_lv.name is not None
        pool = data_lv.convert_to_thinpool(poolmetadata=metadata_lv.name)
        assert pool is not None

        try:
            # Verify sizes match expectations
            assert pool.report
            assert pool.report.lv_size == expected_data_size
            assert pool.report.lv_metadata_size == expected_meta_size
        finally:
            pool.remove(force='', yes='')

    @pytest.mark.parametrize(
        'regular_lv_fixture',
        [{'extents': '20', 'lv_name': 'pool_inactive', 'inactive': True, 'zero': 'n', 'skip_cleanup': True}],
        indirect=True,
    )
    def test_convert_inactive_stays_inactive(self, regular_lv_fixture: LogicalVolume) -> None:
        """Test thin pool remains inactive after conversion.

        Args:
            regular_lv_fixture: Inactive regular LV fixture
        """
        lv = regular_lv_fixture

        # Convert to thin pool
        pool = lv.convert_to_thinpool()
        assert pool is not None

        try:
            # Verify it's still inactive
            assert pool.report
            assert pool.report.lv_attr
            assert pool.report.lv_attr.startswith('twi---tz')
        finally:
            pool.remove(force='', yes='')

    @pytest.mark.parametrize(
        'regular_lv_fixture',
        [{'extents': '20', 'lv_name': 'pool_then_act', 'inactive': True, 'zero': 'n', 'skip_cleanup': True}],
        indirect=True,
    )
    def test_convert_then_activate(self, regular_lv_fixture: LogicalVolume) -> None:
        """Test thin pool activation after conversion.

        Args:
            regular_lv_fixture: Inactive regular LV fixture
        """
        lv = regular_lv_fixture

        # Convert to thin pool
        pool = lv.convert_to_thinpool()
        assert pool is not None

        try:
            # Verify it's inactive
            assert pool.report
            assert pool.report.lv_attr
            assert pool.report.lv_attr.startswith('twi---tz')

            # Activate and verify
            assert pool.activate()
            assert pool.report.lv_attr.startswith('twi-a-tz')
        finally:
            pool.remove(force='', yes='')

    @pytest.mark.parametrize(
        'zero_val',
        ['y', 'n'],
        ids=['zero-y', 'zero-n'],
    )
    def test_convert_with_zero_option(self, setup_loopdev_vg: str, zero_val: str) -> None:
        """Test thin pool conversion with zero option for data wiping.

        Args:
            setup_loopdev_vg: Volume group fixture
            zero_val: Zero option value ('y' or 'n')
        """
        vg_name = setup_loopdev_vg

        lv = LogicalVolume(name=f'pool_zero_{zero_val}', vg=vg_name)
        assert lv.create(extents='15')

        pool = lv.convert_to_thinpool(zero=zero_val, chunksize='128k')
        assert pool is not None
        assert pool.report is not None
        assert pool.report.zero is not None
        assert pool.report.zero == 'zero' if zero_val == 'y' else ''
        pool.remove(force='', yes='')

    @pytest.mark.parametrize(
        'regular_lv_fixture',
        [{'extents': '25', 'lv_name': 'pool_meta_only', 'skip_cleanup': True}],
        indirect=True,
    )
    def test_convert_poolmetadatasize_only(self, regular_lv_fixture: LogicalVolume) -> None:
        """Test conversion specifying only pool metadata size.

        Args:
            regular_lv_fixture: Regular LV fixture
        """
        lv = regular_lv_fixture

        # Convert with only metadata size specified
        pool = lv.convert_to_thinpool(poolmetadatasize='8M')
        assert pool is not None

        try:
            # Verify metadata size
            assert pool.report
            assert pool.report.lv_metadata_size == '8.00m'
        finally:
            pool.remove(force='', yes='')
