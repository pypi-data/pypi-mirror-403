# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for thin_check DMPD tool.

This module contains pytest tests for the thin_check command-line tool,
which is used to check thin provisioning metadata integrity.
"""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pytest

from sts import dmpd


@pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 4096}], indirect=True)
class TestThinCheck:
    """Test cases for thin_check command."""

    def test_thin_check_consolidated(self, setup_thin_metadata_for_dmpd: dict[str, str]) -> None:
        """Test various thin_check operations that can share the same metadata setup."""
        vol_info = setup_thin_metadata_for_dmpd
        metadata_dev = vol_info['metadata_dev']

        # Test basic thin_check without any extra parameters
        result_basic = dmpd.thin_check(metadata_dev)
        assert result_basic.succeeded
        logging.info(result_basic.stdout)
        assert 'TRANSACTION_ID=' in result_basic.stdout
        assert 'METADATA_FREE_BLOCKS=' in result_basic.stdout

        # Test thin_check with --super-block-only flag
        result_super_only = dmpd.thin_check(metadata_dev, super_block_only=True)
        assert result_super_only.succeeded
        assert 'TRANSACTION_ID=' in result_super_only.stdout
        assert 'METADATA_FREE_BLOCKS=' in result_super_only.stdout
        # Should not contain full check output when only checking superblock
        assert 'device details tree' not in result_super_only.stdout
        assert 'mapping tree' not in result_super_only.stdout

        # Test thin_check with --skip-mappings flag
        result_skip_mappings = dmpd.thin_check(metadata_dev, skip_mappings=True)
        assert result_skip_mappings.succeeded
        assert 'TRANSACTION_ID=' in result_skip_mappings.stdout
        assert 'METADATA_FREE_BLOCKS=' in result_skip_mappings.stdout

        # Test thin_check with --ignore-non-fatal-errors flag
        result_ignore_errors = dmpd.thin_check(metadata_dev, ignore_non_fatal_errors=True)
        assert result_ignore_errors.succeeded
        assert 'TRANSACTION_ID=' in result_ignore_errors.stdout
        assert 'METADATA_FREE_BLOCKS=' in result_ignore_errors.stdout

        # Test thin_check with --quiet flag
        result_quiet = dmpd.thin_check(metadata_dev, quiet=True)
        assert result_quiet.succeeded
        # Output should be minimal with quiet flag
        assert len(result_quiet.stdout.strip()) < 100  # Expect much less output

        # Test thin_check with --clear-needs-check-flag
        result_clear_flag = dmpd.thin_check(metadata_dev, clear_needs_check_flag=True)
        assert result_clear_flag.succeeded


@pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 4096}], indirect=True)
class TestThinCheckCorruptedMetadata:
    """Test cases for thin_check with btree structural inconsistencies.

    These tests focus on btree-level corruption that thin_restore accepts
    but thin_check should detect during structural validation.

    Note: These tests manipulate XML and use thin_restore to create binary
    metadata with structural issues that thin_check should catch.
    """

    def test_thin_check_invalid_mapped_blocks_count(
        self, setup_thin_metadata_for_dmpd: dict[str, Any], binary_metadata_file: Path
    ) -> None:
        """Test thin_check detects mismatch between mapped_blocks count and actual mappings.

        Btree structural issue: The device's mapped_blocks attribute doesn't match
        the actual number of blocks mapped in the device's btree. thin_check walks
        the btree and verifies this count matches reality.
        """
        vol_info = setup_thin_metadata_for_dmpd
        backup_file = Path(vol_info['metadata_backup_path'])

        # Create a copy of the metadata file for this test using Path
        xml_file = Path('/var/tmp/metadata_corrupt_mapped_count.xml')
        try:
            xml_file.write_text(backup_file.read_text())
            logging.info(f'Created corrupted metadata file: {xml_file}')
            logging.info(f'Source backup file: {backup_file}')

            # Parse and corrupt the XML
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Find a device and set incorrect mapped_blocks count
            device = root.find('device[@dev_id="1"]')
            assert device is not None, 'Device not found'
            current_count_str = device.get('mapped_blocks')
            assert current_count_str is not None, 'mapped_blocks not found'
            current_count = int(current_count_str)
            # Set it to a significantly wrong value
            device.set('mapped_blocks', str(current_count + 500))
            logging.info(f'Changed mapped_blocks from {current_count} to {current_count + 500}')

            tree.write(xml_file)
            logging.info(f'Corrupted metadata written to: {xml_file}')
            logging.info(f'Corrupted metadata content: {xml_file.read_text()}')

            # Use pre-allocated binary file from fixture
            binary_file = binary_metadata_file
            logging.info(f'Using pre-allocated binary file: {binary_file} (5MB)')

            # Convert corrupted XML to binary using thin_restore
            logging.info(f'Converting XML to binary with thin_restore: {xml_file} -> {binary_file}')
            restore_result = dmpd.thin_restore(input=str(xml_file), output=str(binary_file))
            logging.info(f'thin_restore stdout: {restore_result.stdout}')
            logging.info(f'thin_restore stderr: {restore_result.stderr}')
            assert restore_result.succeeded, 'thin_restore should succeed'

            # Run thin_check on the binary file
            logging.info(f'Running thin_check on binary file: {binary_file}')
            check_result = dmpd.thin_check(str(binary_file))
            logging.info(f'thin_check stdout: {check_result.stdout}')
            logging.info(f'thin_check stderr: {check_result.stderr}')
            assert not check_result.succeeded, 'thin_check should fail on incorrect mapped_blocks count'
            logging.info(f'thin_check correctly detected corruption, exit_status: {check_result.exit_status}')
        finally:
            xml_file.unlink(missing_ok=True)

    def test_thin_check_zero_length_range_mapping(
        self, setup_thin_metadata_for_dmpd: dict[str, Any], binary_metadata_file: Path
    ) -> None:
        """Test behavior with zero-length range mappings.

        Edge case: A range_mapping with length=0 is semantically invalid.
        Tests whether thin_check catches this.

        Real metadata has ranges like: origin_begin="0" length="2"
        We'll change one to length="0".
        """
        vol_info = setup_thin_metadata_for_dmpd
        backup_file = Path(vol_info['metadata_backup_path'])

        xml_file = Path('/var/tmp/metadata_zero_length.xml')
        xml_file.write_text(backup_file.read_text())
        logging.info(f'Created metadata file: {xml_file}')

        tree = ET.parse(xml_file)
        root = tree.getroot()

        device = root.find('device[@dev_id="1"]')
        assert device is not None, 'Device not found'
        range_mapping = device.find('.//range_mapping')
        assert range_mapping is not None, 'Range mapping not found'
        original_length = range_mapping.get('length')
        range_mapping.set('length', '0')
        logging.info(f'Changed range length from {original_length} to 0')

        tree.write(xml_file)
        binary_file = binary_metadata_file

        # Check if thin_restore rejects
        logging.info(f'Running thin_restore with zero-length range: {xml_file} -> {binary_file}')
        restore_result = dmpd.thin_restore(input=str(xml_file), output=str(binary_file))
        logging.info(f'thin_restore result: succeeded={restore_result.succeeded}')
        logging.info(f'thin_restore stderr: {restore_result.stderr}')

        # Run thin_check
        check_result = dmpd.thin_check(str(binary_file))
        logging.info(f'thin_check result: succeeded={check_result.succeeded}')

        assert not check_result.succeeded
