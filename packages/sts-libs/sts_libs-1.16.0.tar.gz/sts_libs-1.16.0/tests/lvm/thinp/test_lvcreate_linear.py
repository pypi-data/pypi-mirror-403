# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for lvcreate thin provisioning linear creation.

This module contains pytest tests for lvcreate command with thin provisioning,
focusing on linear logical volume creation with various options.
"""

from __future__ import annotations

import pytest

from sts.lvm import LogicalVolume, ThinPool


@pytest.mark.parametrize('loop_devices', [{'count': 4, 'size_mb': 512}], indirect=True)
class TestLvcreateLinear:
    """Test cases for lvcreate thin provisioning linear creation."""

    @pytest.mark.parametrize(
        ('pool_size', 'thin_virtualsize'),
        [
            ('4M', '2G'),
            ('8M', '4G'),
        ],
        ids=['4M-pool-2G-thin', '8M-pool-4G-thin'],
    )
    def test_thin_pool_creation_basic(self, setup_loopdev_vg: str, pool_size: str, thin_virtualsize: str) -> None:
        """Test basic thin pool creation with different options.

        This test creates multiple pools with different configurations to verify
        various creation methods work correctly.

        Args:
            setup_loopdev_vg: Volume group fixture
            pool_size: Size for pool2 and pool3
            thin_virtualsize: Virtual size for thin volumes
        """
        vg_name = setup_loopdev_vg

        pools: list[ThinPool] = []

        try:
            # Test thin pool creation with extents
            pool1 = ThinPool.create_thin_pool('pool1', vg_name, extents='1')
            pools.append(pool1)

            # Test thin pool creation with size
            pool2 = ThinPool.create_thin_pool('pool2', vg_name, size=pool_size)
            pools.append(pool2)

            pool3 = ThinPool.create_thin_pool('pool3', vg_name, size=pool_size)
            pools.append(pool3)

            # Create thin volumes in pools
            pool2.create_thin_volume('lv1', virtualsize=thin_virtualsize)
            pool3.create_thin_volume('lv2', virtualsize=thin_virtualsize)
        finally:
            # Clean up
            for pool in pools:
                pool.remove_with_thin_volumes()

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'size': '8M', 'pool_name': 'pool'}],
        indirect=True,
    )
    @pytest.mark.parametrize('num_thin_lvs', [2, 3, 4], ids=['2-lvs', '3-lvs', '4-lvs'])
    def test_thin_lv_in_existing_pool(self, thinpool_fixture: ThinPool, num_thin_lvs: int) -> None:
        """Test creating multiple thin LVs in existing pool.

        Args:
            thinpool_fixture: Thin pool fixture
            num_thin_lvs: Number of thin LVs to create
        """
        pool = thinpool_fixture

        # Create multiple thin LVs
        for i in range(num_thin_lvs):
            pool.create_thin_volume(f'lv{i}', virtualsize='2G')

        # Verify thin volumes were created
        assert pool.get_thin_volume_count() == num_thin_lvs

    def test_thin_type_option_with_virtualsize(self, setup_loopdev_vg: str) -> None:
        """Test --type thin with virtualsize (creates both pool and thin LV).

        Args:
            setup_loopdev_vg: Volume group fixture
        """
        vg_name = setup_loopdev_vg

        # This creates a thin pool and thin LV in one command
        lv = LogicalVolume(name='pool1', vg=vg_name)
        assert lv.create(extents='1', type='thin', virtualsize='1G')

        # Cleanup - this is now a thin LV, not a pool
        assert lv.remove(force='', yes='')

    def test_thin_type_option_without_virtualsize_fails(self, setup_loopdev_vg: str) -> None:
        """Test --type thin without virtualsize should fail (RHEL6.6 bug 1176006).

        Args:
            setup_loopdev_vg: Volume group fixture
        """
        vg_name = setup_loopdev_vg

        # Should fail - type=thin requires virtualsize or thinpool
        lv = LogicalVolume(name='pool_fail', vg=vg_name)
        assert not lv.create(extents='1', type='thin')

    @pytest.mark.parametrize(
        ('thinpool_fixture', 'expected_chunk', 'expected_meta_size'),
        [
            ({'size': '8M', 'pool_name': 'pool_256', 'chunksize': '256'}, '256.00k', '4.00m'),
            ({'size': '8M', 'pool_name': 'pool_512', 'chunksize': '512'}, '512.00k', '4.00m'),
        ],
        indirect=['thinpool_fixture'],
        ids=['256k-chunk', '512k-chunk'],
    )
    def test_lv_metadata_size(self, thinpool_fixture: ThinPool, expected_chunk: str, expected_meta_size: str) -> None:
        """Test if LVM lv_metadata_size is correct with different chunk sizes.

        Args:
            thinpool_fixture: Thin pool fixture with specific chunk size
            expected_chunk: Expected chunk size in output
            expected_meta_size: Expected metadata size in output
        """
        pool = thinpool_fixture

        assert pool.report
        assert pool.report.chunk_size == expected_chunk
        assert pool.report.lv_metadata_size == expected_meta_size

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'size': '16M', 'pool_name': 'pool', 'poolmetadatasize': '8M'}],
        indirect=True,
    )
    def test_custom_metadata_size(self, thinpool_fixture: ThinPool) -> None:
        """Test creating pool with custom metadata size.

        Args:
            thinpool_fixture: Thin pool fixture with custom metadata size
        """
        pool = thinpool_fixture

        assert pool.report
        assert pool.report.lv_metadata_size == '8.00m'

    @pytest.mark.parametrize(
        ('chunksize', 'expected_chunk', 'pool_size'),
        [
            ('64', '64.00k', '4M'),  # Minimum valid
            ('512', '512.00k', '4M'),  # Valid
            ('1048576', '1.00g', '1g'),  # Maximum valid (1G)
        ],
        ids=['64k-min', '512k-ok', '1g-max'],
    )
    def test_chunksize_valid(self, setup_loopdev_vg: str, chunksize: str, expected_chunk: str, pool_size: str) -> None:
        """Test --chunksize with valid values.

        Args:
            setup_loopdev_vg: Volume group fixture
            chunksize: Chunk size to test
            expected_chunk: Expected chunk size in output
            pool_size: Pool size for the test
        """
        vg_name = setup_loopdev_vg

        pool = ThinPool(name=f'pool_{chunksize}', vg=vg_name)
        assert pool.create(chunksize=chunksize, size=pool_size)

        try:
            assert pool.report
            assert pool.report.chunk_size == expected_chunk
        finally:
            pool.remove(force='', yes='')

    @pytest.mark.parametrize('chunksize', ['32', '2097152'], ids=['32k-too-small', '2g-too-big'])
    def test_chunksize_invalid(self, setup_loopdev_vg: str, chunksize: str) -> None:
        """Test --chunksize with invalid values.

        Args:
            setup_loopdev_vg: Volume group fixture
            chunksize: Invalid chunk size to test
        """
        vg_name = setup_loopdev_vg

        pool = ThinPool(name=f'pool_{chunksize}', vg=vg_name)
        pool_size = '2g' if chunksize == '2097152' else '4M'

        assert not pool.create(chunksize=chunksize, size=pool_size)

    @pytest.mark.parametrize(
        'extents_spec',
        ['10%VG', '10%PVS', '10%FREE', '100%FREE', '100%VG', '100%PVS'],
        ids=['10pct-vg', '10pct-pvs', '10pct-free', '100pct-free', '100pct-vg', '100pct-pvs'],
    )
    def test_extents_percentage(self, setup_loopdev_vg: str, extents_spec: str) -> None:
        """Test --extents with percentage options.

        Args:
            setup_loopdev_vg: Volume group fixture
            extents_spec: Extents specification to test
        """
        vg_name = setup_loopdev_vg

        pool = ThinPool.create_thin_pool(f'pool_{extents_spec.replace("%", "pct")}', vg_name, extents=extents_spec)

        try:
            # Verify pool was created
            assert pool.report
            assert pool.report.lv_size  # Has some size
        finally:
            pool.remove_with_thin_volumes()

    def test_extents_invalid_percentage_fails(self, setup_loopdev_vg: str) -> None:
        """Test invalid percentage option fails.

        Args:
            setup_loopdev_vg: Volume group fixture
        """
        vg_name = setup_loopdev_vg

        pool = ThinPool(name='pool_invalid', vg=vg_name)
        assert not pool.create(extents='10%test')

    def test_extents_over_100_percent_free(self, setup_loopdev_vg: str) -> None:
        """Test >100% FREE allocation (RHEL-6.6+ feature).

        Args:
            setup_loopdev_vg: Volume group fixture
        """
        vg_name = setup_loopdev_vg

        # Since RHEL-6.6, percentage is treated as upper limit
        pool = ThinPool.create_thin_pool('pool_110', vg_name, extents='110%FREE')

        try:
            assert pool.report
        finally:
            pool.remove_with_thin_volumes()

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'extents': '90%FREE', 'pool_name': 'pool'}],
        indirect=True,
    )
    @pytest.mark.parametrize(
        'virtualsize',
        ['4096B', '4096K', '4096M', '1G', '1T', '15P'],
        ids=['bytes', 'kilobytes', 'megabytes', 'gigabytes', 'terabytes', '15P'],
    )
    def test_virtualsize_units_valid(self, thinpool_fixture: ThinPool, virtualsize: str) -> None:
        """Test -virtualsize with valid size units.

        Args:
            thinpool_fixture: Thin pool fixture
            virtualsize: Virtual size to test
        """
        pool = thinpool_fixture
        vg_name = pool.vg

        # Create thin LV with specified virtual size
        thin_lv = LogicalVolume(name=f'thin_{virtualsize.replace("P", "p")}', vg=vg_name, pool_name='pool')
        assert thin_lv.create(virtualsize=virtualsize)

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'extents': '90%FREE', 'pool_name': 'pool'}],
        indirect=True,
    )
    def test_virtualsize_units_invalid(self, thinpool_fixture: ThinPool) -> None:
        """Test -virtualsize with invalid size (exceeds maximum).

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture
        vg_name = pool.vg

        # 16P exceeds maximum size
        thin_lv = LogicalVolume(name='thin_16p', vg=vg_name, pool_name='pool')
        assert not thin_lv.create(virtualsize='16P')

    @pytest.mark.parametrize(
        ('thinpool_fixture', 'expected_discards'),
        [
            ({'size': '16m', 'pool_name': 'pool_passdown', 'discards': 'passdown'}, 'passdown'),
            ({'size': '16m', 'pool_name': 'pool_nopassdown', 'discards': 'nopassdown'}, 'nopassdown'),
            ({'size': '16m', 'pool_name': 'pool_ignore', 'discards': 'ignore'}, 'ignore'),
        ],
        indirect=['thinpool_fixture'],
        ids=['passdown', 'nopassdown', 'ignore'],
    )
    def test_discards_option(self, thinpool_fixture: ThinPool, expected_discards: str) -> None:
        """Test --discards option with all valid modes.

        Args:
            thinpool_fixture: Thin pool fixture with specific discards mode
            expected_discards: Expected discards value
        """
        pool = thinpool_fixture

        assert pool.report
        assert pool.report.discards == expected_discards

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'size': '16m', 'pool_name': 'pool_default'}],
        indirect=True,
    )
    def test_discards_default_is_passdown(self, thinpool_fixture: ThinPool) -> None:
        """Test that default discards setting is passdown.

        Args:
            thinpool_fixture: Thin pool fixture with default settings
        """
        pool = thinpool_fixture

        assert pool.report
        assert pool.report.discards == 'passdown'

    def test_thin_pool_mirror_not_supported(self, setup_loopdev_vg: str) -> None:
        """Test that thin pool mirroring is not supported.

        Args:
            setup_loopdev_vg: Volume group fixture
        """
        vg_name = setup_loopdev_vg

        # Thin pool with mirror should fail
        pool = ThinPool(name='pool_mirror', vg=vg_name)
        assert not pool.create(extents='1', mirrors='1')

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'size': '4M', 'pool_name': 'pool'}],
        indirect=True,
    )
    def test_thin_pool_cannot_convert_to_mirror(self, thinpool_fixture: ThinPool) -> None:
        """Test that existing thin pool cannot be converted to mirror.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture

        # Converting to mirror should fail
        assert not pool.convert('-m', '1')

    def test_multiple_pool_creation_methods(self, setup_loopdev_vg: str) -> None:
        """Test various ways to create thin pools.

        This test verifies different API methods for creating thin pools all work correctly.

        Args:
            setup_loopdev_vg: Volume group fixture
        """
        vg_name = setup_loopdev_vg

        pools: list[ThinPool] = []

        try:
            # Method 1: Using ThinPool.create_thin_pool()
            pool1 = ThinPool.create_thin_pool('pool1', vg_name, size='4M')
            pools.append(pool1)

            # Method 2: Using ThinPool instance with create()
            pool2 = ThinPool(name='pool2', vg=vg_name)
            assert pool2.create(size='4M')
            pools.append(pool2)

            # Method 3: Using LogicalVolume with type='thin-pool'
            lv = LogicalVolume(name='pool3', vg=vg_name)
            assert lv.create(size='4M', type='thin-pool')
            pool3 = ThinPool(name='pool3', vg=vg_name)
            pool3.refresh_report()
            pools.append(pool3)

            # Verify all are thin pools
            for pool in pools:
                assert pool.report
                assert pool.report.lv_attr
                assert 't' in pool.report.lv_attr  # Thin pool attribute
        finally:
            # Cleanup
            for pool in pools:
                pool.remove_with_thin_volumes()

    @pytest.mark.parametrize(
        ('thinpool_fixture', 'expected_meta'),
        [
            ({'size': '32M', 'pool_name': 'pool_4M', 'poolmetadatasize': '4M'}, '4.00m'),
            ({'size': '32M', 'pool_name': 'pool_8M', 'poolmetadatasize': '8M'}, '8.00m'),
            ({'size': '32M', 'pool_name': 'pool_16M', 'poolmetadatasize': '16M'}, '16.00m'),
        ],
        indirect=['thinpool_fixture'],
        ids=['4M', '8M', '16M'],
    )
    def test_poolmetadatasize_option(self, thinpool_fixture: ThinPool, expected_meta: str) -> None:
        """Test --poolmetadatasize option with various sizes.

        Args:
            thinpool_fixture: Thin pool fixture with specific metadata size
            expected_meta: Expected metadata size in output
        """
        pool = thinpool_fixture

        assert pool.report
        assert pool.report.lv_metadata_size == expected_meta
