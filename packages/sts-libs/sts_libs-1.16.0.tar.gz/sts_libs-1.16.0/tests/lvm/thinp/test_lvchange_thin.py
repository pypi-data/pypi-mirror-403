# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for lvchange thin provisioning operations.

This module contains pytest tests for lvchange command with thin provisioning,
focusing on changing thin pool and thin volume attributes.
"""

from __future__ import annotations

import pytest

from sts.lvm import ThinPool


@pytest.mark.parametrize('loop_devices', [{'count': 4, 'size_mb': 512}], indirect=True)
class TestLvchangeThin:
    """Test cases for lvchange thin provisioning operations."""

    @pytest.mark.parametrize(
        ('thinpool_fixture', 'to_discard'),
        [
            (
                {'size': '50M', 'pool_name': 'pool1', 'discards': 'passdown', 'create_thin_volume': True},
                'nopassdown',
            ),
            (
                {'size': '50M', 'pool_name': 'pool1', 'discards': 'nopassdown', 'create_thin_volume': True},
                'passdown',
            ),
        ],
        indirect=['thinpool_fixture'],
        ids=['passdown->nopassdown', 'nopassdown->passdown'],
    )
    def test_pool_discards_active_allowed(self, thinpool_fixture: ThinPool, to_discard: str) -> None:
        """Test allowed discard transitions with active pool.

        The transitions passdown <-> nopassdown are allowed on active pools.

        Args:
            thinpool_fixture: Thin pool fixture with initial discards setting and thin volume
            to_discard: Target discard setting to change to
        """
        pool = thinpool_fixture
        from_discard = pool.report.discards if pool.report else 'unknown'

        # Verify initial state
        assert pool.report
        assert pool.report.discards in ['passdown', 'nopassdown']

        # Change discard setting - should succeed
        assert pool.change_discards(discards=to_discard)

        # Verify final state
        assert pool.report.discards == to_discard, (
            f'Expected {to_discard}, got {pool.report.discards} (was {from_discard})'
        )

    @pytest.mark.parametrize(
        ('thinpool_fixture', 'to_discard'),
        [
            (
                {'size': '50M', 'pool_name': 'pool1', 'discards': 'passdown', 'create_thin_volume': True},
                'ignore',
            ),
            (
                {'size': '50M', 'pool_name': 'pool1', 'discards': 'nopassdown', 'create_thin_volume': True},
                'ignore',
            ),
        ],
        indirect=['thinpool_fixture'],
        ids=['passdown->ignore', 'nopassdown->ignore'],
    )
    def test_pool_discards_active_forbidden(self, thinpool_fixture: ThinPool, to_discard: str) -> None:
        """Test forbidden discard transitions with active pool.

        Transitions involving 'ignore' are not allowed when the pool is active.

        Args:
            thinpool_fixture: Thin pool fixture with initial discards setting and thin volume
            to_discard: Target discard setting (should fail)
        """
        pool = thinpool_fixture

        # Verify initial state
        assert pool.report
        from_discard = pool.report.discards

        # Try to change discard setting - should fail
        assert not pool.change_discards(discards=to_discard)

        # Verify state unchanged
        assert pool.report.discards == from_discard

    @pytest.mark.parametrize(
        ('thinpool_fixture', 'to_discard'),
        [
            ({'size': '50M', 'pool_name': 'pool1', 'discards': 'passdown', 'create_thin_volume': True}, 'ignore'),
            ({'size': '50M', 'pool_name': 'pool1', 'discards': 'passdown', 'create_thin_volume': True}, 'nopassdown'),
            ({'size': '50M', 'pool_name': 'pool1', 'discards': 'nopassdown', 'create_thin_volume': True}, 'ignore'),
            ({'size': '50M', 'pool_name': 'pool1', 'discards': 'nopassdown', 'create_thin_volume': True}, 'passdown'),
            ({'size': '50M', 'pool_name': 'pool1', 'discards': 'ignore', 'create_thin_volume': True}, 'nopassdown'),
            ({'size': '50M', 'pool_name': 'pool1', 'discards': 'ignore', 'create_thin_volume': True}, 'passdown'),
        ],
        indirect=['thinpool_fixture'],
        ids=[
            'passdown->ignore',
            'passdown->nopassdown',
            'nopassdown->ignore',
            'nopassdown->passdown',
            'ignore->nopassdown',
            'ignore->passdown',
        ],
    )
    def test_pool_discards_inactive(self, thinpool_fixture: ThinPool, to_discard: str) -> None:
        """Test changing discards with inactive pool and inactive thin volume.

        Validates that all discard mode transitions are allowed when the pool
        is inactive. This provides more flexibility for configuration changes.

        Args:
            thinpool_fixture: Thin pool fixture with initial discards setting and thin volume
            to_discard: Target discard setting to change to
        """
        pool = thinpool_fixture

        # Get thin volume from pool (thin_volumes is populated by create_thin_volume)
        assert pool.thin_volumes, 'Expected at least one thin volume'
        thin_lv = pool.thin_volumes[0]

        # Deactivate pool and thin volume
        assert thin_lv.deactivate()
        assert pool.deactivate()

        # Verify initial state
        assert pool.report
        from_discard = pool.report.discards

        # Change discard setting (should succeed when inactive)
        assert pool.change_discards(discards=to_discard)

        # Activate and verify
        assert pool.activate()
        assert thin_lv.activate()

        # Verify final state
        assert pool.report.discards == to_discard, (
            f'Expected {to_discard}, got {pool.report.discards} (was {from_discard})'
        )

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'size': '100M', 'pool_name': 'pool'}],
        indirect=True,
    )
    @pytest.mark.parametrize('num_volumes', [3, 5], ids=['3-volumes', '5-volumes'])
    def test_thin_lv_activation(self, thinpool_fixture: ThinPool, num_volumes: int) -> None:
        """Test activation and deactivation of multiple thin volumes.

        Args:
            thinpool_fixture: Thin pool fixture
            num_volumes: Number of thin volumes to create and test
        """
        pool = thinpool_fixture

        # Create multiple thin volumes and test activation/deactivation
        for i in range(1, num_volumes + 1):
            lv_name = f'lv{i}'
            thin_lv = pool.create_thin_volume(lv_name, virtualsize='50M')

            # Test activation/deactivation immediately
            assert thin_lv.deactivate()
            assert thin_lv.activate()

    def test_pool_activation(self, thin_pool_with_volume: dict) -> None:
        """Test activation and deactivation of thin pools.

        Args:
            thin_pool_with_volume: Fixture providing pool and thin volume
        """
        pool = thin_pool_with_volume['pool']
        thin_lv = thin_pool_with_volume['thin_lv']

        # Test pool activation/deactivation
        # Deactivate thin volume first
        assert thin_lv.deactivate()

        # Deactivate pool
        assert pool.deactivate()

        # Activate pool
        assert pool.activate()

        # Activate thin volume
        assert thin_lv.activate()

    @pytest.mark.parametrize(
        ('thinpool_fixture', 'new_discards'),
        [
            ({'size': '100M', 'pool_name': 'pool', 'discards': 'nopassdown'}, 'passdown'),
            ({'size': '100M', 'pool_name': 'pool', 'discards': 'nopassdown'}, 'ignore'),
            ({'size': '100M', 'pool_name': 'pool', 'discards': 'passdown'}, 'nopassdown'),
            ({'size': '100M', 'pool_name': 'pool', 'discards': 'ignore'}, 'passdown'),
        ],
        indirect=['thinpool_fixture'],
        ids=['nopassdown->passdown', 'nopassdown->ignore', 'passdown->nopassdown', 'ignore->passdown'],
    )
    def test_pool_attribute_verification(self, thinpool_fixture: ThinPool, new_discards: str) -> None:
        """Test verification of thin pool attributes with various discard settings.

        Args:
            thinpool_fixture: Thin pool fixture with initial discards setting
            new_discards: New discard setting to change to
        """
        pool = thinpool_fixture

        # Verify initial state
        assert pool.report
        initial_discards = pool.report.discards

        # Determine if deactivation is needed for this transition
        needs_deactivation = (initial_discards in ['passdown', 'nopassdown'] and new_discards == 'ignore') or (
            initial_discards == 'ignore' and new_discards in ['passdown', 'nopassdown']
        )

        # Change to new value (may require deactivation depending on values)
        if needs_deactivation:
            # Need to deactivate for transitions involving 'ignore'
            assert pool.deactivate()
            assert pool.change_discards(discards=new_discards)
            assert pool.activate()
        else:
            # Can change while active
            assert pool.change_discards(discards=new_discards)

        # Verify new state
        assert pool.report.discards == new_discards

    def test_multiple_pools_concurrent(self, multiple_thin_pools: list[ThinPool]) -> None:
        """Test operations on multiple pools concurrently.

        Args:
            multiple_thin_pools: Fixture providing list of thin pools with volumes
        """
        # Test operations on each pool
        for pool in multiple_thin_pools:
            # Test changing discards
            assert pool.change_discards(discards='nopassdown')
            # Check discards setting using report data directly
            assert pool.report
            assert pool.report.discards == 'nopassdown'

            # Test changing back
            assert pool.change_discards(discards='passdown')
            assert pool.report.discards == 'passdown'

    @pytest.mark.parametrize(
        ('pool_count', 'pool_size'),
        [
            (2, '50M'),
            (3, '30M'),
        ],
        ids=['2-pools-50M', '3-pools-30M'],
    )
    def test_multiple_pools_with_sizes(self, setup_loopdev_vg: str, pool_count: int, pool_size: str) -> None:
        """Test operations on multiple pools with different configurations.

        Note: This test creates multiple pools inline as the fixture pattern doesn't
        easily support dynamic pool counts. The cleanup is handled explicitly.

        Args:
            setup_loopdev_vg: Volume group fixture
            pool_count: Number of pools to create
            pool_size: Size of each pool
        """
        vg_name = setup_loopdev_vg
        pools: list[ThinPool] = []

        try:
            # Create multiple pools with thin volumes
            for i in range(1, pool_count + 1):
                pool_name = f'pool{i}'
                lv_name = f'lv{i}'

                pool = ThinPool.create_thin_pool(pool_name, vg_name, size=pool_size)
                pools.append(pool)

                # Create thin volume in each pool
                pool.create_thin_volume(lv_name, virtualsize='100M')

                # Test operations on the pool immediately
                assert pool.change_discards(discards='nopassdown')
                assert pool.report
                assert pool.report.discards == 'nopassdown'
        finally:
            # Clean up
            for pool in pools:
                pool.remove_with_thin_volumes()
