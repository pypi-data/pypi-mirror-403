# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Device Mapper test fixtures.

This module provides fixtures for testing Device Mapper (dm) functionality.
Each fixture creates a DM device of a specific type and handles cleanup automatically.

Available Fixtures:
    Basic DM Targets:
    - linear_dm_device: Creates a linear device (passthrough to backing device)
    - error_dm_device: Creates an error device (returns I/O errors, no backing device)
    - zero_dm_device: Creates a zero device (returns zeros, no backing device)
    - delay_dm_device: Creates a delay device (adds I/O latency)
    - delay_device_positional: Creates a delay device using positional arguments
    - flakey_dm_device: Creates a flakey device (simulates unreliable storage)

    Thin Provisioning:
    - thin_pool_dm_device: Creates a thin-pool device
    - thin_dm_device: Creates a thin device from a thin-pool

    Caching:
    - cache_dm_device: Creates a cache device (dm-cache)

    VDO (Deduplication/Compression):
    - vdo_formatted_device: Formats a device with vdoformat
    - vdo_dm_device: Creates a VDO device

    Utilities:
    - mounted_dm_device: Formats and mounts any DM device

Fixture Dependencies:
    Most fixtures require the loop_devices fixture from common_fixtures:
    - linear_dm_device: 1 loop device
    - delay_dm_device: 1-3 loop devices (depending on argument format)
    - flakey_dm_device: 1 loop device
    - thin_pool_dm_device: 2 loop devices (data + metadata)
    - thin_dm_device: thin_pool_dm_device (which needs 2 loop devices)
    - cache_dm_device: 3 loop devices (origin + cache + metadata)
    - vdo_formatted_device: 1 loop device + load_vdo_module
    - vdo_dm_device: vdo_formatted_device

    Devices without backing storage:
    - error_dm_device: No backing device required
    - zero_dm_device: No backing device required

Common Usage:
    1. Basic linear device:
        @pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 512}], indirect=True)
        def test_linear(linear_dm_device):
            assert linear_dm_device.table is not None

    2. Delay device with custom delay:
        @pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 512}], indirect=True)
        @pytest.mark.parametrize('delay_dm_device', [{'delay_ms': 200}], indirect=True)
        def test_delay(delay_dm_device):
            assert 'delay' in delay_dm_device.table

    3. Thin provisioning:
        @pytest.mark.parametrize('loop_devices', [{'count': 2, 'size_mb': 512}], indirect=True)
        def test_thin(thin_dm_device):
            assert 'thin' in thin_dm_device.table

    4. VDO device:
        @pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 8192}], indirect=True)
        def test_vdo(vdo_dm_device):
            assert 'vdo' in vdo_dm_device.table

    5. Error device (no backing storage):
        def test_error(error_dm_device):
            assert 'error' in error_dm_device.table

Error Handling:
    - Device creation failures cause test to fail with pytest.fail()
    - Module loading failures (VDO) skip the test
    - vdoformat failures skip the test
    - Device cleanup runs even if test fails
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from sts.blockdevice import BlockDevice
from sts.dm import (
    CacheDevice,
    DelayDevice,
    DmDevice,
    ErrorDevice,
    FlakeyDevice,
    LinearDevice,
    ThinDevice,
    ThinPoolDevice,
    VdoDevice,
    ZeroDevice,
)
from sts.udevadm import udevadm_settle
from sts.utils.cmdline import run
from sts.utils.files import Directory, mkfs, mount, umount, write_zeroes
from sts.vdo import VdoFormat

if TYPE_CHECKING:
    from collections.abc import Generator


# Default Linear device configuration
DEFAULT_LINEAR_DM_NAME = 'test-linear'

# Default Delay device configuration
DEFAULT_DELAY_DM_NAME = 'test-delay'
DEFAULT_DELAY_MS = 100  # Default delay in milliseconds

# Default Error device configuration
DEFAULT_ERROR_DM_NAME = 'test-error'
DEFAULT_ERROR_SIZE_SECTORS = 2097152  # 1 GB in 512-byte sectors

# Default Zero device configuration
DEFAULT_ZERO_DM_NAME = 'test-zero'
DEFAULT_ZERO_SIZE_SECTORS = 2097152  # 1 GB in 512-byte sectors

# Default Thin Pool device configuration
DEFAULT_THIN_POOL_DM_NAME = 'test-thin-pool'
DEFAULT_THIN_BLOCK_SIZE_SECTORS = 128  # 64KB in 512-byte sectors
DEFAULT_THIN_LOW_WATER_MARK = 0  # Auto

# Default Thin device configuration
DEFAULT_THIN_DM_NAME = 'test-thin'
DEFAULT_THIN_SIZE_SECTORS = 2097152  # 1 GB in 512-byte sectors

# Default Flakey device configuration
DEFAULT_FLAKEY_DM_NAME = 'test-flakey'
DEFAULT_FLAKEY_UP_INTERVAL = 60  # Seconds device is reliable
DEFAULT_FLAKEY_DOWN_INTERVAL = 0  # Seconds device is unreliable (0 = always up for basic tests)

# Default Cache device configuration
DEFAULT_CACHE_DM_NAME = 'test-cache'
DEFAULT_CACHE_BLOCK_SIZE_SECTORS = 512  # 256KB in 512-byte sectors

