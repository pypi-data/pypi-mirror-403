# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for discard performance with thin provisioning.

This module contains pytest tests for measuring discard performance
and verifying mkfs behavior with large thin volumes.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

import pytest

from sts.utils.files import mkfs

if TYPE_CHECKING:
    from sts.lvm import ThinPool


@pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 4096}], indirect=True)
class TestDiscardPerf:
    """Test cases for discard performance with thin provisioning."""

    @pytest.mark.slow
    @pytest.mark.parametrize('thinpool_fixture', [{'size': '3G'}], indirect=True)
    @pytest.mark.parametrize(
        ('virtual_size', 'filesystem'),
        [
            ('1T', 'ext4'),
            ('2T', 'ext4'),
        ],
        ids=['1T-volume', '2T-volume'],
    )
    def test_discard_performance(self, thinpool_fixture: ThinPool, virtual_size: str, filesystem: str) -> None:
        """Test mkfs performance with and without discard on large thin volume.

        This test relates to BZ1404736 - hang on mkfs a 300T Thinp device.
        Uses large virtual sizes (1T-2T) to test how filesystems handle
        discard operations on very large thin volumes.

        Args:
            thinpool_fixture: Thin pool fixture
            virtual_size: Virtual size of the thin volume to create
            filesystem: Filesystem type to test
        """
        pool = thinpool_fixture

        # Create large thin volume
        lv = pool.create_thin_volume('discard', virtualsize=virtual_size)

        # Test 1: mkfs without discard
        # Using lazy_itable_init to reduce actual writes while still testing large volumes
        logging.info('Measuring time of mkfs without discard')
        no_discard_start_time = time.perf_counter()
        assert mkfs(lv.path, filesystem, '-F', '-E', 'nodiscard,lazy_itable_init=1,lazy_journal_init=1')
        no_discard_end_time = time.perf_counter()
        no_discard_duration = no_discard_end_time - no_discard_start_time
        logging.info(f'INFO: mkfs without discard took {no_discard_duration:.2f} seconds')

        # Remove and recreate LV for next test
        assert lv.remove(force='', yes='')
        lv = pool.create_thin_volume('discard', virtualsize=virtual_size)

        # Test 2: mkfs with discard (default behavior)
        # Using lazy init options to keep actual space usage reasonable
        logging.info('Measuring time of mkfs with discard')
        discard_start_time = time.perf_counter()
        assert mkfs(lv.path, filesystem, '-F', '-E', 'lazy_itable_init=1,lazy_journal_init=1')
        discard_end_time = time.perf_counter()
        discard_duration = discard_end_time - discard_start_time
        logging.info(f'INFO: mkfs with discard took {discard_duration:.2f} seconds')

        # Performance comparison
        ratio = discard_duration / no_discard_duration if no_discard_duration > 0 else 0
        logging.info(f'INFO: Performance ratio (discard/no-discard): {ratio:.2f}')

        # Verify both operations completed (no hang)
        assert no_discard_duration > 0, 'mkfs without discard should complete'
        assert discard_duration > 0, 'mkfs with discard should complete'

        # Sanity check - neither should take more than reasonable time (e.g., 5 minutes)
        assert no_discard_duration < 300, 'mkfs without discard took too long'
        assert discard_duration < 300, 'mkfs with discard took too long (possible hang)'

    @pytest.mark.parametrize(
        ('thinpool_fixture', 'filesystem', 'virtual_size'),
        [
            ({'size': '200M'}, 'ext4', '1G'),
            ({'size': '400M'}, 'ext4', '2G'),
            ({'size': '200M'}, 'xfs', '1G'),
        ],
        indirect=['thinpool_fixture'],
        ids=['ext4-1G', 'ext4-2G', 'xfs-1G'],
    )
    def test_discard_options(self, thinpool_fixture: ThinPool, filesystem: str, virtual_size: str) -> None:
        """Test different discard options with mkfs.

        Args:
            thinpool_fixture: Thin pool fixture
            filesystem: Filesystem type to test
            virtual_size: Virtual size of the thin volume to create
        """
        pool = thinpool_fixture

        # Create thin volume
        lv = pool.create_thin_volume('lv1', virtualsize=virtual_size)

        # Test filesystem with explicit nodiscard
        start_time = time.perf_counter()
        if filesystem == 'ext4':
            assert mkfs(lv.path, filesystem, '-F', '-E', 'nodiscard')
        else:  # xfs
            assert mkfs(lv.path, filesystem, '-K', force=True)
        nodiscard_time = time.perf_counter() - start_time
        logging.info(f'{filesystem} nodiscard time: {nodiscard_time:.2f}s')

        # Test filesystem with default (discard enabled)
        start_time = time.perf_counter()
        assert mkfs(lv.path, filesystem, force=True)
        discard_time = time.perf_counter() - start_time
        logging.info(f'{filesystem} discard time: {discard_time:.2f}s')

        # Verify both completed successfully
        assert nodiscard_time > 0
        assert discard_time > 0

    @pytest.mark.parametrize('thinpool_fixture', [{'size': '600M'}], indirect=True)
    @pytest.mark.parametrize(
        'volume_count',
        [2, 3],
        ids=['two-volumes', 'three-volumes'],
    )
    def test_discard_with_multiple_volumes(self, thinpool_fixture: ThinPool, volume_count: int) -> None:
        """Test discard behavior with multiple thin volumes.

        Args:
            thinpool_fixture: Thin pool fixture
            volume_count: Number of thin volumes to create
        """
        pool = thinpool_fixture

        # Create and format multiple volumes
        timings = []
        for i in range(volume_count):
            lv = pool.create_thin_volume(f'lv{i}', virtualsize='1G')

            # Format with discard enabled
            start_time = time.perf_counter()
            assert mkfs(lv.path, 'ext4', force=True)
            elapsed = time.perf_counter() - start_time
            timings.append(elapsed)
            logging.info(f'mkfs on lv{i} took {elapsed:.2f}s')

        # Verify all operations completed
        assert len(timings) == volume_count
        assert all(t > 0 for t in timings)

        # Log average time
        avg_time = sum(timings) / len(timings)
        logging.info(f'Average mkfs time across {volume_count} volumes: {avg_time:.2f}s')

        # Cleanup handled by fixture

    @pytest.mark.parametrize('thinpool_fixture', [{'size': '600M'}], indirect=True)
    def test_discard_comparison_by_filesystem(self, thinpool_fixture: ThinPool) -> None:
        """Compare discard performance across different filesystems.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture

        filesystems = ['ext4', 'xfs']
        results = {}

        for fs in filesystems:
            # Create thin volume for this filesystem
            lv = pool.create_thin_volume(f'{fs}_lv', virtualsize='1G')

            # Test nodiscard
            start_time = time.perf_counter()
            if fs == 'ext4':
                assert mkfs(lv.path, fs, '-F', '-E', 'nodiscard')
            else:  # xfs
                assert mkfs(lv.path, fs, '-K', force=True)
            nodiscard_time = time.perf_counter() - start_time

            # Test with discard
            start_time = time.perf_counter()
            assert mkfs(lv.path, fs, force=True)
            discard_time = time.perf_counter() - start_time

            results[fs] = {
                'nodiscard': nodiscard_time,
                'discard': discard_time,
                'ratio': discard_time / nodiscard_time if nodiscard_time > 0 else 0,
            }

            logging.info(
                f'{fs}: nodiscard={nodiscard_time:.2f}s, discard={discard_time:.2f}s, ratio={results[fs]["ratio"]:.2f}'
            )

        # Verify all operations completed
        for fs, timing in results.items():
            assert timing['nodiscard'] > 0, f'{fs} nodiscard should complete'
            assert timing['discard'] > 0, f'{fs} discard should complete'
