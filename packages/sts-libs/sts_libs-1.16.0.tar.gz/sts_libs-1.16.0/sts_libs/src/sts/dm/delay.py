# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Device Mapper device management.

This module provides functionality for managing Device Mapper devices:
- Device discovery
- Device information
- Device operations
- Device Mapper targets

Device Mapper is a Linux kernel framework for mapping physical block devices
onto higher-level virtual block devices. It forms the foundation for (example):
- LVM (Logical Volume Management)
- Software RAID (dm-raid)
- Disk encryption (dm-crypt)
- Thin provisioning (dm-thin)

Class Hierarchy:
    BlockDevice
        └── DmDevice (base for all DM devices)
                ├── LinearDevice
                ├── DelayDevice
                ├── VdoDevice
                ├── MultipathTarget
                ├── ThinPoolDevice
                ├── ThinDevice
                ├── ZeroDevice
                └── ErrorDevice

Each device class can be in two states:
1. Configuration: has target config (start, size, args) but not yet created
2. Active: device exists on system, has path, name, dm_name, etc.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from sts.dm.base import DmDevice

if TYPE_CHECKING:
    from sts.blockdevice import BlockDevice


@dataclass
class DelayDevice(DmDevice):
    """Delay target.

    Delays reads and/or writes and/or flushes and optionally maps them
    to different devices. Useful for testing how applications handle slow devices.

    Table line has to either have 3, 6 or 9 arguments:

    - 3 args: <device> <offset> <delay>
        Apply offset and delay to read, write and flush operations on device

    - 6 args: <device> <offset> <delay> <write_device> <write_offset> <write_delay>
        Apply offset and delay to device for reads, also apply write_offset and
        write_delay to write and flush operations on optionally different write_device

    - 9 args: <device> <offset> <delay> <write_device> <write_offset> <write_delay>
              <flush_device> <flush_offset> <flush_delay>
        Same as 6 arguments plus define flush_offset and flush_delay explicitly
        on/with optionally different flush_device/flush_offset

    Offsets are specified in sectors. Delays are specified in milliseconds.

    Attributes:
        read_device: Device for read operations (parsed from args)
        read_offset: Offset in read device sectors (parsed from args)
        read_delay_ms: Delay for read operations in milliseconds (parsed from args)
        write_device: Device for write operations (parsed from args, 6+ arg format)
        write_offset: Offset in write device sectors (parsed from args, 6+ arg format)
        write_delay_ms: Delay for write operations in milliseconds (parsed from args, 6+ arg format)
        flush_device: Device for flush operations (parsed from args, 9 arg format)
        flush_offset: Offset in flush device sectors (parsed from args, 9 arg format)
        flush_delay_ms: Delay for flush operations in milliseconds (parsed from args, 9 arg format)
        arg_format: Format indicator ('3', '6', or '9')

    Example:
        ```python
        # 3 args: 100ms delay for all operations
        target = DelayTarget(0, 1000000, '8:16 0 100')
        str(target)
        '0 1000000 delay 8:16 0 100'
        target.read_delay_ms
        100

        # 6 args: no read delay, 400ms write/flush delay
        target = DelayTarget(0, 1000000, '8:16 0 0 8:32 0 400')
        str(target)
        '0 1000000 delay 8:16 0 0 8:32 0 400'
        target.write_delay_ms
        400

        # 9 args: 50ms read, 100ms write, 333ms flush
        target = DelayTarget(0, 1000000, '8:16 0 50 8:16 0 100 8:16 0 333')
        str(target)
        '0 1000000 delay 8:16 0 50 8:16 0 100 8:16 0 333'
        target.flush_delay_ms
        333
        ```
    """

    # Parsed attributes (populated by refresh)
    read_device: str | None = field(init=False, default=None)
    read_offset: int | None = field(init=False, default=None)
    read_delay_ms: int | None = field(init=False, default=None)
    write_device: str | None = field(init=False, default=None)
    write_offset: int | None = field(init=False, default=None)
    write_delay_ms: int | None = field(init=False, default=None)
    flush_device: str | None = field(init=False, default=None)
    flush_offset: int | None = field(init=False, default=None)
    flush_delay_ms: int | None = field(init=False, default=None)
    arg_format: str | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        """Set target type and initialize."""
        self.target_type = 'delay'
        super().__post_init__()

    @classmethod
    def from_block_device(
        cls,
        device: BlockDevice,
        delay_ms: int,
        start: int = 0,
        size_sectors: int | None = None,
        offset: int = 0,
    ) -> DelayDevice:
        """Create DelayDevice from BlockDevice (3 argument format).

        This applies the same delay to read, write, and flush operations.

        Args:
            device: Source block device
            delay_ms: Delay in milliseconds for all operations
            start: Start sector in virtual device (default: 0)
            size_sectors: Size in sectors (default: device size in sectors)
            offset: Offset in source device sectors (default: 0)

        Returns:
            DelayDevice instance

        Example:
            ```python
            device = BlockDevice('/dev/sdb')
            delay = DelayDevice.from_block_device(device, delay_ms=100, size_sectors=1000000)
            delay.create('my-delay')
            ```
        """
        if size_sectors is None and device.size is not None:
            size_sectors = device.size // device.sector_size

        device_id = cls._get_device_identifier(device)
        args = f'{device_id} {offset} {delay_ms}'

        if size_sectors is None:
            raise ValueError('size_sectors must be provided or device.size must be available')
        dev = cls(start=start, size_sectors=size_sectors, args=args)
        # Set attributes directly - we know the values
        dev.read_device = device_id
        dev.read_offset = offset
        dev.read_delay_ms = delay_ms
        dev.arg_format = '3'
        return dev

    @classmethod
    def from_block_devices_rw(
        cls,
        read_device: BlockDevice,
        read_offset: int,
        read_delay_ms: int,
        write_device: BlockDevice,
        write_offset: int,
        write_delay_ms: int,
        start: int = 0,
        size: int | None = None,
    ) -> DelayDevice:
        """Create DelayTarget with separate read and write/flush devices (6 argument format).

        This allows different devices, offsets, and delays for read operations
        versus write and flush operations.

        Args:
            read_device: Device for read operations
            read_offset: Offset in read device sectors
            read_delay_ms: Delay for read operations in milliseconds
            write_device: Device for write and flush operations
            write_offset: Offset in write device sectors
            write_delay_ms: Delay for write and flush operations in milliseconds
            start: Start sector in virtual device (default: 0)
            size: Size in sectors (default: read device size in sectors)

        Returns:
            DelayTarget instance

        Example:
            ```python
            read_dev = BlockDevice('/dev/sdb')
            write_dev = BlockDevice('/dev/sdc')
            target = DelayTarget.from_block_devices_rw(
                read_dev, read_offset=2048, read_delay_ms=0,
                write_dev, write_offset=4096, write_delay_ms=400,
                size=1000000
            )
            str(target)
            '0 1000000 delay 8:16 2048 0 8:32 4096 400'
            ```
        """
        if size is None and read_device.size is not None:
            size = read_device.size // read_device.sector_size

        read_device_id = cls._get_device_identifier(read_device)
        write_device_id = cls._get_device_identifier(write_device)

        args = f'{read_device_id} {read_offset} {read_delay_ms} {write_device_id} {write_offset} {write_delay_ms}'

        if size is None:
            raise ValueError('size must be provided or read_device.size must be available')
        target = cls(start=start, size_sectors=size, args=args)
        # Set attributes directly - we know the values
        target.read_device = read_device_id
        target.read_offset = read_offset
        target.read_delay_ms = read_delay_ms
        target.write_device = write_device_id
        target.write_offset = write_offset
        target.write_delay_ms = write_delay_ms
        target.arg_format = '6'
        return target

    @classmethod
    def from_block_devices_rwf(
        cls,
        read_device: BlockDevice,
        read_offset: int,
        read_delay_ms: int,
        write_device: BlockDevice,
        write_offset: int,
        write_delay_ms: int,
        flush_device: BlockDevice,
        flush_offset: int,
        flush_delay_ms: int,
        start: int = 0,
        size: int | None = None,
    ) -> DelayDevice:
        """Create DelayTarget with separate read, write, and flush devices (9 argument format).

        This allows different devices, offsets, and delays for read, write,
        and flush operations separately.

        Args:
            read_device: Device for read operations
            read_offset: Offset in read device sectors
            read_delay_ms: Delay for read operations in milliseconds
            write_device: Device for write operations
            write_offset: Offset in write device sectors
            write_delay_ms: Delay for write operations in milliseconds
            flush_device: Device for flush operations
            flush_offset: Offset in flush device sectors
            flush_delay_ms: Delay for flush operations in milliseconds
            start: Start sector in virtual device (default: 0)
            size: Size in sectors (default: read device size in sectors)

        Returns:
            DelayTarget instance

        Example:
            ```python
            device = BlockDevice('/dev/sdb')
            target = DelayTarget.from_block_devices_rwf(
                device, read_offset=0, read_delay_ms=50,
                device, write_offset=0, write_delay_ms=100,
                device, flush_offset=0, flush_delay_ms=333,
                size=1000000
            )
            str(target)
            '0 1000000 delay 8:16 0 50 8:16 0 100 8:16 0 333'
            ```
        """
        if size is None and read_device.size is not None:
            size = read_device.size // read_device.sector_size

        read_device_id = cls._get_device_identifier(read_device)
        write_device_id = cls._get_device_identifier(write_device)
        flush_device_id = cls._get_device_identifier(flush_device)

        args = (
            f'{read_device_id} {read_offset} {read_delay_ms} '
            f'{write_device_id} {write_offset} {write_delay_ms} '
            f'{flush_device_id} {flush_offset} {flush_delay_ms}'
        )

        if size is None:
            raise ValueError('size must be provided or read_device.size must be available')
        target = cls(start=start, size_sectors=size, args=args)
        # Set attributes directly - we know the values
        target.read_device = read_device_id
        target.read_offset = read_offset
        target.read_delay_ms = read_delay_ms
        target.write_device = write_device_id
        target.write_offset = write_offset
        target.write_delay_ms = write_delay_ms
        target.flush_device = flush_device_id
        target.flush_offset = flush_offset
        target.flush_delay_ms = flush_delay_ms
        target.arg_format = '9'
        return target

    @classmethod
    def create_positional(
        cls,
        device_path: str,
        offset: int,
        delay_ms: int,
        start: int = 0,
        size: int | None = None,
        write_device_path: str | None = None,
        write_offset: int | None = None,
        write_delay_ms: int | None = None,
        flush_device_path: str | None = None,
        flush_offset: int | None = None,
        flush_delay_ms: int | None = None,
    ) -> DelayDevice:
        """Create DelayTarget with positional arguments from device mapper documentation.

        Supports 3, 6, or 9 argument formats depending on which parameters are provided.

        Args:
            device_path: Read device path (e.g., '/dev/sdb' or '8:16')
            offset: Read offset in source device sectors
            delay_ms: Read delay in milliseconds
            start: Start sector in virtual device (default: 0)
            size: Size in sectors (required)
            write_device_path: Write device path (enables 6-arg format)
            write_offset: Write offset in sectors (required if write_device_path set)
            write_delay_ms: Write delay in milliseconds (required if write_device_path set)
            flush_device_path: Flush device path (enables 9-arg format)
            flush_offset: Flush offset in sectors (required if flush_device_path set)
            flush_delay_ms: Flush delay in milliseconds (required if flush_device_path set)

        Returns:
            DelayTarget instance

        Raises:
            ValueError: If size is not specified or if incomplete write/flush parameters

        Example:
            ```python
            # 3 argument format
            target = DelayTarget.create_positional('/dev/sdb', offset=0, delay_ms=100, size=2097152)
            str(target)
            '0 2097152 delay /dev/sdb 0 100'

            # 6 argument format
            target = DelayTarget.create_positional(
                '/dev/sdb',
                offset=2048,
                delay_ms=0,
                size=2097152,
                write_device_path='/dev/sdc',
                write_offset=4096,
                write_delay_ms=400,
            )
            str(target)
            '0 2097152 delay /dev/sdb 2048 0 /dev/sdc 4096 400'

            # 9 argument format
            target = DelayTarget.create_positional(
                '/dev/sdb',
                offset=0,
                delay_ms=50,
                size=2097152,
                write_device_path='/dev/sdb',
                write_offset=0,
                write_delay_ms=100,
                flush_device_path='/dev/sdb',
                flush_offset=0,
                flush_delay_ms=333,
            )
            str(target)
            '0 2097152 delay /dev/sdb 0 50 /dev/sdb 0 100 /dev/sdb 0 333'
            ```
        """
        if size is None:
            raise ValueError('Size must be specified for delay targets')

        # Build args based on provided parameters
        args = f'{device_path} {offset} {delay_ms}'
        arg_format = '3'

        # Check for 6-argument format
        if write_device_path is not None:
            if write_offset is None or write_delay_ms is None:
                raise ValueError('write_offset and write_delay_ms required when write_device_path is specified')
            args = f'{args} {write_device_path} {write_offset} {write_delay_ms}'
            arg_format = '6'

            # Check for 9-argument format
            if flush_device_path is not None:
                if flush_offset is None or flush_delay_ms is None:
                    raise ValueError('flush_offset and flush_delay_ms required when flush_device_path is specified')
                args = f'{args} {flush_device_path} {flush_offset} {flush_delay_ms}'
                arg_format = '9'
        elif flush_device_path is not None:
            raise ValueError('flush_device_path requires write_device_path to be specified first')

        target = cls(start=start, size_sectors=size, args=args)
        # Set attributes directly - we know the values
        target.read_device = device_path
        target.read_offset = offset
        target.read_delay_ms = delay_ms
        target.arg_format = arg_format

        if write_device_path is not None:
            target.write_device = write_device_path
            target.write_offset = write_offset
            target.write_delay_ms = write_delay_ms

        if flush_device_path is not None:
            target.flush_device = flush_device_path
            target.flush_offset = flush_offset
            target.flush_delay_ms = flush_delay_ms

        return target

    def refresh(self) -> None:
        """Parse args and update instance attributes.

        Extracts all delay parameters from the args string based on
        the number of arguments (3, 6, or 9) and updates instance attributes.

        Updates:
            - read_device, read_offset, read_delay_ms (always)
            - write_device, write_offset, write_delay_ms (6+ args)
            - flush_device, flush_offset, flush_delay_ms (9 args)
            - arg_format: '3', '6', or '9' indicating format used

        Example:
            ```python
            target = DelayTarget(0, 1000000, '8:16 0 50 8:16 0 100 8:16 0 333')
            target.read_delay_ms  # 50
            target.write_delay_ms  # 100
            target.flush_delay_ms  # 333
            target.arg_format  # '9'
            ```
        """
        parts = self.args.split()

        if len(parts) < 3:
            return

        # Parse read device params (always present)
        self.read_device = parts[0]
        self.read_offset = int(parts[1])
        self.read_delay_ms = int(parts[2])

        if len(parts) == 3:
            self.arg_format = '3'
        elif len(parts) >= 6:
            # Parse write device params
            self.write_device = parts[3]
            self.write_offset = int(parts[4])
            self.write_delay_ms = int(parts[5])

            if len(parts) == 6:
                self.arg_format = '6'
            elif len(parts) >= 9:
                # Parse flush device params
                self.flush_device = parts[6]
                self.flush_offset = int(parts[7])
                self.flush_delay_ms = int(parts[8])
                self.arg_format = '9'

    @classmethod
    def from_table_line(cls, table_line: str) -> DelayDevice | None:
        """Create DelayTarget from a dmsetup table line.

        Parses a full table line (including start, size, and type) and
        creates a DelayTarget instance. Useful for reconstructing targets
        from existing devices.

        Args:
            table_line: Full table line from 'dmsetup table' output

        Returns:
            DelayTarget instance or None if parsing fails

        Example:
            ```python
            line = '0 2097152 delay 8:16 0 100'
            target = DelayTarget.from_table_line(line)
            target.size  # 2097152
            ```
        """
        parts = table_line.strip().split(None, 3)
        if len(parts) < 4:
            logging.warning(f'Invalid table line: {table_line}')
            return None

        start = int(parts[0])
        size = int(parts[1])
        target_type = parts[2]
        args = parts[3]

        if target_type != 'delay':
            logging.warning(f'Not a delay target: {target_type}')
            return None

        target = cls(start=start, size_sectors=size, args=args)
        target.refresh()  # Parse args to populate attributes
        return target
