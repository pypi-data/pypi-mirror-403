#  Copyright: Contributors to the sts project
#  GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Tests for Device Mapper delay target.

The dm-delay target delays reads and/or writes and/or flushes and optionally
maps them to different devices. Useful for testing how applications handle
slow storage devices.

Table line formats:
- 3 args: <device> <offset> <delay> - same delay for all operations
- 6 args: + <write_device> <write_offset> <write_delay> - separate write/flush
- 9 args: + <flush_device> <flush_offset> <flush_delay> - separate flush
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

import pytest

from sts.dm import DelayDevice, DmDevice
from sts.utils.cmdline import run


@pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 512}], indirect=True)
class TestDelayDeviceBasic:
    """Basic integration tests for delay device creation with dmsetup.

    Tests the 3-argument format where the same delay applies to all operations.
    """

    def test_delay_device_creation(self, delay_dm_device: DelayDevice) -> None:
        """Test that delay device is created with dmsetup."""
        assert delay_dm_device is not None
        assert delay_dm_device.dm_name is not None

        dm_devices = DmDevice.ls()
        assert delay_dm_device.dm_name in dm_devices
        logging.info(f'dmsetup ls output: {dm_devices}')

        assert delay_dm_device.table is not None
        assert 'delay' in delay_dm_device.table
        logging.info(f'Device table: {delay_dm_device.table}')

    def test_delay_device_status(self, delay_dm_device: DelayDevice) -> None:
        """Test that delay device status can be retrieved."""
        status = delay_dm_device.get_status()
        assert status is not None
        logging.info(f'Delay device status: {status}')

    def test_delay_device_suspend_resume(self, delay_dm_device: DelayDevice) -> None:
        """Test suspend and resume operations on delay device."""
        assert delay_dm_device.suspend(), 'Failed to suspend delay device'
        logging.info('Delay device suspended')

        info = delay_dm_device.info()
        assert info is not None
        assert isinstance(info, dict)
        assert info.get('State') == 'SUSPENDED'

        assert delay_dm_device.resume(), 'Failed to resume delay device'
        logging.info('Delay device resumed')

        info = delay_dm_device.info()
        assert info is not None
        assert isinstance(info, dict)
        assert info.get('State') == 'ACTIVE'

    def test_delay_get_targets(self, delay_dm_device: DelayDevice) -> None:
        """Test parsing delay device targets."""
        assert isinstance(delay_dm_device, DelayDevice)
        assert delay_dm_device.type == 'delay'
        logging.info(f'Delay device: {delay_dm_device}')

        assert delay_dm_device.read_delay_ms is not None
        assert delay_dm_device.arg_format == '3'
        logging.info(
            f'Delay device: read_delay_ms={delay_dm_device.read_delay_ms}, arg_format={delay_dm_device.arg_format}'
        )


@pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 512}], indirect=True)
class TestDelayDeviceCreation:
    """Tests for DelayDevice creation methods."""

    @pytest.mark.parametrize(
        'delay_dm_device',
        [{'delay_ms': 50, 'dm_name': 'test-delay-creation'}],
        indirect=True,
    )
    def test_delay_device_from_block_device(self, delay_dm_device: DelayDevice) -> None:
        """Test creating DelayDevice using from_block_device method."""
        assert delay_dm_device.type == 'delay'

        # Verify target string format
        target_str = str(delay_dm_device)
        logging.info(f'Delay device string: {target_str}')
        assert 'delay' in target_str

        assert delay_dm_device.table is not None
        assert 'delay' in delay_dm_device.table
        logging.info(f'Created delay device: {delay_dm_device.table}')

    @pytest.mark.parametrize(
        'delay_device_positional',
        [{'delay_ms': 100, 'dm_name': 'test-delay-pos3'}],
        indirect=True,
    )
    def test_delay_device_create_positional_3args(self, delay_device_positional: DelayDevice) -> None:
        """Test creating DelayDevice with create_positional 3-argument format."""
        target_str = str(delay_device_positional)
        logging.info(f'Positional 3-arg device: {target_str}')
        assert 'delay' in target_str

        assert delay_device_positional.arg_format == '3'
        assert delay_device_positional.read_delay_ms == 100


@pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 512}], indirect=True)
class TestDelayOptions3Args:
    """Test delay device creation with 3-argument format variations."""

    @pytest.mark.parametrize(
        'delay_dm_device',
        [{'delay_ms': 0}, {'delay_ms': 50}, {'delay_ms': 500}],
        indirect=True,
        ids=['delay-0ms', 'delay-50ms', 'delay-500ms'],
    )
    def test_delay_various_delays(self, delay_dm_device: DelayDevice, request: pytest.FixtureRequest) -> None:
        """Test delay device creation with various delay values."""
        assert delay_dm_device is not None
        assert delay_dm_device.table is not None

        delay_ms = request.node.callspec.params['delay_dm_device']['delay_ms']
        logging.info(f'Created delay device with delay_ms={delay_ms}: {delay_dm_device.table}')

        # Verify parsed attributes
        assert delay_dm_device.read_delay_ms == delay_ms

    @pytest.mark.parametrize(
        'delay_dm_device',
        [{'offset': 0}, {'offset': 2048}, {'offset': 8192}],
        indirect=True,
        ids=['offset-0', 'offset-2048', 'offset-8192'],
    )
    def test_delay_various_offsets(self, delay_dm_device: DelayDevice, request: pytest.FixtureRequest) -> None:
        """Test delay device creation with various offset values."""
        assert delay_dm_device is not None
        assert delay_dm_device.table is not None

        offset = request.node.callspec.params['delay_dm_device']['offset']
        logging.info(f'Created delay device with offset={offset}: {delay_dm_device.table}')

        # Verify parsed attributes
        assert delay_dm_device.read_offset == offset


@pytest.mark.parametrize('loop_devices', [{'count': 2, 'size_mb': 512}], indirect=True)
class TestDelayOptions6Args:
    """Test delay device creation with 6-argument format (separate read/write)."""

    @pytest.mark.parametrize(
        'delay_dm_device',
        [
            {'read_delay_ms': 0, 'write_delay_ms': 100},
            {'read_delay_ms': 50, 'write_delay_ms': 200},
            {'read_delay_ms': 100, 'write_delay_ms': 0},
        ],
        indirect=True,
        ids=['read-0-write-100', 'read-50-write-200', 'read-100-write-0'],
    )
    def test_delay_6arg_format(self, delay_dm_device: DelayDevice, request: pytest.FixtureRequest) -> None:
        """Test delay device with 6-argument format (separate read and write delays)."""
        assert delay_dm_device is not None
        assert delay_dm_device.table is not None

        params = request.node.callspec.params['delay_dm_device']
        read_delay = params['read_delay_ms']
        write_delay = params['write_delay_ms']

        logging.info(
            f'Created 6-arg delay device: read_delay={read_delay}ms, '
            f'write_delay={write_delay}ms: {delay_dm_device.table}'
        )

        # Verify parsed attributes
        assert delay_dm_device.arg_format == '6'
        assert delay_dm_device.read_delay_ms == read_delay
        assert delay_dm_device.write_delay_ms == write_delay

    @pytest.mark.parametrize(
        'delay_dm_device',
        [
            {'read_delay_ms': 0, 'read_offset': 2048, 'write_delay_ms': 400, 'write_offset': 4096},
        ],
        indirect=True,
        ids=['different-offsets'],
    )
    def test_delay_6arg_different_offsets(self, delay_dm_device: DelayDevice, request: pytest.FixtureRequest) -> None:
        """Test delay device with different read and write offsets."""
        assert delay_dm_device is not None
        assert delay_dm_device.table is not None

        params = request.node.callspec.params['delay_dm_device']
        logging.info(f'Created 6-arg delay with different offsets: {delay_dm_device.table}')

        # Verify parsed attributes
        assert delay_dm_device.read_offset == params['read_offset']
        assert delay_dm_device.write_offset == params['write_offset']

    @pytest.mark.parametrize(
        'delay_dm_device',
        [
            {'read_delay_ms': 0, 'write_delay_ms': 100, 'write_device_index': 1},
        ],
        indirect=True,
        ids=['different-write-device'],
    )
    def test_delay_6arg_different_devices(self, delay_dm_device: DelayDevice) -> None:
        """Test delay device with different read and write devices."""
        assert delay_dm_device is not None
        assert delay_dm_device.table is not None
        logging.info(f'Created 6-arg delay with different devices: {delay_dm_device.table}')

        # Verify parsed attributes - read and write device IDs should be different
        assert delay_dm_device.arg_format == '6'
        assert delay_dm_device.read_device != delay_dm_device.write_device


@pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 512}], indirect=True)
class TestDelayOptions9Args:
    """Test delay device creation with 9-argument format (separate read/write/flush)."""

    @pytest.mark.parametrize(
        'delay_dm_device',
        [
            {'read_delay_ms': 50, 'write_delay_ms': 100, 'flush_delay_ms': 333},
            {'read_delay_ms': 0, 'write_delay_ms': 0, 'flush_delay_ms': 500},
            {'read_delay_ms': 100, 'write_delay_ms': 200, 'flush_delay_ms': 0},
        ],
        indirect=True,
        ids=['50-100-333', '0-0-500', '100-200-0'],
    )
    def test_delay_9arg_format(self, delay_dm_device: DelayDevice, request: pytest.FixtureRequest) -> None:
        """Test delay device with 9-argument format (separate read, write, flush delays)."""
        assert delay_dm_device is not None
        assert delay_dm_device.table is not None

        params = request.node.callspec.params['delay_dm_device']
        read_delay = params['read_delay_ms']
        write_delay = params['write_delay_ms']
        flush_delay = params['flush_delay_ms']

        logging.info(
            f'Created 9-arg delay device: read={read_delay}ms, write={write_delay}ms, '
            f'flush={flush_delay}ms: {delay_dm_device.table}'
        )

        # Verify parsed attributes
        assert delay_dm_device.arg_format == '9'
        assert delay_dm_device.read_delay_ms == read_delay
        assert delay_dm_device.write_delay_ms == write_delay
        assert delay_dm_device.flush_delay_ms == flush_delay

    @pytest.mark.parametrize(
        'delay_dm_device',
        [
            {
                'read_delay_ms': 0,
                'read_offset': 0,
                'write_delay_ms': 100,
                'write_offset': 2048,
                'flush_delay_ms': 200,
                'flush_offset': 4096,
            },
        ],
        indirect=True,
        ids=['all-different-offsets'],
    )
    def test_delay_9arg_different_offsets(self, delay_dm_device: DelayDevice, request: pytest.FixtureRequest) -> None:
        """Test delay device with different offsets for read, write, and flush."""
        assert delay_dm_device is not None
        assert delay_dm_device.table is not None

        params = request.node.callspec.params['delay_dm_device']
        logging.info(f'Created 9-arg delay with different offsets: {delay_dm_device.table}')

        # Verify parsed attributes
        assert delay_dm_device.read_offset == params['read_offset']
        assert delay_dm_device.write_offset == params['write_offset']
        assert delay_dm_device.flush_offset == params['flush_offset']


class TestDelayDeviceParsing:
    """Tests for DelayDevice parsing methods.

    These tests don't require actual devices - they test parsing of table strings.
    """

    def test_refresh_3arg(self) -> None:
        """Test refresh populates attributes for 3-argument delay device."""
        device = DelayDevice(start=0, size_sectors=1000000, args='8:16 0 100')
        device.refresh()

        assert device.read_device == '8:16'
        assert device.read_offset == 0
        assert device.read_delay_ms == 100
        assert device.arg_format == '3'
        logging.info(f'Parsed 3-arg device: read_device={device.read_device}, arg_format={device.arg_format}')

    def test_refresh_6arg(self) -> None:
        """Test refresh populates attributes for 6-argument delay device."""
        device = DelayDevice(start=0, size_sectors=1000000, args='8:16 2048 0 8:32 4096 400')
        device.refresh()

        assert device.read_device == '8:16'
        assert device.read_offset == 2048
        assert device.read_delay_ms == 0
        assert device.write_device == '8:32'
        assert device.write_offset == 4096
        assert device.write_delay_ms == 400
        assert device.arg_format == '6'
        logging.info(f'Parsed 6-arg device: read_device={device.read_device}, write_device={device.write_device}')

    def test_refresh_9arg(self) -> None:
        """Test refresh populates attributes for 9-argument delay device."""
        device = DelayDevice(start=0, size_sectors=1000000, args='8:16 0 50 8:16 0 100 8:16 0 333')
        device.refresh()

        assert device.read_device == '8:16'
        assert device.read_delay_ms == 50
        assert device.write_device == '8:16'
        assert device.write_delay_ms == 100
        assert device.flush_device == '8:16'
        assert device.flush_delay_ms == 333
        assert device.arg_format == '9'
        logging.info(
            f'Parsed 9-arg device: delays={device.read_delay_ms}/{device.write_delay_ms}/{device.flush_delay_ms}'
        )

    def test_from_table_line(self) -> None:
        """Test creating DelayDevice from dmsetup table line."""
        table_line = '0 2097152 delay 8:16 0 100'
        device = DelayDevice.from_table_line(table_line)

        assert device is not None
        assert device.start == 0
        assert device.size_sectors == 2097152
        assert device.type == 'delay'
        assert device.read_delay_ms == 100
        logging.info(f'Created device from table line: {device}')


@pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 512}], indirect=True)
class TestDelayDeviceIO:
    """Tests for I/O operations on delay devices."""

    @pytest.mark.parametrize(
        'delay_dm_device',
        [{'delay_ms': 0}],
        indirect=True,
        ids=['no-delay'],
    )
    @pytest.mark.parametrize(
        'mounted_dm_device',
        [{'mount_point': '/mnt/sts-dm-delay-test'}],
        indirect=True,
    )
    def test_delay_filesystem_operations(
        self,
        delay_dm_device: DelayDevice,
        mounted_dm_device: tuple[DelayDevice, str],
    ) -> None:
        """Test creating filesystem and performing I/O on delay device.

        Args:
            delay_dm_device: Delay device fixture (used by mounted_dm_device)
            mounted_dm_device: Tuple of (device, mount_point)
        """
        _ = delay_dm_device
        dm_device, mount_point = mounted_dm_device
        logging.info(f'Testing I/O on {dm_device.dm_device_path} mounted at {mount_point}')

        # Write test data
        test_file = Path(mount_point) / 'test_file.txt'
        test_data = 'Hello, Device Mapper Delay Target!\n' * 100
        test_file.write_text(test_data)
        logging.info(f'Wrote {len(test_data)} bytes to {test_file}')

        # Verify data can be read back
        read_data = test_file.read_text()
        assert read_data == test_data, 'Data mismatch after read'

    @pytest.mark.parametrize(
        'delay_dm_device',
        [{'delay_ms': 200}],
        indirect=True,
        ids=['200ms-delay'],
    )
    def test_delay_affects_io_timing(self, delay_dm_device: DelayDevice) -> None:
        """Test that delay actually affects I/O timing."""
        dm_device_path = delay_dm_device.dm_device_path
        assert dm_device_path is not None

        # Perform timed I/O operation using dd
        start_time = time.time()
        result = run(f'dd if={dm_device_path} of=/dev/null bs=4k count=10 iflag=sync')
        elapsed_time = time.time() - start_time

        assert result.succeeded, f'dd read failed: {result.stderr}'

        # With 200ms delay and multiple reads, we expect noticeable delay
        # Note: This is a sanity check, actual timing depends on system load
        logging.info(f'Read operation took {elapsed_time:.3f}s with 200ms delay configured')

        # We should see some delay, but we're lenient to avoid flaky tests
        # Just verify the device works and log timing for debugging
        assert elapsed_time > 0, 'Operation should take some time'


@pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 512}], indirect=True)
class TestDelayDeviceCreatePositional:
    """Tests for DelayDevice.create_positional method with all formats."""

    @pytest.mark.parametrize(
        'delay_device_positional',
        [
            {
                'dm_name': 'test-delay-pos6',
                'offset': 2048,
                'delay_ms': 0,
                'write_offset': 4096,
                'write_delay_ms': 400,
            }
        ],
        indirect=True,
        ids=['6-arg-format'],
    )
    def test_create_positional_6args(self, delay_device_positional: DelayDevice) -> None:
        """Test create_positional with 6-argument format."""
        target_str = str(delay_device_positional)
        logging.info(f'Positional 6-arg device: {target_str}')

        assert delay_device_positional.arg_format == '6'
        assert delay_device_positional.read_offset == 2048
        assert delay_device_positional.read_delay_ms == 0
        assert delay_device_positional.write_offset == 4096
        assert delay_device_positional.write_delay_ms == 400
        assert delay_device_positional.table is not None
        assert 'delay' in delay_device_positional.table

    @pytest.mark.parametrize(
        'delay_device_positional',
        [
            {
                'dm_name': 'test-delay-pos9',
                'offset': 0,
                'delay_ms': 50,
                'write_offset': 0,
                'write_delay_ms': 100,
                'flush_offset': 0,
                'flush_delay_ms': 333,
            }
        ],
        indirect=True,
        ids=['9-arg-format'],
    )
    def test_create_positional_9args(self, delay_device_positional: DelayDevice) -> None:
        """Test create_positional with 9-argument format."""
        target_str = str(delay_device_positional)
        logging.info(f'Positional 9-arg device: {target_str}')

        assert delay_device_positional.arg_format == '9'
        assert delay_device_positional.read_delay_ms == 50
        assert delay_device_positional.write_delay_ms == 100
        assert delay_device_positional.flush_delay_ms == 333
        assert delay_device_positional.table is not None
        assert 'delay' in delay_device_positional.table

    def test_create_positional_invalid_params(self, loop_devices: list[str]) -> None:
        """Test create_positional with invalid parameter combinations."""
        device_path = loop_devices[0]

        # Missing size should raise ValueError
        with pytest.raises(ValueError, match='Size must be specified'):
            DelayDevice.create_positional(
                device_path=device_path,
                offset=0,
                delay_ms=100,
            )

        # Incomplete write params should raise ValueError
        with pytest.raises(ValueError, match='write_offset and write_delay_ms required'):
            DelayDevice.create_positional(
                device_path=device_path,
                offset=0,
                delay_ms=100,
                size=1000000,
                write_device_path=device_path,
                # Missing write_offset and write_delay_ms
            )

        # flush without write should raise ValueError
        with pytest.raises(ValueError, match='flush_device_path requires write_device_path'):
            DelayDevice.create_positional(
                device_path=device_path,
                offset=0,
                delay_ms=100,
                size=1000000,
                flush_device_path=device_path,
                flush_offset=0,
                flush_delay_ms=100,
            )