# Default VDO device configuration
# Logical size larger than physical to test thin provisioning
DEFAULT_VDO_LOGICAL_SIZE_SECTORS = 20971520  # 10 GB = 20971520 sectors of 512 bytes
DEFAULT_VDO_LOGICAL_SIZE_HUMAN = '10G'
DEFAULT_VDO_DM_NAME = 'test-vdo'


def create_dm_device_from_targets(dm_name: str, targets: list[DmDevice]) -> DmDevice | None:
    """Create a DM device from multiple targets.

    This is a helper function for creating concatenated or multi-target devices.

    Args:
        dm_name: Device mapper name
        targets: List of DmDevice instances (in configuration state)

    Returns:
        DmDevice instance or None if creation failed
    """
    if not targets:
        return None

    # Build table from targets
    table_lines = [str(target) for target in targets]
    table = '\n'.join(table_lines)

    logging.info(f'Creating device {dm_name} with table: {table}')
    result = run(f'dmsetup create {dm_name} --table "{table}"')

    if result.failed:
        logging.error(f'Failed to create device {dm_name}: {result.stderr}')
        return None

    return DmDevice.get_by_name(dm_name)


@pytest.fixture
def linear_dm_device(loop_devices: list[str], request: pytest.FixtureRequest) -> Generator[LinearDevice, None, None]:
    """Fixture that creates and cleans up a linear device mapper device.

    This fixture creates a linear DM device using the first loop device
    and handles cleanup automatically.

    Args:
        loop_devices: List of loop device paths from loop_devices fixture
        request: Pytest fixture request for accessing parameters

    Yields:
        LinearDevice instance for the linear device

    Parameters (via pytest.mark.parametrize with indirect=True):
        - dm_name (str): Device mapper name (default: 'test-linear')
        - size (int): Size in sectors (default: full device size)
        - offset (int): Offset in source device (default: 0)

    Example:
        ```python
        @pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 512}], indirect=True)
        def test_linear_device(linear_dm_device):
            dm_dev = linear_dm_device
            assert dm_dev is not None
            assert 'linear' in dm_dev.table
        ```
    """
    device_path = loop_devices[0]
    params = getattr(request, 'param', {})

    dm_name = params.get('dm_name', DEFAULT_LINEAR_DM_NAME)
    size = params.get('size')
    offset = params.get('offset', 0)

    # Clean up any existing device from previous failed runs
    existing = DmDevice.get_by_name(dm_name)
    if existing:
        existing.remove(force=True)

    # Create linear device
    device = BlockDevice(path=device_path)
    linear_dev = LinearDevice.from_block_device(device, size_sectors=size, offset=offset)
    if not linear_dev.create(dm_name):
        pytest.fail(f'Failed to create linear device {dm_name}')

    # Wait for udev to process device creation
    udevadm_settle()

    logging.info(f'Created linear device: {linear_dev.dm_name}')
    yield linear_dev

    # Cleanup: remove the device
    assert linear_dev.remove(force=True)


@pytest.fixture
def error_dm_device(request: pytest.FixtureRequest) -> Generator[ErrorDevice, None, None]:
    """Fixture that creates and cleans up an error device mapper device.

    This fixture creates an error DM device that returns I/O errors
    for all operations. Unlike other DM devices, it doesn't require
    a backing device.

    Args:
        request: Pytest fixture request for accessing parameters

    Yields:
        ErrorDevice instance for the error device

    Parameters (via pytest.mark.parametrize with indirect=True):
        - dm_name (str): Device mapper name (default: 'test-error')
        - size (int): Size in sectors (default: 2097152 = 1GB)

    Example:
        ```python
        def test_error_device(error_dm_device):
            dm_dev = error_dm_device
            assert dm_dev is not None
            assert 'error' in dm_dev.table
        ```

        With custom size:

        ```python
        @pytest.mark.parametrize('error_dm_device', [{'size': 1000000}], indirect=True)
        def test_error_custom_size(error_dm_device):
            dm_dev = error_dm_device
            assert dm_dev.size_sectors == 1000000
        ```
    """
    params = getattr(request, 'param', {})

    dm_name = params.get('dm_name', DEFAULT_ERROR_DM_NAME)
    size = params.get('size', DEFAULT_ERROR_SIZE_SECTORS)

    # Clean up any existing device from previous failed runs
    existing = DmDevice.get_by_name(dm_name)
    if existing:
        existing.remove(force=True)

    # Create error device (start is always 0 for single-segment devices)
    error_dev = ErrorDevice.create_config(start=0, size=size)
    if not error_dev.create(dm_name):
        pytest.fail(f'Failed to create error device {dm_name}')

    # Wait for udev to process device creation
    udevadm_settle()

    logging.info(f'Created error device: {error_dev.dm_name}')
    yield error_dev

    # Cleanup: remove the device
    assert error_dev.remove(force=True)


