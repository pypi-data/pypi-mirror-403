# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Test for stripe blkdiscard functionality.

This module contains pytest tests for verifying that blkdiscard works
correctly on striped logical volumes.
"""

from __future__ import annotations

import contextlib
import logging
from pathlib import Path

import pytest

from sts.lvm import LogicalVolume
from sts.utils.cmdline import run


@pytest.mark.parametrize('loop_devices', [{'count': 4, 'size_mb': 40}], indirect=True)
class TestStripeBlkdiscard:
    """Test cases for stripe blkdiscard functionality."""

    def test_stripe_blkdiscard(self, setup_loopdev_vg: str) -> None:
        """Test that blkdiscard works on striped logical volumes.

        This test creates a striped LV using 100% of VG space across 2 stripes
        and verifies that blkdiscard command executes successfully.

        Args:
            setup_loopdev_vg: Volume group fixture
        """
        vg_name = setup_loopdev_vg
        lv_name = 'lv'

        lv = LogicalVolume(name=lv_name, vg=vg_name)

        try:
            logging.info('Starting striped LV blkdiscard test')

            # Create striped LV using 100% of VG space with 2 stripes
            assert lv.create(extents='100%VG', stripes='2'), 'Failed to create striped LV'

            # Verify the LV was created with correct stripe configuration
            assert lv.report is not None, 'LV report not available'
            assert lv.report.stripes == '2', f'Expected 2 stripes, got {lv.report.stripes}'

            # Run blkdiscard on the striped LV
            lv_device = Path(f'/dev/{vg_name}/{lv_name}')
            result = run(f'blkdiscard {lv_device}')
            assert result.succeeded, f'blkdiscard failed: {result.stderr}'

            logging.info('blkdiscard on striped LV completed successfully')

        finally:
            # Cleanup LV
            with contextlib.suppress(RuntimeError):
                lv.remove(force='', yes='')
