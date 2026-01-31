# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""LVM test fixtures.

This module provides fixtures for testing LVM (Logical Volume Management):
- Package installation and cleanup
- Service management
- Device configuration
- VDO (Virtual Data Optimizer) support

Fixture Dependencies:
1. _lvm_test (base fixture)
   - Installs LVM packages
   - Manages volume cleanup
   - Logs system information

2. _vdo_test (depends on _lvm_test)
   - Installs VDO packages
   - Manages kernel module
   - Provides data reduction features

Common Usage:
1. Basic LVM testing:
   @pytest.mark.usefixtures('_lvm_test')
   def test_lvm():
       # LVM utilities are installed
       # Volumes are cleaned up after test

2. VDO-enabled testing:
   @pytest.mark.usefixtures('_vdo_test')
   def test_vdo():
       # VDO module is loaded
       # Data reduction is available

Error Handling:
- Package installation failures fail the test
- Module loading failures fail the test
- Volume cleanup runs even if test fails
- Service issues are logged
"""

from __future__ import annotations

import logging
from os import getenv
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from sts import dmpd
from sts.lvm import LogicalVolume, LvmConfig, PhysicalVolume, ThinPool, VolumeGroup
from sts.udevadm import udevadm_settle
from sts.utils.cmdline import run
from sts.utils.errors import ModuleInUseError
from sts.utils.files import Directory, fallocate, mkfs, mount, umount, write_data
from sts.utils.modules import ModuleManager
from sts.utils.packages import log_package_versions
from sts.utils.system import SystemManager
from sts.utils.version import VersionInfo

if TYPE_CHECKING:
    from collections.abc import Generator

    from sts.blockdevice import BlockDevice

# Constants
LVM_PACKAGE_NAME = 'lvm2'
VDO_PACKAGE_NAME = 'vdo'


@pytest.fixture(scope='class')
def _lvm_test() -> None:
    """Set up LVM environment.

    This fixture provides the foundation for LVM testing:
    - Installs LVM utilities (lvm2 package)
    - Logs system information for debugging

    Package Installation:
    - lvm2: Core LVM utilities
    - Required device-mapper modules

    System Information:
    - LVM version
    - Device-mapper status

    Example:
        ```python
        @pytest.mark.usefixtures('_lvm_test')
        def test_lvm():
            # Create and test LVM volumes
        ```
    """
    system = SystemManager()
    assert system.package_manager.install(LVM_PACKAGE_NAME)
    log_package_versions(LVM_PACKAGE_NAME)


@pytest.fixture(scope='class')
def lvm2_version() -> VersionInfo:
    """Get LVM2 package version as VersionInfo.

    This fixture retrieves the LVM2 version from the installed package
    and returns it as a VersionInfo object for proper version comparison.

    Returns:
        VersionInfo: Parsed LVM2 version or VersionInfo(0, 0, 0) if not found

    Example:
        ```python
        def test_with_version(lvm2_version):
            if lvm2_version >= VersionInfo.from_string('2.02.171-6'):
                # Handle new behavior
            else:
                # Handle old behavior
        ```
    """
    result = run('rpm -q lvm2 --queryformat "%{VERSION}-%{RELEASE}"')
    if result.rc == 0:
        return VersionInfo.from_string(result.stdout.strip())

    # Fallback to lvm version command
    result = run('lvm version')
    if result.rc == 0:
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if 'LVM version:' in line:
                return VersionInfo.from_string(line.split(':')[1].strip())

    return VersionInfo(0, 0, 0)


@pytest.fixture(scope='class')
def load_vdo_module(_lvm_test: None) -> str:
    """Load the appropriate VDO kernel module based on kernel version.

    This fixture installs the VDO package and loads the correct VDO kernel module
    depending on the system's kernel version:
    - For kernel 6.9+: uses dm-vdo module (built into kernel)
    - For kernel 6.8 and earlier: uses kvdo module (from kmod-kvdo package)

    The fixture handles kernel version detection and falls back to dm-vdo if
    version parsing fails.

    Args:
        _lvm_test: LVM test fixture dependency (ensures LVM setup is complete)

    Returns:
        str: Name of the loaded VDO module ('dm-vdo' or 'kvdo')

    Raises:
        AssertionError: If VDO package installation or module loading fails
    """
    module = 'dm_vdo'
    system = SystemManager()
    assert system.package_manager.install(VDO_PACKAGE_NAME)
    log_package_versions(VDO_PACKAGE_NAME)
    try:
        k_version = system.info.kernel
        if k_version:
            k_version = k_version.split('.')
            # dm-vdo is available from kernel 6.9, for older version it's available
            # from kmod-kvdo package
            if int(k_version[0]) < 6 or (int(k_version[0]) == 6 and int(k_version[1]) <= 8):
                logging.info('Using kmod-kvdo')
                assert system.package_manager.install('kmod-kvdo')
                log_package_versions('kmod-kvdo')
                module = 'kvdo'
    except (ValueError, IndexError):
        # if we can't get kernel version, just try to load dm-vdo
        logging.warning('Unable to parse kernel version; defaulting to dm-vdo')

    kmod = ModuleManager()
    assert kmod.load(name=module)

    return module


@pytest.fixture(scope='class')
def _vdo_test(load_vdo_module: str) -> Generator[None, None, None]:
    """Set up VDO environment.

    Args:
       load_vdo_module: Load VDO module

    Features:
       - Automatic module loading/unloading

    Example:
       @pytest.mark.usefixtures('_vdo_test')
       def test_vdo():
           # Test VDO functionality
           pass
    """
    module = load_vdo_module

    yield

    kmod = ModuleManager()
    try:
        # ignore failures
        if not kmod.unload(name=module):
            logging.info(f'VDO module {module} could not be unloaded cleanly; continuing.')
    except (ModuleInUseError, RuntimeError):
        logging.info(f'Ignoring unload error for {module}.')


@pytest.fixture
def setup_vg(
    _lvm_test: None, ensure_minimum_devices_with_same_block_sizes: list[BlockDevice]
) -> Generator[str, None, None]:
    """Set up an LVM Volume Group (VG) with Physical Volumes (PVs) for testing.

    This fixture creates a Volume Group using the provided block devices. It handles the creation
    of Physical Volumes from the block devices and ensures proper cleanup after tests, even if
    they fail.

    Args:
        ensure_minimum_devices_with_same_block_sizes: List of BlockDevice objects with matching
            block sizes to be used for creating Physical Volumes.

    Yields:
        str: Name of the created Volume Group.

    Raises:
        AssertionError: If PV creation fails for any device.

    Example:
        def test_volume_group(setup_vg):
            vg_name = setup_vg
            # Use vg_name in your test...
    """
    vg_name = getenv('STS_VG_NAME', 'stsvg0')
    pvs = []

    try:
        # Create PVs
        for device in ensure_minimum_devices_with_same_block_sizes:
            device_name = str(device.path).replace('/dev/', '')
            device_path = str(device.path)

            pv = PhysicalVolume(name=device_name, path=device_path)
            assert pv.create(), f'Failed to create PV on device {device_path}'
            pvs.append(pv)

        # Create VG
        vg = VolumeGroup(name=vg_name, pvs=[pv.path for pv in pvs])
        assert vg.create(), f'Failed to create VG {vg_name}'

        yield vg_name

    finally:
        # Cleanup in reverse order
        vg = VolumeGroup(name=vg_name)
        if not vg.remove():
            logging.warning(f'Failed to remove VG {vg_name}')

        for pv in pvs:
            if not pv.remove():
                logging.warning(f'Failed to remove PV {pv.path}')


@pytest.fixture
def setup_loopdev_vg(_lvm_test: None, loop_devices: list[str]) -> Generator[str, None, None]:
    """Set up a volume group using loop devices.

    This fixture creates a volume group using the provided loop devices.
    The volume group name can be customized using the STS_VG_NAME environment
    variable, otherwise defaults to 'stsvg0'.

    Args:
        loop_devices: List of loop device paths to use as physical volumes.

    Yields:
        str: The name of the created volume group.

    Examples:
        Basic usage with custom loop device configuration:

        ```python
        @pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 4096}], indirect=True)
        @pytest.mark.usefixtures('setup_loopdev_vg')
        def test_large_vg_operations(setup_loopdev_vg):
            vg_name = setup_loopdev_vg
            # Create logical volumes in the 4GB VG
            lv = LogicalVolume(name='testlv', vg=vg_name, size='1G')
            assert lv.create()
        ```

        Using with multiple loop devices:

        ```python
        @pytest.mark.parametrize('loop_devices', [{'count': 2, 'size_mb': 2048}], indirect=True)
        @pytest.mark.usefixtures('setup_loopdev_vg')
        def test_multi_pv_vg(setup_loopdev_vg):
            vg_name = setup_loopdev_vg
            vg = VolumeGroup(name=vg_name)
            assert vg.exists()
        ```
    """
    vg_name = getenv('STS_VG_NAME', 'stsvg0')
    pvs = []

    try:
        for device in loop_devices:
            pv = PhysicalVolume(name=device, path=device)
            assert pv.create(), f'Failed to create PV on device {device}'
            pvs.append(pv)

        vg = VolumeGroup(name=vg_name, pvs=[pv.path for pv in pvs])
        assert vg.create(), f'Failed to create VG {vg_name}'

        yield vg_name

    finally:
        vg = VolumeGroup(name=vg_name)
        if not vg.remove():
            logging.warning(f'Failed to remove VG {vg_name}')

        for pv in pvs:
            if not pv.remove():
                logging.warning(f'Failed to remove PV {pv.path}')


@pytest.fixture
def lv_fixture(_lvm_test: None, setup_vg: str, request: pytest.FixtureRequest) -> Generator[str, None, None]:
    """Create a logical volume for testing with automatic cleanup.

    This fixture creates either a COW (regular) or thin logical volume depending on
    the parameters provided. It handles proper cleanup including thin pool removal
    for thin volumes.

    Args:
        _lvm_test: LVM test fixture dependency
        setup_vg: Volume group name from setup_vg fixture
        request: Pytest fixture request for accessing parameters

    Yields:
        str: Device path to the created logical volume

    Default Configuration:
        - lv_type: 'cow' (regular logical volume)
        - extents: '25%vg'

    Parameters (via pytest.mark.parametrize with indirect=True):
        - lv_type (str): 'cow' for regular LV or 'thin' for thin LV (default: 'cow')
        - lv_name (str): Name for the logical volume (default: based on lv_type)
        - extents (str): Size specification in extents (default: '25%vg')
        - pool_name (str): Thin pool name (only for thin type, default: 'stspool1_25vg')
        - virtualsize (str): Virtual size for thin LV (only for thin type, default: '512M')

    Examples:
        Basic COW usage with default parameters:

        ```python
        def test_cow_operations(lv_fixture):
            dev_path = lv_fixture
            # dev_path is '/dev/vgname/stscow25vglv1'
        ```

        With thin LV:

        ```python
        @pytest.mark.parametrize('lv_fixture', [{'lv_type': 'thin'}], indirect=True)
        def test_thin_operations(lv_fixture):
            dev_path = lv_fixture
            # dev_path is '/dev/vgname/ststhin25vglv1'
        ```

        With custom configuration:

        ```python
        @pytest.mark.parametrize(
            'lv_fixture',
            [
                {'lv_type': 'cow', 'extents': '50%vg', 'lv_name': 'custom_lv'},
                {'lv_type': 'thin', 'virtualsize': '1G', 'pool_name': 'mypool'},
            ],
            indirect=True,
            ids=['large-cow', 'large-thin'],
        )
        def test_various_lvs(lv_fixture):
            dev_path = lv_fixture
        ```
    """
    params = getattr(request, 'param', {})
    lv_type = params.get('lv_type', 'cow')
    vg_name = setup_vg

    # Set defaults based on lv_type
    if lv_type == 'thin':
        default_lv_name = 'ststhin25vglv1'
        default_pool_name = 'stspool1_25vg'
    else:
        default_lv_name = 'stscow25vglv1'
        default_pool_name = None

    lv_name = params.get('lv_name', getenv('LV_NAME', default_lv_name))
    extents = params.get('extents', '25%vg')
    pool_name = params.get('pool_name', getenv('THIN_POOL_NAME', default_pool_name)) if lv_type == 'thin' else None
    virtualsize = params.get('virtualsize', '512M')

    lv = LogicalVolume(name=lv_name, vg=vg_name)

    if lv_type == 'thin':
        assert pool_name is not None, 'pool_name is required for thin LV'
        assert lv.create(
            type='thin',
            thinpool=pool_name,
            extents=extents.upper(),
            virtualsize=virtualsize,
        )
    else:
        assert lv.create(extents=extents)

    yield f'/dev/{vg_name}/{lv_name}'

    # Cleanup
    if lv_type == 'thin' and pool_name:
        pool = ThinPool(name=pool_name, vg=vg_name)
        assert pool.remove_with_thin_volumes(force='', yes='')
    else:
        lv = LogicalVolume(name=lv_name, vg=vg_name)
        assert lv.remove()


@pytest.fixture
def mount_lv_fixture(
    _lvm_test: None, setup_vg: str, request: pytest.FixtureRequest
) -> Generator[Directory, None, None]:
    """Mount a logical volume on a test directory with automatic cleanup.

    This fixture creates a logical volume (COW or thin), formats it with a filesystem,
    mounts it, and handles cleanup. It combines the functionality of lv_fixture and
    mount operations.

    Args:
        _lvm_test: LVM test fixture dependency
        setup_vg: Volume group name from setup_vg fixture
        request: Pytest fixture request for accessing parameters

    Yields:
        Directory: Directory representation of mount point

    Default Configuration:
        - lv_type: 'cow' (regular logical volume)
        - fs_type: 'xfs'
        - mount_point: '/mnt/lvmntdir'

    Parameters (via pytest.mark.parametrize with indirect=True):
        - lv_type (str): 'cow' for regular LV or 'thin' for thin LV (default: 'cow')
        - lv_name (str): Name for the logical volume (default: based on lv_type)
        - extents (str): Size specification in extents (default: '25%vg')
        - pool_name (str): Thin pool name (only for thin type)
        - virtualsize (str): Virtual size for thin LV (default: '512M')
        - fs_type (str): Filesystem type (default: 'xfs')
        - mount_point (str): Mount point path (default: '/mnt/lvmntdir')

    Examples:
        Basic COW usage:

        ```python
        def test_filesystem_operations(mount_lv_fixture):
            mnt_dir = mount_lv_fixture
            # Write files to mnt_dir.path
        ```

        With thin LV and ext4:

        ```python
        @pytest.mark.parametrize('mount_lv_fixture', [{'lv_type': 'thin', 'fs_type': 'ext4'}], indirect=True)
        def test_thin_ext4(mount_lv_fixture):
            mnt_dir = mount_lv_fixture
        ```

        Multiple configurations:

        ```python
        @pytest.mark.parametrize(
            'mount_lv_fixture',
            [
                {'lv_type': 'cow', 'fs_type': 'xfs'},
                {'lv_type': 'thin', 'fs_type': 'xfs'},
                {'lv_type': 'cow', 'fs_type': 'ext4'},
                {'lv_type': 'thin', 'fs_type': 'ext4'},
            ],
            indirect=True,
            ids=['cow-xfs', 'thin-xfs', 'cow-ext4', 'thin-ext4'],
        )
        def test_all_combinations(mount_lv_fixture):
            mnt_dir = mount_lv_fixture
        ```
    """
    params = getattr(request, 'param', {})
    lv_type = params.get('lv_type', 'cow')
    vg_name = setup_vg

    # Set defaults based on lv_type
    if lv_type == 'thin':
        default_lv_name = 'ststhinmntlv1'
        default_pool_name = 'stspool1_mnt'
        default_mount_point = '/mnt/thinlvmntdir'
    else:
        default_lv_name = 'stscowmntlv1'
        default_pool_name = None
        default_mount_point = '/mnt/lvcowmntdir'

    lv_name = params.get('lv_name', default_lv_name)
    extents = params.get('extents', '25%vg')
    pool_name = params.get('pool_name', default_pool_name) if lv_type == 'thin' else None
    virtualsize = params.get('virtualsize', '512M')
    fs_type = params.get('fs_type', 'xfs')
    mount_point = params.get('mount_point', default_mount_point)

    # Create LV
    lv = LogicalVolume(name=lv_name, vg=vg_name)
    if lv_type == 'thin':
        assert pool_name is not None, 'pool_name is required for thin LV'
        assert lv.create(
            type='thin',
            thinpool=pool_name,
            extents=extents.upper(),
            virtualsize=virtualsize,
        )
    else:
        assert lv.create(extents=extents)

    dev_path = f'/dev/{vg_name}/{lv_name}'

    # Create filesystem
    assert mkfs(device=dev_path, fs_type=fs_type)

    # Create mount point directory
    mnt_dir = Directory(Path(mount_point), create=True)
    assert mnt_dir.exists, f'Failed to create mount point directory {mount_point}'

    # Mount the LV
    assert mount(device=dev_path, mountpoint=mount_point)

    yield mnt_dir

    # Cleanup
    assert umount(mountpoint=mount_point)
    mnt_dir.remove_dir()

    if lv_type == 'thin' and pool_name:
        pool = ThinPool(name=pool_name, vg=vg_name)
        assert pool.remove_with_thin_volumes(force='', yes='')
    else:
        lv = LogicalVolume(name=lv_name, vg=vg_name)
        assert lv.remove()


def _create_multiple_lv_mntpoints(
    vg_name: str,
    lv_type: str | None = None,
    lv_name: str | None = None,
    mount_point: str | None = None,
    pool_name: str | None = None,
    fs_type: str | None = None,
    num_of_mntpoints: int | None = None,
    virtualsize: str | None = None,
    percentage_of_vg_to_use: int | None = None,
) -> Generator[list[Directory], None, None]:
    """Creating multiple logical volumes with mounted filesystems.

    Args:
        vg_name: Volume group name
        lv_type: Type of logical volume ('cow' or 'thin'), defaults to 'cow'
        lv_name: Base name for logical volumes (defaults based on lv_type)
        mount_point: Base mount point path (defaults based on lv_type)
        pool_name: Base name for thin pools (only used for thin LVs)
        fs_type: Filesystem type (defaults to env var or 'xfs')
        num_of_mntpoints: Number of mount points (defaults to env var or 6)
        virtualsize: Virtual size for thin logical volumes (defaults to '512M')
        percentage_of_vg_to_use: Percentage of volume group to use across all LVs (defaults to 50)

    Yields:
        list[Directory]: List of Directory objects representing the mount points
    """
    # Default lv_type if not provided
    lv_type = lv_type or 'cow'

    # Set defaults based on lv_type
    if lv_type == 'thin':
        default_lv_name = 'ststhinmultiplemntpoints'
        default_mount_point = '/mnt/lvthinmntdir'
        default_pool_name = 'stspool1mutiplethin'
    else:  # cow
        default_lv_name = 'stscowmultiplemntpoints'
        default_mount_point = '/mnt/lvcowmntdir'
        default_pool_name = None
    percentage_of_vg_to_use = percentage_of_vg_to_use or 50
    default_virtualsize = '512M'
    # Use provided values or fall back to environment variables or defaults
    lv_name = lv_name or getenv('LV_NAME', default_lv_name)
    mount_point = mount_point or getenv('STS_LV_MOUNT_POINT', default_mount_point)
    fs_type = fs_type or getenv('STS_LV_FS_TYPE', 'xfs')
    virtualsize = virtualsize or getenv('STS_LV_VIRTUALSIZE', default_virtualsize)

    if lv_type == 'thin':
        pool_name = pool_name or getenv('STS_THIN_POOL_NAME', default_pool_name)

    if num_of_mntpoints is None:
        try:
            num_of_mntpoints = int(getenv('STS_COW_MNTPOINT_NUMBER', '6'))
        except (ValueError, TypeError):
            pytest.fail('STS_COW_MNTPOINT_NUMBER variable has incorrect value!')

    vg_percentage = int(percentage_of_vg_to_use / int(num_of_mntpoints))
    sources: list[Directory] = []
    logical_volumes: list[LogicalVolume] = []

    # Create LV
    for num in range(num_of_mntpoints):
        lv = LogicalVolume(name=f'{lv_name}{num}', vg=vg_name)
        logical_volumes.append(lv)

        # Create LV based on type
        if lv_type == 'thin':
            assert lv.create(
                type='thin',
                thinpool=f'{pool_name}{num}',
                extents=f'{vg_percentage}%vg',
                virtualsize=virtualsize,
            )
        elif lv_type == 'cow':
            assert lv.create(extents=f'{vg_percentage}%vg')
        else:
            pytest.fail(f'Invalid LV type: {lv_type}')

        dev_path = f'/dev/{vg_name}/{lv_name}{num}'
        assert mkfs(device=dev_path, fs_type=fs_type)

        mnt_dir = Directory(Path(f'{mount_point}{num}'), create=True)
        assert mnt_dir.exists, f'Failed to create mount point directory {mount_point}{num}'
        # Mount the LV
        assert mount(device=dev_path, mountpoint=f'{mount_point}{num}')
        sources.append(mnt_dir)

    yield sources

    # Cleanup
    for num in range(num_of_mntpoints):
        assert umount(mountpoint=f'{mount_point}{num}')
        mnt_dir = Directory(Path(f'{mount_point}{num}'), create=True)
        mnt_dir.remove_dir()
    for lv in logical_volumes:
        assert lv.remove()


@pytest.fixture
def multiple_mntpoints_fixture(
    _lvm_test: None, setup_vg: str, request: pytest.FixtureRequest
) -> Generator[list[Directory], None, None]:
    """Create multiple logical volumes with mounted filesystems for testing.

    This fixture creates multiple logical volumes (COW or thin) within a volume group,
    formats them with filesystems, and mounts them to separate mount points. It provides
    a unified interface replacing the separate cow/thin and xfs/ext4 fixtures.

    Args:
        _lvm_test: LVM test fixture dependency
        setup_vg: Volume group name from setup_vg fixture
        request: Pytest fixture request for accessing parameters

    Yields:
        list[Directory]: List of Directory objects representing the mount points

    Default Configuration:
        - lv_type: 'cow'
        - fs_type: 'xfs'
        - num_of_mntpoints: 6

    Parameters (via pytest.mark.parametrize with indirect=True):
        - lv_type (str): 'cow' for regular LVs or 'thin' for thin LVs (default: 'cow')
        - fs_type (str): Filesystem type - 'xfs' or 'ext4' (default: 'xfs')
        - num_of_mntpoints (int): Number of mount points to create (default: 6)
        - lv_name (str): Base name for logical volumes
        - mount_point (str): Base mount point path
        - pool_name (str): Base name for thin pools (thin only)
        - virtualsize (str): Virtual size for thin LVs (default: '512M')
        - percentage_of_vg_to_use (int): Total VG percentage to use (default: 50)

    Examples:
        Basic COW with xfs (default):

        ```python
        def test_cow_xfs(multiple_mntpoints_fixture):
            mntpoints = multiple_mntpoints_fixture
            assert len(mntpoints) == 6
        ```

        Thin with ext4:

        ```python
        @pytest.mark.parametrize('multiple_mntpoints_fixture', [{'lv_type': 'thin', 'fs_type': 'ext4'}], indirect=True)
        def test_thin_ext4(multiple_mntpoints_fixture):
            mntpoints = multiple_mntpoints_fixture
        ```

        All combinations for comprehensive testing:

        ```python
        @pytest.mark.parametrize(
            'multiple_mntpoints_fixture',
            [
                {'lv_type': 'cow', 'fs_type': 'xfs'},
                {'lv_type': 'thin', 'fs_type': 'xfs'},
                {'lv_type': 'cow', 'fs_type': 'ext4'},
                {'lv_type': 'thin', 'fs_type': 'ext4'},
            ],
            indirect=True,
            ids=['cow-xfs', 'thin-xfs', 'cow-ext4', 'thin-ext4'],
        )
        def test_all_fs_types(multiple_mntpoints_fixture):
            mntpoints = multiple_mntpoints_fixture
        ```

        Custom number of mount points:

        ```python
        @pytest.mark.parametrize(
            'multiple_mntpoints_fixture', [{'num_of_mntpoints': 10, 'percentage_of_vg_to_use': 80}], indirect=True
        )
        def test_many_volumes(multiple_mntpoints_fixture):
            assert len(multiple_mntpoints_fixture) == 10
        ```
    """
    params = getattr(request, 'param', {})

    yield from _create_multiple_lv_mntpoints(
        vg_name=setup_vg,
        **params,
    )


@pytest.fixture(scope='class')
def install_dmpd(_lvm_test: None) -> None:
    """Install required packages for device-mapper-persistent-data tools.

    This fixture installs the device-mapper-persistent-data package which provides
    cache metadata tools like cache_check, cache_dump, cache_repair, etc.

    Example:
        ```python
        @pytest.mark.usefixtures('install_dmpd_packages')
        def test_cache_tools():
            # DMPD tools are now available
            pass
        ```
    """
    system = SystemManager()
    package = 'device-mapper-persistent-data'

    assert system.package_manager.install(package), f'Failed to install {package}'


@pytest.fixture
def lvm_config() -> LvmConfig:
    """Provide an LvmConfig instance for LVM configuration management.

    This fixture provides access to LVM configuration settings through the LvmConfig class.
    Use this for tests that need to read or modify lvm.conf settings.

    Yields:
        LvmConfig: An LvmConfig instance for configuration management

    Example:
        ```python
        def test_config_value(lvm_config):
            threshold = lvm_config.get_thin_pool_autoextend_threshold()
            assert threshold == '100'
        ```
    """
    return LvmConfig()


@pytest.fixture
def lvm_config_restore(lvm_config: LvmConfig) -> Generator[LvmConfig, None, None]:
    """Provide LvmConfig with automatic restoration of thin pool settings after test.

    This fixture saves the current thin pool configuration values before the test
    and restores them after the test completes. Use this when your test modifies
    LVM configuration settings that should be restored.

    Args:
        lvm_config: LvmConfig fixture dependency

    Yields:
        LvmConfig: The same LvmConfig instance with restoration on cleanup

    Example:
        ```python
        def test_modify_config(lvm_config_restore):
            config = lvm_config_restore
            config.set_thin_pool_metadata_require_separate_pvs('1')
            # ... test ...
            # Configuration is automatically restored after test
        ```
    """
    # Save original values
    original_values = {
        LvmConfig.THIN_POOL_METADATA_REQUIRE_SEPARATE_PVS: lvm_config.get_thin_pool_metadata_require_separate_pvs(),
        LvmConfig.THIN_POOL_AUTOEXTEND_THRESHOLD: lvm_config.get_thin_pool_autoextend_threshold(),
        LvmConfig.THIN_POOL_AUTOEXTEND_PERCENT: lvm_config.get_thin_pool_autoextend_percent(),
    }

    yield lvm_config

    # Restore original values
    for key, value in original_values.items():
        if value is not None:
            lvm_config.set(key, value)


@pytest.fixture
def thinpool_fixture(setup_loopdev_vg: str, request: pytest.FixtureRequest) -> Generator[ThinPool, None, None]:
    """Create a thin pool for testing with automatic cleanup.

    This fixture creates a thin pool and automatically removes all thin volumes
    and the pool itself during cleanup. It supports parameterization for flexible
    pool configuration.

    Args:
        setup_loopdev_vg: Volume group name from setup_loopdev_vg fixture
        request: Pytest fixture request for accessing parameters

    Yields:
        ThinPool: The created thin pool object that can be used to create thin volumes

    Default Configuration:
        - pool_name: 'pool'
        - size: '500M'

    Parameters (via pytest.mark.parametrize with indirect=True):
        - pool_name (str): Name for the thin pool (default: 'pool')
        - size (str): Size of the thin pool (default: '500M')
        - extents (str): Size in extents (alternative to size)
        - discards (str): Discard mode - 'passdown', 'nopassdown', or 'ignore' (default: None)
        - stripes (str): Number of stripes for the pool (default: None)
        - stripesize (str): Stripe size in KB (default: None)
        - chunksize (str): Chunk size for the pool (default: None)
        - poolmetadatasize (str): Metadata size for the pool (default: None)
        - poolmetadataspare (str): Create pool metadata spare - 'y' or 'n' (default: None)
        - create_thin_volume (bool): Whether to create a thin volume (default: False)
        - thin_volume_name (str): Name for the thin volume (default: 'lv1')
        - thin_volume_size (str): Virtual size for thin volume (default: '50M')

    Examples:
        Basic usage with default parameters:

        ```python
        def test_thin_operations(thinpool_fixture):
            pool = thinpool_fixture
            lv = pool.create_thin_volume('test_lv', virtualsize='100M')
            # ... test operations ...
            # Cleanup is automatic - all thin volumes and pool are removed
        ```

        With custom pool size:

        ```python
        @pytest.mark.parametrize('thinpool_fixture', [{'size': '1G'}], indirect=True)
        def test_large_pool(thinpool_fixture):
            pool = thinpool_fixture
            lv = pool.create_thin_volume('large_lv', virtualsize='500M')
        ```

        With multiple parameter combinations:

        ```python
        @pytest.mark.parametrize(
            'thinpool_fixture',
            [
                {'size': '200M', 'pool_name': 'small_pool'},
                {'size': '1G', 'pool_name': 'large_pool'},
            ],
            indirect=True,
            ids=['small', 'large'],
        )
        def test_various_sizes(thinpool_fixture):
            pool = thinpool_fixture
            # Test with different pool configurations
        ```

        Combined with loop_devices parameterization:

        ```python
        @pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 4096}], indirect=True)
        @pytest.mark.parametrize('thinpool_fixture', [{'size': '3G'}], indirect=True)
        def test_discard_performance(thinpool_fixture):
            pool = thinpool_fixture
            discard_lv = pool.create_thin_volume('discard', virtualsize='1T')
            # ... performance test ...
        ```
    """
    vg_name = setup_loopdev_vg
    params = getattr(request, 'param', {})

    pool_name = params.get('pool_name', 'pool')
    size = params.get('size')
    extents = params.get('extents')
    discards = params.get('discards')
    stripes = params.get('stripes')
    stripesize = params.get('stripesize')
    chunksize = params.get('chunksize')
    poolmetadatasize = params.get('poolmetadatasize')
    poolmetadataspare = params.get('poolmetadataspare')
    create_thin_volume = params.get('create_thin_volume', False)
    thin_volume_name = params.get('thin_volume_name', 'lv1')
    thin_volume_size = params.get('thin_volume_size', '50M')

    # Default size if neither size nor extents specified
    if not size and not extents:
        size = '500M'

    # Build options dict, filtering out None values
    pool_options: dict[str, str] = {}
    if size:
        pool_options['size'] = size
    if extents:
        pool_options['extents'] = extents
    if discards:
        pool_options['discards'] = discards
    if stripes:
        pool_options['stripes'] = stripes
    if stripesize:
        pool_options['stripesize'] = stripesize
    if chunksize:
        pool_options['chunksize'] = chunksize
    if poolmetadatasize:
        pool_options['poolmetadatasize'] = poolmetadatasize
    if poolmetadataspare:
        pool_options['poolmetadataspare'] = poolmetadataspare

    pool = ThinPool.create_thin_pool(
        pool_name,
        vg_name,
        **pool_options,
    )
    logging.info(f'Created thin pool {pool_name} with size {size or extents} in VG {vg_name}')

    if create_thin_volume:
        pool.create_thin_volume(thin_volume_name, virtualsize=thin_volume_size)
        logging.info(f'Created thin volume {thin_volume_name} with size {thin_volume_size}')

    yield pool

    # Cleanup - remove all thin volumes and the pool
    pool.remove_with_thin_volumes(force='', yes='')
    logging.info(f'Cleaned up thin pool {pool_name} and all its volumes')


@pytest.fixture
def regular_lv_fixture(setup_loopdev_vg: str, request: pytest.FixtureRequest) -> Generator[LogicalVolume, None, None]:
    """Create a regular (non-thin) logical volume for testing.

    This fixture creates a regular LV that can be used for conversion to thin,
    testing, or other operations that require a standard logical volume.

    Args:
        setup_loopdev_vg: Volume group name from setup_loopdev_vg fixture
        request: Pytest fixture request for accessing parameters

    Yields:
        LogicalVolume: The created regular logical volume

    Default Configuration:
        - lv_name: 'lv'
        - size: '50M' (or extents if specified)

    Parameters (via pytest.mark.parametrize with indirect=True):
        - lv_name (str): Name for the LV (default: 'lv')
        - size (str): Size of the LV (default: '50M')
        - extents (str): Size in extents (alternative to size)
        - inactive (bool): Create as inactive LV with '-an' flag (default: False)
        - zero (str): Zero option for LV creation (default: None)
        - skip_cleanup (bool): Skip automatic cleanup (default: False) - use when
          LV will be converted to thin pool and cleanup handled separately

    Examples:
        Basic usage:

        ```python
        def test_regular_lv(regular_lv_fixture):
            lv = regular_lv_fixture
            assert lv.report.lv_attr[0] == '-'  # Regular volume
        ```

        With custom size:

        ```python
        @pytest.mark.parametrize('regular_lv_fixture', [{'size': '100M', 'lv_name': 'data'}], indirect=True)
        def test_large_lv(regular_lv_fixture):
            lv = regular_lv_fixture
        ```
    """
    vg_name = setup_loopdev_vg
    params = getattr(request, 'param', {})

    lv_name = params.get('lv_name', 'lv')
    size = params.get('size', '50M')
    extents = params.get('extents')
    inactive = params.get('inactive', False)
    zero = params.get('zero')
    skip_cleanup = params.get('skip_cleanup', False)

    lv = LogicalVolume(name=lv_name, vg=vg_name)

    # Build create options
    create_args = []
    create_kwargs: dict[str, str] = {}

    if inactive:
        create_args.append('-an')
    if zero:
        create_kwargs['zero'] = zero
    if extents:
        create_kwargs['extents'] = extents
    else:
        create_kwargs['size'] = size

    assert lv.create(*create_args, **create_kwargs)

    logging.info(f'Created regular LV {lv_name} in VG {vg_name}')

    yield lv

    # Cleanup - skip if LV was converted to pool (conversion tests handle cleanup)
    if not skip_cleanup:
        lv.remove(force='', yes='')
        logging.info(f'Cleaned up regular LV {lv_name}')


@pytest.fixture
def temp_mount_fixture(request: pytest.FixtureRequest) -> Generator[dict[str, Any], None, None]:
    """Create a temporary mount point with automatic cleanup.

    This fixture creates a mount point directory and handles cleanup of
    the directory and any temp files after the test.

    Args:
        request: Pytest fixture request for accessing parameters

    Yields:
        dict: Mount information including:
            - mount_point: Path to the mount point
            - mount_dir: Directory object
            - temp_files: List to track temp files for cleanup

    Default Configuration:
        - mount_point: '/mnt/test'

    Parameters (via pytest.mark.parametrize with indirect=True):
        - mount_point (str): Path for the mount point (default: '/mnt/test')

    Examples:
        ```python
        def test_with_mount(temp_mount_fixture, regular_lv_fixture):
            mount_info = temp_mount_fixture
            lv = regular_lv_fixture

            mkfs(lv.device_path, 'ext4')
            mount(lv.device_path, mount_info['mount_point'])
            # ... test operations ...
            umount(mount_info['mount_point'])
        ```
    """
    params = getattr(request, 'param', {})
    mount_point = Path(params.get('mount_point', '/mnt/test'))

    mount_dir = Directory(mount_point, create=True)
    temp_files: list[str] = []

    mount_info = {
        'mount_point': mount_point,
        'mount_dir': mount_dir,
        'temp_files': temp_files,
    }

    yield mount_info

    # Cleanup - unmount if mounted, remove dir, clean temp files
    umount(mount_point)

    if mount_dir.exists:
        mount_dir.remove_dir()

    for temp_file in temp_files:
        run(f'rm -f {temp_file}')


@pytest.fixture
def thin_volumes_with_lifecycle(setup_loopdev_vg: str) -> Generator[dict[str, Any], None, None]:
    """Create thin volumes and perform filesystem lifecycle operations.

    Creates a 3GB thin pool and 10 thin volumes of 300MB each, then performs
    filesystem operations (create, mount, unmount, deactivate) to generate
    metadata activity.

    Args:
        setup_loopdev_vg: Volume group name from setup_loopdev_vg fixture

    Yields:
        dict: Extended pool information with thin volume details
    """
    vg_name = setup_loopdev_vg
    pool_name = 'thinpool'

    # Create thin pool (3GB to accommodate 10x300MB thin volumes with filesystem support)
    pool = ThinPool.create_thin_pool(pool_name, vg_name, size='3G')

    pool_info: dict[str, Any] = {
        'vg_name': vg_name,
        'pool_name': pool_name,
        'pool_path': f'/dev/{vg_name}/{pool_name}',
    }
    thin_base_name = 'thinvol'
    run(f'vgchange {vg_name} --setautoactivation n')
    # Create 10 thin volumes of 300MB each (minimum size for filesystem support)
    thin_lvs = []
    for i in range(10):
        thin_name = f'{thin_base_name}{i}'
        thin_lv = LogicalVolume(name=thin_name, vg=vg_name)
        assert thin_lv.create(type='thin', thinpool=pool_name, virtualsize='300M')
        thin_lvs.append(thin_lv)
    for thin_lv in thin_lvs:
        # Create filesystem and mount/unmount to generate metadata activity
        # This matches the mount_lv/umount_lv logic from setup.py
        thin_path = f'/dev/{vg_name}/{thin_lv.name}'
        mount_point = f'/mnt/{thin_lv.name}'

        mnt_dir = Directory(Path(mount_point), create=True)
        assert mkfs(device=thin_path, fs_type='xfs')
        assert mount(device=thin_path, mountpoint=mount_point)
        random_data_file = f'{mount_point}/random_data.txt'
        assert write_data(target=random_data_file, source='/dev/urandom', count=10, bs='1M'), (
            f'Failed to write random data to {random_data_file}'
        )
        logging.info(f'Wrote 10MB of random data to {random_data_file}')
        udevadm_settle()
        assert umount(mountpoint=mount_point)
        mnt_dir.remove_dir()

        # Deactivate thin LV with verification
        assert thin_lv.deactivate()

    pool_info.update(
        {
            'thin_count': 10,
            'thin_base_name': thin_base_name,
            'thin_lvs': thin_lvs,
        }
    )

    yield pool_info

    # Cleanup thin volumes and pool
    for thin_lv in thin_lvs:
        thin_lv.remove()
    pool.remove_with_thin_volumes(force='', yes='')


@pytest.fixture
def thin_pool_with_volume(setup_loopdev_vg: str) -> Generator[dict[str, Any], None, None]:
    """Create a thin pool with a single thin volume for testing.

    Creates a basic thin pool and one thin volume for simple activation and
    attribute testing scenarios.

    Args:
        setup_loopdev_vg: Volume group name from setup_loopdev_vg fixture

    Yields:
        dict: Information about the thin pool and thin volume
    """
    vg_name = setup_loopdev_vg
    pool_name = 'pool'
    lv_name = 'lv1'

    # Create thin pool
    pool = ThinPool.create_thin_pool(pool_name, vg_name, size='100M')

    # Create thin volume
    thin_lv = pool.create_thin_volume(lv_name, virtualsize='50M')

    yield {
        'vg_name': vg_name,
        'pool': pool,
        'thin_lv': thin_lv,
        'pool_name': pool_name,
        'lv_name': lv_name,
    }

    # Cleanup
    pool.remove_with_thin_volumes()


@pytest.fixture
def multiple_thin_pools(setup_loopdev_vg: str) -> Generator[list[ThinPool], None, None]:
    """Create multiple thin pools with thin volumes for concurrent testing.

    Creates configurable number of thin pools, each with a thin volume,
    for testing concurrent operations.

    Args:
        setup_loopdev_vg: Volume group name from setup_loopdev_vg fixture

    Yields:
        list: List of ThinPool objects
    """
    vg_name = setup_loopdev_vg
    pools: list[ThinPool] = []

    # Create 3 thin pools with thin volumes
    for i in range(1, 4):
        pool_name = f'pool{i}'
        lv_name = f'lv{i}'

        pool = ThinPool.create_thin_pool(pool_name, vg_name, size='30M')
        pool.create_thin_volume(lv_name, virtualsize='50M')
        pools.append(pool)

    yield pools

    # Cleanup
    for pool in pools:
        pool.remove_with_thin_volumes()


@pytest.fixture
def swap_volume(setup_loopdev_vg: str) -> Generator[dict[str, Any], None, None]:
    """Create a swap volume for metadata operations.

    Creates a 75MB swap logical volume that can be used for metadata swapping.

    Args:
        setup_loopdev_vg: Volume group name from setup_loopdev_vg fixture

    Yields:
        dict: Information about the created swap volume
    """
    vg_name = setup_loopdev_vg
    swap_name = 'swapvol'

    # Create swap LV (75MB as per original setup)
    swap_lv = LogicalVolume(name=swap_name, vg=vg_name)
    assert swap_lv.create(size='75M')

    swap_info = {
        'vg_name': vg_name,
        'swap_name': swap_name,
        'swap_path': f'/dev/{vg_name}/{swap_name}',
        'swap_lv': swap_lv,
    }

    yield swap_info

    # Cleanup
    swap_lv.remove()


@pytest.fixture
def thin_and_regular_lvs(setup_loopdev_vg: str) -> Generator[dict[str, Any], None, None]:
    """Create a thin pool with thin volume and a regular LV for performance testing.

    Creates:
    - Thin pool (1G)
    - Thin volume (900M virtual size)
    - Regular logical volume (900M)

    This fixture is useful for comparing thin vs regular LV performance.

    Args:
        setup_loopdev_vg: Volume group name from setup_loopdev_vg fixture

    Yields:
        dict: Information about created volumes including:
            - vg_name: Volume group name
            - pool: ThinPool object
            - regular_lv: LogicalVolume object
            - thin_device: Device path for thin volume
            - regular_device: Device path for regular volume
    """
    vg_name = setup_loopdev_vg

    # Create thin pool and volumes
    pool = ThinPool.create_thin_pool('pool', vg_name, size='1G')
    pool.create_thin_volume('thin_lv', virtualsize='900M')
    regular_lv = LogicalVolume(name='regular_lv', vg=vg_name)
    assert regular_lv.create(size='900M')

    yield {
        'vg_name': vg_name,
        'pool': pool,
        'regular_lv': regular_lv,
        'thin_device': f'/dev/mapper/{vg_name}-thin_lv',
        'regular_device': f'/dev/mapper/{vg_name}-regular_lv',
    }

    # Cleanup
    regular_lv.remove(force='', yes='')
    pool.remove_with_thin_volumes(force='', yes='')


@pytest.fixture
def mounted_thin_and_regular_lvs(thin_and_regular_lvs: dict[str, Any]) -> Generator[dict[str, Any], None, None]:
    """Mount thin and regular LVs for performance testing.

    Creates ext4 filesystems on both volumes and mounts them.
    Useful for I/O performance comparison tests.

    Args:
        thin_and_regular_lvs: Volume information from thin_and_regular_lvs fixture

    Yields:
        dict: Extended information including:
            - All fields from thin_and_regular_lvs
            - thin_lv_mnt: Path to thin volume mount point
            - regular_lv_mnt: Path to regular volume mount point
            - filesystem: Filesystem type used (ext4)
    """
    vol_info = thin_and_regular_lvs.copy()
    thin_device = vol_info['thin_device']
    regular_device = vol_info['regular_device']

    thin_lv_mnt = Path('/mnt/thin_lv')
    regular_lv_mnt = Path('/mnt/regular_lv')

    # Create directories and filesystems
    thin_dir = Directory(thin_lv_mnt, create=True)
    regular_dir = Directory(regular_lv_mnt, create=True)

    filesystem = 'ext4'  # Use ext4 for consistent performance testing
    assert mkfs(thin_device, filesystem, force=True)
    assert mkfs(regular_device, filesystem, force=True)

    assert mount(thin_device, thin_lv_mnt)
    assert mount(regular_device, regular_lv_mnt)

    vol_info.update(
        {
            'thin_lv_mnt': thin_lv_mnt,
            'regular_lv_mnt': regular_lv_mnt,
            'filesystem': filesystem,
        }
    )

    yield vol_info

    # Cleanup
    umount(thin_lv_mnt)
    umount(regular_lv_mnt)
    thin_dir.remove_dir()
    regular_dir.remove_dir()


@pytest.fixture
def metadata_snapshot(thin_volumes_with_lifecycle: dict[str, Any]) -> Generator[dict[str, Any], None, None]:
    """Create metadata snapshot for thin pool.

    Creates a metadata snapshot while the thin pool is active and handles
    the suspend/message/resume sequence for snapshot creation.

    Args:
        thin_volumes_with_lifecycle: Thin volumes setup from thin_volumes_with_lifecycle fixture

    Yields:
        dict: Pool information with snapshot status
    """
    pool_info = thin_volumes_with_lifecycle.copy()
    vg_name = pool_info['vg_name']
    pool_name = pool_info['pool_name']

    udevadm_settle()

    # Create metadata snapshot while pool is still active
    pool_device = f'/dev/mapper/{vg_name}-{pool_name}-tpool'

    # Suspend -> message -> resume sequence (matching metadata_snapshot from setup.py)
    suspend_result = run(f'dmsetup suspend {pool_device}')
    assert suspend_result.succeeded

    message_result = run(f'dmsetup message {pool_device} 0 reserve_metadata_snap')
    assert message_result.succeeded

    resume_result = run(f'dmsetup resume {pool_device}')
    assert resume_result.succeeded

    # Now deactivate thin volumes (matching deactivate_thinvols from setup)
    for i in range(int(pool_info['thin_count'])):
        thin_name = f'{pool_info["thin_base_name"]}{i}'
        thin_lv = LogicalVolume(name=thin_name, vg=vg_name)
        thin_lv.deactivate()

    udevadm_settle()

    pool_info.update(
        {
            'pool_device': pool_device,
            'has_snapshot': True,
        }
    )

    yield pool_info

    # Release metadata snapshot
    run(f'dmsetup message {pool_device} 0 release_metadata_snap')


@pytest.fixture
def metadata_swap(metadata_snapshot: dict[str, Any], swap_volume: dict[str, Any]) -> dict[str, Any]:
    """Perform metadata swap operation between thin pool and swap volume.

    Deactivates the thin pool and swap volume, then uses lvconvert to swap
    the metadata from the thin pool to the swap volume.

    Args:
        metadata_snapshot: Metadata snapshot setup from metadata_snapshot fixture
        swap_volume: Swap volume setup from swap_volume fixture

    Returns:
        dict: Combined information with metadata device details
    """
    pool_info = metadata_snapshot.copy()
    swap_info = swap_volume

    # Ensure both fixtures reference the same VG
    assert pool_info['vg_name'] == swap_info['vg_name'], 'Pool and swap must be in same VG'

    vg_name = pool_info['vg_name']
    pool_name = pool_info['pool_name']
    swap_name = swap_info['swap_name']

    # Deactivate pool and swap (matching swap_metadata logic from setup.py)
    pool_lv = LogicalVolume(name=pool_name, vg=vg_name)
    pool_lv.deactivate()
    swap_lv = LogicalVolume(name=swap_name, vg=vg_name)
    swap_lv.deactivate()

    logging.info(run('lvs').stdout)
    udevadm_settle()

    # Swap metadata using lv_convert --poolmetadata (exact logic from setup.py)
    # This converts the swap LV to hold the thin pool's metadata
    convert_cmd = f'lvconvert -y --thinpool {vg_name}/{pool_name} --poolmetadata {vg_name}/{swap_name}'
    convert_result = run(convert_cmd)
    assert convert_result.succeeded

    # Activate swap volume (now containing metadata)
    swap_lv = LogicalVolume(name=swap_name, vg=vg_name)
    swap_lv.activate()

    # Use swap LV as metadata device (it now contains the metadata)
    metadata_dev = f'/dev/{vg_name}/{swap_name}'

    # Combine information from both fixtures
    combined_info = pool_info.copy()
    combined_info.update(swap_info)
    combined_info.update(
        {
            'metadata_dev': metadata_dev,
        }
    )

    return combined_info


@pytest.fixture
def metadata_backup(metadata_swap: dict[str, Any]) -> Generator[dict[str, Any], None, None]:
    """Create metadata backup files for testing.

    Creates metadata backup using thin_dump and prepares repair file for testing.

    Args:
        metadata_swap: Metadata swap setup from metadata_swap fixture

    Yields:
        dict: Extended information with backup file paths
    """
    vol_info = metadata_swap.copy()
    metadata_dev = vol_info['metadata_dev']
    metadata_backup_path = Path('/var/tmp/metadata')
    metadata_repair_path = Path('/var/tmp/metadata_repair')

    # Create metadata backup using thin_dump (matching backup_metadata from main.fmf)
    backup_cmd = f'thin_dump --format xml --repair {metadata_dev} --output {metadata_backup_path}'
    backup_result = run(backup_cmd)
    assert backup_result.succeeded

    # Create proper metadata files for testing
    # 1. Create empty repair file with proper allocation (5MB should be enough)
    assert fallocate(metadata_repair_path, length='5M')

    # 2. Create a working metadata file that thin_repair can actually repair
    metadata_working_path = Path('/var/tmp/metadata_working')
    assert fallocate(metadata_working_path, length='5M')

    # 3. Populate the working metadata file with valid data from backup
    restore_working_cmd = f'thin_restore -i {metadata_backup_path} -o {metadata_working_path}'
    restore_working_result = run(restore_working_cmd)
    assert restore_working_result.succeeded, f'Failed to create working metadata: {restore_working_result.stderr}'

    # Update vol_info to include all metadata files
    vol_info.update(
        {
            'metadata_backup_path': metadata_backup_path,
            'metadata_repair_path': metadata_repair_path,
            'metadata_working_path': metadata_working_path,
        }
    )

    yield vol_info

    # Cleanup files
    run(f'rm -f {metadata_backup_path} {metadata_repair_path} {metadata_working_path}')


@pytest.fixture
def restored_thin_pool(metadata_backup: dict[str, Any]) -> Generator[dict[str, Any], None, None]:
    """Restore thin pool to a usable state after metadata operations.

    WARNING: Use this fixture ONLY for tests that specifically need an active thin pool
    (like thin_trim). Most DMPD tools are designed to work with "broken" metadata and
    should use setup_thin_metadata_for_dmpd instead, which preserves the intentionally
    inconsistent metadata state.

    This fixture uses thin_restore to repair the metadata and make the pool activatable.

    Args:
        metadata_backup: Metadata backup setup from metadata_backup fixture

    Yields:
        dict: Pool information with restored pool that can be activated
    """
    vol_info = metadata_backup.copy()
    vg_name = vol_info['vg_name']
    pool_name = vol_info['pool_name']
    swap_name = vol_info['swap_name']
    metadata_backup_path = vol_info['metadata_backup_path']
    metadata_dev = vol_info['metadata_dev']

    # Step 1: Use thin_restore to repair the metadata in the swap device
    logging.info(f'Restoring metadata to repair inconsistencies in {metadata_dev}')
    restore_cmd = f'thin_restore -i {metadata_backup_path} -o {metadata_dev}'
    restore_result = run(restore_cmd)
    assert restore_result.succeeded, f'Failed to restore metadata: {restore_result.stderr}'

    # Step 2: Deactivate both volumes before swapping metadata back
    pool_lv = LogicalVolume(name=pool_name, vg=vg_name)
    pool_lv.deactivate()  # Pool might already be deactivated
    swap_lv = LogicalVolume(name=swap_name, vg=vg_name)
    swap_lv.deactivate()
    udevadm_settle()

    # Step 3: "Swap back metadata" - restore the fixed metadata to the pool
    # This matches the "Swapping back metadata" step from python-stqe cleanup
    swap_back_cmd = f'lvconvert -y --thinpool {vg_name}/{pool_name} --poolmetadata {vg_name}/{swap_name}'
    swap_back_result = run(swap_back_cmd)
    assert swap_back_result.succeeded, f'Failed to swap metadata back to pool: {swap_back_result.stderr}'

    # Step 4: Reactivate the swap volume and verify device accessibility
    swap_lv = LogicalVolume(name=swap_name, vg=vg_name)
    activate_swap_result = swap_lv.activate()
    assert activate_swap_result, 'Failed to reactivate swap volume'
    udevadm_settle()

    # Verify the metadata device exists and update the path if needed
    metadata_dev_path = f'/dev/{vg_name}/{swap_name}'
    check_dev = run(f'ls -la {metadata_dev_path}')
    if not check_dev.succeeded:
        # Try alternative device path
        metadata_dev_path = f'/dev/mapper/{vg_name}-{swap_name}'
        check_dev_alt = run(f'ls -la {metadata_dev_path}')
        assert check_dev_alt.succeeded, f'Swap device not accessible at {metadata_dev_path}'

    # Update the metadata_dev path to the verified working path
    vol_info['metadata_dev'] = metadata_dev_path

    # Now the pool should have the fixed metadata and be activatable
    vol_info.update(
        {
            'pool_can_activate': True,
            'metadata_restored': True,
            'metadata_swapped_back': True,
        }
    )

    yield vol_info

    # Leave pool in deactivated state for cleanup
    pool_lv = LogicalVolume(name=pool_name, vg=vg_name)
    pool_lv.deactivate()  # Ignore errors


# Original fixtures refactored to use the new modular approach


@pytest.fixture
def setup_thin_pool_with_vols(
    thin_volumes_with_lifecycle: dict[str, str], swap_volume: dict[str, str]
) -> dict[str, str]:
    """Set up thin pool with thin volumes for DMPD testing.

    This is a backward-compatible fixture that combines the modular fixtures
    to recreate the original functionality. Uses the new modular approach internally.

    Args:
        thin_volumes_with_lifecycle: Thin volumes setup from thin_volumes_with_lifecycle fixture
        swap_volume: Swap volume setup from swap_volume fixture

    Returns:
        dict: Information about created volumes (compatible with original format)
    """
    pool_info = thin_volumes_with_lifecycle.copy()
    swap_info = swap_volume

    # Ensure both fixtures reference the same VG
    assert pool_info['vg_name'] == swap_info['vg_name'], 'Pool and swap must be in same VG'

    # Combine information from both fixtures to match original format
    volume_info = pool_info.copy()
    volume_info.update(
        {
            'swap_name': swap_info['swap_name'],
            'swap_path': swap_info['swap_path'],
        }
    )

    return volume_info


@pytest.fixture
def setup_thin_metadata_for_dmpd(install_dmpd: None, metadata_backup: dict[str, Any]) -> dict[str, Any]:
    """Set up thin metadata configuration for DMPD tool testing with snapshot support.

    This fixture creates the intended "broken" metadata state that DMPD tools are designed
    to detect, analyze, and repair. The metadata swap operation intentionally leaves the
    thin pool in an inconsistent state (transaction_id mismatch) to test that DMPD tools
    can properly handle corrupted/problematic metadata scenarios.

    Args:
        install_dmpd: DMPD package installation fixture
        metadata_backup: Metadata backup setup from metadata_backup fixture

    Returns:
        dict: Extended volume information with intentionally inconsistent metadata for testing
    """
    # DMPD packages are installed via install_dmpd fixture
    _ = install_dmpd

    # Use metadata_backup which preserves the "broken" metadata state for DMPD testing
    return metadata_backup.copy()


@pytest.fixture
def binary_metadata_file() -> Generator[Path, None, None]:
    """Create a pre-allocated binary file for thin metadata operations.

    This fixture creates a 5MB binary file in /var/tmp that can be used as output
    for thin_restore or other DMPD tools that require pre-allocated files.

    Yields:
        Path: Path to the allocated binary metadata file in /var/tmp

    Example:
        ```python
        def test_thin_restore(binary_metadata_file, metadata_backup):
            xml_file = metadata_backup['metadata_backup_path']
            binary_file = binary_metadata_file

            # thin_restore can now write to the pre-allocated binary file
            restore_result = dmpd.thin_restore(input=str(xml_file), output=str(binary_file))
            assert restore_result.succeeded
        ```
    """
    binary_file = Path('/var/tmp/thin_check_metadata.bin')
    assert fallocate(str(binary_file), length='5M'), f'Failed to allocate {binary_file}'
    logging.info(f'Allocated binary metadata file: {binary_file} (5MB)')

    yield binary_file

    # Cleanup
    if binary_file.exists():
        binary_file.unlink()
        logging.debug(f'Cleaned up binary metadata file: {binary_file}')


# Cache-specific fixtures


@pytest.fixture
def cache_volumes(setup_loopdev_vg: str) -> Generator[dict[str, Any], None, None]:
    """Create cache volumes for testing.

    Creates cache metadata, origin, and data logical volumes that can be used
    for creating cache pools and cached volumes.

    Args:
        setup_loopdev_vg: Volume group name from setup_loopdev_vg fixture

    Yields:
        dict: Information about the created cache volumes
    """
    vg_name = setup_loopdev_vg
    cache_meta_name = 'cache_meta'
    cache_origin_name = 'cache_origin'
    cache_data_name = 'cache_data'

    # Create cache metadata LV (12MB as per original setup)
    cache_meta_lv = LogicalVolume(name=cache_meta_name, vg=vg_name)
    assert cache_meta_lv.create(size='12M')

    # Create cache origin LV (300MB as per original setup)
    cache_origin_lv = LogicalVolume(name=cache_origin_name, vg=vg_name)
    assert cache_origin_lv.create(size='300M')

    # Create cache data LV (100MB as per original setup)
    cache_data_lv = LogicalVolume(name=cache_data_name, vg=vg_name)
    assert cache_data_lv.create(size='100M')

    cache_info = {
        'vg_name': vg_name,
        'cache_meta_name': cache_meta_name,
        'cache_origin_name': cache_origin_name,
        'cache_data_name': cache_data_name,
        'cache_meta_path': f'/dev/{vg_name}/{cache_meta_name}',
        'cache_origin_path': f'/dev/{vg_name}/{cache_origin_name}',
        'cache_data_path': f'/dev/{vg_name}/{cache_data_name}',
        'cache_meta_lv': cache_meta_lv,
        'cache_origin_lv': cache_origin_lv,
        'cache_data_lv': cache_data_lv,
    }

    yield cache_info

    # Cleanup
    cache_data_lv.remove()
    cache_origin_lv.remove()
    cache_meta_lv.remove()


@pytest.fixture
def cache_pool(cache_volumes: dict[str, Any]) -> dict[str, Any]:
    """Create cache pool by merging cache data and metadata volumes.

    Args:
        cache_volumes: Cache volumes setup from cache_volumes fixture

    Returns:
        dict: Extended cache information with pool details
    """
    cache_info = cache_volumes.copy()
    vg_name = cache_info['vg_name']
    cache_data_name = cache_info['cache_data_name']
    cache_meta_name = cache_info['cache_meta_name']

    # Use lvm convert to create cache pool (matching setup logic)
    convert_result = run(
        f'lvconvert -y --type cache-pool --cachemode writeback '
        f'--poolmetadata {vg_name}/{cache_meta_name} {vg_name}/{cache_data_name}'
    )
    assert convert_result.succeeded

    cache_info.update(
        {
            'cache_pool_created': True,
            'cache_pool_name': cache_data_name,  # Pool takes the name of data LV
            'cache_pool_path': f'/dev/{vg_name}/{cache_data_name}',
        }
    )

    return cache_info


@pytest.fixture
def cache_volume(cache_pool: dict[str, Any]) -> dict[str, Any]:
    """Create cached volume by adding origin to cache pool.

    Args:
        cache_pool: Cache pool setup from cache_pool fixture

    Returns:
        dict: Extended cache information with cached volume details
    """
    cache_info = cache_pool.copy()
    vg_name = cache_info['vg_name']
    cache_origin_name = cache_info['cache_origin_name']
    cache_pool_name = cache_info['cache_pool_name']

    # Convert origin LV to cached LV
    convert_result = run(
        f'lvconvert -y --type cache --cachepool {vg_name}/{cache_pool_name} {vg_name}/{cache_origin_name}'
    )
    assert convert_result.succeeded

    # Create ext4 filesystem on cached volume (matching setup logic)
    assert mkfs(f'/dev/{vg_name}/{cache_origin_name}', 'ext4', force=True)

    cache_info.update(
        {
            'cache_volume_created': True,
            'cached_lv_name': cache_origin_name,  # Origin LV becomes the cached LV
            'cached_lv_path': f'/dev/{vg_name}/{cache_origin_name}',
        }
    )

    return cache_info


@pytest.fixture
def cache_split(cache_volume: dict[str, Any]) -> dict[str, Any]:
    """Split cache volume to separate cache pool and origin.

    Args:
        cache_volume: Cache volume setup from cache_volume fixture

    Returns:
        dict: Extended cache information with split cache details
    """
    cache_info = cache_volume.copy()
    vg_name = cache_info['vg_name']
    cached_lv_name = cache_info['cached_lv_name']

    # Split cache (matching setup logic)
    split_result = run(f'lvconvert -y --splitcache {vg_name}/{cached_lv_name}')
    assert split_result.succeeded

    cache_info.update(
        {
            'cache_split': True,
        }
    )

    return cache_info


@pytest.fixture
def cache_metadata_swap(cache_split: dict[str, Any], swap_volume: dict[str, Any]) -> dict[str, Any]:
    """Perform cache metadata swap operation.

    Swaps cache metadata to the swap volume for DMPD testing.

    Args:
        cache_split: Cache split setup from cache_split fixture
        swap_volume: Swap volume setup from swap_volume fixture

    Returns:
        dict: Combined information with cache metadata device details
    """
    cache_info = cache_split.copy()
    swap_info = swap_volume

    # Ensure both fixtures reference the same VG
    assert cache_info['vg_name'] == swap_info['vg_name'], 'Cache and swap must be in same VG'

    vg_name = cache_info['vg_name']
    cache_pool_name = cache_info['cache_pool_name']
    swap_name = swap_info['swap_name']

    # Deactivate volumes before metadata swap
    cache_pool_lv = LogicalVolume(name=cache_pool_name, vg=vg_name)
    cache_pool_lv.deactivate()  # Ignore errors
    swap_lv = LogicalVolume(name=swap_name, vg=vg_name)
    swap_lv.deactivate()
    run('udevadm settle')

    # Swap cache metadata to swap volume (matching setup logic)
    convert_result = run(f'lvconvert -y --cachepool {vg_name}/{cache_pool_name} --poolmetadata {vg_name}/{swap_name}')
    assert convert_result.succeeded

    # Activate swap volume (now containing cache metadata)
    swap_lv = LogicalVolume(name=swap_name, vg=vg_name)
    swap_lv.activate()
    run('udevadm settle')

    # Use swap LV as cache metadata device
    cache_metadata_dev = f'/dev/{vg_name}/{swap_name}'

    # Combine information from both fixtures
    combined_info = cache_info.copy()
    combined_info.update(swap_info)
    combined_info.update(
        {
            'cache_metadata_dev': cache_metadata_dev,
            'cache_metadata_swapped': True,
        }
    )

    return combined_info


@pytest.fixture
def cache_metadata_backup(cache_metadata_swap: dict[str, Any]) -> Generator[dict[str, Any], None, None]:
    """Create cache metadata backup files for testing.

    Creates cache metadata dump and prepares repair files for testing.

    Args:
        cache_metadata_swap: Cache metadata swap setup from cache_metadata_swap fixture

    Yields:
        dict: Extended information with backup file paths
    """
    cache_info = cache_metadata_swap.copy()
    cache_metadata_dev = cache_info['cache_metadata_dev']
    cache_dump_path = Path('/var/tmp/cache_dump')
    cache_repair_path = Path('/var/tmp/cache_repair')

    # Create cache metadata dump (to match testing expectations)
    dump_result = dmpd.cache_dump(cache_metadata_dev, output=str(cache_dump_path))
    assert dump_result.succeeded

    # Create empty repair file with proper allocation (5MB should be enough)
    assert fallocate(cache_repair_path, length='5M')

    cache_info.update(
        {
            'cache_dump_path': cache_dump_path,
            'cache_repair_path': cache_repair_path,
        }
    )

    yield cache_info

    # Cleanup files
    run(f'rm -f {cache_dump_path} {cache_repair_path}')


@pytest.fixture
def setup_cache_metadata_for_dmpd(install_dmpd: None, cache_metadata_backup: dict[str, Any]) -> dict[str, Any]:
    """Set up cache metadata configuration for DMPD tool testing.

    This fixture creates the necessary cache metadata setup that DMPD cache tools
    can operate on. Unlike thin metadata which intentionally creates "broken" state,
    cache metadata swap creates a working metadata device that cache tools can analyze.

    Args:
        install_dmpd: DMPD package installation fixture
        cache_metadata_backup: Cache metadata backup setup from cache_metadata_backup fixture

    Returns:
        dict: Extended cache information for DMPD testing
    """
    # DMPD packages are installed via install_dmpd fixture
    _ = install_dmpd

    # Use cache_metadata_backup which provides working cache metadata for DMPD testing
    return cache_metadata_backup.copy()