@pytest.fixture
def zero_dm_device(request: pytest.FixtureRequest) -> Generator[ZeroDevice, None, None]:
    """Fixture that creates and cleans up a zero device mapper device.

    This fixture creates a zero DM device that returns zeros on read
    and discards writes. Unlike other DM devices, it doesn't require
    a backing device.

    Args:
        request: Pytest fixture request for accessing parameters

    Yields:
        ZeroDevice instance for the zero device

    Parameters (via pytest.mark.parametrize with indirect=True):
        - dm_name (str): Device mapper name (default: 'test-zero')
        - size (int): Size in sectors (default: 2097152 = 1GB)

    Example:
        ```python
        def test_zero_device(zero_dm_device):
            dm_dev = zero_dm_device
            assert dm_dev is not None
            assert 'zero' in dm_dev.table
        ```

        With custom size:

        ```python
        @pytest.mark.parametrize('zero_dm_device', [{'size': 1000000}], indirect=True)
        def test_zero_custom_size(zero_dm_device):
            dm_dev = zero_dm_device
            assert dm_dev.size_sectors == 1000000
        ```
    """
    params = getattr(request, 'param', {})

    dm_name = params.get('dm_name', DEFAULT_ZERO_DM_NAME)
    size = params.get('size', DEFAULT_ZERO_SIZE_SECTORS)

    # Create zero device (start is always 0 for single-segment devices)
    zero_dev = ZeroDevice.create_config(start=0, size=size)
    if not zero_dev.create(dm_name):
        pytest.fail(f'Failed to create zero device {dm_name}')

    # Wait for udev to process device creation
    udevadm_settle()

    logging.info(f'Created zero device: {zero_dev.dm_name}')
    yield zero_dev

    # Cleanup: remove the device
    assert zero_dev.remove(force=True)


@pytest.fixture
def delay_dm_device(loop_devices: list[str], request: pytest.FixtureRequest) -> Generator[DmDevice, None, None]:
    """Fixture that creates and cleans up a delay device mapper device.

    This fixture creates a delay DM device using the loop device(s)
    and handles cleanup automatically. Supports 3, 6, and 9 argument formats.

    Args:
        loop_devices: List of loop device paths from loop_devices fixture
        request: Pytest fixture request for accessing parameters

    Yields:
        DmDevice instance for the delay device

    Parameters (via pytest.mark.parametrize with indirect=True):
        - dm_name (str): Device mapper name (default: 'test-delay')
        - size (int): Size in sectors (default: full device size)

        3-argument format (default - same delay for all operations):
        - delay_ms (int): Delay for all operations in milliseconds (default: 100)
        - offset (int): Offset in source device sectors (default: 0)

        6-argument format (separate read and write/flush):
        - read_delay_ms (int): Delay for read operations (replaces delay_ms)
        - read_offset (int): Offset for read operations
        - write_delay_ms (int): Delay for write and flush operations
        - write_offset (int): Offset for write operations
        - write_device_index (int): Index in loop_devices for write device (default: 0)

        9-argument format (separate read, write, and flush):
        - All of the above, plus:
        - flush_delay_ms (int): Delay for flush operations
        - flush_offset (int): Offset for flush operations
        - flush_device_index (int): Index in loop_devices for flush device (default: 0)

    Example:
        ```python
        # Basic 3-argument delay (100ms for all operations)
        @pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 512}], indirect=True)
        def test_delay_device(delay_dm_device):
            dm_dev = delay_dm_device
            assert dm_dev is not None
            assert 'delay' in dm_dev.table


        # 6-argument format (different devices for read vs write)
        @pytest.mark.parametrize('loop_devices', [{'count': 2, 'size_mb': 512}], indirect=True)
        @pytest.mark.parametrize(
            'delay_dm_device', [{'read_delay_ms': 0, 'write_delay_ms': 400, 'write_device_index': 1}], indirect=True
        )
        def test_delay_rw(delay_dm_device):
            dm_dev = delay_dm_device
            assert 'delay' in dm_dev.table


        # 9-argument format (different delays for read, write, flush)
        @pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 512}], indirect=True)
        @pytest.mark.parametrize(
            'delay_dm_device', [{'read_delay_ms': 50, 'write_delay_ms': 100, 'flush_delay_ms': 333}], indirect=True
        )
        def test_delay_rwf(delay_dm_device):
            dm_dev = delay_dm_device
            assert 'delay' in dm_dev.table
        ```
    """
    params = getattr(request, 'param', {})

    dm_name = params.get('dm_name', DEFAULT_DELAY_DM_NAME)
    size = params.get('size')

    # Clean up any existing device from previous failed runs
    existing = DmDevice.get_by_name(dm_name)
    if existing:
        existing.remove(force=True)

    # Determine which format to use based on parameters
    read_delay_ms = params.get('read_delay_ms')
    write_delay_ms = params.get('write_delay_ms')
    flush_delay_ms = params.get('flush_delay_ms')

    # Get devices
    read_device = BlockDevice(path=loop_devices[0])

    if read_delay_ms is not None and write_delay_ms is not None:
        # 6 or 9 argument format
        read_offset = params.get('read_offset', 0)
        write_offset = params.get('write_offset', 0)
        write_device_index = params.get('write_device_index', 0)
        write_device = BlockDevice(path=loop_devices[write_device_index])

        if flush_delay_ms is not None:
            # 9 argument format
            flush_offset = params.get('flush_offset', 0)
            flush_device_index = params.get('flush_device_index', 0)
            flush_device = BlockDevice(path=loop_devices[flush_device_index])

            # Calculate size accounting for offsets to avoid accessing beyond device boundaries
            if size is None and read_device.size is not None:
                max_offset = max(read_offset, write_offset, flush_offset)
                size = read_device.size // read_device.sector_size - max_offset

            delay_dev = DelayDevice.from_block_devices_rwf(
                read_device=read_device,
                read_offset=read_offset,
                read_delay_ms=read_delay_ms,
                write_device=write_device,
                write_offset=write_offset,
                write_delay_ms=write_delay_ms,
                flush_device=flush_device,
                flush_offset=flush_offset,
                flush_delay_ms=flush_delay_ms,
                size=size,
            )
        else:
            # 6 argument format
            # Calculate size accounting for offsets to avoid accessing beyond device boundaries
            if size is None and read_device.size is not None:
                max_offset = max(read_offset, write_offset)
                size = read_device.size // read_device.sector_size - max_offset

            delay_dev = DelayDevice.from_block_devices_rw(
                read_device=read_device,
                read_offset=read_offset,
                read_delay_ms=read_delay_ms,
                write_device=write_device,
                write_offset=write_offset,
                write_delay_ms=write_delay_ms,
                size=size,
            )
    else:
        # 3 argument format (default)
        delay_ms = params.get('delay_ms', DEFAULT_DELAY_MS)
        offset = params.get('offset', 0)

        # Calculate size accounting for offset to avoid accessing beyond device boundaries
        if size is None and read_device.size is not None:
            size = read_device.size // read_device.sector_size - offset

        delay_dev = DelayDevice.from_block_device(
            device=read_device,
            delay_ms=delay_ms,
            offset=offset,
            size_sectors=size,
        )

    if not delay_dev.create(dm_name):
        pytest.fail(f'Failed to create delay device {dm_name}')

    logging.info(f'Created delay device: {delay_dev.dm_name}')
    yield delay_dev

    # Cleanup: remove the device
    assert delay_dev.remove(force=True)


