# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Multipath fixtures module for the STS testing framework.

This module provides pytest fixtures for managing multipath devices during testing.
It includes fixtures for:
- Enabling multipath service and accessing multipath devices
- Disabling multipath service temporarily
- Accessing active paths of multipath devices
- Creating multipath devices using LIO loopback targets with fileio backstore

The fixtures handle proper setup and cleanup of multipath configurations to ensure
isolated and reliable testing environments.
"""

from __future__ import annotations

import logging
import time
from os import getenv
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from sts.multipath import MultipathDevice, MultipathService
from sts.target import BackstoreFileio, Loopback, LoopbackLUN
from sts.udevadm import udevadm_settle
from sts.utils.cmdline import run
from sts.utils.system import SystemManager

if TYPE_CHECKING:
    from collections.abc import Generator

# Constants for multipath device creation
DEFAULT_NUM_PATHS = 4
DEFAULT_DEVICE_SIZE = '100M'
DEFAULT_IMAGE_PATH = '/var/tmp/'
MULTIPATH_SETTLE_TIME = 2  # seconds to wait for multipath to discover paths


@pytest.fixture(scope='class')
def with_target_service() -> Generator[None, None, None]:
    """Fixture to ensure target service is running.

    Installs targetcli package if needed, starts the target service if not running,
    and restores original state on cleanup.
    The target service (targetcli/LIO) is required for creating iSCSI, loopback,
    and other target-based storage devices.

    Yields:
        None

    Raises:
        pytest.skip: If targetcli cannot be installed or target service cannot be started
    """
    system = SystemManager()
    service_name = 'target'

    # Ensure targetcli package is installed
    if not system.package_manager.install('targetcli'):
        pytest.skip('Failed to install targetcli package')

    was_stopped = not system.is_service_running(service_name)

    if was_stopped:
        logging.info('Starting target service...')
        if not system.service_start(service_name):
            pytest.skip('Failed to start target service')

    yield

    # Cleanup only if we started the service
    if was_stopped:
        logging.info('Stopping target service...')
        system.service_stop(service_name)


@pytest.fixture(scope='class')
def with_multipath_enabled() -> Generator[None, None, None]:
    """Fixture to temporarily enable multipath service."""
    mpath_service = MultipathService()
    was_stopped = not mpath_service.is_running()

    if was_stopped:
        logging.info('Starting multipath service...')
        if not mpath_service.start():
            pytest.skip('Failed to start multipath service')

    yield

    # Cleanup only if we started the service
    if was_stopped:
        logging.info('Stopping multipath service...')
        mpath_service.stop()


@pytest.fixture(scope='class')
def with_multipath_disabled() -> Generator[None, None, None]:
    """Fixture to temporarily disable multipath service."""
    mpath_service = MultipathService()
    was_running = mpath_service.is_running()

    if was_running:
        logging.info('Temporarily disabling multipath service...')
        mpath_service.stop()

        # Flush devices after service is stopped
        if MultipathDevice.get_all():
            logging.warning('Flushing existing multipath devices...')
            if not mpath_service.flush():
                pytest.skip('Failed to flush multipath devices')

    yield

    if was_running:
        logging.info('Restoring multipath service...')
        mpath_service.start()


@pytest.fixture(scope='class')
def get_multipath_active_paths() -> Generator[tuple[MultipathDevice, list[dict]], None, None]:
    """Fixture to get first multipath device with its active paths.

    Yields:
        tuple: (MultipathDevice, list of active path dictionaries)
              Each path dict contains: {'dev': device_name, 'dm_st': state, ...}

    Raises:
        pytest.skip: If no multipath device with active paths is found
    """
    mpath_devices = MultipathDevice.get_all()
    if not mpath_devices:
        pytest.skip('No multipath devices found')

    # Find first device with active paths
    for device in mpath_devices:
        active_paths = [path for path in device.paths if path.get('dm_st') == 'active']
        if active_paths:
            device_path = Path(device.path) if device.path else None
            if device_path and device_path.exists():
                yield device, active_paths
                break
    else:
        pytest.skip('No multipath device with active paths found')


@pytest.fixture(scope='class')
def multipath_device(
    request: pytest.FixtureRequest,
    with_target_service: None,
) -> Generator[MultipathDevice, None, None]:
    """Create a multipath device for testing using LIO loopback targets.

    Creates a multipath device using LIO loopback targets with fileio backstore.
    Multiple loopback targets share a single backstore to simulate multiple paths
    to the same storage device.

    Requires the target service to be running (handled by with_target_service fixture).

    Configuration:
        num_paths: Number of paths to create (default: 4)
        size: Device size (default: '100M')

    Example:
        ```python
        # Default configuration (4 paths, 100M)
        def test_multipath(multipath_device):
            assert multipath_device.n_paths >= 4


        # Custom configuration
        @pytest.mark.parametrize('multipath_device', [{'num_paths': 2, 'size': '500M'}], indirect=True)
        def test_multipath_custom(multipath_device):
            assert multipath_device.n_paths >= 2
        ```

    Yields:
        MultipathDevice: The created multipath device

    Raises:
        pytest.skip: If multipath device creation fails
    """
    _ = with_target_service
    # Parse configuration from parametrize
    param = getattr(request, 'param', {})
    if isinstance(param, dict):
        num_paths = param.get('num_paths', DEFAULT_NUM_PATHS)
        size = param.get('size', DEFAULT_DEVICE_SIZE)
    else:
        num_paths = DEFAULT_NUM_PATHS
        size = DEFAULT_DEVICE_SIZE

    # Setup multipath service
    mpath_service = MultipathService()
    service_running = mpath_service.is_running()
    if not service_running and not mpath_service.start():
        pytest.skip('Failed to start multipath service')

    # Create multipath device using loopback
    yield from _create_multipath_loopback(num_paths, size)

    # Stop multipath service if it was not running originally
    if not service_running:
        mpath_service.stop()


def _create_multipath_loopback(
    num_paths: int,
    size: str,
) -> Generator[MultipathDevice, None, None]:
    """Create multipath device using LIO loopback targets with fileio backstore.

    Creates a single fileio backstore and multiple loopback targets, each with
    a LUN pointing to the same backstore. This simulates multiple paths to the
    same storage device.

    Note: Requires target service to be running. Use with_target_service fixture.

    Args:
        num_paths: Number of loopback targets (paths) to create
        size: Device size (e.g., '100M', '1G')

    Yields:
        MultipathDevice: The created multipath device
    """
    logging.info(f'Creating multipath device with LIO loopback ({num_paths} paths)')

    image_path = getenv('IMAGE_PATH', DEFAULT_IMAGE_PATH)
    backstore_name = 'mpath-backstore'
    backstore_file = f'{image_path}{backstore_name}.img'

    # Create fileio backstore
    backstore = BackstoreFileio(name=backstore_name)
    result = backstore.create_backstore(size=size, file_or_dev=backstore_file)
    if result.failed:
        pytest.skip(f'Failed to create fileio backstore: {result.stderr}')

    # Create loopback targets and LUNs
    loopbacks: list[Loopback] = []
    wwn_base = '5001400'

    for i in range(num_paths):
        # Generate unique WWN for each loopback target
        wwn = f'naa.{wwn_base}{i + 1:09d}'

        loopback = Loopback(target_wwn=wwn)
        result = loopback.create_target()
        if result.failed:
            logging.error(f'Failed to create loopback target {wwn}: {result.stderr}')
            continue

        loopbacks.append(loopback)

        # Create LUN pointing to the shared backstore
        lun = LoopbackLUN(target_wwn=wwn)
        result = lun.create(storage_object=backstore.path)
        if result.failed:
            logging.error(f'Failed to create LUN for {wwn}: {result.stderr}')

    if not loopbacks:
        backstore.delete_backstore()
        Path(backstore_file).unlink(missing_ok=True)
        pytest.fail('Failed to create any loopback targets')

    # Wait for multipath to discover the device
    time.sleep(MULTIPATH_SETTLE_TIME)
    udevadm_settle()

    # Rescan multipath
    run('multipath -r')
    time.sleep(MULTIPATH_SETTLE_TIME)

    # Get the multipath device
    devices = MultipathDevice.get_all()
    if not devices:
        # Cleanup on failure
        for loopback in loopbacks:
            loopback.delete_target()
        backstore.delete_backstore()
        Path(backstore_file).unlink(missing_ok=True)
        pytest.skip('No multipath device found after loopback setup')

    # Find the device created by LIO (vendor 'LIO-ORG')
    mpath_device = None
    for device in devices:
        if device.vendor and 'LIO' in device.vendor:
            mpath_device = device
            break

    if not mpath_device:
        # Try first device if vendor not matching
        mpath_device = devices[0]

    logging.info(f'Created multipath device: {mpath_device.name} with {mpath_device.n_paths} paths')

    yield mpath_device

    # Cleanup
    logging.info('Cleaning up loopback multipath device')
    udevadm_settle()
    time.sleep(MULTIPATH_SETTLE_TIME)

    # Step 1: Remove the multipath device
    logging.info(f'Removing multipath device: {mpath_device.name}')
    mpath_device.remove()

    # Step 2: Flush all unused multipath devices (multipath -F)
    mpath_service = MultipathService()
    mpath_service.flush()

    # Step 3: Wait for udev to settle before deleting targets
    udevadm_settle()
    time.sleep(MULTIPATH_SETTLE_TIME)

    # Step 4: Delete loopback targets (must be done before backstore)
    for loopback in loopbacks:
        result = loopback.delete_target()
        if result.failed:
            logging.error(f'Failed to delete loopback target {loopback.target_wwn}: {result.stderr}')

    # Step 5: Delete backstore
    result = backstore.delete_backstore()
    if result.failed:
        logging.error(f'Failed to delete backstore: {result.stderr}')
    else:
        logging.info(f'Deleted backstore: {backstore_name}')

    # Step 6: Remove backstore file
    Path(backstore_file).unlink(missing_ok=True)
    logging.info(f'Removed backstore file: {backstore_file}')
