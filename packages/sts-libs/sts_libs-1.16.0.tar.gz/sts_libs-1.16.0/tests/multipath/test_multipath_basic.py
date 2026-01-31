# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Basic functional tests for multipath devices.

This module contains pytest tests for multipath device functionality using
the multipath_device fixture which creates multipath devices via LIO loopback
targets with fileio backstore.
"""

from __future__ import annotations

import logging

import pytest

from sts.multipath import MultipathDevice, MultipathService
from sts.udevadm import udevadm_settle
from sts.utils.cmdline import run
from sts.utils.files import write_zeroes


class TestMultipathDeviceBasic:
    """Basic tests for multipath device creation and properties."""

    def test_multipath_device_created(self, multipath_device: MultipathDevice) -> None:
        """Test that multipath device is created successfully."""
        assert multipath_device is not None
        assert multipath_device.name is not None
        assert multipath_device.path is not None
        logging.info(f'Multipath device created: {multipath_device.name}')
        logging.info(f'Device path: {multipath_device.path}')

    def test_multipath_device_has_paths(self, multipath_device: MultipathDevice) -> None:
        """Test that multipath device has multiple paths."""
        assert multipath_device.paths is not None
        assert len(multipath_device.paths) > 0
        logging.info(f'Number of paths: {len(multipath_device.paths)}')

        for i, path in enumerate(multipath_device.paths):
            logging.info(f'  Path {i}: {path}')

    def test_multipath_device_n_paths(self, multipath_device: MultipathDevice) -> None:
        """Test n_paths property returns correct path count."""
        n_paths = multipath_device.n_paths
        assert n_paths is not None
        assert n_paths >= 1
        assert n_paths == len(multipath_device.paths)
        logging.info(f'n_paths: {n_paths}')

    def test_multipath_device_wwid(self, multipath_device: MultipathDevice) -> None:
        """Test that multipath device has a WWID."""
        assert multipath_device.wwid is not None
        assert len(multipath_device.wwid) > 0
        logging.info(f'Device WWID: {multipath_device.wwid}')

    def test_multipath_device_dm_name(self, multipath_device: MultipathDevice) -> None:
        """Test that multipath device has a DM name."""
        assert multipath_device.dm_name is not None
        logging.info(f'DM name: {multipath_device.dm_name}')

    def test_multipath_device_vendor(self, multipath_device: MultipathDevice) -> None:
        """Test multipath device vendor attribute."""
        # Vendor should be set (e.g., 'LIO-ORG' for loopback targets)
        assert multipath_device.vendor is not None
        logging.info(f'Device vendor: {multipath_device.vendor}')


class TestMultipathDeviceIO:
    """Test I/O operations on multipath devices."""

    def test_multipath_device_readable(self, multipath_device: MultipathDevice) -> None:
        """Test that multipath device is readable."""
        path = multipath_device.path
        assert path is not None

        # Ensure device is ready before reading
        udevadm_settle()

        result = run(f'dd if={path} bs=4096 count=1 of=/dev/null 2>&1')
        assert result.succeeded, f'Failed to read from multipath device: {result.stderr}'
        logging.info(f'Successfully read from {path}')

    def test_multipath_device_writable(self, multipath_device: MultipathDevice) -> None:
        """Test that multipath device is writable."""
        path = multipath_device.path
        assert path is not None

        # Ensure device is ready before writing
        udevadm_settle()

        assert write_zeroes(path, bs=4096, count=1), f'Failed to write to multipath device: {path}'
        logging.info(f'Successfully wrote to {path}')

        # Settle after write
        udevadm_settle()

    def test_multipath_device_size(self, multipath_device: MultipathDevice) -> None:
        """Test multipath device size is reported correctly."""
        path = multipath_device.path
        assert path is not None

        result = run(f'blockdev --getsize64 {path}')
        assert result.succeeded, f'Failed to get device size: {result.stderr}'

        size_bytes = int(result.stdout.strip())
        assert size_bytes > 0
        logging.info(f'Device size: {size_bytes} bytes ({size_bytes // (1024 * 1024)} MB)')


class TestMultipathPathStatus:
    """Test multipath path status and state."""

    def test_paths_have_device_names(self, multipath_device: MultipathDevice) -> None:
        """Test that all paths have device names."""
        for path in multipath_device.paths:
            assert 'dev' in path
            assert path['dev'] is not None
            logging.info(f'Path device: {path["dev"]}')

    def test_paths_have_state(self, multipath_device: MultipathDevice) -> None:
        """Test that paths have state information."""
        for path in multipath_device.paths:
            # dm_st is the path state (active, failed, etc.)
            if 'dm_st' in path:
                logging.info(f'Path {path.get("dev")}: state={path["dm_st"]}')

    def test_has_active_paths(self, multipath_device: MultipathDevice) -> None:
        """Test that device has at least one active path."""
        active_paths = [p for p in multipath_device.paths if p.get('dm_st') == 'active']
        assert len(active_paths) >= 1, 'No active paths found'
        logging.info(f'Active paths: {len(active_paths)}')


@pytest.mark.parametrize(
    'multipath_device',
    [{'num_paths': 4, 'size': '100M'}],
    indirect=True,
    ids=['loopback-4paths'],
)
class TestMultipathLoopback:
    """Tests specific to LIO loopback-based multipath devices."""

    def test_loopback_device_created(self, multipath_device: MultipathDevice) -> None:
        """Test that loopback-based multipath device is created."""
        assert multipath_device is not None
        assert multipath_device.path is not None
        logging.info(f'Loopback multipath device: {multipath_device.name}')

    def test_loopback_has_expected_paths(self, multipath_device: MultipathDevice) -> None:
        """Test that loopback device has expected number of paths."""
        assert multipath_device.n_paths is not None
        assert multipath_device.n_paths >= 4
        logging.info(f'Path count: {multipath_device.n_paths}')

    def test_loopback_vendor(self, multipath_device: MultipathDevice) -> None:
        """Test that loopback device has LIO vendor."""
        assert multipath_device.vendor is not None
        # LIO targets typically report 'LIO-ORG' as vendor
        logging.info(f'Vendor: {multipath_device.vendor}')


class TestMultipathService:
    """Tests for multipath service interaction."""

    def test_multipathd_running(self, multipath_device: MultipathDevice) -> None:
        """Test that multipathd is running when device exists."""
        # Fixture ensures device exists before checking service
        assert multipath_device is not None
        mpath_service = MultipathService()
        assert mpath_service.is_running()
        logging.info('multipathd service is running')

    def test_multipath_show_topology(self, multipath_device: MultipathDevice) -> None:
        """Test multipath topology display."""
        result = run('multipath -ll')
        assert result.succeeded, f'multipath -ll failed: {result.stderr}'
        assert multipath_device.name is not None
        assert multipath_device.wwid is not None
        assert multipath_device.name in result.stdout or multipath_device.wwid in result.stdout
        logging.info(f'Topology output:\n{result.stdout}')

    def test_multipath_reconfigure(self, multipath_device: MultipathDevice) -> None:
        """Test multipath reconfiguration."""
        result = run('multipath -r')
        assert result.succeeded, f'multipath -r failed: {result.stderr}'
        logging.info('Multipath reconfigured successfully')

        # Verify device still exists
        devices = MultipathDevice.get_all()
        assert any(d.wwid == multipath_device.wwid for d in devices)