@pytest.fixture
def delay_device_positional(
    loop_devices: list[str], request: pytest.FixtureRequest
) -> Generator[DelayDevice, None, None]:
    """Fixture that creates a delay device using create_positional method.

    This fixture creates a delay DM device using DelayDevice.create_positional()
    and handles cleanup automatically. Supports 3, 6, and 9 argument formats.

    Args:
        loop_devices: List of loop device paths from loop_devices fixture
        request: Pytest fixture request for accessing parameters

    Yields:
        DelayDevice instance

    Parameters (via pytest.mark.parametrize with indirect=True):
        - dm_name (str): Device mapper name (default: 'test-delay-positional')
        - offset (int): Read offset in sectors (default: 0)
        - delay_ms (int): Read delay in milliseconds (default: 100)

        6-argument format (when write_device_path is provided):
        - write_offset (int): Write offset in sectors (default: 0)
        - write_delay_ms (int): Write delay in milliseconds
        - write_device_index (int): Index in loop_devices for write device (default: 0)

        9-argument format (when flush_device_path is also provided):
        - flush_offset (int): Flush offset in sectors (default: 0)
        - flush_delay_ms (int): Flush delay in milliseconds
        - flush_device_index (int): Index in loop_devices for flush device (default: 0)

    Example:
        ```python
        # 3-argument format
        @pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 512}], indirect=True)
        @pytest.mark.parametrize('delay_device_positional', [{'delay_ms': 100}], indirect=True)
        def test_positional_3arg(delay_device_positional):
            assert delay_device_positional.arg_format == '3'


        # 6-argument format
        @pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 512}], indirect=True)
        @pytest.mark.parametrize(
            'delay_device_positional', [{'delay_ms': 0, 'write_delay_ms': 400, 'write_offset': 4096}], indirect=True
        )
        def test_positional_6arg(delay_device_positional):
            assert delay_device_positional.arg_format == '6'
        ```
    """
    params = getattr(request, 'param', {})

    dm_name = params.get('dm_name', 'test-delay-positional')
    device_path = loop_devices[0]
    offset = params.get('offset', 0)
    delay_ms = params.get('delay_ms', DEFAULT_DELAY_MS)

    # Get write parameters (6-arg format)
    write_delay_ms = params.get('write_delay_ms')
    write_offset = params.get('write_offset', 0)
    write_device_index = params.get('write_device_index', 0)

    # Get flush parameters (9-arg format)
    flush_delay_ms = params.get('flush_delay_ms')
    flush_offset = params.get('flush_offset', 0)
    flush_device_index = params.get('flush_device_index', 0)

    # Calculate size accounting for offsets
    block_device = BlockDevice(path=device_path)
    if write_delay_ms is not None:
        if flush_delay_ms is not None:
            max_offset = max(offset, write_offset, flush_offset)
        else:
            max_offset = max(offset, write_offset)
    else:
        max_offset = offset
    if block_device.size is None:
        pytest.fail(f'Cannot determine size of device {device_path}')
    size = block_device.size // block_device.sector_size - max_offset

    # Clean up any existing device
    existing = DmDevice.get_by_name(dm_name)
    if existing:
        existing.remove(force=True)

    # Build creation arguments
    create_args: dict = {
        'device_path': device_path,
        'offset': offset,
        'delay_ms': delay_ms,
        'size': size,
    }

    if write_delay_ms is not None:
        write_device_path = loop_devices[write_device_index]
        create_args.update(
            {
                'write_device_path': write_device_path,
                'write_offset': write_offset,
                'write_delay_ms': write_delay_ms,
            }
        )

        if flush_delay_ms is not None:
            flush_device_path = loop_devices[flush_device_index]
            create_args.update(
                {
                    'flush_device_path': flush_device_path,
                    'flush_offset': flush_offset,
                    'flush_delay_ms': flush_delay_ms,
                }
            )

    delay_dev = DelayDevice.create_positional(**create_args)

    if not delay_dev.create(dm_name):
        pytest.fail(f'Failed to create delay device {dm_name}')

    logging.info(f'Created delay device (positional): {delay_dev.dm_name}')
    yield delay_dev

    # Cleanup
    assert delay_dev.remove(force=True)


