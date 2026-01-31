# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for LVM configuration with thin provisioning.

This module contains pytest tests for LVM configuration settings related to thin provisioning,
including metadata requirements and default values.
"""

from __future__ import annotations

import pytest

from sts.lvm import LvmConfig, ThinPool


class TestLvconfThinp:
    """Test cases for LVM configuration with thin provisioning."""

    @pytest.mark.parametrize('loop_devices', [{'count': 2, 'size_mb': 128}], indirect=True)
    def test_metadata_separate_pvs_enabled(self, setup_loopdev_vg: str, lvm_config_restore: LvmConfig) -> None:
        """Test thin pool creation with metadata on separate PV requirement enabled.

        When thin_pool_metadata_require_separate_pvs=1, LVM should place
        the pool metadata on a different PV than the data.

        Args:
            setup_loopdev_vg: Volume group fixture
            lvm_config_restore: LvmConfig fixture with automatic restoration
        """
        vg_name = setup_loopdev_vg
        config = lvm_config_restore

        # Set require separate PVs to 1
        assert config.set_thin_pool_metadata_require_separate_pvs('1')

        # Create a thin pool - should place metadata on separate PV
        pool = ThinPool.create_thin_pool('pool', vg_name, size='4M')

        try:
            # Get devices for tdata and tmeta using ThinPool attributes
            assert pool.tdata is not None, 'Could not get tdata volume'
            assert pool.tmeta is not None, 'Could not get tmeta volume'

            # Refresh reports to get device info
            assert pool.tdata.refresh_report()
            assert pool.tmeta.refresh_report()

            # Get device info from report
            assert pool.tdata.report is not None, 'tdata report not available'
            assert pool.tmeta.report is not None, 'tmeta report not available'

            tdata_devices = pool.tdata.report.devices
            tmeta_devices = pool.tmeta.report.devices

            assert tdata_devices is not None, 'Could not get tdata device info'
            assert tmeta_devices is not None, 'Could not get tmeta device info'

            # They should be on different devices
            assert tdata_devices != tmeta_devices, (
                f'Expected tmeta and tdata to be on different devices, '
                f'but both are on: tdata={tdata_devices}, tmeta={tmeta_devices}'
            )
        finally:
            pool.remove_with_thin_volumes(force='', yes='')

    @pytest.mark.parametrize('loop_devices', [{'count': 2, 'size_mb': 128}], indirect=True)
    def test_metadata_separate_pvs_fails_with_too_many_stripes(
        self, setup_loopdev_vg: str, lvm_config_restore: LvmConfig
    ) -> None:
        """Test that pool creation fails when stripes use all PVs with separate metadata required.

        When thin_pool_metadata_require_separate_pvs=1 and stripes=3 with only 2 PVs,
        there's no free device for separate metadata, so creation should fail.

        Args:
            setup_loopdev_vg: Volume group fixture
            lvm_config_restore: LvmConfig fixture with automatic restoration
        """
        vg_name = setup_loopdev_vg
        config = lvm_config_restore

        # Set require separate PVs to 1
        assert config.set_thin_pool_metadata_require_separate_pvs('1')

        # Should fail with 3 stripes as there will be no free device for separate metadata
        # (we only have 2 PVs)
        pool = ThinPool(name='pool_fail', vg=vg_name)
        assert not pool.create(size='4M', stripes='3'), (
            'Pool creation should fail when stripes use all PVs with separate metadata required'
        )

    @pytest.mark.parametrize('loop_devices', [{'count': 2, 'size_mb': 128}], indirect=True)
    def test_metadata_separate_pvs_disabled(self, setup_loopdev_vg: str, lvm_config_restore: LvmConfig) -> None:
        """Test thin pool creation with metadata on separate PV requirement disabled.

        When thin_pool_metadata_require_separate_pvs=0, LVM can place
        metadata on the same PV as data.

        Args:
            setup_loopdev_vg: Volume group fixture
            lvm_config_restore: LvmConfig fixture with automatic restoration
        """
        vg_name = setup_loopdev_vg
        config = lvm_config_restore

        # Set require separate PVs to 0
        assert config.set_thin_pool_metadata_require_separate_pvs('0')

        # Both should work now
        pool1 = ThinPool.create_thin_pool('pool1', vg_name, size='4M')
        pool2 = ThinPool.create_thin_pool('pool2', vg_name, size='4M', stripes='2')

        try:
            # Verify pools were created
            assert pool1.refresh_report()
            assert pool2.refresh_report()
        finally:
            pool1.remove_with_thin_volumes(force='', yes='')
            pool2.remove_with_thin_volumes(force='', yes='')

    @pytest.mark.parametrize(
        ('config_key', 'expected_value'),
        [
            (LvmConfig.THIN_POOL_AUTOEXTEND_THRESHOLD, '100'),
            (LvmConfig.THIN_POOL_AUTOEXTEND_PERCENT, '20'),
            (LvmConfig.THIN_POOL_METADATA_REQUIRE_SEPARATE_PVS, '0'),
        ],
        ids=['autoextend-threshold', 'autoextend-percent', 'require-separate-pvs'],
    )
    def test_default_config_values(self, lvm_config: LvmConfig, config_key: str, expected_value: str) -> None:
        """Test default LVM configuration values for thin provisioning.

        Verifies that the default values in lvm.conf are set correctly.

        Args:
            lvm_config: LvmConfig fixture
            config_key: Configuration key to check
            expected_value: Expected value for the key
        """
        if not lvm_config.exists():
            pytest.skip(f'LVM config file {lvm_config.config_path} not found')

        actual_value = lvm_config.get(config_key)
        assert actual_value == expected_value, f'{config_key} should be {expected_value}, but got {actual_value}'

    @pytest.mark.parametrize('loop_devices', [{'count': 2, 'size_mb': 128}], indirect=True)
    @pytest.mark.parametrize(
        'thinpool_fixture',
        [{'size': '8M', 'pool_name': 'pool'}],
        indirect=True,
    )
    @pytest.mark.parametrize(
        ('autoextend_threshold', 'autoextend_percent'),
        [
            ('70', '20'),
            ('80', '50'),
        ],
        ids=['threshold-70-percent-20', 'threshold-80-percent-50'],
    )
    def test_autoextend_config(
        self,
        lvm_config_restore: LvmConfig,
        thinpool_fixture: ThinPool,
        autoextend_threshold: str,
        autoextend_percent: str,
    ) -> None:
        """Test thin pool autoextend configuration.

        Verifies that autoextend threshold and percent can be configured.

        Args:
            lvm_config_restore: LvmConfig fixture with automatic restoration
            thinpool_fixture: Thin pool fixture with automatic cleanup
            autoextend_threshold: Threshold value to set
            autoextend_percent: Percent value to set
        """
        config = lvm_config_restore
        pool = thinpool_fixture

        # Set autoextend configuration using set_multiple
        assert config.set_multiple(
            {
                LvmConfig.THIN_POOL_AUTOEXTEND_THRESHOLD: autoextend_threshold,
                LvmConfig.THIN_POOL_AUTOEXTEND_PERCENT: autoextend_percent,
            }
        )

        # Verify values were set
        assert config.get_thin_pool_autoextend_threshold() == autoextend_threshold
        assert config.get_thin_pool_autoextend_percent() == autoextend_percent

        # Verify pool is accessible
        assert pool.refresh_report()

    @pytest.mark.parametrize('loop_devices', [{'count': 4, 'size_mb': 128}], indirect=True)
    @pytest.mark.parametrize(
        'stripes',
        ['2', '3'],
        ids=['two-stripes', 'three-stripes'],
    )
    def test_striped_pool_with_separate_metadata(
        self, setup_loopdev_vg: str, lvm_config_restore: LvmConfig, stripes: str
    ) -> None:
        """Test striped thin pool creation with separate metadata PV.

        With enough PVs, striped pools should work with separate metadata requirement.

        Args:
            setup_loopdev_vg: Volume group fixture
            lvm_config_restore: LvmConfig fixture with automatic restoration
            stripes: Number of stripes to use
        """
        vg_name = setup_loopdev_vg
        config = lvm_config_restore

        # Set require separate PVs to 1
        assert config.set_thin_pool_metadata_require_separate_pvs('1')

        # Create striped pool - should succeed with 4 PVs
        pool = ThinPool.create_thin_pool(f'pool_stripe{stripes}', vg_name, size='8M', stripes=stripes)

        try:
            # Get devices for tdata and tmeta using ThinPool attributes
            assert pool.tdata is not None, 'Could not get tdata volume'
            assert pool.tmeta is not None, 'Could not get tmeta volume'

            # Refresh reports to get device info
            assert pool.tdata.refresh_report()
            assert pool.tmeta.refresh_report()

            # Get device info from report
            assert pool.tdata.report is not None, 'tdata report not available'
            assert pool.tmeta.report is not None, 'tmeta report not available'

            tdata_devices = pool.tdata.report.devices
            tmeta_devices = pool.tmeta.report.devices

            assert tdata_devices is not None, 'Could not get tdata device info'
            assert tmeta_devices is not None, 'Could not get tmeta device info'

            # Metadata should be on a separate device from any of the stripe devices
            assert tmeta_devices not in tdata_devices, (
                f'Metadata device {tmeta_devices} should not be part of data stripe devices {tdata_devices}'
            )
        finally:
            pool.remove_with_thin_volumes(force='', yes='')
