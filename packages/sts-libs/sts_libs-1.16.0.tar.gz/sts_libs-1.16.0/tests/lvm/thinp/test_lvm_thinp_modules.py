# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for thin provisioning kernel modules.

This module contains pytest tests for loading, unloading, and monitoring
thin provisioning kernel modules (dm_thin_pool and dm_persistent_data).
"""

from __future__ import annotations

import contextlib
import logging

import pytest

from sts import lvm
from sts.utils.cmdline import run
from sts.utils.errors import ModuleInUseError
from sts.utils.modules import ModuleInfo


@pytest.mark.parametrize('loop_devices', [{'count': 4, 'size_mb': 128}], indirect=True)
class TestLvmThinpModules:
    """Test cases for thin provisioning kernel modules."""

    def test_module_load_unload(self, setup_loopdev_vg: str) -> None:
        """Test loading and unloading thin provisioning modules.

        Args:
            setup_loopdev_vg: Volume group fixture (ensures VG exists for test isolation)
        """
        _ = setup_loopdev_vg  # Fixture needed for test isolation, value unused

        dm_thin_pool = ModuleInfo(name='dm_thin_pool')
        dm_persistent_data = ModuleInfo(name='dm_persistent_data')

        # Unload dm_thin_pool module if possible
        with contextlib.suppress(ModuleInUseError, RuntimeError):
            dm_thin_pool.unload()

        # Load and unload dm_thin_pool 100 times
        logging.info('load & unload dm_thin_pool 100 times')
        for _ in range(100):
            assert dm_thin_pool.load(), 'Failed to load dm_thin_pool'
            # Refresh module info
            dm_thin_pool = ModuleInfo(name='dm_thin_pool')
            with contextlib.suppress(ModuleInUseError, RuntimeError):
                dm_thin_pool.unload()
            dm_thin_pool = ModuleInfo(name='dm_thin_pool')

        # Clean up cache modules that might prevent dm_persistent_data unload
        for mod_name in ['dm_cache_cleaner', 'dm_cache_smq', 'dm_cache', 'dm_persistent_data']:
            mod = ModuleInfo(name=mod_name)
            with contextlib.suppress(ModuleInUseError, RuntimeError):
                mod.unload()

        # Verify no thin pools exist and modules are not loaded
        result = run('lvs -omodules | grep thin-pool')
        assert result.failed, 'No thin pools should exist'

        dm_thin_pool = ModuleInfo(name='dm_thin_pool')
        dm_persistent_data = ModuleInfo(name='dm_persistent_data')

        assert not dm_thin_pool.loaded, 'dm_thin_pool module should not be loaded'
        assert not dm_persistent_data.loaded, 'dm_persistent_data module should not be loaded'

    def test_module_info(self, setup_loopdev_vg: str) -> None:
        """Test module information and reference counting.

        Note: This test creates multiple pools and LVs in a specific sequence
        to verify module reference counting. Cannot use thinpool_fixture as
        it needs precise control over creation order and reference counts.

        Args:
            setup_loopdev_vg: Volume group fixture
        """
        vg_name = setup_loopdev_vg

        pool1 = lvm.LogicalVolume(name='pool1', vg=vg_name)
        pool2 = lvm.LogicalVolume(name='pool2', vg=vg_name)
        pool3 = lvm.LogicalVolume(name='pool3', vg=vg_name)
        pool4 = lvm.LogicalVolume(name='pool4', vg=vg_name)

        try:
            # Test module information using ModuleInfo
            dm_thin_pool = ModuleInfo(name='dm_thin_pool')
            dm_persistent_data = ModuleInfo(name='dm_persistent_data')

            assert dm_thin_pool.exists, 'dm_thin_pool module should exist'
            assert dm_persistent_data.exists, 'dm_persistent_data module should exist'

            # Check module descriptions via modinfo command
            result = run('modinfo -d dm_thin_pool | grep "^device-mapper thin provisioning target$"')
            assert result.succeeded, 'dm_thin_pool description check failed'

            result = run('modinfo -d dm_persistent_data | grep "^Immutable metadata library for dm$"')
            assert result.succeeded, 'dm_persistent_data description check failed'

            # Test module reference counting with linear pools
            assert pool1.create(size='4M', type='thin-pool')

            lv1 = lvm.LogicalVolume(name='lv1', vg=vg_name)
            assert lv1.create(virtualsize='100M', type='thin', thinpool='pool1')

            self._check_module_refcount('dm_persistent_data', 1)
            self._check_module_refcount('dm_thin_pool', 2)

            lv2 = lvm.LogicalVolume(name='lv2', vg=vg_name)
            assert lv2.create(virtualsize='100M', type='thin', thinpool='pool1')
            self._check_module_refcount('dm_thin_pool', 3)

            # Test with second pool
            assert pool2.create(size='4M', type='thin-pool')

            lv21 = lvm.LogicalVolume(name='lv21', vg=vg_name)
            assert lv21.create(virtualsize='100M', type='thin', thinpool='pool2')
            self._check_module_refcount('dm_thin_pool', 5)

            # Reduce active pool count
            assert lv21.deactivate()
            self._check_module_refcount('dm_thin_pool', 4)
            assert pool2.deactivate()
            self._check_module_refcount('dm_thin_pool', 3)

            # Test with striped pools
            assert pool3.create(size='4M', type='thin-pool', stripes='1')

            lv31 = lvm.LogicalVolume(name='lv31', vg=vg_name)
            assert lv31.create(virtualsize='100M', type='thin', thinpool='pool3')
            self._check_module_refcount('dm_thin_pool', 5)

            lv32 = lvm.LogicalVolume(name='lv32', vg=vg_name)
            assert lv32.create(virtualsize='100M', type='thin', thinpool='pool3')
            self._check_module_refcount('dm_thin_pool', 6)

            # Test with 2-stripe pool
            assert pool4.create(size='4M', type='thin-pool', stripes='2')

            lv41 = lvm.LogicalVolume(name='lv41', vg=vg_name)
            assert lv41.create(virtualsize='100M', type='thin', thinpool='pool4')
            self._check_module_refcount('dm_thin_pool', 8)

            # Reduce striped pool
            assert lv41.deactivate()
            self._check_module_refcount('dm_thin_pool', 7)
            assert pool4.deactivate()
            self._check_module_refcount('dm_thin_pool', 6)

            # Show module and LV information
            run('lsmod | grep -w dm_thin_pool')
            run(f'lvs -o +modules {vg_name}')

            # Should NOT be able to unload the module now (it's in use)
            dm_thin_pool = ModuleInfo(name='dm_thin_pool')
            with pytest.raises(ModuleInUseError):
                dm_thin_pool.unload()

            # Verify modules are still loaded
            dm_thin_pool = ModuleInfo(name='dm_thin_pool')
            dm_persistent_data = ModuleInfo(name='dm_persistent_data')

            assert dm_thin_pool.loaded, 'dm_thin_pool should still be loaded'
            assert dm_persistent_data.loaded, 'dm_persistent_data should still be loaded'

        finally:
            # Remove all pools with their thin volumes
            for pool_name in ['pool1', 'pool2', 'pool3', 'pool4']:
                pool = lvm.ThinPool(name=pool_name, vg=vg_name)
                with contextlib.suppress(RuntimeError):
                    pool.remove_with_thin_volumes(force='', yes='')

            # Should be able to unload the module now
            dm_thin_pool = ModuleInfo(name='dm_thin_pool')
            with contextlib.suppress(ModuleInUseError, RuntimeError):
                dm_thin_pool.unload()

            # Verify modules are unloaded (if unload succeeded)
            dm_thin_pool = ModuleInfo(name='dm_thin_pool')
            dm_persistent_data = ModuleInfo(name='dm_persistent_data')

            if not dm_thin_pool.loaded:
                assert not dm_persistent_data.loaded, 'dm_persistent_data should not be loaded after removal'

    def _check_module_refcount(self, module_name: str, expected_count: int) -> None:
        """Check that module has expected reference count.

        Args:
            module_name: Kernel module name
            expected_count: Expected reference count
        """
        info = ModuleInfo(name=module_name)
        # ModuleInfo.state contains the use count from /proc/modules (3rd column)
        actual_count = int(info.state) if info.state else 0
        assert actual_count == expected_count, (
            f"Module '{module_name}' should have refcount '{expected_count}', but has '{actual_count}'"
        )
