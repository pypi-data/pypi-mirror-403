# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Device Mapper flakey target.

The flakey target is similar to linear but exhibits unreliable behavior
periodically. It's useful for simulating failing devices for testing.

Starting from when the table is loaded, the device is available for
<up interval> seconds, then exhibits unreliable behavior for <down interval>
seconds, and then this cycle repeats.

Table format:
    <dev path> <offset> <up interval> <down interval> [<num_features> [<feature args>]]

Features:
    - drop_writes: Silently ignore all writes, reads work normally
    - error_writes: Fail all writes with error, reads work normally
    - corrupt_bio_byte <Nth_byte> <direction> <value> <flags>: Corrupt specific bytes
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sts.dm.base import DmDevice

if TYPE_CHECKING:
    from sts.blockdevice import BlockDevice


@dataclass
class FlakeyDevice(DmDevice):
    """Flakey target.

    Simulates an unreliable device that periodically fails or corrupts I/O.
    Useful for testing error handling and recovery.

    Args format: <device> <offset> <up_interval> <down_interval> [<num_features> [<features>]]

    Example:
        ```python
        # Device up for 60s, down for 10s, dropping writes when down
        target = FlakeyDevice(0, 1000000, '253:0 0 60 10 1 drop_writes')
        str(target)
        '0 1000000 flakey 253:0 0 60 10 1 drop_writes'
        ```
    """

    def __post_init__(self) -> None:
        """Set target type and initialize."""
        self.target_type = 'flakey'
        super().__post_init__()

    @classmethod
    def from_block_device(
        cls,
        device: BlockDevice,
        up_interval: int,
        down_interval: int,
        offset: int = 0,
        size_sectors: int | None = None,
        corrupt_bio_byte: tuple[int, str, int, int] | None = None,
        start: int = 0,
        *,
        drop_writes: bool = False,
        error_writes: bool = False,
    ) -> FlakeyDevice:
        """Create FlakeyDevice from BlockDevice.

        Args:
            device: Underlying block device
            up_interval: Seconds device is available (reliable)
            down_interval: Seconds device is unreliable
            offset: Starting sector in underlying device (default: 0)
            size_sectors: Size in sectors (default: full device)
            drop_writes: Silently drop writes when down (default: False)
            error_writes: Error writes when down (default: False)
            corrupt_bio_byte: Tuple of (nth_byte, direction, value, flags) for corruption
            start: Start sector in virtual device (default: 0)

        Returns:
            FlakeyDevice instance

        Example:
            ```python
            # Device available 60s, then drops writes for 10s
            device = BlockDevice('/dev/sdb')
            flakey = FlakeyDevice.from_block_device(device, up_interval=60, down_interval=10, drop_writes=True)
            ```
        """
        if size_sectors is None and device.size is not None:
            size_sectors = device.size // device.sector_size

        device_id = cls._get_device_identifier(device)

        # Build args: <device> <offset> <up_interval> <down_interval> [features]
        args_parts = [
            device_id,
            str(offset),
            str(up_interval),
            str(down_interval),
        ]

        # Build feature list
        features: list[str] = []
        if drop_writes:
            features.append('drop_writes')
        if error_writes:
            features.append('error_writes')
        if corrupt_bio_byte is not None:
            nth_byte, direction, value, flags = corrupt_bio_byte
            features.append(f'corrupt_bio_byte {nth_byte} {direction} {value} {flags}')

        # Add features if any
        if features:
            args_parts.append(str(len(features)))
            args_parts.extend(features)

        args = ' '.join(args_parts)
        if size_sectors is None:
            raise ValueError('size_sectors must be provided or device.size must be available')
        return cls(start=start, size_sectors=size_sectors, args=args)
