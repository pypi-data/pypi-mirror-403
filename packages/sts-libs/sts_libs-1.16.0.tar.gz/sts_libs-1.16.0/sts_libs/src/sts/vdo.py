# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""VDO device management.

This module provides functionality for managing VDO devices:
- VDO volume creation/removal
- Deduplication and compression
- Device statistics

VDO (Virtual Data Optimizer) is a kernel module that provides inline
data reduction through:
- Deduplication: Eliminates duplicate blocks
- Compression: Reduces block size using LZ4 algorithm
- Thin provisioning: Allocates space on demand
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import ClassVar, Literal, TypedDict

from sts.lvm import LogicalVolume
from sts.utils.cmdline import CommandResult, run

# Constants
DEFAULT_SLAB_SIZE = '2G'  # Default allocation unit size
MIN_SLAB_SIZE_MB = 128  # Minimum slab size (128 MB)
MAX_SLABS = 8192  # Maximum number of slabs per volume
DEFAULT_SLAB_SIZE_MB = 2048  # Default slab size in MB (2 GB)

# Size multipliers for parsing device sizes
SIZE_MULTIPLIERS = ['M', 'G', 'T', 'P', 'E']  # Mega, Giga, Tera, Peta, Exa

# Write policy options:
# - sync: Acknowledge writes after writing to physical storage
# - async: Acknowledge writes after writing to memory
WritePolicy = Literal['sync', 'async']


class VdoState(str, Enum):
    """VDO feature state.

    Used to enable/disable features like compression and deduplication.
    """

    ENABLED = 'y'
    DISABLED = 'n'


class VdoOptions(TypedDict, total=False):
    """VDO volume options.

    Common options:
    - size: Volume size (e.g. '1G', '500M')
    - extents: Volume size in LVM extents
    - type: Volume type (must be 'vdo')
    - compression: Enable compression (y/n)
    - deduplication: Enable deduplication (y/n)
    - vdowritepolicy: Write policy (sync/async)
    - vdoslabsize: Slab size - allocation unit (e.g. '2G', '512M')

    The slab size affects memory usage and performance:
    - Larger slabs = Better performance but more memory
    - Smaller slabs = Less memory but lower performance
    """

    size: str
    extents: str
    type: str
    compression: VdoState
    deduplication: VdoState
    vdowritepolicy: WritePolicy
    vdoslabsize: str


