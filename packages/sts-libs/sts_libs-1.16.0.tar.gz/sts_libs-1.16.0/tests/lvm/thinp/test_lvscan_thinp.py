# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for lvscan command with thin provisioning.

This module contains pytest tests for the lvscan command showing information
about thin pools, thin volumes, and snapshots.
"""

from __future__ import annotations

import contextlib
import json

import pytest

from sts.lvm import ThinPool


@pytest.mark.parametrize('loop_devices', [{'count': 4, 'size_mb': 128}], indirect=True)
class TestLvscanThinp:
    """Test cases for lvscan command with thin provisioning."""

    def _parse_lvscan_json(self, json_output: str, target_vg: str) -> dict[str, dict]:
        """Parse lvscan JSON output and extract LV information for the target VG.

        Args:
            json_output: JSON output from lvscan --reportformat json
            target_vg: Volume group name to filter by

        Returns:
            Dictionary mapping LV names to their information (status, message, device_path)
        """
        scan_data = json.loads(json_output)
        log_entries = scan_data.get('log', [])

        lv_info = {}
        for entry in log_entries:
            if entry.get('log_object_type') == 'lv':
                lv_name = entry.get('log_object_name')
                vg_name_from_log = entry.get('log_object_group')
                message = entry.get('log_message', '')

                if vg_name_from_log == target_vg:
                    # Extract status from message (ACTIVE or inactive)
                    status = 'ACTIVE' if 'ACTIVE' in message else 'inactive'
                    lv_info[lv_name] = {
                        'status': status,
                        'message': message,
                        'device_path': f'/dev/{target_vg}/{lv_name}',
                    }

        return lv_info

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'size': '40M', 'pool_name': 'pool'}],
        indirect=True,
    )
    @pytest.mark.parametrize(
        'snapshot_count',
        [1, 2],
        ids=['one-snapshot', 'two-snapshots'],
    )
    def test_lvscan_thin_volumes(self, thinpool_fixture: ThinPool, snapshot_count: int) -> None:
        """Test lvscan command with thin pools, volumes, and snapshots.

        Args:
            thinpool_fixture: Thin pool fixture
            snapshot_count: Number of snapshots to create
        """
        pool = thinpool_fixture
        assert pool.vg is not None
        vg_name = pool.vg

        # Create thin volume
        thin_lv = pool.create_thin_volume('lv1', virtualsize='100M')

        # Create snapshot chain
        snapshots = []
        prev_lv = thin_lv
        for i in range(1, snapshot_count + 1):
            snap = prev_lv.create_snapshot(f'snap{i}')
            assert snap is not None
            snapshots.append(snap)
            prev_lv = snap

        # Run lvscan with JSON format
        result = pool.scan('--reportformat', 'json')
        assert result.succeeded

        # Parse JSON output to extract LV information
        lv_info = self._parse_lvscan_json(result.stdout, vg_name)

        # Verify expected volumes and their states
        assert 'pool' in lv_info, 'Pool should appear in lvscan'
        assert lv_info['pool']['status'] == 'ACTIVE', 'Pool should be ACTIVE'

        assert 'lv1' in lv_info, 'Thin volume should appear in lvscan'
        assert lv_info['lv1']['status'] == 'ACTIVE', 'Thin volume should be ACTIVE'

        # Verify all snapshots appear as inactive
        for i in range(1, snapshot_count + 1):
            snap_name = f'snap{i}'
            assert snap_name in lv_info, f'{snap_name} should appear in lvscan'
            assert lv_info[snap_name]['status'] == 'inactive', f'{snap_name} should be inactive'

        # Hidden tdata and tmeta volumes should NOT appear in regular lvscan
        assert 'pool_tdata' not in lv_info, 'pool_tdata should not appear in regular lvscan'
        assert 'pool_tmeta' not in lv_info, 'pool_tmeta should not appear in regular lvscan'

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'pool_size',
        ['40M', '80M'],
        ids=['40M-pool', '80M-pool'],
    )
    def test_lvscan_all_volumes(self, setup_loopdev_vg: str, pool_size: str) -> None:
        """Test lvscan -a command showing all volumes including hidden ones.

        Args:
            setup_loopdev_vg: Volume group fixture
            pool_size: Size of the thin pool to create
        """
        vg_name = setup_loopdev_vg

        pool: ThinPool | None = None
        try:
            # Create thin pool and volume
            pool = ThinPool.create_thin_pool('pool', vg_name, size=pool_size)
            pool.create_thin_volume('lv1', virtualsize='100M')

            # Run lvscan -a with JSON format to show hidden volumes
            result = pool.scan('-a', '--reportformat', 'json')
            assert result.succeeded

            # Parse JSON output to extract LV information
            lv_info = self._parse_lvscan_json(result.stdout, vg_name)

            # With -a flag, hidden volumes should appear
            assert 'pool_tdata' in lv_info, 'pool_tdata should appear in lvscan -a'
            assert lv_info['pool_tdata']['status'] == 'ACTIVE', 'pool_tdata should be ACTIVE'

            assert 'pool_tmeta' in lv_info, 'pool_tmeta should appear in lvscan -a'
            assert lv_info['pool_tmeta']['status'] == 'ACTIVE', 'pool_tmeta should be ACTIVE'

            assert 'pool' in lv_info, 'pool should appear in lvscan -a'
            assert lv_info['pool']['status'] == 'ACTIVE', 'pool should be ACTIVE'

            assert 'lv1' in lv_info, 'lv1 should appear in lvscan -a'
            assert lv_info['lv1']['status'] == 'ACTIVE', 'lv1 should be ACTIVE'

            # Cleanup
            assert pool.remove_with_thin_volumes()
            pool = None
        finally:
            if pool:
                with contextlib.suppress(RuntimeError):
                    pool.remove_with_thin_volumes()

    def test_lvscan_multiple_pools(self, setup_loopdev_vg: str) -> None:
        """Test lvscan command with multiple thin pools.

        Args:
            setup_loopdev_vg: Volume group fixture
        """
        vg_name = setup_loopdev_vg

        pool1: ThinPool | None = None
        pool2: ThinPool | None = None
        try:
            # Create multiple pools with volumes
            pool1 = ThinPool.create_thin_pool('pool1', vg_name, size='40M')
            pool1.create_thin_volume('lv1', virtualsize='100M')

            pool2 = ThinPool.create_thin_pool('pool2', vg_name, size='40M')
            pool2.create_thin_volume('lv2', virtualsize='100M')

            # Run lvscan with JSON format
            result = pool1.scan('--reportformat', 'json')
            assert result.succeeded

            # Parse JSON output
            lv_info = self._parse_lvscan_json(result.stdout, vg_name)

            # Verify all pools and volumes appear
            assert 'pool1' in lv_info, 'pool1 should appear in lvscan'
            assert lv_info['pool1']['status'] == 'ACTIVE'

            assert 'pool2' in lv_info, 'pool2 should appear in lvscan'
            assert lv_info['pool2']['status'] == 'ACTIVE'

            assert 'lv1' in lv_info, 'lv1 should appear in lvscan'
            assert lv_info['lv1']['status'] == 'ACTIVE'

            assert 'lv2' in lv_info, 'lv2 should appear in lvscan'
            assert lv_info['lv2']['status'] == 'ACTIVE'

            # Cleanup
            assert pool1.remove_with_thin_volumes()
            pool1 = None
            assert pool2.remove_with_thin_volumes()
            pool2 = None
        finally:
            if pool1:
                with contextlib.suppress(RuntimeError):
                    pool1.remove_with_thin_volumes()
            if pool2:
                with contextlib.suppress(RuntimeError):
                    pool2.remove_with_thin_volumes()

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'size': '40M', 'pool_name': 'pool'}],
        indirect=True,
    )
    @pytest.mark.parametrize(
        'report_format',
        ['json', 'json_std'],
        ids=['json-format', 'json-std-format'],
    )
    def test_lvscan_report_formats(self, thinpool_fixture: ThinPool, report_format: str) -> None:
        """Test lvscan command with different report formats.

        Args:
            thinpool_fixture: Thin pool fixture
            report_format: Report format to test
        """
        pool = thinpool_fixture
        assert pool.vg is not None
        vg_name = pool.vg

        # Create thin volume
        pool.create_thin_volume('lv1', virtualsize='100M')

        # Run lvscan with specified report format
        result = pool.scan('--reportformat', report_format)
        assert result.succeeded

        # Verify JSON output is parseable
        lv_info = self._parse_lvscan_json(result.stdout, vg_name)
        assert 'pool' in lv_info
        assert 'lv1' in lv_info

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'size': '100M', 'pool_name': 'pool'}],
        indirect=True,
    )
    @pytest.mark.parametrize(
        'volume_count',
        [1, 2, 3],
        ids=['one-volume', 'two-volumes', 'three-volumes'],
    )
    def test_lvscan_multiple_thin_volumes(self, thinpool_fixture: ThinPool, volume_count: int) -> None:
        """Test lvscan with multiple thin volumes in same pool.

        Args:
            thinpool_fixture: Thin pool fixture
            volume_count: Number of thin volumes to create
        """
        pool = thinpool_fixture
        assert pool.vg is not None
        vg_name = pool.vg

        # Create multiple thin volumes
        for i in range(1, volume_count + 1):
            pool.create_thin_volume(f'lv{i}', virtualsize='100M')

        # Run lvscan with JSON format
        result = pool.scan('--reportformat', 'json')
        assert result.succeeded

        # Parse and verify all volumes appear
        lv_info = self._parse_lvscan_json(result.stdout, vg_name)
        assert 'pool' in lv_info

        for i in range(1, volume_count + 1):
            lv_name = f'lv{i}'
            assert lv_name in lv_info, f'{lv_name} should appear in lvscan'
            assert lv_info[lv_name]['status'] == 'ACTIVE'

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'size': '40M', 'pool_name': 'pool'}],
        indirect=True,
    )
    def test_lvscan_with_inactive_volumes(self, thinpool_fixture: ThinPool) -> None:
        """Test lvscan command with inactive thin volumes.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture
        assert pool.vg is not None
        vg_name = pool.vg

        # Create thin volume and snapshot
        lv1 = pool.create_thin_volume('lv1', virtualsize='100M')
        snap1 = lv1.create_snapshot('snap1')
        assert snap1 is not None

        # Run lvscan
        result = pool.scan('--reportformat', 'json')
        assert result.succeeded

        # Parse and verify
        lv_info = self._parse_lvscan_json(result.stdout, vg_name)

        # lv1 should be active, snap1 should be inactive
        assert lv_info['lv1']['status'] == 'ACTIVE'
        assert lv_info['snap1']['status'] == 'inactive'

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'stripes',
        [None, '2'],
        ids=['linear-pool', 'striped-pool'],
    )
    def test_lvscan_striped_pools(self, setup_loopdev_vg: str, stripes: str | None) -> None:
        """Test lvscan with linear and striped thin pools.

        Args:
            setup_loopdev_vg: Volume group fixture
            stripes: Number of stripes (None for linear)
        """
        vg_name = setup_loopdev_vg

        pool: ThinPool | None = None
        try:
            # Create pool with specified striping
            pool_name = f'pool_{"linear" if stripes is None else "striped"}'
            if stripes:
                pool = ThinPool.create_thin_pool(pool_name, vg_name, size='40M', stripes=stripes)
            else:
                pool = ThinPool.create_thin_pool(pool_name, vg_name, size='40M')

            pool.create_thin_volume('lv1', virtualsize='100M')

            # Run lvscan
            result = pool.scan('--reportformat', 'json')
            assert result.succeeded

            # Parse and verify
            lv_info = self._parse_lvscan_json(result.stdout, vg_name)
            assert pool_name in lv_info
            assert lv_info[pool_name]['status'] == 'ACTIVE'
            assert 'lv1' in lv_info
            assert lv_info['lv1']['status'] == 'ACTIVE'

            # Cleanup
            assert pool.remove_with_thin_volumes()
            pool = None
        finally:
            if pool:
                with contextlib.suppress(RuntimeError):
                    pool.remove_with_thin_volumes()