@pytest.fixture
def mounted_dm_device(
    request: pytest.FixtureRequest,
) -> Generator[tuple[DmDevice, str], None, None]:
    """Fixture that formats and mounts a DM device.

    This fixture takes a DM device (from another fixture), creates a filesystem,
    mounts it, and handles cleanup automatically.

    Args:
        request: Pytest fixture request for accessing parameters and other fixtures

    Yields:
        Tuple of (DmDevice, mount_point_path)

    Parameters (via pytest.mark.parametrize with indirect=True):
        - dm_device_fixture (str): Name of fixture providing DM device (default: 'delay_dm_device')
        - fs_type (str): Filesystem type (default: 'ext4')
        - mount_point (str): Mount point path (default: '/mnt/sts-dm-test')

    Example:
        ```python
        @pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 512}], indirect=True)
        @pytest.mark.parametrize('delay_dm_device', [{'delay_ms': 0}], indirect=True)
        def test_mounted_device(mounted_dm_device):
            dm_device, mount_point = mounted_dm_device
            # Device is formatted and mounted at mount_point
        ```
    """
    params = getattr(request, 'param', {})

    dm_device_fixture = params.get('dm_device_fixture', 'delay_dm_device')
    fs_type = params.get('fs_type', 'ext4')
    mount_point = params.get('mount_point', '/mnt/sts-dm-test')

    # Get the DM device from the specified fixture
    dm_device = request.getfixturevalue(dm_device_fixture)
    dm_device_path = dm_device.dm_device_path

    if dm_device_path is None:
        pytest.fail('DM device path not available')

    # Create filesystem
    logging.info(f'Creating {fs_type} filesystem on {dm_device_path}')
    if not mkfs(dm_device_path, fs_type, force=True):
        pytest.fail(f'Failed to create {fs_type} filesystem on {dm_device_path}')

    # Create mount point and mount
    mount_dir = Directory(Path(mount_point), create=True)
    if not mount_dir.exists:
        pytest.fail(f'Failed to create mount point {mount_point}')

    logging.info(f'Mounting {dm_device_path} at {mount_point}')
    if not mount(dm_device_path, mount_point):
        mount_dir.remove_dir()
        pytest.fail(f'Failed to mount {dm_device_path} at {mount_point}')

    yield dm_device, mount_point

    # Cleanup: unmount and remove mount point
    if not umount(mount_point):
        logging.warning(f'Failed to unmount {mount_point}')
    mount_dir.remove_dir()
    logging.info(f'Unmounted and removed {mount_point}')


@pytest.fixture
def vdo_formatted_device(
    load_vdo_module: str, loop_devices: list[str], request: pytest.FixtureRequest
) -> tuple[str, BlockDevice]:
    """Fixture that provides a vdoformat-formatted device.

    This fixture formats a loop device with vdoformat for VDO testing.
    Requires the loop_devices fixture to provide the backing device.

    Args:
        load_vdo_module: VDO module fixture ensuring module is loaded
        loop_devices: List of loop device paths from loop_devices fixture
        request: Pytest fixture request for accessing parameters

    Returns:
        Tuple of (device_path, BlockDevice)

    Parameters (via pytest.mark.parametrize with indirect=True):
        - logical_size (str): Logical size for vdoformat (default: '1G')
        - slab_bits (int): Slab size as power of 2 (default: None)
        - uds_memory_size (float): Memory for deduplication index (default: None)
        - uds_sparse (bool): Use sparse index (default: False)
        - force (bool): Force format even if VDO exists (default: True)

    Example:
        ```python
        @pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 8192}], indirect=True)
        def test_vdo_format(vdo_formatted_device):
            device_path, block_device = vdo_formatted_device
            assert device_path.startswith('/dev/loop')
        ```

        With custom format options:

        ```python
        @pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 8192}], indirect=True)
        @pytest.mark.parametrize('vdo_formatted_device', [{'logical_size': '2G', 'slab_bits': 17}], indirect=True)
        def test_vdo_custom_format(vdo_formatted_device):
            device_path, block_device = vdo_formatted_device
        ```
    """
    _ = load_vdo_module  # Ensure VDO module is loaded

    device_path = loop_devices[0]
    params = getattr(request, 'param', {})

    logical_size = params.get('logical_size', DEFAULT_VDO_LOGICAL_SIZE_HUMAN)
    slab_bits = params.get('slab_bits')
    uds_memory_size = params.get('uds_memory_size')
    uds_sparse = params.get('uds_sparse', False)
    force = params.get('force', True)

    # Format device with VdoFormat class
    vdo_format = VdoFormat(
        device=device_path,
        logical_size=logical_size,
        slab_bits=slab_bits,
        uds_memory_size=uds_memory_size,
        uds_sparse=uds_sparse,
        force=force,
    )

    if not vdo_format.format():
        pytest.fail(f'vdoformat failed on {device_path} (tool may not be installed)')

    logging.info(f'Formatted {device_path} with vdoformat (logical_size={logical_size})')

    device = BlockDevice(path=device_path)
    return device_path, device


