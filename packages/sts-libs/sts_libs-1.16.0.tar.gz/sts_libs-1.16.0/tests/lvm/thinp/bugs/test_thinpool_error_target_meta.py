# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""thin pool with error target meta device causes kernel panic.

This module contains pytest tests for verifying that setting the thin pool
metadata device to error target doesn't cause kernel panic.

"""

from __future__ import annotations

import logging
import time

import pytest

from sts.lvm import ThinPool
from sts.utils.cmdline import run


@pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 10240}], indirect=True)
class TestThinpoolErrorTargetMeta:
    """Error target metadata device."""

    @pytest.mark.slow
    def test_thinpool_error_target_metadata(self, setup_loopdev_vg: str) -> None:
        """Test that setting thin pool metadata to error target doesn't crash kernel.

        This test creates a thin pool, sets the metadata device to error target,
        and waits to ensure the system doesn't crash .

        Note: This test deliberately corrupts the pool metadata, so it uses
        dmsetup remove_all for cleanup instead of normal LVM removal.

        Args:
            setup_loopdev_vg: Volume group fixture
        """
        vg_name = setup_loopdev_vg
        pool_name = 'POOL'

        # Create thin pool using factory method
        # Note: Cannot use thinpool_fixture here because we deliberately corrupt
        # the pool metadata, which would cause fixture cleanup to fail
        pool = ThinPool.create_thin_pool(pool_name, vg_name, size='5G', poolmetadatasize='4M', zero='n')

        try:
            # Create thin volumes using ThinPool helper
            logging.info('Creating thin LVs')
            origin_lv = pool.create_thin_volume('origin', virtualsize='1G')
            assert origin_lv is not None, 'Failed to create origin thin volume'

            other1_lv = pool.create_thin_volume('other1', virtualsize='1G')
            assert other1_lv is not None, 'Failed to create other1 thin volume'

            # Create snapshot of origin
            snap1_lv = origin_lv.create_snapshot('snap1')
            assert snap1_lv is not None, 'Failed to create snapshot'

            # Display LVs
            logging.info('Displaying LVs')
            run(f'lvs -a -o +devices {vg_name}')

            # Get metadata device name from ThinPool
            assert pool.tmeta is not None, 'tmeta not available'
            dm_dev = f'{vg_name}-{pool_name}_tmeta'

            # Show current dmsetup table
            run('dmsetup table | grep tmeta')

            # Set metadata device to error target
            logging.info(f'Going to set {dm_dev} to error')
            result = run(f'dmsetup wipe_table {dm_dev}')
            if not result.succeeded:
                # Try alternative method if wipe_table fails
                result = run(f'dmsetup table {dm_dev}')
                if result.succeeded:
                    # Get device size from existing table
                    table_info = result.stdout.strip().split()
                    if len(table_info) >= 2:
                        device_size = table_info[1]
                        # Load error target
                        result = run(f'echo "0 {device_size} error" | dmsetup load {dm_dev}')
                        assert result.succeeded, 'Failed to load error target'
                        result = run(f'dmsetup resume {dm_dev}')
                        assert result.succeeded, 'Failed to resume device with error target'

            # Display devices again (might show errors)
            logging.info('Going to display the devices now, it might show some errors')
            logging.info(run(f'lvs -a -o +devices {vg_name}').stdout)
            # Don't assert success here as errors are expected

            logging.info(run('dmsetup table | grep tmeta').stdout)

            # Rescan for PVs
            logging.info('Rescanning for PV')
            run('pvscan')

            # Wait to ensure system stability (BZ1305983 would fail here)
            logging.info('Waiting 5 mins to make sure system did not crash')
            logging.info('(This is the critical test - BZ1305983 would cause kernel panic here)')
            time.sleep(5 * 60)  # 5 minutes

            logging.info('System remained stable after metadata error target test')

        finally:
            # Cleanup - remove any failed devices
            # Note: Normal LVM cleanup won't work because metadata is corrupted
            logging.info('Cleaning up failed devices')
            run(f'dmsetup remove -f {vg_name}*')

            # Additional wait to ensure cleanup completed
            logging.info('Waiting additional time to ensure cleanup completed')
            time.sleep(60)  # 1 minute

            logging.info('Test completed - no kernel panic occurred')