@dataclass
class VdoFormat:
    """VDO format utility.

    This class encapsulates the vdoformat command for formatting
    block devices as VDO volumes. It handles:
    - Low-level VDO device formatting
    - Logical size configuration
    - Slab size configuration via slab bits
    - UDS index memory allocation
    - Sparse index configuration

    Args:
        device: Block device path to format
        logical_size: Logical (provisioned) size (e.g. '1G', '500M')
        slab_bits: Slab size as power of 2 (13-23, default 19 = 2GB)
        uds_memory_size: Memory for deduplication index in GB
        uds_sparse: Use sparse index for deduplication
        force: Format even if VDO already exists
        verbose: Show detailed formatting information

    Note:
        The slab_bits parameter controls the slab size:
        - 13 = 32 MB (minimum)
        - 19 = 2 GB (default)
        - 23 = 32 GB (maximum)

        Maximum 8192 slabs per volume, so slab size determines
        the maximum physical volume size.

    Example:
        ```python
        fmt = VdoFormat('/dev/sda1', logical_size='10G')
        fmt.format()
        True
        ```
    """

    # Valid slab bits range (13-23 inclusive)
    MIN_SLAB_BITS: ClassVar[int] = 13  # 32 MB slab size
    MAX_SLAB_BITS: ClassVar[int] = 23  # 32 GB slab size
    DEFAULT_SLAB_BITS: ClassVar[int] = 19  # 2 GB slab size (default)

    # Valid UDS memory sizes in gigabytes
    VALID_UDS_MEMORY_SIZES: ClassVar[tuple[float, ...]] = (0.25, 0.5, 0.75)

    device: str | Path
    logical_size: str | None = None
    slab_bits: int | None = None
    uds_memory_size: float | None = None
    uds_sparse: bool = False
    force: bool = False
    verbose: bool = False

    def __post_init__(self) -> None:
        """Convert device to Path after initialization."""
        self.device = Path(self.device)

    def _build_command(self) -> list[str]:
        """Build vdoformat command with options.

        Returns:
            List of command arguments
        """
        cmd = ['vdoformat']

        if self.force:
            cmd.append('--force')

        if self.logical_size:
            cmd.append(f'--logical-size={self.logical_size}')

        if self.slab_bits is not None:
            cmd.append(f'--slab-bits={self.slab_bits}')

        if self.uds_memory_size is not None:
            cmd.append(f'--uds-memory-size={self.uds_memory_size}')

        if self.uds_sparse:
            cmd.append('--uds-sparse')

        if self.verbose:
            cmd.append('--verbose')

        cmd.append(str(self.device))
        return cmd

    def format(self) -> bool:
        """Format device as VDO volume.

        Performs low-level VDO formatting on the device.
        The device will not be formatted if it already contains
        a VDO, unless force=True was set.

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            fmt = VdoFormat('/dev/sda1', logical_size='10G')
            fmt.format()
            True

            # Force reformat existing VDO
            fmt = VdoFormat('/dev/sda1', force=True)
            fmt.format()
            True
            ```
        """
        cmd = self._build_command()
        result = run(' '.join(cmd))

        if result.failed:
            logging.error(f'Failed to format VDO device: {result.stderr}')
            return False

        logging.info(f'Successfully formatted {self.device} as VDO')
        return True

    @staticmethod
    def get_version() -> str | None:
        """Get vdoformat version.

        Returns:
            Version string or None if command failed

        Example:
            ```python
            VdoFormat.get_version()
            '8.2.0.2'
            ```
        """
        result = run('vdoformat --version')
        if result.failed:
            logging.error(f'Failed to get vdoformat version: {result.stderr}')
            return None
        return result.stdout.strip()

    @property
    def slab_size_mb(self) -> int:
        """Get slab size in megabytes.

        Calculates the actual slab size based on slab_bits:
        slab_size = 2^slab_bits * 4KB

        Returns:
            Slab size in megabytes

        Example:
            ```python
            fmt = VdoFormat('/dev/sda1', slab_bits=19)
            fmt.slab_size_mb
            2048
            ```
        """
        bits = self.slab_bits if self.slab_bits is not None else self.DEFAULT_SLAB_BITS
        # Each slab is 2^bits blocks of 4KB
        return (2**bits * 4) // 1024


@dataclass
class VdoCalculateSize:
    """VDO space and memory usage calculator.

    This class encapsulates the vdocalculatesize command for calculating
    VDO space and memory requirements. It helps determine:
    - Physical storage requirements
    - Memory usage for deduplication index
    - Block map cache sizing

    Args:
        logical_size: VDO logical size in MB (e.g. '2048' for 2GB)
        physical_size: VDO physical size in MB (e.g. '600' for 600MB)
        slab_bits: Slab size as power of 2 (13-23, default 19 = 2GB)
        slab_size: Slab size in MB (mutually exclusive with slab_bits)
        block_map_cache_size: Block map cache size in 4K blocks
        index_memory_size: Memory for deduplication index in GB
        sparse_index: Use sparse index for deduplication

    Note:
        The slab_bits and slab_size parameters are mutually exclusive.
        Use slab_bits for power-of-2 sizes, or slab_size for direct MB values.

    Example:
        ```python
        calc = VdoCalculateSize(physical_size='600G', logical_size='2T', slab_bits=22, index_memory_size=1)
        result = calc.calculate()
        ```
    """

    # Valid slab bits range (13-23 inclusive)
    MIN_SLAB_BITS: ClassVar[int] = 13  # 32 MB slab size
    MAX_SLAB_BITS: ClassVar[int] = 23  # 32 GB slab size
    DEFAULT_SLAB_BITS: ClassVar[int] = 19  # 2 GB slab size (default)

    # Valid index memory sizes in gigabytes
    VALID_INDEX_MEMORY_SIZES: ClassVar[tuple[float, ...]] = (0.25, 0.5, 0.75)

    logical_size: str | None = None
    physical_size: str | None = None
    slab_bits: int | None = None
    slab_size: str | None = None
    block_map_cache_size: int | None = None
    index_memory_size: float | None = None
    sparse_index: bool = False

    def _build_command(self) -> list[str]:
        """Build vdocalculatesize command with options.

        Returns:
            List of command arguments
        """
        cmd = ['vdocalculatesize']

        if self.logical_size:
            cmd.append(f'--logical-size={self.logical_size}')

        if self.physical_size:
            cmd.append(f'--physical-size={self.physical_size}')

        if self.slab_bits is not None:
            cmd.append(f'--slab-bits={self.slab_bits}')

        if self.slab_size:
            cmd.append(f'--slab-size={self.slab_size}')

        if self.block_map_cache_size is not None:
            cmd.append(f'--block-map-cache-size={self.block_map_cache_size}')

        if self.index_memory_size is not None:
            cmd.append(f'--index-memory-size={self.index_memory_size}')

        if self.sparse_index:
            cmd.append('--sparse-index')

        return cmd

    def calculate(self) -> CommandResult:
        """Calculate VDO space and memory usage.

        Runs vdocalculatesize with the configured options and returns
        the command result.

        Returns:
            CommandResult with rc, stdout, and stderr

        Example:
            ```python
            calc = VdoCalculateSize(
                physical_size='600G', logical_size='2T', slab_bits=22, index_memory_size=1, block_map_cache_size=32768
            )
            result = calc.calculate()
            if result.succeeded:
                print(result.stdout)
            ```
        """
        cmd = self._build_command()
        return run(' '.join(cmd))