@pytest.fixture
def vdo_dm_device(
    vdo_formatted_device: tuple[str, BlockDevice], request: pytest.FixtureRequest
) -> Generator[DmDevice, None, None]:
    """Fixture that creates and cleans up a VDO device mapper device.

    This fixture creates a VDO device using dmsetup and handles cleanup.
    Uses the vdo_formatted_device fixture for the backing storage.

    Args:
        vdo_formatted_device: Tuple of (device_path, BlockDevice) from vdo_formatted_device fixture
        request: Pytest fixture request for accessing parameters

    Yields:
        DmDevice instance for the VDO device

    Parameters (via pytest.mark.parametrize with indirect=True):
        - dm_name (str): Device mapper name (default: 'test-vdo')
        - logical_size_sectors (int): Logical size in sectors (default: 2097152)
        - minimum_io_size (int): Minimum I/O size in bytes (default: 4096)
        - block_map_cache_size_mb (int): Block map cache size in MB (default: 128)
        - block_map_period (int): Block map era length (default: 16380)
        - ack (int): Number of ack threads (default: None)
        - bio (int): Number of bio threads (default: None)
        - bioRotationInterval (int): Bio rotation interval (default: None)
        - cpu (int): Number of CPU threads (default: None)
        - hash (int): Number of hash zone threads (default: None)
        - logical (int): Number of logical threads (default: None)
        - physical (int): Number of physical threads (default: None)
        - maxDiscard (int): Maximum discard size (default: None)
        - deduplication (bool): Enable deduplication (default: True)
        - compression (bool): Enable compression (default: False)

    Example:
        ```python
        @pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 8192}], indirect=True)
        def test_vdo_device(vdo_dm_device):
            vdo_dev = vdo_dm_device
            assert vdo_dev is not None
            assert 'vdo' in vdo_dev.table
        ```

        With custom VDO options:

        ```python
        @pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 8192}], indirect=True)
        @pytest.mark.parametrize('vdo_dm_device', [{'compression': True, 'ack': 2, 'bio': 4}], indirect=True)
        def test_vdo_with_options(vdo_dm_device):
            vdo_dev = vdo_dm_device
            assert 'compression on' in vdo_dev.table
        ```
    """
    _, device = vdo_formatted_device
    params = dict(getattr(request, 'param', {}))

    dm_name = params.pop('dm_name', DEFAULT_VDO_DM_NAME)
    logical_size_sectors = params.pop('logical_size_sectors', DEFAULT_VDO_LOGICAL_SIZE_SECTORS)

    # Required VDO parameters with defaults
    minimum_io_size = params.pop('minimum_io_size', 4096)
    block_map_cache_size_mb = params.pop('block_map_cache_size_mb', 128)
    block_map_period = params.pop('block_map_period', 16380)

    # Clean up any existing device from previous failed runs
    run(f'dmsetup remove -f {dm_name}')

    # Create VDO device using VdoDevice.from_block_device()
    vdo_dev = VdoDevice.from_block_device(
        device=device,
        logical_size_sectors=logical_size_sectors,
        minimum_io_size=minimum_io_size,
        block_map_cache_size_mb=block_map_cache_size_mb,
        block_map_period=block_map_period,
        **params,
    )
    if not vdo_dev.create(dm_name):
        pytest.fail(f'Failed to create VDO device {dm_name}')

    logging.info(f'Created VDO device: {vdo_dev.dm_name}')
    yield vdo_dev

    # Cleanup: remove the device
    assert vdo_dev.remove(force=True)


@pytest.fixture
def thin_pool_dm_device(
    loop_devices: list[str], request: pytest.FixtureRequest
) -> Generator[ThinPoolDevice, None, None]:
    """Fixture that creates and cleans up a thin-pool device mapper device.

    This fixture creates a thin-pool DM device using two loop devices
    (one for metadata, one for data) and handles cleanup automatically.

    Args:
        loop_devices: List of loop device paths from loop_devices fixture
            - First device: data device
            - Second device: metadata device (smaller is fine)
        request: Pytest fixture request for accessing parameters

    Yields:
        ThinPoolDevice instance for the thin-pool device

    Parameters (via pytest.mark.parametrize with indirect=True):
        - dm_name (str): Device mapper name (default: 'test-thin-pool')
        - block_size_sectors (int): Block size in sectors (default: 128 = 64KB)
        - low_water_mark (int): Low water mark in blocks (default: 0 = auto)
        - features (list[str]): Pool features (default: ['skip_block_zeroing'])

    Example:
        ```python
        @pytest.mark.parametrize('loop_devices', [{'count': 2, 'size_mb': 512}], indirect=True)
        def test_thin_pool(thin_pool_dm_device):
            pool = thin_pool_dm_device
            assert pool is not None
            assert 'thin-pool' in pool.table
        ```
    """
    if len(loop_devices) < 2:
        pytest.fail('Thin pool requires at least 2 loop devices (data and metadata)')

    data_device_path = loop_devices[0]
    metadata_device_path = loop_devices[1]
    params = getattr(request, 'param', {})

    dm_name = params.get('dm_name', DEFAULT_THIN_POOL_DM_NAME)
    block_size_sectors = params.get('block_size_sectors', DEFAULT_THIN_BLOCK_SIZE_SECTORS)
    low_water_mark = params.get('low_water_mark', DEFAULT_THIN_LOW_WATER_MARK)
    features = params.get('features', ['skip_block_zeroing'])

    # Clean up any existing device from previous failed runs
    existing = DmDevice.get_by_name(dm_name)
    if existing:
        existing.remove(force=True)

    # Zero the metadata device (required for fresh thin-pool)
    if not write_zeroes(metadata_device_path, bs=4096, count=1, conv='fsync'):
        pytest.fail('Failed to zero metadata device')

    # Create block devices
    data_device = BlockDevice(path=data_device_path)
    metadata_device = BlockDevice(path=metadata_device_path)

    # Create thin-pool device
    pool_dev = ThinPoolDevice.from_block_devices(
        metadata_device=metadata_device,
        data_device=data_device,
        block_size_sectors=block_size_sectors,
        low_water_mark=low_water_mark,
        features=features,
    )
    if not pool_dev.create(dm_name):
        pytest.fail(f'Failed to create thin-pool device {dm_name}')

    # Wait for udev to process device creation
    udevadm_settle()

    logging.info(f'Created thin-pool device: {pool_dev.dm_name}')
    yield pool_dev

    # Cleanup: remove the device
    assert pool_dev.remove(force=True)


