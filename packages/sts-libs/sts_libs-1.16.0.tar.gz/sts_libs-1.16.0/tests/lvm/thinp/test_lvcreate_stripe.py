# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for lvcreate thin provisioning stripe creation.

This module contains pytest tests for lvcreate command with thin provisioning,
focusing on striped logical volume creation with various stripe options.

The tests use the ThinPool class which provides access to stripe information
through the pool's data component (tdata).
"""

import pytest

from sts.lvm import ThinPool


@pytest.mark.parametrize('loop_devices', [{'count': 4, 'size_mb': 512}], indirect=True)
class TestLvcreateStripe:
    """Test cases for lvcreate thin provisioning stripe creation."""

    def test_stripes_option(self, setup_loopdev_vg: str) -> None:
        """Test -i|--stripes option with various stripe counts.

        This test creates multiple pools with different stripe counts to verify
        various stripe configurations work correctly.

        Args:
            setup_loopdev_vg: Volume group fixture
        """
        vg_name = setup_loopdev_vg

        pools: list[ThinPool] = []

        try:
            # Test different stripe counts
            pool1 = ThinPool.create_thin_pool('pool1', vg_name, stripes='1', extents='1')
            assert pool1.tdata is not None
            assert pool1.tdata.report is not None
            assert pool1.tdata.report.stripes == '1'
            pools.append(pool1)

            pool2 = ThinPool.create_thin_pool('pool2', vg_name, stripes='2', size='4M')
            assert pool2.tdata is not None
            assert pool2.tdata.report is not None
            assert pool2.tdata.report.stripes == '2'
            pools.append(pool2)

            pool3 = ThinPool.create_thin_pool('pool3', vg_name, stripes='3', size='4M')
            assert pool3.tdata is not None
            assert pool3.tdata.report is not None
            assert pool3.tdata.report.stripes == '3'
            pools.append(pool3)

            pool4 = ThinPool.create_thin_pool('pool4', vg_name, stripes='4', size='4M')
            assert pool4.tdata is not None
            assert pool4.tdata.report is not None
            assert pool4.tdata.report.stripes == '4'
            pools.append(pool4)

            # Test stripe count too high - should fail (only 4 PVs available)
            pool5 = ThinPool(name='pool5', vg=vg_name)
            assert not pool5.create(stripes='5', size='4M')
        finally:
            # Clean up - remove thin volumes first if any, then pools
            for pool in pools:
                pool.remove_with_thin_volumes()

    @pytest.mark.parametrize(
        ('thinpool_fixture', 'expected_stripe_size'),
        [
            ({'stripes': '2', 'stripesize': '4', 'size': '8M', 'pool_name': 'pool_4k'}, '4.00k'),
            ({'stripes': '2', 'stripesize': '8', 'size': '8M', 'pool_name': 'pool_8k'}, '8.00k'),
            ({'stripes': '2', 'stripesize': '16', 'size': '8M', 'pool_name': 'pool_16k'}, '16.00k'),
            ({'stripes': '2', 'stripesize': '32', 'size': '8M', 'pool_name': 'pool_32k'}, '32.00k'),
            ({'stripes': '2', 'stripesize': '64', 'size': '8M', 'pool_name': 'pool_64k'}, '64.00k'),
            ({'stripes': '2', 'stripesize': '128', 'size': '16M', 'pool_name': 'pool_128k'}, '128.00k'),
            ({'stripes': '2', 'stripesize': '256', 'size': '16M', 'pool_name': 'pool_256k'}, '256.00k'),
            ({'stripes': '2', 'stripesize': '512', 'size': '32M', 'pool_name': 'pool_512k'}, '512.00k'),
            ({'stripes': '2', 'stripesize': '1024', 'size': '64M', 'pool_name': 'pool_1m'}, '1.00m'),
        ],
        indirect=['thinpool_fixture'],
        ids=['4k', '8k', '16k', '32k', '64k', '128k', '256k', '512k', '1m'],
    )
    def test_stripe_size_option(self, thinpool_fixture: ThinPool, expected_stripe_size: str) -> None:
        """Test -I|--stripesize option with various stripe sizes.

        Args:
            thinpool_fixture: Thin pool fixture with specific stripe size
            expected_stripe_size: Expected stripe size in output
        """
        pool = thinpool_fixture

        assert pool.tdata is not None
        assert pool.tdata.report is not None
        data_stripe_size = pool.tdata.report.stripe_size
        assert data_stripe_size
        assert data_stripe_size.strip() == expected_stripe_size

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        ('thinpool_fixture', 'expected_stripe_size'),
        [
            ({'stripes': '2', 'stripesize': '4k', 'size': '8M', 'pool_name': 'pool_4k'}, '4.00k'),
            ({'stripes': '2', 'stripesize': '128k', 'size': '16M', 'pool_name': 'pool_128k'}, '128.00k'),
            ({'stripes': '2', 'stripesize': '1m', 'size': '64M', 'pool_name': 'pool_1m'}, '1.00m'),
        ],
        indirect=['thinpool_fixture'],
        ids=['4k-unit', '128k-unit', '1m-unit'],
    )
    def test_stripe_size_units(self, thinpool_fixture: ThinPool, expected_stripe_size: str) -> None:
        """Test stripe size with different unit suffixes (k, m).

        Args:
            thinpool_fixture: Thin pool fixture with specific stripe size using unit suffix
            expected_stripe_size: Expected stripe size in output
        """
        pool = thinpool_fixture

        assert pool.tdata is not None
        assert pool.tdata.report is not None
        data_stripe_size = pool.tdata.report.stripe_size
        assert data_stripe_size
        assert data_stripe_size.strip() == expected_stripe_size

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [
            {'stripes': '2', 'stripesize': '4', 'size': '8M', 'pool_name': 'pool_4'},
            {'stripes': '2', 'stripesize': '8', 'size': '8M', 'pool_name': 'pool_8'},
            {'stripes': '2', 'stripesize': '16', 'size': '8M', 'pool_name': 'pool_16'},
            {'stripes': '2', 'stripesize': '32', 'size': '8M', 'pool_name': 'pool_32'},
            {'stripes': '2', 'stripesize': '64', 'size': '8M', 'pool_name': 'pool_64'},
            {'stripes': '2', 'stripesize': '128', 'size': '8M', 'pool_name': 'pool_128'},
            {'stripes': '2', 'stripesize': '256', 'size': '8M', 'pool_name': 'pool_256'},
            {'stripes': '2', 'stripesize': '512', 'size': '8M', 'pool_name': 'pool_512'},
        ],
        indirect=True,
        ids=['4', '8', '16', '32', '64', '128', '256', '512'],
    )
    def test_stripe_size_validation_valid(self, thinpool_fixture: ThinPool) -> None:
        """Test stripe size validation with valid sizes (power of 2).

        Args:
            thinpool_fixture: Thin pool fixture with valid stripe size
        """
        # Just verify the pool was created successfully
        assert thinpool_fixture.tdata is not None

        # Cleanup handled by fixture

    @pytest.mark.parametrize('stripe_size', ['3', '5', '6', '7', '9', '10', '15'])
    def test_stripe_size_validation_invalid(self, setup_loopdev_vg: str, stripe_size: str) -> None:
        """Test stripe size validation with invalid sizes (not power of 2) - should fail.

        Args:
            setup_loopdev_vg: Volume group fixture
            stripe_size: Invalid stripe size to test
        """
        vg_name = setup_loopdev_vg

        pool = ThinPool(name='invalid1', vg=vg_name)
        assert not pool.create(stripes='2', stripesize=stripe_size, size='8M')

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'stripes': '2', 'stripesize': '4', 'size': '8M', 'pool_name': 'pool1'}],
        indirect=True,
    )
    def test_stripe_size_minimum(self, thinpool_fixture: ThinPool) -> None:
        """Test minimum stripe size (4k).

        Args:
            thinpool_fixture: Thin pool fixture with minimum stripe size
        """
        pool = thinpool_fixture

        assert pool.tdata is not None
        assert pool.tdata.report is not None
        data_stripe_size = pool.tdata.report.stripe_size
        assert data_stripe_size
        assert data_stripe_size.strip() == '4.00k'

        # Cleanup handled by fixture

    def test_stripe_size_too_small_fails(self, setup_loopdev_vg: str) -> None:
        """Test stripe size too small - should fail.

        Args:
            setup_loopdev_vg: Volume group fixture
        """
        vg_name = setup_loopdev_vg

        pool = ThinPool(name='pool2', vg=vg_name)
        assert not pool.create(stripes='2', stripesize='2', size='8M')

    @pytest.mark.parametrize(
        ('thinpool_fixture', 'expected_stripes', 'expected_stripe_size'),
        [
            (
                {'stripes': '2', 'stripesize': '64', 'size': '16M', 'pool_name': 'pool_2_64k'},
                '2',
                '64.00k',
            ),
            (
                {'stripes': '3', 'stripesize': '128', 'size': '24M', 'pool_name': 'pool_3_128k'},
                '3',
                '128.00k',
            ),
            (
                {'stripes': '4', 'stripesize': '256', 'size': '32M', 'pool_name': 'pool_4_256k'},
                '4',
                '256.00k',
            ),
        ],
        indirect=['thinpool_fixture'],
        ids=['2-stripes-64k', '3-stripes-128k', '4-stripes-256k'],
    )
    def test_combined_stripe_options(
        self,
        thinpool_fixture: ThinPool,
        expected_stripes: str,
        expected_stripe_size: str,
    ) -> None:
        """Test combining stripe count and stripe size options.

        Args:
            thinpool_fixture: Thin pool fixture with combined stripe options
            expected_stripes: Expected stripe count
            expected_stripe_size: Expected stripe size
        """
        pool = thinpool_fixture

        # Verify both stripe count and stripe size
        assert pool.tdata is not None
        assert pool.tdata.report is not None
        actual_stripes = pool.tdata.report.stripes
        assert actual_stripes
        assert actual_stripes == expected_stripes

        actual_stripe_size = pool.tdata.report.stripe_size
        assert actual_stripe_size
        assert actual_stripe_size.strip() == expected_stripe_size

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        ('thinpool_fixture', 'expected_stripes'),
        [
            ({'stripes': '2', 'extents': '10%VG', 'pool_name': 'pool_2_10vg'}, '2'),
            ({'stripes': '3', 'extents': '20%PVS', 'pool_name': 'pool_3_20pvs'}, '3'),
            ({'stripes': '4', 'extents': '30%FREE', 'pool_name': 'pool_4_30free'}, '4'),
        ],
        indirect=['thinpool_fixture'],
        ids=['2-stripes-10pct-vg', '3-stripes-20pct-pvs', '4-stripes-30pct-free'],
    )
    def test_stripe_with_percentage_size(self, thinpool_fixture: ThinPool, expected_stripes: str) -> None:
        """Test striping with percentage-based size allocation.

        Args:
            thinpool_fixture: Thin pool fixture with percentage-based size
            expected_stripes: Expected stripe count
        """
        pool = thinpool_fixture

        # Verify stripe count
        assert pool.tdata is not None
        assert pool.tdata.report is not None
        assert pool.tdata.report.stripes == expected_stripes

        # Cleanup handled by fixture
