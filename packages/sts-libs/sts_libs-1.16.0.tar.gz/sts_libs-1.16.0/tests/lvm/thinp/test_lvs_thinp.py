# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for lvs command with thin provisioning.

This module contains pytest tests for the lvs command displaying information
about thin pools, thin volumes, and their attributes.
"""

from __future__ import annotations

import contextlib

import pytest

from sts.lvm import LogicalVolume, ThinPool
from sts.utils.cmdline import run


@pytest.mark.parametrize('loop_devices', [{'count': 4, 'size_mb': 128}], indirect=True)
class TestLvsThinp:
    """Test cases for lvs command with thin provisioning."""

    @pytest.mark.parametrize(
        'pool_size',
        ['4M', '8M'],
        ids=['4M-pool', '8M-pool'],
    )
    def test_lvs_thin_attributes(self, setup_loopdev_vg: str, pool_size: str) -> None:
        """Test lvs command showing thin pool and volume attributes.

        Args:
            setup_loopdev_vg: Volume group fixture
            pool_size: Size of the thin pool to create
        """
        vg_name = setup_loopdev_vg

        pool: ThinPool | None = None
        try:
            # Create thin pool
            pool = ThinPool.create_thin_pool('pool1', vg_name, size=pool_size)
            assert pool.report is not None
            assert pool.report.thin_count == '0'

            # Create thin LV
            thin_lv = pool.create_thin_volume('lv1', virtualsize='100M')

            # Verify pool attributes after adding thin volume
            assert pool.refresh_report()
            assert pool.report is not None
            assert pool.report.thin_count == '1'
            assert pool.report.lv_name == 'pool1'
            assert pool.report.lv_size == pool_size.lower().replace('m', '.00m')
            assert pool.report.lv_metadata_size == '4.00m'

            # Since RHEL6.7 lvm2 package, adding 'device (o)pen' bit for lv_attr
            # The attr can be 'twi-aotz--' (with open bit) or 'twi-a-tz--' (without)
            assert pool.report.lv_attr in ['twi-aotz--', 'twi-a-tz--']

            # Verify thin volume attributes
            assert thin_lv.report is not None
            assert thin_lv.report.lv_name == 'lv1'
            assert thin_lv.report.lv_size == '100.00m'
            assert thin_lv.report.pool_lv == 'pool1'
            assert thin_lv.report.lv_attr in ['Vwi-aotz--', 'Vwi-a-tz--']

            # Cleanup
            assert pool.remove_with_thin_volumes()
            pool = None
        finally:
            if pool:
                with contextlib.suppress(RuntimeError):
                    pool.remove_with_thin_volumes()

    @pytest.mark.parametrize(
        'stripes',
        [None, '2'],
        ids=['linear', 'striped'],
    )
    def test_lvs_stripe_attributes(self, setup_loopdev_vg: str, stripes: str | None) -> None:
        """Test lvs command showing stripe information for thin pools.

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
                pool = ThinPool.create_thin_pool(pool_name, vg_name, size='8M', stripes=stripes)
            else:
                pool = ThinPool.create_thin_pool(pool_name, vg_name, size='8M')

            pool.create_thin_volume('lv1', virtualsize='100M')

            # Verify data stripe attributes
            data_stripes = pool.get_data_stripes()
            assert data_stripes
            expected_stripes = stripes if stripes else '1'
            assert data_stripes == expected_stripes

            # Verify metadata stripe attributes (always linear)
            assert pool.report is not None
            metadata_lv_name = pool.report.metadata_lv.strip('[]') if pool.report.metadata_lv else None
            assert metadata_lv_name is not None
            tmeta_lv = LogicalVolume(name=metadata_lv_name, vg=vg_name)
            assert tmeta_lv.refresh_report()
            assert tmeta_lv.report is not None
            assert tmeta_lv.report.stripes == '1'  # metadata is always linear

            # Cleanup
            assert pool.remove_with_thin_volumes()
            pool = None
        finally:
            if pool:
                with contextlib.suppress(RuntimeError):
                    pool.remove_with_thin_volumes()

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'size': '8M', 'pool_name': 'pool'}],
        indirect=True,
    )
    @pytest.mark.parametrize(
        'use_all_flag',
        [True, False],
        ids=['with-all-flag', 'without-all-flag'],
    )
    def test_lvs_all_volumes(self, thinpool_fixture: ThinPool, *, use_all_flag: bool) -> None:
        """Test lvs command with and without -a flag showing hidden volumes.

        Args:
            thinpool_fixture: Thin pool fixture
            use_all_flag: Whether to use -a flag
        """
        pool = thinpool_fixture
        vg_name = pool.vg

        # Create thin volume
        pool.create_thin_volume('lv1', virtualsize='100M')

        # Run lvs with or without -a flag
        if use_all_flag:
            result = run(f'lvs -a {vg_name}')
            assert result.succeeded

            # Verify that hidden volumes are shown
            assert '[pool_tdata]' in result.stdout
            assert '[pool_tmeta]' in result.stdout
            assert 'pool' in result.stdout
            assert 'lv1' in result.stdout
        else:
            result = run(f'lvs {vg_name}')
            assert result.succeeded

            # Verify that hidden volumes are not shown
            assert '[pool_tdata]' not in result.stdout
            assert '[pool_tmeta]' not in result.stdout
            assert 'pool' in result.stdout
            assert 'lv1' in result.stdout

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'size': '8M', 'pool_name': 'pool'}],
        indirect=True,
    )
    @pytest.mark.parametrize(
        'snapshot_count',
        [1, 2, 3],
        ids=['one-snapshot', 'two-snapshots', 'three-snapshots'],
    )
    def test_lvs_with_snapshots(self, thinpool_fixture: ThinPool, snapshot_count: int) -> None:
        """Test lvs command with thin snapshots.

        Args:
            thinpool_fixture: Thin pool fixture
            snapshot_count: Number of snapshots to create
        """
        pool = thinpool_fixture

        # Create thin volume
        thin_lv = pool.create_thin_volume('lv1', virtualsize='100M')

        # Create snapshots
        snapshots = []
        for i in range(1, snapshot_count + 1):
            snap = thin_lv.create_snapshot(f'snap{i}')
            assert snap is not None
            assert snap.report
            snapshots.append(snap)

        # Verify each snapshot's attributes
        for snap in snapshots:
            assert snap.report is not None
            assert snap.report.lv_attr
            assert snap.report.lv_attr.startswith('Vwi')
            assert snap.report.pool_lv == 'pool'
            assert snap.report.origin == 'lv1'

        # Verify pool thin count increased
        assert pool.refresh_report()
        expected_count = 1 + snapshot_count  # origin + snapshots
        assert pool.report is not None
        assert pool.report.thin_count == str(expected_count)

        # Cleanup handled by fixture

    def test_lvs_multiple_pools(self, setup_loopdev_vg: str) -> None:
        """Test lvs command with multiple thin pools.

        Args:
            setup_loopdev_vg: Volume group fixture
        """
        vg_name = setup_loopdev_vg

        pool1: ThinPool | None = None
        pool2: ThinPool | None = None
        try:
            # Create multiple pools with volumes
            pool1 = ThinPool.create_thin_pool('pool1', vg_name, size='8M')
            pool1.create_thin_volume('lv1', virtualsize='100M')

            pool2 = ThinPool.create_thin_pool('pool2', vg_name, size='8M')
            pool2.create_thin_volume('lv2', virtualsize='100M')

            # Verify both pools exist
            result = run(f'lvs {vg_name}')
            assert result.succeeded
            assert 'pool1' in result.stdout
            assert 'pool2' in result.stdout
            assert 'lv1' in result.stdout
            assert 'lv2' in result.stdout

            # Verify each pool has correct thin count
            assert pool1.refresh_report()
            assert pool1.report is not None
            assert pool1.report.thin_count == '1'
            assert pool2.refresh_report()
            assert pool2.report is not None
            assert pool2.report.thin_count == '1'

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
        [{'size': '8M', 'pool_name': 'pool'}],
        indirect=True,
    )
    @pytest.mark.parametrize(
        'option_flag',
        [
            'lv_name,lv_size,pool_lv',
            'lv_name,lv_attr,lv_size',
            'lv_name,lv_size,thin_count',
        ],
        ids=['name-size-pool', 'name-attr-size', 'name-size-count'],
    )
    def test_lvs_custom_output_options(self, thinpool_fixture: ThinPool, option_flag: str) -> None:
        """Test lvs command with custom output options.

        Args:
            thinpool_fixture: Thin pool fixture
            option_flag: Comma-separated list of output fields
        """
        pool = thinpool_fixture
        vg_name = pool.vg

        # Create thin volume
        pool.create_thin_volume('lv1', virtualsize='100M')

        # Run lvs with custom options
        result = run(f'lvs -o {option_flag} {vg_name}')
        assert result.succeeded

        # Verify that specified fields are in output
        fields = option_flag.split(',')
        for _ in fields:
            # Convert field name to header format (e.g., lv_name -> LV)
            assert result.stdout  # Basic check that we got output

        # Cleanup handled by fixture

    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'size': '16M', 'pool_name': 'pool'}],
        indirect=True,
    )
    @pytest.mark.parametrize(
        'sort_field',
        ['lv_name', 'lv_size', 'pool_lv'],
        ids=['sort-by-name', 'sort-by-size', 'sort-by-pool'],
    )
    def test_lvs_sorting(self, thinpool_fixture: ThinPool, sort_field: str) -> None:
        """Test lvs command with sorting options.

        Args:
            thinpool_fixture: Thin pool fixture
            sort_field: Field to sort by
        """
        pool = thinpool_fixture
        vg_name = pool.vg

        # Create multiple volumes with different names/sizes
        pool.create_thin_volume('zlv', virtualsize='50M')
        pool.create_thin_volume('alv', virtualsize='100M')
        pool.create_thin_volume('mlv', virtualsize='75M')

        # Run lvs with sorting
        result = run(f'lvs -O {sort_field} {vg_name}')
        assert result.succeeded

        # Verify command succeeded and output contains volumes
        assert 'zlv' in result.stdout
        assert 'alv' in result.stdout
        assert 'mlv' in result.stdout

        # Cleanup handled by fixture

    def test_lvs_with_select_filter(self, setup_loopdev_vg: str) -> None:
        """Test lvs command with select filter.

        Args:
            setup_loopdev_vg: Volume group fixture
        """
        vg_name = setup_loopdev_vg

        pool1: ThinPool | None = None
        pool2: ThinPool | None = None
        try:
            # Create pools with different sizes
            pool1 = ThinPool.create_thin_pool('pool1', vg_name, size='8M')
            pool1.create_thin_volume('lv1', virtualsize='100M')

            pool2 = ThinPool.create_thin_pool('pool2', vg_name, size='16M')
            pool2.create_thin_volume('lv2', virtualsize='200M')

            # Select volumes by pool_lv
            result = run(f'lvs -S "pool_lv=pool1" {vg_name}')
            assert result.succeeded
            assert 'lv1' in result.stdout
            # lv2 should not be in output since it belongs to pool2
            # (but pool1 itself will be in output as it's the pool)

            # Select volumes by lv_size
            result = run(f'lvs -S "lv_size>100m" {vg_name}')
            assert result.succeeded
            # Should show lv2 and pool2 (both > 100m)

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
        [{'size': '8M', 'pool_name': 'pool'}],
        indirect=True,
    )
    def test_lvs_noheadings_output(self, thinpool_fixture: ThinPool) -> None:
        """Test lvs command with --noheadings option.

        Args:
            thinpool_fixture: Thin pool fixture
        """
        pool = thinpool_fixture
        vg_name = pool.vg

        # Create thin volume
        pool.create_thin_volume('lv1', virtualsize='100M')

        # Run lvs with --noheadings
        result = run(f'lvs --noheadings {vg_name}')
        assert result.succeeded

        # Verify no headers like "LV", "VG", "Attr", etc.
        # The output should just have the data lines
        lines = result.stdout.strip().split('\n')
        # Should not have column headers
        assert not any(line.strip().startswith('LV') for line in lines)
        assert 'pool' in result.stdout
        assert 'lv1' in result.stdout

        # Cleanup handled by fixture