@pytest.fixture
def thin_dm_device(
    thin_pool_dm_device: ThinPoolDevice, request: pytest.FixtureRequest
) -> Generator[ThinDevice, None, None]:
    """Fixture that creates and cleans up a thin device from a thin-pool.

    This fixture creates a thin DM device from a thin-pool device
    and handles cleanup automatically. Uses the pool's create_thin method
    for proper parent-child tracking.

    Args:
        thin_pool_dm_device: ThinPoolDevice fixture providing the pool
        request: Pytest fixture request for accessing parameters

    Yields:
        ThinDevice instance for the thin device

    Parameters (via pytest.mark.parametrize with indirect=True):
        - dm_name (str): Device mapper name (default: 'test-thin')
        - thin_id (int): Thin device ID within pool (default: 0)
        - size (int): Size in sectors (default: 2097152 = 1GB)

    Example:
        ```python
        @pytest.mark.parametrize('loop_devices', [{'count': 2, 'size_mb': 512}], indirect=True)
        def test_thin_device(thin_dm_device):
            thin = thin_dm_device
            assert thin is not None
            assert 'thin' in thin.table
        ```
    """
    params = getattr(request, 'param', {})

    dm_name = params.get('dm_name', DEFAULT_THIN_DM_NAME)
    thin_id = params.get('thin_id', 0)
    size = params.get('size', DEFAULT_THIN_SIZE_SECTORS)

    # Clean up any existing device from previous failed runs
    existing = DmDevice.get_by_name(dm_name)
    if existing:
        existing.remove(force=True)

    # Create thin device using pool's create_thin method
    thin_dev = thin_pool_dm_device.create_thin(
        thin_id=thin_id,
        size=size,
        dm_name=dm_name,
    )
    if thin_dev is None:
        pytest.fail(f'Failed to create thin device {dm_name}')

    # Wait for udev to process device creation
    udevadm_settle()

    logging.info(f'Created thin device: {thin_dev.dm_name}')
    yield thin_dev

    # Cleanup: use pool's delete_thin method for proper cleanup
    thin_pool_dm_device.delete_thin(thin_id, force=True)


@pytest.fixture
def flakey_dm_device(loop_devices: list[str], request: pytest.FixtureRequest) -> Generator[FlakeyDevice, None, None]:
    """Fixture that creates and cleans up a flakey device mapper device.

    This fixture creates a flakey DM device that simulates unreliable
    storage behavior. The device is reliable for up_interval seconds,
    then unreliable for down_interval seconds, cycling.

    Args:
        loop_devices: List of loop device paths from loop_devices fixture
        request: Pytest fixture request for accessing parameters

    Yields:
        FlakeyDevice instance for the flakey device

    Parameters (via pytest.mark.parametrize with indirect=True):
        - dm_name (str): Device mapper name (default: 'test-flakey')
        - up_interval (int): Seconds device is reliable (default: 60)
        - down_interval (int): Seconds device is unreliable (default: 0)
        - offset (int): Offset in underlying device (default: 0)
        - size (int): Size in sectors (default: full device)
        - drop_writes (bool): Drop writes when down (default: False)
        - error_writes (bool): Error writes when down (default: False)
        - corrupt_bio_byte (tuple): Corruption config (nth_byte, direction, value, flags)

    Example:
        ```python
        @pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 512}], indirect=True)
        def test_flakey_device(flakey_dm_device):
            dm_dev = flakey_dm_device
            assert dm_dev is not None
            assert 'flakey' in dm_dev.table
        ```

        With drop_writes during down interval:

        ```python
        @pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 512}], indirect=True)
        @pytest.mark.parametrize(
            'flakey_dm_device', [{'up_interval': 5, 'down_interval': 5, 'drop_writes': True}], indirect=True
        )
        def test_flakey_drop_writes(flakey_dm_device):
            # Device will drop writes after 5 seconds
            pass
        ```
    """
    device_path = loop_devices[0]
    params = getattr(request, 'param', {})

    dm_name = params.get('dm_name', DEFAULT_FLAKEY_DM_NAME)
    up_interval = params.get('up_interval', DEFAULT_FLAKEY_UP_INTERVAL)
    down_interval = params.get('down_interval', DEFAULT_FLAKEY_DOWN_INTERVAL)
    offset = params.get('offset', 0)
    size = params.get('size')
    drop_writes = params.get('drop_writes', False)
    error_writes = params.get('error_writes', False)
    corrupt_bio_byte = params.get('corrupt_bio_byte')

    # Clean up any existing device from previous failed runs
    existing = DmDevice.get_by_name(dm_name)
    if existing:
        existing.remove(force=True)

    # Create flakey device
    device = BlockDevice(path=device_path)
    flakey_dev = FlakeyDevice.from_block_device(
        device=device,
        up_interval=up_interval,
        down_interval=down_interval,
        offset=offset,
        size_sectors=size,
        drop_writes=drop_writes,
        error_writes=error_writes,
        corrupt_bio_byte=corrupt_bio_byte,
    )
    if not flakey_dev.create(dm_name):
        pytest.fail(f'Failed to create flakey device {dm_name}')

    # Wait for udev to process device creation
    udevadm_settle()

    logging.info(f'Created flakey device: {flakey_dev.dm_name}')
    yield flakey_dev

    # Cleanup: remove the device
    assert flakey_dev.remove(force=True)