def get_minimum_slab_size(device: str | Path, *, use_default: bool = True) -> str:
    """Get minimum slab size for device.

    Calculates the minimum slab size based on device size:
    1. Get device size
    2. Calculate minimum size that allows MAX_SLABS
    3. Ensure size is at least MIN_SLAB_SIZE_MB
    4. Optionally use default if calculated size is smaller

    Args:
        device: Device path
        use_default: Return default size if calculated size is smaller

    Returns:
        Slab size string (e.g. '2G')

    Example:
        ```python
        get_minimum_slab_size('/dev/sda')
        '2G'
        get_minimum_slab_size('/dev/sdb', use_default=False)
        '512M'
        ```
    """
    device = Path(device)

    # Get device name - handle MD devices specially
    if str(device).startswith('/dev/md'):
        # For MD (RAID) devices, resolve the actual device name
        result = run(f'ls -al /dev/md | grep {device.name}')
        if result.failed:
            logging.warning(f'Device {device.name} not found in /dev/md')
            return DEFAULT_SLAB_SIZE
        device = Path(result.stdout.split('../')[-1])

    # Get device size from lsblk output
    result = run(f"lsblk | grep '{device.name} '")
    if result.failed:
        logging.warning(f'Device {device.name} not found using lsblk')
        return DEFAULT_SLAB_SIZE

    # Parse size (e.g. '1G', '2T') and convert to MB
    size = result.stdout.split()[3]
    multiplier = SIZE_MULTIPLIERS.index(size[-1:])
    device_size = int(float(size[:-1]) * (1024**multiplier))

    # Calculate minimum size:
    # 1. Divide device size by MAX_SLABS
    # 2. Round up to next power of 2
    # 3. Ensure at least MIN_SLAB_SIZE_MB
    minimum_size = 2 ** int(device_size / MAX_SLABS).bit_length()
    minimum_size = max(minimum_size, MIN_SLAB_SIZE_MB)

    # Use default size if calculated size is smaller
    if use_default and minimum_size < DEFAULT_SLAB_SIZE_MB:
        return DEFAULT_SLAB_SIZE
    return f'{minimum_size}M'


