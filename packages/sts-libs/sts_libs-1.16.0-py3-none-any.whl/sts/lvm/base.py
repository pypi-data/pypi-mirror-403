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

from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from sts.base import StorageDevice
from sts.utils.cmdline import run

if TYPE_CHECKING:
    from sts.utils.cmdline import CommandResult


@dataclass
class LvmDevice(StorageDevice):
    """Base class for LVM devices.

    Provides common functionality for all LVM device types:
    - Command execution with standard options
    - Configuration management
    - Basic device operations

    Args:
        name: Device name (optional)
        path: Device path (optional, defaults to /dev/<name>)
        size: Device size in bytes (optional, discovered from device)
        model: Device model (optional)
        yes: Automatically answer yes to prompts
        force: Force operations without confirmation

    The yes and force options are useful for automation:
    - yes: Skip interactive prompts
    - force: Ignore warnings and errors
    """

    # Optional parameters from parent classes
    name: str | None = None
    path: Path | str | None = None
    size: int | None = None
    model: str | None = None
    validate_on_init = False

    # Optional parameters for this class
    yes: bool = True  # Answer yes to prompts
    force: bool = False  # Force operations

    # Internal fields
    config_path: Path | str = Path('/etc/lvm/lvm.conf')

    def __post_init__(self) -> None:
        """Initialize LVM device."""
        # Set path based on name if not provided
        if not self.path and self.name:
            self.path = f'/dev/{self.name}'

        # Initialize parent class
        super().__post_init__()

    def _run(self, cmd: str, *args: str | Path | None, **kwargs: str) -> CommandResult:
        """Run LVM command.

        Builds and executes LVM commands with standard options:
        - Adds --yes for non-interactive mode
        - Adds --force to ignore warnings
        - Converts Python parameters to LVM options

        Args:
            cmd: Command name (e.g. 'pvcreate')
            *args: Command arguments
            **kwargs: Command parameters

        Returns:
            Command result
        """
        command = [cmd]
        if self.yes:
            command.append('--yes')
        if self.force:
            command.append('--force')
        if args:
            command.extend(str(arg) for arg in args if arg)
        if kwargs:
            command.extend(f'--{k.replace("_", "-")}={v}' for k, v in kwargs.items() if v)

        return run(' '.join(command))

    @abstractmethod
    def create(self, **options: str) -> bool:
        """Create LVM device.

        Args:
            **options: Device options (see LvmOptions)

        Returns:
            True if successful, False otherwise
        """

    @abstractmethod
    def remove(self, **options: str) -> bool:
        """Remove LVM device.

        Args:
            **options: Device options (see LvmOptions)

        Returns:
            True if successful, False otherwise
        """