@pytest.fixture
def cache_dm_device(loop_devices: list[str], request: pytest.FixtureRequest) -> Generator[CacheDevice, None, None]:
    """Fixture that creates and cleans up a cache device mapper device.

    This fixture creates a dm-cache device that caches data from a slow
    origin device on a fast cache device. Requires 3 loop devices:
    - First: origin device (slow, large)
    - Second: cache device (fast, smaller)
    - Third: metadata device (small)

    Args:
        loop_devices: List of loop device paths from loop_devices fixture
            - loop_devices[0]: origin device
            - loop_devices[1]: cache device
            - loop_devices[2]: metadata device
        request: Pytest fixture request for accessing parameters

    Yields:
        CacheDevice instance for the cache device

    Parameters (via pytest.mark.parametrize with indirect=True):
        - dm_name (str): Device mapper name (default: 'test-cache')
        - block_size_sectors (int): Cache block size (default: 512 = 256KB)
        - writethrough (bool): Use writethrough mode (default: False)
        - passthrough (bool): Use passthrough mode (default: False)
        - metadata2 (bool): Use metadata v2 (default: False)
        - no_discard_passdown (bool): Don't pass discards (default: False)
        - policy (str): Cache policy (default: 'default')
        - policy_args (dict): Policy arguments (default: None)

    Example:
        ```python
        @pytest.mark.parametrize('loop_devices', [{'count': 3, 'size_mb': 512}], indirect=True)
        def test_cache_device(cache_dm_device):
            cache = cache_dm_device
            assert cache is not None
            assert 'cache' in cache.table
        ```

        With writethrough mode:

        ```python
        @pytest.mark.parametrize('loop_devices', [{'count': 3, 'size_mb': 512}], indirect=True)
        @pytest.mark.parametrize('cache_dm_device', [{'writethrough': True}], indirect=True)
        def test_cache_writethrough(cache_dm_device):
            assert 'writethrough' in cache_dm_device.table
        ```
    """
    if len(loop_devices) < 3:
        pytest.fail('Cache device requires at least 3 loop devices (origin, cache, metadata)')

    origin_device_path = loop_devices[0]
    cache_device_path = loop_devices[1]
    metadata_device_path = loop_devices[2]
    params = getattr(request, 'param', {})

    dm_name = params.get('dm_name', DEFAULT_CACHE_DM_NAME)
    block_size_sectors = params.get('block_size_sectors', DEFAULT_CACHE_BLOCK_SIZE_SECTORS)
    writethrough = params.get('writethrough', False)
    passthrough = params.get('passthrough', False)
    metadata2 = params.get('metadata2', False)
    no_discard_passdown = params.get('no_discard_passdown', False)
    policy = params.get('policy', 'default')
    policy_args = params.get('policy_args')

    # Clean up any existing device from previous failed runs
    existing = DmDevice.get_by_name(dm_name)
    if existing:
        existing.remove(force=True)

    # Zero the metadata device (required for fresh cache)
    if not write_zeroes(metadata_device_path, bs=4096, count=1, conv='fsync'):
        pytest.fail('Failed to zero metadata device')

    # Create block devices
    origin_device = BlockDevice(path=origin_device_path)
    cache_device = BlockDevice(path=cache_device_path)
    metadata_device = BlockDevice(path=metadata_device_path)

    # Create cache device
    cache_dev = CacheDevice.from_block_devices(
        metadata_device=metadata_device,
        cache_device=cache_device,
        origin_device=origin_device,
        block_size_sectors=block_size_sectors,
        writethrough=writethrough,
        passthrough=passthrough,
        metadata2=metadata2,
        no_discard_passdown=no_discard_passdown,
        policy=policy,
        policy_args=policy_args,
    )
    if not cache_dev.create(dm_name):
        pytest.fail(f'Failed to create cache device {dm_name}')

    # Wait for udev to process device creation
    udevadm_settle()

    logging.info(f'Created cache device: {cache_dev.dm_name}')
    yield cache_dev

    # Cleanup: remove the device
    assert cache_dev.remove(force=True)