@dataclass
class VdoDevice(LogicalVolume):
    """VDO device.

    This class extends LogicalVolume to provide VDO-specific functionality:
    - Inline deduplication
    - Inline compression
    - Configurable write policy
    - Statistics reporting

    Args:
        name: Device name
        path: Device path
        size: Device size in bytes
        model: Device model (optional)
        yes: Automatically answer yes to prompts
        force: Force operations without confirmation
        vg: Volume group name
        deduplication: Enable deduplication
        compression: Enable compression
        write_policy: Write policy (sync/async)
        slab_size: Slab size (e.g. '2G', '512M')

    Example:
        ```python
        device = VdoDevice.create('vdo0', vg='vg0', size='1G')
        device.exists
        True
        ```
    """

    # VDO-specific options
    deduplication: bool = True
    compression: bool = True
    write_policy: WritePolicy = 'sync'
    slab_size: str | None = None

    # Class-level paths
    CONFIG_PATH: ClassVar[Path] = Path('/etc/vdoconf.yml')

    def create(self, *args: str, **options: str) -> bool:
        """Create VDO volume.

        Creates a new VDO volume with specified options:
        - Compression and deduplication state
        - Write policy (sync/async)
        - Slab size for memory allocation

        Args:
            **options: VDO parameters (see VdoOptions)

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            device = VdoDevice('vdo0', vg='vg0')
            device.create(size='1G')
            True
            ```
        """
        if not self.vg:
            logging.error('Volume group required')
            return False

        # Build VDO-specific options
        vdo_opts = [
            '--type',
            'vdo',
            '--compression',
            VdoState.ENABLED if self.compression else VdoState.DISABLED,
            '--deduplication',
            VdoState.ENABLED if self.deduplication else VdoState.DISABLED,
            '--vdowritepolicy',
            self.write_policy,
        ]
        if self.slab_size:
            vdo_opts.extend(['--vdoslabsize', self.slab_size])

        # Create VDO volume using LVM
        result = self._run('lvcreate', '-n', self.name, self.vg, *args, *vdo_opts, **options)
        return result.succeeded

    def remove(self, *args: str, **options: str) -> bool:
        """Remove VDO volume.

        Removes the VDO volume and its metadata.
        All data will be lost.

        Args:
            **options: VDO parameters (see VdoOptions)

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            device = VdoDevice('vdo0', vg='vg0')
            device.remove()
            True
            ```
        """
        if not self.vg:
            logging.error('Volume group required')
            return False

        result = self._run('lvremove', f'{self.vg}/{self.name}', *args, **options)
        return result.succeeded

    def get_stats(self, *, human_readable: bool = True) -> dict[str, str] | None:
        """Get VDO statistics.

        Retrieves statistics about:
        - Space usage (physical vs logical)
        - Deduplication ratio
        - Compression ratio
        - Block allocation

        Args:
            human_readable: Use human readable sizes (e.g. '1.0G' vs bytes)

        Returns:
            Dictionary of statistics or None if error

        Example:
            ```python
            device = VdoDevice('vdo0', vg='vg0')
            stats = device.get_stats()
            stats['physical_blocks']  # Actually used space
            '1.0G'
            stats['data_blocks']  # Space before optimization
            '500M'
            ```
        """
        cmd = ['vdostats']
        if human_readable:
            cmd.append('--human-readable')
        cmd.append(str(self.path))

        result = run(' '.join(cmd))
        if result.failed:
            logging.error(f'Failed to get VDO stats: {result.stderr}')
            return None

        # Parse statistics output
        stats: dict[str, str] = {}
        for line in result.stdout.splitlines():
            if ':' not in line:
                continue
            key, value = line.split(':', 1)
            stats[key.strip().lower().replace(' ', '_')] = value.strip()

        return stats

    def set_deduplication(self, *, enabled: bool = True) -> bool:
        """Set deduplication state.

        Enables or disables inline deduplication:
        - When enabled, duplicate blocks are detected and eliminated
        - When disabled, all blocks are stored as-is

        Args:
            enabled: Enable or disable deduplication

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            device = VdoDevice('vdo0', vg='vg0')
            device.set_deduplication(enabled=False)
            True
            ```
        """
        cmd = 'enableDeduplication' if enabled else 'disableDeduplication'
        result = run(f'vdo {cmd} --name={self.name}')
        if result.failed:
            logging.error(f'Failed to set deduplication: {result.stderr}')
            return False

        self.deduplication = enabled
        return True

    def set_compression(self, *, enabled: bool = True) -> bool:
        """Set compression state.

        Enables or disables inline compression:
        - When enabled, blocks are compressed using LZ4
        - When disabled, blocks are stored uncompressed

        Args:
            enabled: Enable or disable compression

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            device = VdoDevice('vdo0', vg='vg0')
            device.set_compression(enabled=False)
            True
            ```
        """
        cmd = 'enableCompression' if enabled else 'disableCompression'
        result = run(f'vdo {cmd} --name={self.name}')
        if result.failed:
            logging.error(f'Failed to set compression: {result.stderr}')
            return False

        self.compression = enabled
        return True

    def set_write_policy(self, policy: WritePolicy) -> bool:
        """Set write policy.

        Changes how writes are acknowledged:
        - sync: Wait for physical write (safer but slower)
        - async: Acknowledge after memory write (faster but risk data loss)

        Args:
            policy: Write policy (sync/async)

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            device = VdoDevice('vdo0', vg='vg0')
            device.set_write_policy('async')
            True
            ```
        """
        result = run(f'vdo changeWritePolicy --name={self.name} --writePolicy={policy}')
        if result.failed:
            logging.error(f'Failed to set write policy: {result.stderr}')
            return False

        self.write_policy = policy
        return True
