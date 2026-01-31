# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""LVM device management.

This module provides functionality for managing LVM devices:
- Physical Volume (PV) operations
- Volume Group (VG) operations
- Logical Volume (LV) operations

LVM (Logical Volume Management) provides flexible disk space management:
1. Physical Volumes (PVs): Physical disks or partitions
2. Volume Groups (VGs): Pool of space from PVs
3. Logical Volumes (LVs): Virtual partitions from VG space

Key benefits:
- Resize filesystems online
- Snapshot and mirror volumes
- Stripe across multiple disks
- Move data between disks
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from sts.lvm.base import LvmDevice
from sts.lvm.lvreport import LVReport
from sts.udevadm import udevadm_settle
from sts.utils.cmdline import run

if TYPE_CHECKING:
    from sts.utils.cmdline import CommandResult


@dataclass
class LogicalVolume(LvmDevice):
    """Logical Volume device.

    A Logical Volume (LV) is a virtual partition created from VG space.
    LVs appear as block devices that can be formatted and mounted.

    Key features:
    - Flexible sizing
    - Online resizing
    - Snapshots
    - Striping and mirroring
    - Thin provisioning

    Args:
        name: Device name (optional)
        path: Device path (optional, defaults to /dev/<vg>/<name>)
        size: Device size in bytes (optional, discovered from device)
        model: Device model (optional)
        yes: Automatically answer yes to prompts
        force: Force operations without confirmation
        vg: Volume group name (optional, discovered from device)
        report: LV report instance (optional, created automatically)
        prevent_report_updates: Prevent automatic report updates (defaults to False)

    The LogicalVolume class now includes integrated report functionality:
    - Automatic report creation when name and vg are provided
    - Automatic report refresh after state-changing operations
    - Access to detailed LV information directly via report attributes
    - Prevention of updates via prevent_report_updates flag

    Example:
        ```python
        # Basic usage with automatic report
        lv = LogicalVolume(name='lv0', vg='vg0')
        lv.create(size='100M')
        print(lv.report.lv_size)

        # Prevent automatic updates
        lv = LogicalVolume(name='lv0', vg='vg0', prevent_report_updates=True)

        # Manual report refresh
        lv.refresh_report()
        ```
    """

    # Optional parameters for this class
    vg: str | None = None  # Parent VG
    pool_name: str | None = None
    report: LVReport | None = field(default=None, repr=False)
    prevent_report_updates: bool = False

    # Available LV commands
    COMMANDS: ClassVar[list[str]] = [
        'lvchange',  # Change LV attributes
        'lvcreate',  # Create LV
        'lvconvert',  # Convert LV type
        'lvdisplay',  # Show LV details
        'lvextend',  # Increase LV size
        'lvreduce',  # Reduce LV size
        'lvremove',  # Remove LV
        'lvrename',  # Rename LV
        'lvresize',  # Change LV size
        'lvs',  # List LVs
        'lvscan',  # Scan for LVs
    ]

    def __post_init__(self) -> None:
        """Initialize Logical Volume.

        - Sets device path from name and VG
        - Discovers VG membership
        - Creates and updates from report
        """
        # Set path based on name and vg if not provided
        if not self.path and self.name and self.vg:
            self.path = f'/dev/{self.vg}/{self.name}'

        # Initialize parent class
        super().__post_init__()

    def refresh_report(self) -> bool:
        """Refresh LV report data.

        Creates or updates the LV report with the latest information.

        Returns:
            bool: True if refresh was successful
        """
        # Create new report if needed
        if not self.report:
            # Do not provide name and vg during init to prevent update
            self.report = LVReport()
            self.report.name = self.name
            self.report.vg = self.vg

        # Refresh the report data
        return self.report.refresh()

    def discover_vg(self) -> str | None:
        """Discover VG if name is available."""
        if self.name and not self.vg:
            result = run(f'lvs {self.name} -o vg_name --noheadings')
            if result.succeeded:
                self.vg = result.stdout.strip()
                return self.vg
        return None

    def create(self, *args: str, **options: str) -> bool:
        """Create Logical Volume.

        Creates a new LV in the specified VG:
        - Allocates space from VG
        - Creates device mapper device
        - Initializes LV metadata

        If pool_name is set, automatically adds --thinpool or --vdopool option
        depending on the volume type:
        - For VDO volumes (type='vdo'): uses --vdopool
        - For thin volumes: uses --thinpool

        Args:
            *args: Additional arguments passed to lvcreate
            **options: LV options (see LvmOptions)

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            # Create regular LV
            lv = LogicalVolume(name='lv0', vg='vg0')
            lv.create(size='1G')
            True

            # Create thin volume (with pool_name set)
            thin_lv = LogicalVolume(name='thin1', vg='vg0', pool_name='pool1')
            thin_lv.create(virtualsize='500M')
            True

            # Create VDO volume (with pool_name set)
            vdo_lv = LogicalVolume(name='vdo1', vg='vg0', pool_name='vdopool1')
            vdo_lv.create(type='vdo', size='8G')
            True
            ```
        """
        if not self.name:
            logging.error('Logical volume name required')
            return False
        if not self.vg:
            logging.error('Volume group required')
            return False

        # If pool_name is set, automatically add the appropriate pool option
        # Use --vdopool for VDO volumes, --thinpool for thin volumes
        if self.pool_name:
            lv_type = options.get('type', '')
            if lv_type == 'vdo' and 'vdopool' not in options:
                options = {**options, 'vdopool': self.pool_name}
            elif 'thinpool' not in options and lv_type != 'vdo':
                options = {**options, 'thinpool': self.pool_name}

        result = self._run('lvcreate', '-n', self.name, self.vg, *args, **options)
        if result.succeeded:
            self.refresh_report()
        return result.succeeded

    def remove(self, *args: str, **options: str) -> bool:
        """Remove Logical Volume.

        Removes LV and its data:
        - Data is permanently lost
        - Space is returned to VG
        - Device mapper device is removed

        Args:
            *args: Additional volume paths to remove (for removing multiple volumes)
            **options: LV options (see LvmOptions)

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            # Remove single volume
            lv = LogicalVolume(name='lv0', vg='vg0')
            lv.remove()
            True

            # Remove multiple volumes
            lv = LogicalVolume(name='lv1', vg='vg0')
            lv.remove('vg0/lv2', 'vg0/lv3')
            True
            ```
        """
        if not self.name:
            logging.error('Logical volume name required')
            return False
        if not self.vg:
            logging.error('Volume group required')
            return False

        # Start with this LV
        targets = [f'{self.vg}/{self.name}']

        # Add any additional volumes from args
        if args:
            targets.extend(args)

        result = self._run('lvremove', *targets, **options)
        return result.succeeded

    def change(self, *args: str, **options: str) -> bool:
        """Change Logical Volume attributes.

        Change a general LV attribute:

        Args:
            *args: LV options (see LVMOptions)
            **options: LV options (see LvmOptions)

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            lv = LogicalVolume(name='lv0', vg='vg0')
            lv.change('-an', 'vg0/lv0')
            True
            ```
        """
        result = self._run('lvchange', *args, **options)
        if result.succeeded:
            self.refresh_report()
        return result.succeeded

    def extend(self, *args: str, **options: str) -> bool:
        """Extend Logical volume.

        - LV must be initialized (using lvcreate)
        - VG must have sufficient usable space

        Args:
            *args: Additional arguments passed to lvextend
            **options: All options passed as strings to lvextend command

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            lv = LogicalVolume(name='lvol0', vg='vg0')
            lv.extend(extents='100%vg')
            True
            ```
        """
        if not self.vg:
            logging.error('Volume group name required')
            return False
        if not self.name:
            logging.error('Logical volume name required')
            return False

        result = self._run('lvextend', f'{self.vg}/{self.name}', *args, **options)
        if result.succeeded:
            self.refresh_report()
        return result.succeeded

    def lvs(self, *args: str, **options: str) -> CommandResult:
        """Get information about logical volumes.

        Executes the 'lvs' command with optional filtering to display
        information about logical volumes.

        Args:
            *args: Positional args passed through to `lvs` (e.g., LV selector, flags).
            **options: LV command options (see LvmOptions).

        Returns:
            CommandResult object containing command output and status

        Example:
            ```python
            lv = LogicalVolume()
            result = lv.lvs()
            print(result.stdout)
            ```
        """
        return self._run('lvs', *args, **options)

    def convert(self, *args: str, **options: str) -> bool:
        """Convert Logical Volume type.

        Converts LV type (linear, striped, mirror, snapshot, etc):
        - Can change between different LV types
        - May require additional space or devices
        - Some conversions are irreversible

        Args:
            *args: LV conversion arguments
            **options: LV options (see LvmOptions)

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            lv = LogicalVolume(name='lv0', vg='vg0')
            lv.convert('--type', 'mirror')
            True
            ```
        """
        if not self.vg:
            logging.error('Volume group name required')
            return False
        if not self.name:
            logging.error('Logical volume name required')
            return False

        result = self._run('lvconvert', f'{self.vg}/{self.name}', *args, **options)
        if result.succeeded:
            self.refresh_report()
        return result.succeeded

    def convert_to_thinpool(self, *args: str, **options: str) -> ThinPool | None:
        """Convert logical volume to thin pool.

        Converts an existing LV to a thin pool using lvconvert --thinpool.
        The LV must already exist and have sufficient space.

        Args:
            *args: Additional arguments passed to lvconvert
            **options: All options passed as strings to lvconvert command

        Returns:
            ThinPool instance if successful, None otherwise

        Example:
            ```python
            # Basic conversion
            lv = LogicalVolume(name='lv0', vg='vg0')
            lv.create(size='100M')
            pool = lv.convert_to_thinpool()

            # Conversion with parameters
            pool = lv.convert_to_thinpool(chunksize='256k', zero='y', discards='nopassdown', poolmetadatasize='4M')

            # Conversion with separate metadata LV
            pool = lv.convert_to_thinpool(poolmetadata='metadata_lv')
            ```
        """
        if not self.vg:
            logging.error('Volume group name required')
            return None
        if not self.name:
            logging.error('Logical volume name required')
            return None

        # Build the lvconvert command - pass all args and options through
        cmd_args = ['--thinpool', f'{self.vg}/{self.name}']
        if args:
            cmd_args.extend(args)

        result = self._run('lvconvert', *cmd_args, **options)
        if not result.succeeded:
            return None

        # Create and return new ThinPool instance based on current LV's properties
        thin_pool = ThinPool(
            name=self.name,
            vg=self.vg,
            yes=self.yes,
            force=self.force,
        )
        thin_pool.refresh_report()
        thin_pool.discover_thin_volumes()
        return thin_pool

    def convert_splitmirrors(self, *args: str, **options: str) -> tuple[bool, LogicalVolume | None]:
        """Split images from a raid1 or mirror LV and create a new LV.

        Splits the specified number of images from a raid1 or mirror LV and uses them
        to create a new LV with the specified name.

        Args:
            *args: All arguments passed to lvconvert (including count, new_name, etc.)
            **options: All options passed as strings to lvconvert command

        Returns:
            Tuple of (success, new_lv) where:
            - success: True if successful, False otherwise
            - new_lv: LogicalVolume object for the new split LV, or None if failed

        Example:
            ```python
            lv = LogicalVolume(name='mirror_lv', vg='vg0')
            success, split_lv = lv.convert_splitmirrors('--splitmirrors', '1', '--name', 'split_lv')
            if success:
                print(f'Created new LV: {split_lv.name}')
            ```
        """
        if not self.vg:
            logging.error('Volume group name required')
            return False, None
        if not self.name:
            logging.error('Logical volume name required')
            return False, None

        result = self._run('lvconvert', f'{self.vg}/{self.name}', *args, **options)
        success = result.succeeded

        if success:
            self.refresh_report()

        # Try to find the new LV name from args (this is a best effort)
        new_lv = None
        if success:
            # Look for --name parameter in args
            new_name = None
            for i, arg in enumerate(args):
                if arg == '--name' and i + 1 < len(args):
                    new_name = args[i + 1]
                    break

            if new_name:
                try:
                    new_lv = LogicalVolume(name=new_name, vg=self.vg)
                    if not new_lv.refresh_report():
                        logging.warning(f'Failed to refresh report for new LV {new_name}')
                except (ValueError, OSError) as e:
                    logging.warning(f'Failed to create LogicalVolume object for {new_name}: {e}')
                    new_lv = None

        return success, new_lv

    def convert_originname(self, *args: str, **options: str) -> tuple[bool, LogicalVolume | None]:
        """Convert LV to thin LV with named external origin.

        Converts the LV to a thin LV in the specified thin pool, using the original LV
        as an external read-only origin with the specified name.

        Args:
            *args: Additional arguments passed to lvconvert (optional)
            **options: Options for the conversion:
                - thinpool: Name of the thin pool (required, format: vg/pool or pool)
                - originname: Name for the read-only origin LV (required)
                - type: LV type (defaults to 'thin')
                - Other lvconvert options as needed

        Returns:
            Tuple of (success, origin_lv) where:
            - success: True if successful, False otherwise
            - origin_lv: LogicalVolume object for the read-only origin LV, or None if failed

        Example:
            ```python
            # Simple usage with keyword arguments
            lv = LogicalVolume(name='data_lv', vg='vg0')
            success, origin_lv = lv.convert_originname(thinpool='vg0/thin_pool', originname='data_origin')

            # With additional options
            success, origin_lv = lv.convert_originname(
                thinpool='vg0/thin_pool', originname='data_origin', chunksize='128k'
            )
            ```
        """
        if not self.vg:
            logging.error('Volume group name required')
            return False, None
        if not self.name:
            logging.error('Logical volume name required')
            return False, None

        # Extract required parameters
        thinpool = options.pop('thinpool', None)
        originname = options.pop('originname', None)

        if not thinpool:
            logging.error('thinpool parameter is required')
            return False, None
        if not originname:
            logging.error('originname parameter is required')
            return False, None

        # Build command arguments
        cmd_args = ['--type', options.pop('type', 'thin')]
        cmd_args.extend(['--thinpool', thinpool])
        cmd_args.extend(['--originname', originname])

        # Add any additional args passed positionally
        if args:
            cmd_args.extend(args)

        # Add any remaining options as --key value pairs
        for key, value in options.items():
            cmd_args.extend([f'--{key}', value])

        # Execute the conversion
        result = self._run('lvconvert', f'{self.vg}/{self.name}', *cmd_args)
        success = result.succeeded

        if success:
            self.refresh_report()

        # Create LogicalVolume object for the origin
        origin_lv = None
        if success and originname:
            try:
                origin_lv = LogicalVolume(name=originname, vg=self.vg)
                if not origin_lv.refresh_report():
                    logging.warning(f'Failed to refresh report for origin LV {originname}')
            except (ValueError, OSError) as e:
                logging.warning(f'Failed to create LogicalVolume object for {originname}: {e}')
                origin_lv = None

        return success, origin_lv

    def display(self, *args: str, **options: str) -> CommandResult:
        """Display Logical Volume details.

        Shows detailed information about the LV:
        - Size and allocation
        - Attributes and permissions
        - Segment information
        - Device mapper details

        Args:
            *args: Additional arguments passed to lvdisplay
            **options: All options passed as strings to lvdisplay command

        Returns:
            CommandResult object containing command output and status

        Example:
            ```python
            lv = LogicalVolume(name='lv0', vg='vg0')
            result = lv.display()
            print(result.stdout)
            ```
        """
        if not self.vg or not self.name:
            return self._run('lvdisplay', *args, **options)
        return self._run('lvdisplay', f'{self.vg}/{self.name}', *args, **options)

    def reduce(self, *args: str, **options: str) -> bool:
        """Reduce Logical Volume size.

        Reduces LV size (shrinks the volume):
        - Filesystem must be shrunk first
        - Data loss risk if not done carefully
        - Cannot reduce below used space

        Args:
            *args: Additional lvreduce arguments
            **options: LV options (see LvmOptions)

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            lv = LogicalVolume(name='lv0', vg='vg0')
            lv.reduce(size='500M')
            True

            # With additional arguments
            lv.reduce('--test', size='500M')
            True
            ```
        """
        if not self.vg:
            logging.error('Volume group name required')
            return False
        if not self.name:
            logging.error('Logical volume name required')
            return False
        result = self._run('lvreduce', f'{self.vg}/{self.name}', *args, **options)
        if result.succeeded:
            self.refresh_report()
        return result.succeeded

    def rename(self, new_name: str, *args: str, **options: str) -> bool:
        """Rename Logical Volume.

        Changes the LV name:
        - Must not conflict with existing LV names
        - Updates device mapper devices
        - May require remounting if mounted

        Args:
            new_name: New name for the LV
            *args: Additional arguments passed to lvrename
            **options: All options passed as strings to lvrename command

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            lv = LogicalVolume(name='lv0', vg='vg0')
            lv.rename('new_lv')
            True
            ```
        """
        if not self.vg:
            logging.error('Volume group name required')
            return False
        if not self.name:
            logging.error('Logical volume name required')
            return False
        if not new_name:
            logging.error('New name required')
            return False

        result = self._run('lvrename', f'{self.vg}/{self.name}', new_name, *args, **options)
        if result.succeeded:
            self.name = new_name
            self.path = f'/dev/{self.vg}/{self.name}'
            self.refresh_report()
        return result.succeeded

    def resize(self, *args: str, **options: str) -> bool:
        """Resize Logical Volume.

        Changes LV size (can grow or shrink):
        - Combines extend and reduce functionality
        - Safer than lvreduce for shrinking
        - Can resize filesystem simultaneously

        Args:
            *args: Additional lvresize arguments (e.g., '-l+2', '-t', '--test')
            **options: LV options (see LvmOptions)

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            lv = LogicalVolume(name='lv0', vg='vg0')
            lv.resize(size='2G')
            True

            # With additional arguments
            lv.resize('-l+2', size='2G')
            True

            # With test flag
            lv.resize('--test', size='2G')
            True
            ```
        """
        if not self.vg:
            logging.error('Volume group name required')
            return False
        if not self.name:
            logging.error('Logical volume name required')
            return False

        result = self._run('lvresize', f'{self.vg}/{self.name}', *args, **options)
        if result.succeeded:
            self.refresh_report()
        return result.succeeded

    def scan(self, *args: str, **options: str) -> CommandResult:
        """Scan for Logical Volumes.

        Scans all devices for LV information:
        - Discovers new LVs
        - Updates device mapper
        - Useful after system changes

        Args:
            **options: LV options (see LvmOptions)

        Returns:
            CommandResult object containing command output and status

        Example:
            ```python
            lv = LogicalVolume()
            result = lv.scan()
            print(result.stdout)
            ```
        """
        return self._run('lvscan', *args, **options)

    def deactivate(self) -> bool:
        """Deactivate Logical Volume."""
        udevadm_settle()
        result = self.change('-an', f'{self.vg}/{self.name}')
        udevadm_settle()
        if result:
            return self.wait_for_lv_deactivation()
        return result

    def activate(self) -> bool:
        """Activate Logical Volume."""
        return self.change('-ay', f'{self.vg}/{self.name}')

    def wait_for_lv_deactivation(self, timeout: int = 30) -> bool:
        """Wait for logical volume to be fully deactivated.

        Args:
            timeout: Maximum wait time in seconds

        Returns:
            True if deactivated successfully, False if timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Check LV status using lvs command
            self.refresh_report()
            logging.info(self.report.lv_active if self.report else None)
            if self.report and self.report.lv_active != 'active':
                # LV is inactive - also verify device node is gone
                if self.path is not None:
                    device_path = Path(self.path)
                    if not device_path.exists():
                        return True
                else:
                    return True  # If no path, consider it deactivated
            time.sleep(2)  # Poll every 2 seconds

        logging.warning(f'LV {self.vg}/{self.name} deactivation timed out after {timeout}s')
        return False

    def change_discards(self, *args: str, **options: str) -> bool:
        """Change discards setting for logical volume.

        Args:
            *args: Additional arguments passed to lvchange
            **options: All options passed as strings to lvchange command

        Returns:
            True if change succeeded
        """
        if not self.vg or not self.name:
            logging.error('Volume group and logical volume name required')
            return False

        return self.change(f'{self.vg}/{self.name}', *args, **options)

    def create_snapshot(self, snapshot_name: str, *args: str, **options: str) -> LogicalVolume | None:
        """Create snapshot of this LV.

        Creates a snapshot of the current LV (self) with the given snapshot name.
        For thin LVs, creates thin snapshots. For regular LVs, creates COW snapshots.

        Args:
            snapshot_name: Name for the new snapshot LV
            *args: Additional command-line arguments (e.g., '-K', '-k', '--test')
            **options: Snapshot options (see LvmOptions)

        Returns:
            LogicalVolume instance representing the created snapshot, or None if failed

        Example:
            ```python
            # Create origin LV and then snapshot it
            origin_lv = LogicalVolume(name='thin_lv', vg='vg0')
            # ... create the origin LV ...
            # Create thin snapshot (no size needed)
            snap1 = origin_lv.create_snapshot('snap1')

            # Create COW snapshot with ignore activation skip
            snap2 = origin_lv.create_snapshot('snap2', '-K', size='100M')
            ```
        """
        if not self.name:
            logging.error('Origin LV name required')
            return None
        if not self.vg:
            logging.error('Volume group required')
            return None
        if not snapshot_name:
            logging.error('Snapshot name required')
            return None

        # Build snapshot command
        cmd_args = ['-s']

        # Add any additional arguments
        if args:
            cmd_args.extend(args)

        # Add origin (this LV)
        cmd_args.append(f'{self.vg}/{self.name}')

        # Add snapshot name
        cmd_args.extend(['-n', snapshot_name])

        result = self._run('lvcreate', *cmd_args, **options)
        if result.succeeded:
            self.refresh_report()
            # Return new LogicalVolume instance representing the snapshot
            snap = LogicalVolume(name=snapshot_name, vg=self.vg)
            snap.refresh_report()
            return snap
        return None

    @classmethod
    def from_report(cls, report: LVReport) -> LogicalVolume | None:
        """Create LogicalVolume from LVReport.

        Args:
            report: LV report data

        Returns:
            LogicalVolume instance or None if invalid

        Example:
            ```python
            lv = LogicalVolume.from_report(report)
            ```
        """
        if not report.name or not report.vg:
            return None

        # Create LogicalVolume with report already attached
        return cls(
            name=report.name,
            vg=report.vg,
            path=report.lv_path,
            report=report,  # Attach the report directly
            prevent_report_updates=True,  # Avoid double refresh since report is already fresh
        )

    @classmethod
    def get_all(cls, vg: str | None = None) -> list[LogicalVolume]:
        """Get all Logical Volumes.

        Args:
            vg: Optional volume group to filter by

        Returns:
            List of LogicalVolume instances

        Example:
            ```python
            LogicalVolume.get_all()
            [LogicalVolume(name='lv0', vg='vg0', ...), LogicalVolume(name='lv1', vg='vg1', ...)]
            ```
        """
        logical_volumes: list[LogicalVolume] = []

        # Get all reports
        reports = LVReport.get_all(vg)

        # Create LogicalVolumes from reports
        logical_volumes.extend(lv for report in reports if (lv := cls.from_report(report)))

        return logical_volumes

    def __eq__(self, other: object) -> bool:
        """Compare two LogicalVolume instances for equality.

        Two LogicalVolume instances are considered equal if they have the same:
        - name
        - volume group (vg)
        - pool_name (if both have a pool_name)

        For thin LVs that belong to a pool, the pool_name must also match.
        For regular LVs or when either LV has no pool_name, only name and vg are compared.

        Args:
            other: Object to compare with

        Returns:
            True if the LogicalVolume instances are equal, False otherwise

        Example:
            ```python
            lv1 = LogicalVolume(name='lv0', vg='vg0')
            lv2 = LogicalVolume(name='lv0', vg='vg0')
            lv3 = LogicalVolume(name='lv1', vg='vg0')

            assert lv1 == lv2  # Same name and vg
            assert lv1 != lv3  # Different name

            # For thin LVs with pools
            thin1 = LogicalVolume(name='thin1', vg='vg0')
            thin1.pool_name = 'pool'
            thin2 = LogicalVolume(name='thin1', vg='vg0')
            thin2.pool_name = 'pool'
            thin3 = LogicalVolume(name='thin1', vg='vg0')
            thin3.pool_name = 'other_pool'

            assert thin1 == thin2  # Same name, vg, and pool
            assert thin1 != thin3  # Different pool
            ```
        """
        if not isinstance(other, LogicalVolume):
            return False
        if self.pool_name is None or other.pool_name is None:
            return self.name == other.name and self.vg == other.vg
        return self.name == other.name and self.vg == other.vg and self.pool_name == other.pool_name

    def __hash__(self) -> int:
        """Generate hash for LogicalVolume instance.

        The hash is based on the combination of name, volume group (vg), and pool_name.
        This allows LogicalVolume instances to be used in sets and as dictionary keys.
        The hash is consistent with the equality comparison in __eq__.

        Returns:
            int: Hash value based on (name, vg, pool_name) tuple

        Example:
            ```python
            lv1 = LogicalVolume(name='lv0', vg='vg0')
            lv2 = LogicalVolume(name='lv0', vg='vg0')

            # Can be used in sets
            lv_set = {lv1, lv2}  # Only one instance since they're equal

            # Can be used as dictionary keys
            lv_dict = {lv1: 'some_value'}
            ```
        """
        return hash((self.name, self.vg, self.pool_name))


@dataclass
class ThinPool(LogicalVolume):
    """Thin Pool logical volume.

    A Thin Pool is a special type of logical volume that provides thin provisioning
    capabilities. It manages multiple thin volumes and consists of two special
    components:
    - tdata: The data component that stores actual data
    - tmeta: The metadata component that stores thin provisioning metadata

    The thin pool can hold multiple logical volumes (thin volumes) that share
    the pool's space dynamically.

    Args:
        name: Pool name (required)
        vg: Volume group name (required)
        path: Device path (optional, defaults to /dev/<vg>/<name>)
        size: Device size in bytes (optional, discovered from device)
        model: Device model (optional)
        yes: Automatically answer yes to prompts
        force: Force operations without confirmation
        report: LV report instance (optional, created automatically)
        prevent_report_updates: Prevent automatic report updates (defaults to False)
        thin_volumes: List of thin volumes in this pool (discovered automatically)

    Key features:
    - Thin provisioning with overcommitment
    - Automatic space allocation
    - Snapshot support
    - Pool usage monitoring
    - Component conversion (tdata/tmeta)

    Example:
        ```python
        # Create thin pool
        pool = ThinPool(name='pool1', vg='vg0')
        pool.create(size='1G')

        # Create thin volumes in the pool
        thin_lv1 = pool.create_thin_volume('thin1', virtualsize='500M')
        thin_lv2 = pool.create_thin_volume('thin2', virtualsize='800M')

        # Monitor pool usage
        data_usage, meta_usage = pool.get_pool_usage()

        # Access special volumes
        tdata = pool.get_tdata_volume()
        tmeta = pool.get_tmeta_volume()
        ```
    """

    # Thin volumes in this pool
    thin_volumes: list[LogicalVolume] = field(default_factory=list, repr=False)
    tdata: LogicalVolume | None = None
    tmeta: LogicalVolume | None = None

    def __post_init__(self) -> None:
        """Initialize Thin Pool.

        - Sets device path from name and VG
        - Initializes parent LogicalVolume
        - Discovers thin volumes in the pool
        - Populates tdata and tmeta component references
        """
        super().__post_init__()

    # @override
    def refresh_report(self) -> bool:
        """Refresh Thin pool LV report data.

        Creates or updates the Thin pool LV report with the latest information.
        Also refreshes the tdata and tmeta component reports if they exist.

        Returns:
            bool: True if refresh was successful
        """
        # Create new report if needed
        if not self.report:
            # Do not provide name and vg during init to prevent update
            self.report = LVReport()
            self.report.name = self.name
            self.report.vg = self.vg

        # Refresh the pool report
        success = self.report.refresh()

        # Refresh tdata and tmeta if they exist
        if self.get_tdata_volume() and self.tdata:
            self.tdata.refresh_report()
        if self.get_tmeta_volume() and self.tmeta:
            self.tmeta.refresh_report()

        return success

    # @override
    def create(self, *args: str, **options: str) -> bool:
        """Create Thin Pool logical volume.

        Overrides the parent LogicalVolume.create() method to automatically
        set type='thin-pool' since ThinPool objects are always thin pools.

        Args:
            *args: Additional arguments passed to lvcreate
            **options: All options passed as strings to lvcreate command

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            pool = ThinPool(name='pool1', vg='vg0')
            pool.create(size='1G')  # type='thin-pool' is automatically set

            # Can also specify additional options
            pool.create(size='1G', chunksize='256k', poolmetadatasize='4M')
            ```
        """
        # Always set type to 'thin-pool' for ThinPool objects
        # This ensures the correct LV type is created regardless of what user passes
        options['type'] = 'thin-pool'

        # Call parent create method
        return super().create(*args, **options)

    def discover_thin_volumes(self) -> list[LogicalVolume]:
        """Discover thin volumes in this pool.

        Returns:
            List of LogicalVolume instances representing thin volumes in this pool
        """
        self.thin_volumes = []

        # Get all LVs in the VG
        all_lvs = LogicalVolume.get_all(self.vg)

        # Filter for thin volumes that belong to this pool
        for lv in all_lvs:
            if (
                lv.report
                and lv.report.pool_lv
                and lv.report.pool_lv.strip('[]') == self.name
                and lv.report.lv_layout
                and 'thin' in lv.report.lv_layout
            ):
                self.thin_volumes.append(lv)

        return self.thin_volumes

    def get_tdata_volume(self) -> LogicalVolume | None:
        """Get the tdata (data) component of the thin pool.

        The tdata volume stores the actual data for all thin volumes in the pool.
        It's always named <pool_name>_tdata by LVM convention.

        Returns:
            LogicalVolume instance for the tdata component, or None if not found

        Example:
            ```python
            pool = ThinPool(name='pool1', vg='vg0')
            tdata = pool.get_tdata_volume()
            if tdata:
                print(f'Data volume: {tdata.name}')
            ```
        """
        if not self.name or not self.vg:
            return None

        # LVM always names the data component as {pool_name}_tdata
        data_lv_name = f'{self.name}_tdata'

        if self.tdata:
            return self.tdata

        try:
            self.tdata = LogicalVolume(name=data_lv_name, vg=self.vg)
        except (ValueError, OSError) as e:
            logging.warning(f'Failed to get tdata volume {data_lv_name}: {e}')
            return None
        else:
            return self.tdata

    def get_tmeta_volume(self) -> LogicalVolume | None:
        """Get the tmeta (metadata) component of the thin pool.

        The tmeta volume stores the thin provisioning metadata for the pool.
        It's always named <pool_name>_tmeta by LVM convention.

        Returns:
            LogicalVolume instance for the tmeta component, or None if not found

        Example:
            ```python
            pool = ThinPool(name='pool1', vg='vg0')
            tmeta = pool.get_tmeta_volume()
            if tmeta:
                print(f'Metadata volume: {tmeta.name}')
            ```
        """
        if not self.name or not self.vg:
            return None

        # LVM always names the metadata component as {pool_name}_tmeta
        meta_lv_name = f'{self.name}_tmeta'

        if self.tmeta:
            return self.tmeta

        try:
            self.tmeta = LogicalVolume(name=meta_lv_name, vg=self.vg)
        except (ValueError, OSError) as e:
            logging.warning(f'Failed to get tmeta volume {meta_lv_name}: {e}')
            return None
        else:
            return self.tmeta

    def convert_pool_data(self, *args: str, **options: str) -> bool:
        """Convert thin pool data component to specified type.

        Converts the thin pool's data component (e.g., from linear to RAID1).
        This is typically used to add mirroring or change the RAID level of the pool's data.

        Args:
            *args: Additional arguments passed to lvconvert
            **options: All options passed as strings to lvconvert command

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            # Convert pool data to RAID1 with 3 mirrors
            pool.convert_pool_data(type='raid1', mirrors='3')
            ```
        """
        if not self.vg:
            logging.error('Volume group name required')
            return False
        if not self.name:
            logging.error('Logical volume name required')
            return False

        # Convert the pool's data component (always named {pool_name}_tdata)
        result = self._run('lvconvert', f'{self.vg}/{self.name}_tdata', *args, **options)
        if result.succeeded:
            self.refresh_report()
        return result.succeeded

    def convert_pool_metadata(self, *args: str, **options: str) -> bool:
        """Convert thin pool metadata component to specified type.

        Converts the thin pool's metadata component (e.g., from linear to RAID1).
        This is typically used to add mirroring or change the RAID level of the pool's metadata.

        Args:
            *args: Additional arguments passed to lvconvert
            **options: All options passed as strings to lvconvert command

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            # Convert pool metadata to RAID1 with 1 mirror
            pool.convert_pool_metadata(type='raid1', mirrors='1')
            ```
        """
        if not self.vg:
            logging.error('Volume group name required')
            return False
        if not self.name:
            logging.error('Logical volume name required')
            return False

        # Convert the pool's metadata component (always named {pool_name}_tmeta)
        result = self._run('lvconvert', f'{self.vg}/{self.name}_tmeta', *args, **options)
        if result.succeeded:
            self.refresh_report()
        return result.succeeded

    def swap_metadata(self, metadata_lv: str, *args: str, **options: str) -> bool:
        """Swap thin pool metadata with another LV.

        Swaps the thin pool's metadata device with the specified LV.
        This is useful for metadata repair operations where you need to
        extract, check, or replace the metadata device.

        The command executed is:
            lvconvert --thinpool <vg>/<pool> --poolmetadata <metadata_lv>

        Args:
            metadata_lv: The LV to swap with the pool's metadata (format: vg/lv or just lv)
            *args: Additional arguments passed to lvconvert
            **options: All options passed as strings to lvconvert command

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            # Create a temporary LV for metadata swap
            meta_swap = LogicalVolume(name='meta_swap', vg='vg0')
            meta_swap.create(size='4M')

            # Swap metadata - the pool's current metadata goes to meta_swap
            pool.swap_metadata('vg0/meta_swap')

            # Now meta_swap contains the old metadata, pool has new empty metadata
            # You can activate meta_swap and run thin_check on it

            # Swap back
            pool.swap_metadata('vg0/meta_swap')
            ```
        """
        if not self.vg:
            logging.error('Volume group name required')
            return False
        if not self.name:
            logging.error('Logical volume name required')
            return False
        if not metadata_lv:
            logging.error('Metadata LV path required')
            return False

        # Build the command with --thinpool option
        result = self._run(
            'lvconvert',
            '--thinpool',
            f'{self.vg}/{self.name}',
            '--poolmetadata',
            metadata_lv,
            *args,
            **options,
        )
        if result.succeeded:
            self.refresh_report()
        return result.succeeded

    def repair(self, pv_device: str | None = None, *args: str, **options: str) -> bool:
        """Repair thin pool metadata.

        Attempts to repair the thin pool's metadata using lvconvert --repair.
        This creates a new metadata device and attempts to recover the pool.

        Args:
            pv_device: Optional PV device to use for the new metadata
            *args: Additional arguments passed to lvconvert
            **options: All options passed as strings to lvconvert command

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            # Repair pool using any available space
            pool.repair()

            # Repair pool using specific PV for new metadata
            pool.repair('/dev/sdb')
            ```
        """
        if not self.vg:
            logging.error('Volume group name required')
            return False
        if not self.name:
            logging.error('Logical volume name required')
            return False

        cmd_args = ['--repair', f'{self.vg}/{self.name}']
        if pv_device:
            cmd_args.append(pv_device)
        if args:
            cmd_args.extend(args)

        result = self._run('lvconvert', *cmd_args, **options)
        logging.info(result.stdout)
        logging.info(result.stderr)
        logging.info(result.rc)
        if result.succeeded:
            self.refresh_report()
        return result.succeeded

    def get_pool_usage(self) -> tuple[str, str]:
        """Get thin pool data and metadata usage percentages.

        Returns:
            Tuple of (data_percent, metadata_percent) as strings

        Example:
            ```python
            pool = ThinPool(name='pool1', vg='vg0')
            data_usage, meta_usage = pool.get_pool_usage()
            print(f'Data usage: {data_usage}%, Metadata usage: {meta_usage}%')
            ```
        """
        if not self.vg or not self.name:
            logging.error('Volume group and logical volume name required')
            return 'unknown', 'unknown'

        # Get data usage
        data_result = self.lvs(f'{self.vg}/{self.name}', o='data_percent', noheadings='')
        data_percent = data_result.stdout.strip() if data_result.succeeded else 'unknown'

        # Get metadata usage
        meta_result = self.lvs(f'{self.vg}/{self.name}', o='metadata_percent', noheadings='')
        meta_percent = meta_result.stdout.strip() if meta_result.succeeded else 'unknown'

        return data_percent, meta_percent

    def get_data_stripes(self) -> str | None:
        """Get stripe count for thin pool data component.

        For thin pools, the actual stripe information is stored in the data component (_tdata),
        not in the main pool LV. This method returns the stripe count from the data component.

        Returns:
            String representing stripe count, or None if not a thin pool or stripes not found

        Example:
            ```python
            pool = ThinPool(name='pool', vg='vg0')
            pool.create(stripes='2', size='100M')
            stripe_count = pool.get_data_stripes()  # Returns '2'
            ```
        """
        assert self.refresh_report()
        if self.tdata and self.tdata.report:
            return self.tdata.report.stripes
        return None

    def get_data_stripe_size(self) -> str | None:
        """Get stripe size for thin pool data component.

        For thin pools, the actual stripe size information is stored in the data component (_tdata),
        not in the main pool LV. This method returns the stripe size from the data component.

        Returns:
            String representing stripe size, or None if not a thin pool or stripe size not found

        Example:
            ```python
            pool = ThinPool(name='pool', vg='vg0')
            pool.create(stripes='2', stripesize='64k', size='100M')
            stripe_size = pool.get_data_stripe_size()  # Returns '64.00k'
            ```
        """
        assert self.refresh_report()
        if self.tdata and self.tdata.report:
            return self.tdata.report.stripe_size
        return None

    def create_thin_volume(self, lv_name: str, *args: str, **options: str) -> LogicalVolume:
        """Create thin volume in this pool.

        Args:
            lv_name: Thin volume name
            *args: Additional arguments passed to lvcreate
            **options: All options passed as strings to lvcreate command

        Returns:
            LogicalVolume object for the created thin volume

        Raises:
            AssertionError: If volume creation fails

        Example:
            ```python
            pool = ThinPool(name='pool1', vg='vg0')
            thin_lv = pool.create_thin_volume('thin1', virtualsize='500M')
            ```
        """
        thin_lv = LogicalVolume(name=lv_name, pool_name=self.name, vg=self.vg)
        assert thin_lv.create(*args, **options), f'Failed to create thin volume {lv_name}'
        assert self.refresh_report()

        # Add to our thin volumes list
        self.thin_volumes.append(thin_lv)

        return thin_lv

    def get_thin_volume_count(self) -> int:
        """Get the number of thin volumes in this pool.

        Returns:
            Number of thin volumes in the pool
        """
        if self.report and self.report.thin_count:
            try:
                return int(self.report.thin_count)
            except ValueError:
                pass

        # Fallback to counting discovered volumes
        return len(self.thin_volumes)

    @classmethod
    def create_thin_pool(cls, pool_name: str, vg_name: str, *args: str, **options: str) -> ThinPool:
        """Create thin pool with specified options.

        Args:
            pool_name: Pool name
            vg_name: Volume group name
            *args: Additional arguments passed to lvcreate
            **options: All options passed as strings to lvcreate command

        Returns:
            ThinPool object for the created pool

        Raises:
            AssertionError: If pool creation fails

        Example:
            ```python
            pool = ThinPool.create_thin_pool('pool1', 'vg0', size='1G')
            ```
        """
        pool = cls(name=pool_name, vg=vg_name)
        assert pool.create(*args, **options), f'Failed to create thin pool {pool_name}'
        return pool

    def remove_thin_volumes(self, *, force: bool = True) -> bool:
        """Remove all thin volumes in this pool.

        This method discovers and removes all thin volumes that belong to this pool.
        It should be called before removing the pool itself.

        Args:
            force: If True, use force flags for removal (default: True)

        Returns:
            True if all thin volumes were removed successfully, False otherwise

        Example:
            ```python
            pool = ThinPool(name='pool1', vg='vg0')
            pool.remove_thin_volumes()  # Remove all thin volumes first
            pool.remove()  # Now remove the pool
            ```
        """
        # Discover thin volumes in this pool
        self.discover_thin_volumes()

        if not self.thin_volumes:
            logging.info(f'No thin volumes found in pool {self.name}')
            return True

        all_removed = True
        for thin_lv in self.thin_volumes:
            logging.info(f'Removing thin volume {thin_lv.name} from pool {self.name}')
            success = thin_lv.remove(force='', yes='') if force else thin_lv.remove()

            if not success:
                logging.warning(f'Failed to remove thin volume {thin_lv.name}')
                all_removed = False

        # Clear the thin volumes list after removal
        if all_removed:
            self.thin_volumes = []

        return all_removed

    def remove_with_thin_volumes(self, *args: str, **options: str) -> bool:
        """Remove thin pool along with all its thin volumes.

        This is a convenience method that handles the proper cleanup order:
        1. Remove all thin volumes in the pool
        2. Remove the pool itself

        Args:
            *args: Additional arguments passed to lvremove
            **options: All options passed as strings to lvremove command

        Returns:
            True if pool and all thin volumes were removed successfully

        Example:
            ```python
            pool = ThinPool(name='pool1', vg='vg0')
            pool.create(size='1G')
            pool.create_thin_volume('thin1', virtualsize='500M')
            pool.remove_with_thin_volumes(force='', yes='')  # Removes everything
            ```
        """
        # First remove all thin volumes
        if not self.remove_thin_volumes(force='force' in options or 'yes' in options):
            logging.error(f'Failed to remove thin volumes from pool {self.name}')
            return False

        # Then remove the pool
        return self.remove(*args, **options)

    def __str__(self) -> str:
        """String representation of ThinPool."""
        thin_count = self.get_thin_volume_count()
        return f"ThinPool(name='{self.name}', vg='{self.vg}', thin_volumes={thin_count})"
