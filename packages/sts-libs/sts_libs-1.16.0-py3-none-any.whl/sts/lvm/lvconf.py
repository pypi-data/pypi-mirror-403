# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""LVM configuration management.

This module provides functionality for managing LVM configuration:
- Reading configuration values from lvm.conf
- Updating configuration values in lvm.conf
- Managing thin provisioning configuration

LVM configuration is stored in /etc/lvm/lvm.conf and controls various
aspects of LVM behavior including:
- Thin pool autoextend settings
- Metadata placement requirements
- Device filtering and caching

Note: LVM configuration files often have default values commented out
with '#'. This class handles both commented and uncommented values.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LvmConfig:
    """LVM configuration manager.

    Provides methods to read and update LVM configuration values
    in /etc/lvm/lvm.conf.

    Args:
        config_path: Path to lvm.conf (default: /etc/lvm/lvm.conf)

    Key configuration options for thin provisioning:
    - thin_pool_autoextend_threshold: When to trigger autoextend (default: 100)
    - thin_pool_autoextend_percent: How much to extend (default: 20)
    - thin_pool_metadata_require_separate_pvs: Require separate PV for metadata (default: 0)

    Note:
        LVM config files typically have default values commented out (e.g., `# key = value`).
        The `get` method reads both commented and uncommented values.
        The `set` method will uncomment a line when setting a value.

    Example:
        ```python
        # Create config manager
        config = LvmConfig()

        # Read a value (works for both commented and uncommented)
        threshold = config.get('thin_pool_autoextend_threshold')
        print(f'Autoextend threshold: {threshold}')

        # Update a value (uncomments if necessary)
        config.set('thin_pool_autoextend_threshold', '80')

        # Update multiple values
        config.set_multiple(
            {
                'thin_pool_autoextend_threshold': '80',
                'thin_pool_autoextend_percent': '50',
            }
        )
        ```
    """

    config_path: Path = field(default_factory=lambda: Path('/etc/lvm/lvm.conf'))

    # Common thin provisioning configuration keys
    THIN_POOL_AUTOEXTEND_THRESHOLD: str = 'thin_pool_autoextend_threshold'
    THIN_POOL_AUTOEXTEND_PERCENT: str = 'thin_pool_autoextend_percent'
    THIN_POOL_METADATA_REQUIRE_SEPARATE_PVS: str = 'thin_pool_metadata_require_separate_pvs'

    def exists(self) -> bool:
        """Check if the configuration file exists.

        Returns:
            True if the configuration file exists, False otherwise
        """
        return self.config_path.exists()

    def get(self, key: str) -> str | None:
        """Get configuration value from lvm.conf.

        Searches for the specified key in lvm.conf and returns its value.
        Handles both commented (default) and uncommented (active) values.
        If both exist, returns the uncommented (active) value.

        Args:
            key: Configuration key to look up

        Returns:
            Configuration value if found, None otherwise

        Example:
            ```python
            config = LvmConfig()
            threshold = config.get('thin_pool_autoextend_threshold')
            # Returns '100' (default value, even if commented)
            ```
        """
        if not self.exists():
            logging.warning(f'LVM config file {self.config_path} not found')
            return None

        # Pattern to match both commented and uncommented key = value
        # Captures: (optional #) (whitespace) key (whitespace) = (whitespace) value
        # The value pattern handles the last occurrence of "key = value" format
        search_regex = re.compile(rf'^\s*#?\s*{re.escape(key)}\s*=\s*(\S+)')

        uncommented_value = None
        commented_value = None

        try:
            for line in self.config_path.read_text().splitlines():
                match = search_regex.match(line)
                if match:
                    value = match.group(1)
                    # Check if this is a commented line
                    if line.strip().startswith('#'):
                        commented_value = value
                    else:
                        uncommented_value = value
        except OSError:
            logging.exception(f'Failed to read LVM config file {self.config_path}')
            return None

        # Prefer uncommented (active) value over commented (default) value
        return uncommented_value if uncommented_value is not None else commented_value

    def set(self, key: str, value: str) -> bool:
        """Update a configuration value in lvm.conf.

        Searches for the specified key in lvm.conf and updates its value.
        If the key is commented out, it will be uncommented.
        Preserves the original indentation.

        Args:
            key: Configuration key to update
            value: New value to set

        Returns:
            True if successful, False otherwise

        Example:
            ```python
            config = LvmConfig()
            config.set('thin_pool_autoextend_threshold', '80')
            ```
        """
        if not self.exists():
            logging.error(f'LVM config file {self.config_path} not found')
            return False

        # Pattern to match both commented and uncommented key = value
        # Captures leading whitespace and optional comment marker
        search_regex = re.compile(rf'^(\s*)(#?\s*){re.escape(key)}(\s*)=(\s*)\S*')

        try:
            lines = self.config_path.read_text().splitlines()
            updated_lines = []
            found = False

            for line in lines:
                match = search_regex.match(line)
                if match and not found:
                    # Get the leading whitespace (indentation)
                    indent = match.group(1)
                    # Create new line without comment marker
                    updated_lines.append(f'{indent}{key} = {value}')
                    found = True
                else:
                    updated_lines.append(line)

            if not found:
                logging.warning(f'Configuration key {key} not found in {self.config_path}')
                return False

            self.config_path.write_text('\n'.join(updated_lines) + '\n')

        except OSError:
            logging.exception(f'Failed to update LVM config file {self.config_path}')
            return False

        return True

    def set_multiple(self, settings: dict[str, str]) -> bool:
        """Update multiple configuration values in lvm.conf.

        Updates all specified key-value pairs in a single operation.
        More efficient than calling set() multiple times.
        If keys are commented out, they will be uncommented.

        Args:
            settings: Dictionary of key-value pairs to update

        Returns:
            True if all updates were successful, False otherwise

        Example:
            ```python
            config = LvmConfig()
            config.set_multiple(
                {
                    'thin_pool_autoextend_threshold': '80',
                    'thin_pool_autoextend_percent': '50',
                }
            )
            ```
        """
        if not self.exists():
            logging.error(f'LVM config file {self.config_path} not found')
            return False

        try:
            lines = self.config_path.read_text().splitlines()
            updated_lines = []
            keys_found: set[str] = set()

            for line in lines:
                updated_line = line
                for key, value in settings.items():
                    if key in keys_found:
                        continue
                    # Pattern to match both commented and uncommented key = value
                    search_regex = re.compile(rf'^(\s*)(#?\s*){re.escape(key)}(\s*)=(\s*)\S*')
                    match = search_regex.match(line)
                    if match:
                        # Get the leading whitespace (indentation)
                        indent = match.group(1)
                        # Create new line without comment marker
                        updated_line = f'{indent}{key} = {value}'
                        keys_found.add(key)
                        break
                updated_lines.append(updated_line)

            # Check if all keys were found
            missing_keys = set(settings.keys()) - keys_found
            if missing_keys:
                logging.warning(f'Configuration keys not found: {missing_keys}')
                return False

            self.config_path.write_text('\n'.join(updated_lines) + '\n')

        except OSError:
            logging.exception(f'Failed to update LVM config file {self.config_path}')
            return False

        return True

    def get_thin_pool_autoextend_threshold(self) -> str | None:
        """Get thin pool autoextend threshold.

        Returns:
            Threshold value as string, or None if not found
        """
        return self.get(self.THIN_POOL_AUTOEXTEND_THRESHOLD)

    def set_thin_pool_autoextend_threshold(self, value: str) -> bool:
        """Set thin pool autoextend threshold.

        Args:
            value: Threshold value (0-100)

        Returns:
            True if successful, False otherwise
        """
        return self.set(self.THIN_POOL_AUTOEXTEND_THRESHOLD, value)

    def get_thin_pool_autoextend_percent(self) -> str | None:
        """Get thin pool autoextend percent.

        Returns:
            Percent value as string, or None if not found
        """
        return self.get(self.THIN_POOL_AUTOEXTEND_PERCENT)

    def set_thin_pool_autoextend_percent(self, value: str) -> bool:
        """Set thin pool autoextend percent.

        Args:
            value: Percent value

        Returns:
            True if successful, False otherwise
        """
        return self.set(self.THIN_POOL_AUTOEXTEND_PERCENT, value)

    def get_thin_pool_metadata_require_separate_pvs(self) -> str | None:
        """Get thin pool metadata require separate PVs setting.

        Returns:
            Setting value ('0' or '1'), or None if not found
        """
        return self.get(self.THIN_POOL_METADATA_REQUIRE_SEPARATE_PVS)

    def set_thin_pool_metadata_require_separate_pvs(self, value: str) -> bool:
        """Set thin pool metadata require separate PVs setting.

        Args:
            value: Setting value ('0' or '1')

        Returns:
            True if successful, False otherwise
        """
        return self.set(self.THIN_POOL_METADATA_REQUIRE_SEPARATE_PVS, value)
