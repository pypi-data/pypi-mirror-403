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

Note: For multipath devices managed by multipathd daemon, use
`sts.multipath.MultipathDevice` which inherits from BlockDevice directly.

Each device class can be in two states:
1. Configuration: has target config (start, size, args) but not yet created
2. Active: device exists on system, has path, name, dm_name, etc.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from sts.blockdevice import BlockDevice
from sts.utils.cmdline import run
from sts.utils.errors import DeviceError, DeviceNotFoundError

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass
class DmDevice(BlockDevice):
    """Base class for all Device Mapper devices.

    A DM device can be in two states:
    1. Configuration: has target config (start, size, args) but not yet created on system
    2. Active: device exists on system, has path, dm_name, table, etc.

    This class unifies target configuration and device management. Before calling
    create(), the device is just a configuration. After create(), it becomes a
    full block device with all BlockDevice functionality.

    Args:
        start: Start sector (where this target begins)
        size: Size in sectors (length of this target)
        args: Target-specific arguments (e.g. device paths, options)
        dm_name: Device Mapper name (set after creation or when loading existing device)
        name: Kernel device name like 'dm-0' (set after creation)
        path: Device path like '/dev/dm-0' (set after creation)

    Example:
        ```python
        # Create configuration
        device = LinearDevice.from_block_device(backing_dev, size=1000000)

        # Create on system
        device.create('my-linear')

        # Now it's a full device
        device.dm_device_path  # '/dev/mapper/my-linear'
        device.suspend()
        device.resume()
        device.remove()
        ```
    """

    # Target configuration (always available)
    start: int = 0
    size_sectors: int = 0  # Size in sectors (renamed to avoid conflict with BlockDevice.size)
    args: str = ''

    # Device Mapper name (set after creation or when loading existing device)
    dm_name: str | None = None

    # Target type - override in subclasses
    target_type: str = field(init=False, default='')

    # Internal state
    table: str | None = field(init=False, default=None, repr=False)
    is_created: bool = field(init=False, default=False, repr=False)

    # Class-level paths
    DM_PATH: ClassVar[Path] = Path('/sys/class/block')
    DM_DEV_PATH: ClassVar[Path] = Path('/dev/mapper')

    def __post_init__(self) -> None:
        """Initialize Device Mapper device.

        If dm_name or path is provided, assumes device exists and initializes
        BlockDevice properties. Otherwise, stays in configuration-only state.
        """
        # Check if this is an existing device (has dm_name or path)
        if self.dm_name or self.path:
            # Set path based on dm_name if not provided
            if not self.path and self.dm_name:
                self.path = f'/dev/mapper/{self.dm_name}'
            elif not self.path and self.name:
                self.path = f'/dev/{self.name}'

            # Initialize BlockDevice (queries system)
            super().__post_init__()

            # Get device mapper name if not provided
            if not self.dm_name and self.name:
                result = run(f'dmsetup info -c --noheadings -o name {self.name}')
                if result.succeeded:
                    self.dm_name = result.stdout.strip()

            # Load table from system
            if self.dm_name:
                result = run(f'dmsetup table {self.dm_name}')
                if result.succeeded:
                    self.table = result.stdout.strip()
                    self._parse_table()

            self.is_created = True

    @property
    def type(self) -> str:
        """Get target type.

        Returns:
            Target type string (e.g. 'linear', 'delay', 'vdo')
        """
        if self.target_type:
            return self.target_type
        # Fallback: Remove 'Device' suffix from class name and convert to lowercase
        return self.__class__.__name__.lower().removesuffix('device')

    def __str__(self) -> str:
        """Return target table entry.

        Format: <start> <size> <type> <args>
        Used in dmsetup table commands.
        """
        return f'{self.start} {self.size_sectors} {self.type} {self.args}'

    @property
    def device_path(self) -> Path:
        """Get path to device in sysfs.

        Returns:
            Path to device directory

        Raises:
            DeviceNotFoundError: If device does not exist
        """
        if not self.is_created or not self.name:
            msg = 'Device not created yet'
            raise DeviceNotFoundError(msg)

        path = self.DM_PATH / self.name
        if not path.exists():
            msg = f'Device {self.name} not found'
            raise DeviceNotFoundError(msg)
        return path

    @property
    def device_root_dir(self) -> str:
        """Get device mapper root directory.

        Returns:
            Device mapper root directory path (/dev/mapper)
        """
        return str(self.DM_DEV_PATH)

    @property
    def dm_device_path(self) -> str | None:
        """Get full device mapper device path.

        Returns:
            Full device path (e.g. '/dev/mapper/my-device') or None if not available
        """
        if not self.dm_name:
            return None
        return f'{self.device_root_dir}/{self.dm_name}'

    def create(
        self,
        dm_name: str,
        *,
        uuid: str | None = None,
        readonly: bool = False,
        notable: bool = False,
        readahead: str | int | None = None,
        addnodeoncreate: bool = False,
        addnodeonresume: bool = False,
    ) -> bool:
        """Create the device on the system.

        After successful creation, this device becomes a full BlockDevice
        with all properties populated from the system.

        Args:
            dm_name: Name for the device mapper device
            uuid: Optional UUID for the device (can be used in place of name in commands)
            readonly: Set the table being loaded as read-only
            notable: Create device without loading any table
            readahead: Read ahead size in sectors, or 'auto', 'none', or '+N' for minimum
            addnodeoncreate: Ensure /dev/mapper node exists after create
            addnodeonresume: Ensure /dev/mapper node exists after resume (default with udev)

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            device = DelayDevice.from_block_device(backing, delay_ms=100)
            if device.create('my-delay', uuid='my-uuid-123'):
                print(f'Created: {device.dm_device_path}')
            ```
        """
        if self.is_created:
            logging.warning(f'Device {self.dm_name} already created')
            return True

        cmd = f'dmsetup create {dm_name}'

        if uuid:
            cmd += f' --uuid {uuid}'
        if readonly:
            cmd += ' --readonly'
        if addnodeoncreate:
            cmd += ' --addnodeoncreate'
        if addnodeonresume:
            cmd += ' --addnodeonresume'
        if readahead is not None:
            cmd += f' --readahead {readahead}'

        if notable:
            cmd += ' --notable'
        else:
            # Build table from this device's configuration
            table = str(self)
            cmd += f' --table "{table}"'
            logging.info(f'Creating device {dm_name} with table: {table}')

        result = run(cmd)

        if result.failed:
            logging.error(f'Failed to create device {dm_name}: {result.stderr}')
            return False

        logging.info(f'Successfully created device mapper device: {dm_name}')

        # Set dm_name and reinitialize as existing device
        self.dm_name = dm_name
        self.path = f'/dev/mapper/{dm_name}'

        # Initialize BlockDevice properties from system
        super().__post_init__()

        # Get kernel device name
        if not self.name:
            result = run(f'dmsetup info -c --noheadings -o name,blkdevname {dm_name}')
            if result.succeeded:
                parts = result.stdout.strip().split()
                if len(parts) >= 2:
                    self.name = parts[1]

        # Load table from system
        result = run(f'dmsetup table {dm_name}')
        if result.succeeded:
            self.table = result.stdout.strip()
            self._parse_table()

        self.is_created = True
        return True

    def _parse_table(self) -> None:
        """Parse table and update target configuration from system.

        Subclasses should override this to parse target-specific attributes.
        """
        if not self.table:
            return

        parts = self.table.strip().split(None, 3)
        if len(parts) >= 4:
            self.start = int(parts[0])
            self.size_sectors = int(parts[1])
            # parts[2] is the target type
            self.args = parts[3]

            # Call refresh if available (subclasses implement this for target-specific parsing)
            if hasattr(self, 'refresh') and callable(getattr(self, 'refresh', None)):
                self.refresh()

    def refresh(self) -> None:
        """Refresh device state from system.

        Re-reads the device table and status from the system.
        Subclasses should override to parse target-specific attributes.

        Returns:
            True if successful, False otherwise
        """
        if not self.is_created or not self.dm_name:
            return

        # Refresh table from system
        result = run(f'dmsetup table {self.dm_name}')
        if result.succeeded:
            self.table = result.stdout.strip()
            self._parse_table()

    def get_status(
        self,
        *,
        target_type: str | None = None,
        noflush: bool = False,
    ) -> str | None:
        """Get device status from dmsetup.

        Outputs status information for each of the device's targets.

        Args:
            target_type: Only display information for the specified target type
            noflush: Do not commit thin-pool metadata before reporting statistics

        Returns:
            Status string or None if not available
        """
        if not self.is_created or not self.dm_name:
            logging.error('Device not created or dm_name not available')
            return None

        cmd = f'dmsetup status {self.dm_name}'
        if target_type:
            cmd += f' --target {target_type}'
        if noflush:
            cmd += ' --noflush'

        result = run(cmd)
        if result.failed:
            logging.error(f'Failed to get status for {self.dm_name}')
            return None

        return result.stdout.strip()

    def suspend(
        self,
        *,
        nolockfs: bool = False,
        noflush: bool = False,
    ) -> bool:
        """Suspend device.

        Suspends I/O to the device. Any I/O that has already been mapped by the device
        but has not yet completed will be flushed. Any further I/O to that device will
        be postponed for as long as the device is suspended.

        Args:
            nolockfs: Do not attempt to synchronize filesystem (skip fsfreeze)
            noflush: Let outstanding I/O remain unflushed (requires target support)

        Returns:
            True if successful, False otherwise
        """
        if not self.is_created or not self.dm_name:
            logging.error('Device not created or dm_name not available')
            return False

        cmd = f'dmsetup suspend {self.dm_name}'
        if nolockfs:
            cmd += ' --nolockfs'
        if noflush:
            cmd += ' --noflush'

        result = run(cmd)
        if result.failed:
            logging.error('Failed to suspend device')
            return False
        return True

    def resume(
        self,
        *,
        addnodeoncreate: bool = False,
        addnodeonresume: bool = False,
        noflush: bool = False,
        nolockfs: bool = False,
        readahead: str | int | None = None,
    ) -> bool:
        """Resume device.

        Un-suspends a device. If an inactive table has been loaded, it becomes live.
        Postponed I/O then gets re-queued for processing.

        Args:
            addnodeoncreate: Ensure /dev/mapper node exists after create
            addnodeonresume: Ensure /dev/mapper node exists after resume (default with udev)
            noflush: Do not flush outstanding I/O
            nolockfs: Do not attempt to synchronize filesystem
            readahead: Read ahead size in sectors, or 'auto', 'none', or '+N' for minimum

        Returns:
            True if successful, False otherwise
        """
        if not self.is_created or not self.dm_name:
            logging.error('Device not created or dm_name not available')
            return False

        cmd = f'dmsetup resume {self.dm_name}'
        if addnodeoncreate:
            cmd += ' --addnodeoncreate'
        if addnodeonresume:
            cmd += ' --addnodeonresume'
        if noflush:
            cmd += ' --noflush'
        if nolockfs:
            cmd += ' --nolockfs'
        if readahead is not None:
            cmd += f' --readahead {readahead}'

        result = run(cmd)
        if result.failed:
            logging.error('Failed to resume device')
            return False
        return True

    def remove(
        self,
        *,
        force: bool = False,
        retry: bool = False,
        deferred: bool = False,
    ) -> bool:
        """Remove device.

        Removes the device mapping. The underlying devices are unaffected.
        Open devices cannot be removed, but --force will replace the table with
        one that fails all I/O. --deferred enables deferred removal when the device
        is in use.

        Args:
            force: Replace the table with one that fails all I/O
            retry: Retry removal for a few seconds if it fails (e.g., udev race)
            deferred: Enable deferred removal - device removed when last user closes it

        Returns:
            True if successful, False otherwise

        Note:
            Do NOT combine --force and --udevcookie as this may cause
            nondeterministic results.
        """
        if not self.is_created or not self.dm_name:
            logging.error('Device not created or dm_name not available')
            return False

        cmd = f'dmsetup remove {self.dm_name}'
        if force:
            cmd += ' --force'
        if retry:
            cmd += ' --retry'
        if deferred:
            cmd += ' --deferred'

        result = run(cmd)
        if result.failed:
            logging.error('Failed to remove device')
            return False

        self.is_created = False
        return True

    def clear(self) -> bool:
        """Clear the inactive table slot.

        Destroys the table in the inactive table slot for the device.
        This is useful when you want to abort a table load before resuming.

        Returns:
            True if successful, False otherwise
        """
        if not self.is_created or not self.dm_name:
            logging.error('Device not created or dm_name not available')
            return False

        result = run(f'dmsetup clear {self.dm_name}')
        if result.failed:
            logging.error(f'Failed to clear inactive table for {self.dm_name}')
            return False
        return True

    def deps(self, *, output_format: str = 'devno') -> list[str]:
        """Get device dependencies.

        Outputs a list of devices referenced by the live table for this device.

        Args:
            output_format: Output format for device names:
                - 'devno': Major and minor pair (default)
                - 'blkdevname': Block device name
                - 'devname': Map name for DM devices, blkdevname otherwise

        Returns:
            List of device identifiers (format depends on output_format)
        """
        if not self.is_created or not self.dm_name:
            logging.error('Device not created or dm_name not available')
            return []

        result = run(f'dmsetup deps -o {output_format} {self.dm_name}')
        if result.failed:
            logging.error(f'Failed to get dependencies for {self.dm_name}')
            return []

        # Parse output: "1 dependencies  : (major, minor) ..."
        output = result.stdout.strip()
        deps = []
        if ':' in output:
            deps_part = output.split(':', 1)[1].strip()
            # Extract device identifiers from the output
            if output_format == 'devno':
                # Format: (major, minor) or (major:minor)
                matches = re.findall(r'\((\d+[,:]\s*\d+)\)', deps_part)
                deps = [m.replace(' ', '').replace(',', ':') for m in matches]
            else:
                # Format: (device_name)
                matches = re.findall(r'\(([^)]+)\)', deps_part)
                deps = matches

        return deps

    def info(
        self,
        *,
        columns: bool = False,
        noheadings: bool = False,
        fields: str | None = None,
        separator: str | None = None,
        sort_fields: str | None = None,
        nameprefixes: bool = False,
    ) -> dict[str, str] | str | None:
        """Get device information.

        Outputs information about the device in various formats.

        Args:
            columns: Display output in columns rather than Field: Value lines
            noheadings: Suppress the headings line when using columnar output
            fields: Comma-separated list of fields to display
                   (name, major, minor, attr, open, segments, events, uuid)
            separator: Separator for columnar output
            sort_fields: Fields to sort by (prefix with '-' for reverse)
            nameprefixes: Add DM_ prefix plus field name to output

        Returns:
            If columns=False: Dictionary of field names to values
            If columns=True: Raw output string
            None if device not found or error
        """
        if not self.is_created or not self.dm_name:
            logging.error('Device not created or dm_name not available')
            return None

        cmd = f'dmsetup info {self.dm_name}'
        if columns:
            cmd += ' --columns'
            if noheadings:
                cmd += ' --noheadings'
            if fields:
                cmd += f' -o {fields}'
            if separator:
                cmd += f' --separator "{separator}"'
            if sort_fields:
                cmd += f' --sort {sort_fields}'
            if nameprefixes:
                cmd += ' --nameprefixes'

        result = run(cmd)
        if result.failed:
            logging.error(f'Failed to get info for {self.dm_name}')
            return None

        output = result.stdout.strip()

        if columns:
            return output

        # Parse Field: Value format into dictionary
        info_dict: dict[str, str] = {}
        for line in output.splitlines():
            if ':' in line:
                key, value = line.split(':', 1)
                info_dict[key.strip()] = value.strip()

        return info_dict

    def message(self, sector: int, message: str) -> bool:
        """Send message to device target.

        Send a message to the target at the specified sector.
        Use sector 0 if the sector is not relevant to the target.

        Args:
            sector: Sector number (use 0 if not needed)
            message: Message string to send to the target

        Returns:
            True if successful, False otherwise
        """
        if not self.is_created or not self.dm_name:
            logging.error('Device not created or dm_name not available')
            return False

        result = run(f'dmsetup message {self.dm_name} {sector} {message}')
        if result.failed:
            logging.error(f'Failed to send message to {self.dm_name}: {result.stderr}')
            return False
        return True

    def rename(self, new_name: str) -> bool:
        """Rename the device.

        Args:
            new_name: New name for the device

        Returns:
            True if successful, False otherwise
        """
        if not self.is_created or not self.dm_name:
            logging.error('Device not created or dm_name not available')
            return False

        result = run(f'dmsetup rename {self.dm_name} {new_name}')
        if result.failed:
            logging.error(f'Failed to rename {self.dm_name} to {new_name}')
            return False

        # Update internal state
        old_name = self.dm_name
        self.dm_name = new_name
        self.path = f'/dev/mapper/{new_name}'
        logging.info(f'Successfully renamed device from {old_name} to {new_name}')
        return True

    def set_uuid(self, uuid: str) -> bool:
        """Set the UUID of a device that was created without one.

        After a UUID has been set it cannot be changed.

        Args:
            uuid: UUID to set for the device

        Returns:
            True if successful, False otherwise
        """
        if not self.is_created or not self.dm_name:
            logging.error('Device not created or dm_name not available')
            return False

        result = run(f'dmsetup rename {self.dm_name} --setuuid {uuid}')
        if result.failed:
            logging.error(f'Failed to set UUID for {self.dm_name}: {result.stderr}')
            return False

        logging.info(f'Successfully set UUID {uuid} for device {self.dm_name}')
        return True

    def reload_table(self, new_table: str) -> bool:
        """Reload device table.

        Suspends the device, loads a new table, and resumes.

        Args:
            new_table: New table string to load

        Returns:
            True if successful, False otherwise
        """
        if not self.is_created or not self.dm_name:
            logging.error('Device not created or dm_name not available')
            return False

        # Suspend device
        if not self.suspend():
            return False

        # Load new table
        result = run(f'dmsetup load {self.dm_name} "{new_table}"')
        if result.failed:
            logging.error(f'Failed to load new table: {result.stderr}')
            self.resume()
            return False

        # Resume with new table
        if not self.resume():
            return False

        # Refresh from system
        self.refresh()
        logging.info(f'Successfully reloaded table for {self.dm_name}')
        return True

    def load(
        self,
        table: str | None = None,
        table_file: str | None = None,
    ) -> bool:
        """Load table into the inactive table slot.

        Loads a table into the inactive table slot for the device.
        Use resume() to make the inactive table live.

        Args:
            table: Table string to load
            table_file: Path to file containing the table

        Returns:
            True if successful, False otherwise

        Note:
            Either table or table_file must be provided, but not both.
        """
        if not self.is_created or not self.dm_name:
            logging.error('Device not created or dm_name not available')
            return False

        if table and table_file:
            raise ValueError('Cannot specify both table and table_file')

        if table:
            result = run(f'dmsetup load {self.dm_name} --table "{table}"')
        elif table_file:
            result = run(f'dmsetup load {self.dm_name} {table_file}')
        else:
            raise ValueError('Either table or table_file must be provided')

        if result.failed:
            logging.error(f'Failed to load table for {self.dm_name}: {result.stderr}')
            return False
        return True

    def get_table(
        self,
        *,
        concise: bool = False,
        target_type: str | None = None,
        showkeys: bool = False,
    ) -> str | None:
        """Get the current device table.

        Outputs the current table for the device in a format that can be fed
        back using create or load commands.

        Args:
            concise: Output in concise format (name,uuid,minor,flags,table)
            target_type: Only show information for the specified target type
            showkeys: Show real encryption keys (for crypt/integrity targets)

        Returns:
            Table string or None if error
        """
        if not self.is_created or not self.dm_name:
            logging.error('Device not created or dm_name not available')
            return None

        cmd = f'dmsetup table {self.dm_name}'
        if concise:
            cmd += ' --concise'
        if target_type:
            cmd += f' --target {target_type}'
        if showkeys:
            cmd += ' --showkeys'

        result = run(cmd)
        if result.failed:
            logging.error(f'Failed to get table for {self.dm_name}')
            return None

        return result.stdout.strip()

    def wipe_table(
        self,
        *,
        force: bool = False,
        noflush: bool = False,
        nolockfs: bool = False,
    ) -> bool:
        """Wipe device table.

        Wait for any I/O in-flight through the device to complete, then replace
        the table with a new table that fails any new I/O sent to the device.
        If successful, this should release any devices held open by the device's table(s).

        Args:
            force: Force the operation
            noflush: Do not flush outstanding I/O
            nolockfs: Do not attempt to synchronize filesystem

        Returns:
            True if successful, False otherwise
        """
        if not self.is_created or not self.dm_name:
            logging.error('Device not created or dm_name not available')
            return False

        cmd = f'dmsetup wipe_table {self.dm_name}'
        if force:
            cmd += ' --force'
        if noflush:
            cmd += ' --noflush'
        if nolockfs:
            cmd += ' --nolockfs'

        result = run(cmd)
        if result.failed:
            logging.error(f'Failed to wipe table for {self.dm_name}: {result.stderr}')
            return False
        return True

    def mknodes(self) -> bool:
        """Ensure /dev/mapper node is correct.

        Ensures that the node in /dev/mapper for this device is correct.

        Returns:
            True if successful, False otherwise
        """
        if not self.is_created or not self.dm_name:
            logging.error('Device not created or dm_name not available')
            return False

        result = run(f'dmsetup mknodes {self.dm_name}')
        if result.failed:
            logging.error(f'Failed to mknodes for {self.dm_name}')
            return False
        return True

    def setgeometry(
        self,
        cylinders: int,
        heads: int,
        sectors: int,
        start: int,
    ) -> bool:
        """Set the device geometry.

        Sets the device geometry to C/H/S format.

        Args:
            cylinders: Number of cylinders
            heads: Number of heads
            sectors: Sectors per track
            start: Start sector

        Returns:
            True if successful, False otherwise
        """
        if not self.is_created or not self.dm_name:
            logging.error('Device not created or dm_name not available')
            return False

        result = run(f'dmsetup setgeometry {self.dm_name} {cylinders} {heads} {sectors} {start}')
        if result.failed:
            logging.error(f'Failed to set geometry for {self.dm_name}: {result.stderr}')
            return False
        return True

    def wait(
        self,
        event_nr: int | None = None,
        *,
        noflush: bool = False,
    ) -> int | None:
        """Wait for device event.

        Sleeps until the event counter for the device exceeds event_nr.

        Args:
            event_nr: Event number to wait for (waits until counter exceeds this)
            noflush: Do not commit thin-pool metadata before reporting

        Returns:
            Current event number after waiting, or None on error
        """
        if not self.is_created or not self.dm_name:
            logging.error('Device not created or dm_name not available')
            return None

        cmd = f'dmsetup wait {self.dm_name}'
        if noflush:
            cmd += ' --noflush'
        if event_nr is not None:
            cmd += f' {event_nr}'

        result = run(cmd)
        if result.failed:
            logging.error(f'Failed to wait for {self.dm_name}')
            return None

        # Parse event number from output
        try:
            return int(result.stdout.strip())
        except ValueError:
            return None

    def measure(self) -> str | None:
        """Show IMA measurement data.

        Shows the data that the device would report to the IMA subsystem
        if a measurement was triggered. This is for debugging and does not
        actually trigger a measurement.

        Returns:
            Measurement data string or None on error
        """
        if not self.is_created or not self.dm_name:
            logging.error('Device not created or dm_name not available')
            return None

        result = run(f'dmsetup measure {self.dm_name}')
        if result.failed:
            logging.error(f'Failed to measure {self.dm_name}')
            return None

        return result.stdout.strip()

    def mangle(self) -> bool:
        """Mangle device name.

        Ensures the device name and UUID contains only whitelisted characters
        (supported by udev) and renames if necessary.

        Returns:
            True if successful, False otherwise
        """
        if not self.is_created or not self.dm_name:
            logging.error('Device not created or dm_name not available')
            return False

        result = run(f'dmsetup mangle {self.dm_name}')
        if result.failed:
            logging.error(f'Failed to mangle {self.dm_name}')
            return False
        return True

    def splitname(self, subsystem: str = 'LVM') -> dict[str, str] | None:
        """Split device name into subsystem constituents.

        Splits the device name into its subsystem components.
        LVM generates device names by concatenating Volume Group, Logical Volume,
        and any internal Layer with a hyphen separator.

        Args:
            subsystem: Subsystem to use for splitting (default: LVM)

        Returns:
            Dictionary with split name components or None on error
        """
        if not self.is_created or not self.dm_name:
            logging.error('Device not created or dm_name not available')
            return None

        result = run(f'dmsetup splitname {self.dm_name} {subsystem}')
        if result.failed:
            logging.error(f'Failed to split name {self.dm_name}')
            return None

        # Parse output into dictionary
        output = result.stdout.strip()
        name_dict: dict[str, str] = {}
        for line in output.splitlines():
            if ':' in line:
                key, value = line.split(':', 1)
                name_dict[key.strip()] = value.strip()

        return name_dict

    @staticmethod
    def version() -> dict[str, str] | None:
        """Get dmsetup and driver version information.

        Returns:
            Dictionary with 'library' and 'driver' version strings, or None on error
        """
        result = run('dmsetup version')
        if result.failed:
            logging.error('Failed to get dmsetup version')
            return None

        output = result.stdout.strip()
        version_dict: dict[str, str] = {}
        for line in output.splitlines():
            if ':' in line:
                key, value = line.split(':', 1)
                version_dict[key.strip().lower().replace(' ', '_')] = value.strip()

        return version_dict

    @staticmethod
    def targets() -> list[dict[str, str]]:
        """Get list of available device mapper targets.

        Displays the names and versions of currently-loaded targets.

        Returns:
            List of dictionaries with 'name' and 'version' keys
        """
        result = run('dmsetup targets')
        if result.failed:
            logging.error('Failed to get targets')
            return []

        targets_list: list[dict[str, str]] = []
        for line in result.stdout.strip().splitlines():
            parts = line.strip().split()
            if len(parts) >= 2:
                targets_list.append(
                    {
                        'name': parts[0],
                        'version': parts[1],
                    }
                )

        return targets_list

    @staticmethod
    def udevcreatecookie() -> str | None:
        """Create a new udev synchronization cookie.

        Creates a new cookie to synchronize actions with udev processing.
        The cookie can be used with --udevcookie option or exported as
        DM_UDEV_COOKIE environment variable.

        Returns:
            Cookie value string or None on error

        Note:
            The cookie is a system-wide semaphore that needs to be cleaned up
            explicitly by calling udevreleasecookie().
        """
        result = run('dmsetup udevcreatecookie')
        if result.failed:
            logging.error('Failed to create udev cookie')
            return None

        return result.stdout.strip()

    @staticmethod
    def udevreleasecookie(cookie: str | None = None) -> bool:
        """Release a udev synchronization cookie.

        Waits for all pending udev processing bound to the cookie value
        and cleans up the cookie with underlying semaphore.

        Args:
            cookie: Cookie value to release. If not provided, uses DM_UDEV_COOKIE
                   environment variable.

        Returns:
            True if successful, False otherwise
        """
        cmd = 'dmsetup udevreleasecookie'
        if cookie:
            cmd += f' {cookie}'

        result = run(cmd)
        if result.failed:
            logging.error('Failed to release udev cookie')
            return False
        return True

    @staticmethod
    def udevcomplete(cookie: str) -> bool:
        """Signal udev processing completion.

        Wakes any processes that are waiting for udev to complete processing
        the specified cookie.

        Args:
            cookie: Cookie value to signal completion for

        Returns:
            True if successful, False otherwise
        """
        result = run(f'dmsetup udevcomplete {cookie}')
        if result.failed:
            logging.error(f'Failed to complete udev cookie {cookie}')
            return False
        return True

    @staticmethod
    def udevcomplete_all(age_in_minutes: int | None = None) -> bool:
        """Remove all old udev cookies.

        Removes all cookies older than the specified number of minutes.
        Any process waiting on a cookie will be resumed immediately.

        Args:
            age_in_minutes: Remove cookies older than this many minutes

        Returns:
            True if successful, False otherwise
        """
        cmd = 'dmsetup udevcomplete_all'
        if age_in_minutes is not None:
            cmd += f' {age_in_minutes}'

        result = run(cmd)
        if result.failed:
            logging.error('Failed to complete all udev cookies')
            return False
        return True

    @staticmethod
    def udevcookie() -> list[str]:
        """List all existing udev cookies.

        Cookies are system-wide semaphores with keys prefixed by two
        predefined bytes (0x0D4D).

        Returns:
            List of cookie values
        """
        result = run('dmsetup udevcookie')
        if result.failed:
            logging.error('Failed to list udev cookies')
            return []

        return result.stdout.strip().splitlines()

    @staticmethod
    def udevflags(cookie: str) -> dict[str, str]:
        """Parse udev control flags from cookie.

        Parses the cookie value and extracts any udev control flags encoded.
        The output is in environment key format suitable for use in udev rules.

        Args:
            cookie: Cookie value to parse

        Returns:
            Dictionary of flag names to values (typically '1')
        """
        result = run(f'dmsetup udevflags {cookie}')
        if result.failed:
            logging.error(f'Failed to get udev flags for cookie {cookie}')
            return {}

        flags: dict[str, str] = {}
        for line in result.stdout.strip().splitlines():
            if '=' in line:
                key, value = line.split('=', 1)
                flags[key.strip()] = value.strip().strip('\'"')

        return flags

    @classmethod
    def remove_all(cls, *, force: bool = False, deferred: bool = False) -> bool:
        """Remove all device mapper devices.

        Attempts to remove all device definitions (reset the driver).
        This also runs mknodes afterwards. Use with care!

        Args:
            force: Replace tables with one that fails all I/O before removing
            deferred: Enable deferred removal for open devices

        Returns:
            True if successful, False otherwise

        Warning:
            Open devices cannot be removed unless force or deferred is used.
        """
        cmd = 'dmsetup remove_all'
        if force:
            cmd += ' --force'
        if deferred:
            cmd += ' --deferred'

        result = run(cmd)
        if result.failed:
            logging.error('Failed to remove all devices')
            return False
        return True

    @classmethod
    def mknodes_all(cls) -> bool:
        """Ensure all /dev/mapper nodes are correct.

        Ensures that all nodes in /dev/mapper correspond to mapped devices
        currently loaded by the device-mapper kernel driver, adding, changing,
        or removing nodes as necessary.

        Returns:
            True if successful, False otherwise
        """
        result = run('dmsetup mknodes')
        if result.failed:
            logging.error('Failed to run mknodes')
            return False
        return True

    @classmethod
    def ls(
        cls,
        *,
        target_type: str | None = None,
        output_format: str = 'devno',
        tree: bool = False,
        tree_options: str | None = None,
        exec_cmd: str | None = None,
    ) -> list[str] | str:
        """List device mapper devices.

        Lists device names with optional filtering and formatting.

        Args:
            target_type: Only list devices with at least one target of this type
            output_format: Output format for device names:
                - 'devno': Major and minor pair (default)
                - 'blkdevname': Block device name
                - 'devname': Map name for DM devices
            tree: Display dependencies between devices as a tree
            tree_options: Comma-separated tree display options:
                - device/nodevice, blkdevname, active, open, rw, uuid
                - ascii, utf, vt100, compact, inverted, notrunc
            exec_cmd: Execute command for each device (device name appended)

        Returns:
            If tree=True: Tree output as string
            Otherwise: List of device names
        """
        cmd = 'dmsetup ls'
        if target_type:
            cmd += f' --target {target_type}'
        if output_format != 'devno':
            cmd += f' -o {output_format}'
        if tree:
            cmd += ' --tree'
            if tree_options:
                cmd += f' -o {tree_options}'
        if exec_cmd:
            cmd += f' --exec "{exec_cmd}"'

        result = run(cmd)
        if result.failed:
            logging.warning('No Device Mapper devices found')
            return [] if not tree else ''

        output = result.stdout.strip()

        if tree or exec_cmd:
            return output

        # Parse device names from output
        devices = []
        for line in output.splitlines():
            if line.strip():
                parts = line.strip().split()
                if parts:
                    devices.append(parts[0])

        return devices

    @classmethod
    def get_all(cls) -> Sequence[DmDevice]:
        """Get list of all Device Mapper devices.

        Returns:
            List of DmDevice instances
        """
        devices = []
        result = run('dmsetup ls')
        if result.failed:
            logging.warning('No Device Mapper devices found')
            return []

        for line in result.stdout.splitlines():
            try:
                stripped_line = line.strip()
                if not stripped_line:
                    continue

                parts = stripped_line.split()
                if len(parts) < 2:
                    continue

                dm_name = parts[0]
                dev_id = parts[1].strip('()')
                major, minor = dev_id.split(':')

                # Get kernel device name (dm-N)
                result = run(f'ls -l /dev/dm-* | grep "{major}, *{minor}"')
                if result.failed:
                    continue
                name = result.stdout.split('/')[-1].strip()

                devices.append(cls(dm_name=dm_name, name=name, path=f'/dev/{name}'))
            except (ValueError, DeviceError):
                logging.exception('Failed to parse device info')
                continue

        return devices

    @classmethod
    def create_concise(cls, concise_spec: str) -> bool:
        """Create one or more devices from concise device specification.

        Each device is specified by a comma-separated list:
        name,uuid,minor,flags,table[,table]...

        Multiple devices are separated by semicolons.

        Args:
            concise_spec: Concise device specification string
                Format: <name>,<uuid>,<minor>,<flags>,<table>[,<table>+][;<next device>...]
                - name: Device name
                - uuid: Device UUID (optional, can be empty)
                - minor: Minor number (optional, can be empty for auto-assignment)
                - flags: 'ro' for read-only or 'rw' for read-write (default)
                - table: One or more table lines (comma-separated if multiple)

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            # Single linear device
            DmDevice.create_concise('test-linear,,,rw,0 2097152 linear /dev/loop0 0')

            # Two devices at once
            DmDevice.create_concise('dev1,,,,0 2097152 linear /dev/loop0 0;dev2,,,,0 2097152 linear /dev/loop1 0')
            ```

        Note:
            Use backslash to escape commas or semicolons in names or tables.
        """
        result = run(f'dmsetup create --concise "{concise_spec}"')
        if result.failed:
            logging.error(f'Failed to create devices from concise spec: {result.stderr}')
            return False
        return True

    @staticmethod
    def help(*, columns: bool = False) -> str | None:
        """Get dmsetup command help.

        Outputs a summary of the commands available.

        Args:
            columns: Include the list of report fields in the output

        Returns:
            Help text or None on error
        """
        cmd = 'dmsetup help'
        if columns:
            cmd += ' --columns'

        result = run(cmd)
        # Note: dmsetup help returns exit code 0 but writes to stderr
        output = result.stdout.strip() or result.stderr.strip()
        return output if output else None

    @classmethod
    def get_by_name(cls, dm_name: str) -> DmDevice | None:
        """Get Device Mapper device by name.

        Args:
            dm_name: Device Mapper name (e.g. 'my-device')

        Returns:
            DmDevice instance or None if not found
        """
        if not dm_name:
            raise ValueError('Device Mapper name required')

        # Check if device exists
        result = run(f'dmsetup info {dm_name}')
        if result.failed:
            return None

        try:
            return cls(dm_name=dm_name)
        except DeviceError:
            return None

    @staticmethod
    def _get_device_identifier(device: BlockDevice) -> str:
        """Get device identifier for device mapper.

        Args:
            device: BlockDevice instance

        Returns:
            Device identifier (major:minor format)

        Raises:
            DeviceError: If device identifier cannot be determined
        """
        device_id = device.device_id
        if device_id:
            return device_id
        raise DeviceError(f'No device ID available for {device.path}')
