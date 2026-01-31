# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for thin provisioning performance.

This module contains pytest tests for comparing performance between
thin logical volumes and regular logical volumes.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

import pytest

from sts.utils.cmdline import run

if TYPE_CHECKING:
    from sts.lvm import ThinPool


class TestThinPerf:
    """Test cases for thin provisioning performance comparisons."""

    @pytest.mark.slow
    @pytest.mark.parametrize('loop_devices', [{'count': 4, 'size_mb': 512}], indirect=True)
    def test_thin_vs_regular_performance(self, mounted_thin_and_regular_lvs: dict[str, Any]) -> None:
        """Test performance comparison between thin and regular LVs.

        This test relates to BZ1405437 - Performance degradation on thin logical volumes.

        Args:
            mounted_thin_and_regular_lvs: Fixture providing mounted thin and regular LVs
        """
        thin_lv_mnt = mounted_thin_and_regular_lvs['thin_lv_mnt']
        regular_lv_mnt = mounted_thin_and_regular_lvs['regular_lv_mnt']

        # Test write performance
        logging.info('Testing write performance')

        # Write to thin LV
        thin_write_start = time.perf_counter()
        result = run(f'dd if=/dev/zero of={thin_lv_mnt!s}/testfile bs=1M count=100 conv=fsync')
        assert result.succeeded
        thin_write_time = time.perf_counter() - thin_write_start

        # Write to regular LV
        regular_write_start = time.perf_counter()
        result = run(f'dd if=/dev/zero of={regular_lv_mnt!s}/testfile bs=1M count=100 conv=fsync')
        assert result.succeeded
        regular_write_time = time.perf_counter() - regular_write_start

        logging.info(f'Thin LV write time: {thin_write_time:.2f}s')
        logging.info(f'Regular LV write time: {regular_write_time:.2f}s')
        logging.info(f'Performance ratio (thin/regular): {thin_write_time / regular_write_time:.2f}')

        # Test read performance
        logging.info('Testing read performance')

        # Clear cache
        run('echo 3 > /proc/sys/vm/drop_caches')

        # Read from thin LV
        thin_read_start = time.perf_counter()
        result = run(f'dd if={thin_lv_mnt!s}/testfile of=/dev/null bs=1M')
        assert result.succeeded
        thin_read_time = time.perf_counter() - thin_read_start

        # Clear cache
        run('echo 3 > /proc/sys/vm/drop_caches')

        # Read from regular LV
        regular_read_start = time.perf_counter()
        result = run(f'dd if={regular_lv_mnt!s}/testfile of=/dev/null bs=1M')
        assert result.succeeded
        regular_read_time = time.perf_counter() - regular_read_start

        logging.info(f'Thin LV read time: {thin_read_time:.2f}s')
        logging.info(f'Regular LV read time: {regular_read_time:.2f}s')
        logging.info(f'Performance ratio (thin/regular): {thin_read_time / regular_read_time:.2f}')

        # Performance assertions - thin shouldn't be dramatically slower
        # Allow some overhead but flag if it's excessive (e.g., > 3x slower)
        assert thin_write_time < regular_write_time * 3, (
            f'Thin LV write performance too slow: {thin_write_time:.2f}s vs {regular_write_time:.2f}s'
        )
        assert thin_read_time < regular_read_time * 3, (
            f'Thin LV read performance too slow: {thin_read_time:.2f}s vs {regular_read_time:.2f}s'
        )

        # Test random I/O performance
        logging.info('Testing random I/O performance')

        # Random writes to thin LV
        thin_random_start = time.perf_counter()
        result = run(f'dd if=/dev/urandom of={thin_lv_mnt!s}/random bs=4k count=1000 conv=fsync')
        assert result.succeeded
        thin_random_time = time.perf_counter() - thin_random_start

        # Random writes to regular LV
        regular_random_start = time.perf_counter()
        result = run(f'dd if=/dev/urandom of={regular_lv_mnt!s}/random bs=4k count=1000 conv=fsync')
        assert result.succeeded
        regular_random_time = time.perf_counter() - regular_random_start

        logging.info(f'Thin LV random write time: {thin_random_time:.2f}s')
        logging.info(f'Regular LV random write time: {regular_random_time:.2f}s')
        logging.info(f'Performance ratio (thin/regular): {thin_random_time / regular_random_time:.2f}')

        # Random I/O might show more overhead due to metadata updates
        assert thin_random_time < regular_random_time * 4, (
            f'Thin LV random I/O performance too slow: {thin_random_time:.2f}s vs {regular_random_time:.2f}s'
        )

    @pytest.mark.parametrize('loop_devices', [{'count': 4, 'size_mb': 512}], indirect=True)
    @pytest.mark.parametrize('thinpool_fixture', [{'size': '200M'}], indirect=True)
    def test_thin_metadata_performance(self, thinpool_fixture: ThinPool) -> None:
        """Test thin metadata operations performance.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture

        # Test creating many thin volumes
        logging.info('Testing thin volume creation performance')

        creation_start = time.perf_counter()
        thin_volumes = []

        # Create 50 thin volumes
        for i in range(50):
            lv_name = f'thin{i:02d}'
            thin_lv = pool.create_thin_volume(lv_name, virtualsize='10M')
            thin_volumes.append(thin_lv)

        creation_time = time.perf_counter() - creation_start
        logging.info(f'Created 50 thin volumes in {creation_time:.2f}s ({creation_time / 50:.3f}s per volume)')

        # Test removing many thin volumes
        removal_start = time.perf_counter()

        for thin_lv in thin_volumes:
            assert thin_lv.remove(force='', yes='')

        removal_time = time.perf_counter() - removal_start
        logging.info(f'Removed 50 thin volumes in {removal_time:.2f}s ({removal_time / 50:.3f}s per volume)')

        # Performance should be reasonable (< 1s per operation on average)
        assert creation_time / 50 < 1.0, f'Thin volume creation too slow: {creation_time / 50:.3f}s per volume'
        assert removal_time / 50 < 1.0, f'Thin volume removal too slow: {removal_time / 50:.3f}s per volume'
