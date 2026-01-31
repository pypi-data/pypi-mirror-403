# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for creating mirrored thin pools.

This module contains pytest tests for creating thin pools with RAID1 (mirroring)
for both data and metadata components.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest

from sts.utils.version import VersionInfo

if TYPE_CHECKING:
    from sts.lvm import ThinPool


@pytest.mark.parametrize('loop_devices', [{'count': 4, 'size_mb': 128}], indirect=True)
class TestLvcreateMirror:
    """Test cases for creating mirrored thin pools."""

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'size': '4M', 'pool_name': 'pool'}],
        indirect=True,
    )
    def test_mirror_thin_pool_data_and_metadata(self, thinpool_fixture: ThinPool, lvm2_version: VersionInfo) -> None:
        """Test converting thin pool data and metadata to RAID1 mirroring.

        Args:
            thinpool_fixture: Thin pool fixture
            lvm2_version: LVM2 version from fixture
        """
        pool = thinpool_fixture

        # Verify initial stripe count from pool report
        assert pool.report
        assert pool.report.data_stripes == '1', 'Pool data component should have 1 stripe initially'

        # Behavior changed in BZ1462712 - LV must be active to run lvconvert
        if lvm2_version >= VersionInfo.from_string('2.02.171-6'):
            # Deactivate pool and try to convert (should fail)
            assert pool.deactivate()

            # Try to convert inactive pool data component (should fail)
            success = pool.convert_pool_data(type='raid1', mirrors='3')
            assert not success, 'lvconvert should fail on inactive pool'

            # Reactivate pool
            assert pool.activate()
        else:
            # Old behavior - should work without activation
            # Try to convert with insufficient devices (should fail)
            success = pool.convert_pool_data(type='raid1', mirrors='3')
            assert not success, 'lvconvert should fail without enough devices'

            # Deactivate for next step
            assert pool.deactivate()

        # Convert data to RAID1 with 3 mirrors (4 total devices)
        assert pool.convert_pool_data(type='raid1', mirrors='3'), 'Failed to convert tdata to RAID1'

        # Wait for sync
        time.sleep(5)

        # Convert metadata to RAID1 with 1 mirror (2 total devices)
        assert pool.convert_pool_metadata(type='raid1', mirrors='1'), 'Failed to convert tmeta to RAID1'

        # Reactivate pool
        assert pool.activate()

        # Show final state using scan
        pool.scan()

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        ('thinpool_fixture', 'mirrors_count'),
        [
            ({'size': '4M', 'pool_name': 'pool_1'}, 1),
            ({'size': '4M', 'pool_name': 'pool_3'}, 3),
        ],
        indirect=['thinpool_fixture'],
        ids=['1-mirror-2-devices', '3-mirrors-4-devices'],
    )
    def test_mirror_thin_pool_data_various_counts(self, thinpool_fixture: ThinPool, mirrors_count: int) -> None:
        """Test converting thin pool data to RAID1 with different mirror counts.

        Args:
            thinpool_fixture: Thin pool fixture
            mirrors_count: Number of mirrors to create
        """
        pool = thinpool_fixture

        # Convert data to RAID1
        assert pool.convert_pool_data(type='raid1', mirrors=str(mirrors_count)), (
            f'Failed to convert tdata to RAID1 with {mirrors_count} mirrors'
        )

        # Wait for sync
        time.sleep(3)

        # Verify conversion
        pool.scan()
        assert pool.report

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'size': '4M', 'pool_name': 'pool_meta'}],
        indirect=True,
    )
    def test_mirror_thin_pool_metadata_only(self, thinpool_fixture: ThinPool) -> None:
        """Test converting only thin pool metadata to RAID1.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture

        # Convert only metadata to RAID1 with 1 mirror (2 total devices)
        assert pool.convert_pool_metadata(type='raid1', mirrors='1'), 'Failed to convert tmeta to RAID1'

        # Verify conversion
        pool.scan()
        assert pool.report

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [
            {'size': '4M', 'pool_name': 'pool_4M'},
            {'size': '8M', 'pool_name': 'pool_8M'},
            {'size': '16M', 'pool_name': 'pool_16M'},
        ],
        indirect=True,
        ids=['4M-pool', '8M-pool', '16M-pool'],
    )
    def test_mirror_thin_pool_various_sizes(self, thinpool_fixture: ThinPool) -> None:
        """Test creating and mirroring thin pools with various sizes.

        Args:
            thinpool_fixture: Thin pool fixture with various sizes
        """
        pool = thinpool_fixture

        # Convert data to RAID1 with 1 mirror (2 devices)
        assert pool.convert_pool_data(type='raid1', mirrors='1'), f'Failed to convert {pool.name} tdata to RAID1'

        # Wait for sync
        time.sleep(2)

        # Verify conversion
        pool.scan()
        assert pool.report

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [
            {
                'size': '16M',
                'pool_name': 'pool',
                'create_thin_volume': True,
                'thin_volume_name': 'thin1',
                'thin_volume_size': '100M',
            }
        ],
        indirect=True,
    )
    def test_mirror_thin_pool_with_thin_volumes(self, thinpool_fixture: ThinPool) -> None:
        """Test mirroring thin pool that contains thin volumes.

        Args:
            thinpool_fixture: Thin pool fixture with pre-created thin volume
        """
        pool = thinpool_fixture

        # Create additional thin volume (fixture already creates one)
        pool.create_thin_volume('thin2', virtualsize='100M')

        # Convert data to RAID1 with 1 mirror
        assert pool.convert_pool_data(type='raid1', mirrors='1'), (
            'Failed to convert pool data with thin volumes to RAID1'
        )

        # Wait for sync
        time.sleep(3)

        # Verify pool still works
        pool.scan()
        assert pool.report
        assert pool.get_thin_volume_count() == 2

        # Cleanup handled by fixture (removes thin volumes too)
