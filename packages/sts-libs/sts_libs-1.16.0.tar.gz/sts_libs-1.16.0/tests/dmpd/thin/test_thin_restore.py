# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for thin_restore DMPD tool.

This module contains pytest tests for the thin_restore
command-line tool.
"""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pytest

from sts import dmpd


@pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 4096}], indirect=True)
class TestThinRestore:
    """Test cases for thin_restore command."""

    def test_thin_restore(self, setup_thin_metadata_for_dmpd: dict[str, Any]) -> None:
        """Test various thin_restore operations that can share the same metadata setup."""
        vol_info = setup_thin_metadata_for_dmpd
        metadata_dev = vol_info['metadata_dev']
        backup_file = Path(vol_info['metadata_backup_path'])
        restore_file = Path(vol_info['metadata_repair_path'])

        # Test basic thin_restore from backup file
        result_basic = dmpd.thin_restore(input=str(backup_file), output=metadata_dev)
        assert result_basic.succeeded

        # Test thin_restore with quiet flag
        result_quiet = dmpd.thin_restore(input=str(backup_file), output=metadata_dev, quiet=True)
        assert result_quiet.succeeded
        # Should have minimal output with quiet flag
        assert len(result_quiet.stdout.strip()) < 50

        # Test thin_restore to file instead of device
        result_to_file = dmpd.thin_restore(input=str(backup_file), output=str(restore_file))
        assert result_to_file.succeeded
        assert restore_file.exists()
        assert restore_file.stat().st_size > 0


@pytest.mark.parametrize('loop_devices', [{'count': 1, 'size_mb': 4096}], indirect=True)
class TestThinRestoreValidation:
    """Test cases for thin_restore validation and error handling.

    These tests verify that thin_restore properly validates XML metadata
    and rejects invalid inputs.
    """

    def test_thin_restore_rejects_invalid_superblock(
        self, setup_thin_metadata_for_dmpd: dict[str, Any], binary_metadata_file: Path
    ) -> None:
        """Test that thin_restore rejects XML with invalid superblock values.

        Verifies that thin_restore validates superblock attributes like
        data_block_size and rejects invalid values (e.g., 0, negative).
        """
        vol_info = setup_thin_metadata_for_dmpd
        backup_file = Path(vol_info['metadata_backup_path'])

        # Create XML with invalid superblock
        xml_file = Path('/var/tmp/metadata_invalid_superblock.xml')
        try:
            xml_file.write_text(backup_file.read_text())
            logging.info(f'Created metadata file: {xml_file}')

            # Parse and corrupt the superblock
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Set data_block_size to invalid value
            original_block_size = root.get('data_block_size')
            root.set('data_block_size', '0')  # Invalid block size
            logging.info(f'Changed data_block_size from {original_block_size} to 0')

            tree.write(xml_file)

            # Use pre-allocated binary file from fixture
            binary_file = binary_metadata_file
            logging.info(f'Using pre-allocated binary file: {binary_file} (5MB)')

            # thin_restore should reject this
            logging.info(f'Running thin_restore with invalid superblock: {xml_file} -> {binary_file}')
            restore_result = dmpd.thin_restore(input=str(xml_file), output=str(binary_file))
            logging.info(f'thin_restore stdout: {restore_result.stdout}')
            logging.info(f'thin_restore stderr: {restore_result.stderr}')
            assert not restore_result.succeeded, 'thin_restore should reject invalid data_block_size'
            logging.info(
                f'thin_restore correctly rejected invalid superblock, exit_status: {restore_result.exit_status}'
            )
        finally:
            xml_file.unlink(missing_ok=True)

    def test_thin_restore_accepts_cross_device_sharing(
        self, setup_thin_metadata_for_dmpd: dict[str, Any], binary_metadata_file: Path
    ) -> None:
        """Test that thin_restore accepts valid cross-device data block sharing.

        Verifies that thin_restore correctly allows data blocks to be shared
        across different devices, which is normal behavior for snapshots.
        """
        vol_info = setup_thin_metadata_for_dmpd
        backup_file = Path(vol_info['metadata_backup_path'])

        # Create XML with cross-device sharing
        xml_file = Path('/var/tmp/metadata_cross_device_sharing.xml')
        xml_file.write_text(backup_file.read_text())
        logging.info(f'Created metadata file: {xml_file}')

        # Parse and modify the XML
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Make two devices share a data block (valid for snapshots)
        device1 = root.find('device[@dev_id="1"]')
        device2 = root.find('device[@dev_id="2"]')

        if device1 is not None and device2 is not None:
            mapping1 = device1.find('.//single_mapping')
            mapping2 = device2.find('.//single_mapping')

            if mapping1 is not None and mapping2 is not None:
                shared_block = mapping1.get('data_block')
                if shared_block is not None:
                    mapping2.set('data_block', shared_block)
                    logging.info(f'Made devices share data_block={shared_block}')

        tree.write(xml_file)

        # Use pre-allocated binary file from fixture
        binary_file = binary_metadata_file
        logging.info(f'Using pre-allocated binary file: {binary_file} (5MB)')

        # thin_restore should accept this as valid
        logging.info(f'Running thin_restore with cross-device sharing: {xml_file} -> {binary_file}')
        restore_result = dmpd.thin_restore(input=str(xml_file), output=str(binary_file))
        logging.info(f'thin_restore stdout: {restore_result.stdout}')
        logging.info(f'thin_restore stderr: {restore_result.stderr}')
        assert restore_result.succeeded, 'thin_restore should accept valid cross-device sharing'
        logging.info('thin_restore correctly accepted cross-device sharing (valid for snapshots)')

    def test_thin_restore_rejects_data_block_out_of_range(
        self, setup_thin_metadata_for_dmpd: dict[str, Any], binary_metadata_file: Path
    ) -> None:
        """Test that thin_restore rejects data blocks outside valid range.

        Verifies that thin_restore validates data block references and rejects
        mappings that reference data blocks beyond nr_data_blocks.
        """
        vol_info = setup_thin_metadata_for_dmpd
        backup_file = Path(vol_info['metadata_backup_path'])

        # Create XML with out-of-range data block
        xml_file = Path('/var/tmp/metadata_out_of_range.xml')
        xml_file.write_text(backup_file.read_text())
        logging.info(f'Created metadata file: {xml_file}')

        # Parse and corrupt the XML
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Get the total number of data blocks from superblock
        superblock = root
        nr_data_blocks_str = superblock.get('nr_data_blocks')
        if nr_data_blocks_str is not None:
            nr_data_blocks = int(nr_data_blocks_str)

            # Find a mapping and set its data block beyond the limit
            device = root.find('device[@dev_id="1"]')
            if device is not None:
                mapping = device.find('.//single_mapping')
                if mapping is not None:
                    invalid_block = nr_data_blocks + 1000
                    mapping.set('data_block', str(invalid_block))
                    logging.info(f'Set data_block to {invalid_block} (max={nr_data_blocks})')

        tree.write(xml_file)

        # Use pre-allocated binary file from fixture
        binary_file = binary_metadata_file
        logging.info(f'Using pre-allocated binary file: {binary_file} (5MB)')

        # thin_restore should reject this
        logging.info(f'Running thin_restore with out-of-range data block: {xml_file} -> {binary_file}')
        restore_result = dmpd.thin_restore(input=str(xml_file), output=str(binary_file))
        logging.info(f'thin_restore stdout: {restore_result.stdout}')
        logging.info(f'thin_restore stderr: {restore_result.stderr}')
        assert not restore_result.succeeded, 'thin_restore should reject out-of-range data blocks'
        assert 'block out of bounds' in restore_result.stderr or 'out of bounds' in restore_result.stderr
        logging.info(
            f'thin_restore correctly rejected out-of-range data block, exit_status: {restore_result.exit_status}'
        )

    def test_thin_restore_accepts_duplicate_data_blocks_in_device(
        self, setup_thin_metadata_for_dmpd: dict[str, Any], binary_metadata_file: Path
    ) -> None:
        """Test that thin_restore accepts duplicate data block mappings within a device.

        Verifies that thin_restore allows multiple origin blocks within the same
        device to map to the same data block. This is valid behavior in thin
        provisioning (e.g., for deduplication or sharing of identical data).

        Note: This test documents that duplicate mappings within a device are
        actually valid, contrary to initial assumptions.
        """
        vol_info = setup_thin_metadata_for_dmpd
        backup_file = Path(vol_info['metadata_backup_path'])

        # Create XML with duplicate data blocks
        xml_file = Path('/var/tmp/metadata_duplicate_blocks.xml')
        xml_file.write_text(backup_file.read_text())
        logging.info(f'Created metadata file: {xml_file}')

        # Parse and modify the XML - create duplicate data block mapping
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Find the first device and duplicate a data block
        device = root.find('device[@dev_id="1"]')
        if device is not None:
            # Find a single_mapping and duplicate its data_block in another mapping
            mappings = device.findall('.//single_mapping')
            if len(mappings) >= 2:
                # Make the second mapping use the same data_block as the first
                first_data_block = mappings[0].get('data_block')
                if first_data_block is not None:
                    mappings[1].set('data_block', first_data_block)
                    logging.info(f'Created duplicate data_block={first_data_block}')

        tree.write(xml_file)

        # Use pre-allocated binary file from fixture
        binary_file = binary_metadata_file
        logging.info(f'Using pre-allocated binary file: {binary_file} (5MB)')

        # thin_restore should accept this as valid
        logging.info(f'Running thin_restore with duplicate data blocks: {xml_file} -> {binary_file}')
        restore_result = dmpd.thin_restore(input=str(xml_file), output=str(binary_file))
        logging.info(f'thin_restore stdout: {restore_result.stdout}')
        logging.info(f'thin_restore stderr: {restore_result.stderr}')
        assert restore_result.succeeded, 'thin_restore should accept duplicate data blocks within device'
        logging.info('thin_restore correctly accepted duplicate data blocks (valid for deduplication)')

        # Also verify thin_check accepts it
        logging.info(f'Running thin_check to verify metadata is valid: {binary_file}')
        check_result = dmpd.thin_check(str(binary_file))
        logging.info(f'thin_check stdout: {check_result.stdout}')
        logging.info(f'thin_check stderr: {check_result.stderr}')
        assert check_result.succeeded, 'thin_check should also accept duplicate data blocks'
        logging.info('thin_check confirmed metadata is valid')

    def test_thin_restore_rejects_overlapping_range_mappings(
        self, setup_thin_metadata_for_dmpd: dict[str, Any], binary_metadata_file: Path
    ) -> None:
        """Test that thin_restore rejects overlapping range mappings.

        Verifies that thin_restore validates that range mappings don't overlap
        within the same device. Overlapping ranges would violate the invariant
        that each origin LBA should be mapped at most once.

        Note: If metadata doesn't contain range_mappings, test will be skipped.
        """
        vol_info = setup_thin_metadata_for_dmpd
        backup_file = Path(vol_info['metadata_backup_path'])

        # Create XML with overlapping ranges
        xml_file = Path('/var/tmp/metadata_overlapping_ranges.xml')
        xml_file.write_text(backup_file.read_text())
        logging.info(f'Created metadata file: {xml_file}')

        # Parse and modify the XML - create overlapping ranges
        tree = ET.parse(xml_file)
        root = tree.getroot()

        device = root.find('device[@dev_id="1"]')
        modified = False
        if device is not None:
            range_mappings = device.findall('.//range_mapping')
            if len(range_mappings) >= 2:
                # Make second range overlap with first
                first_begin_str = range_mappings[0].get('origin_begin')
                first_length_str = range_mappings[0].get('length')
                if first_begin_str is not None and first_length_str is not None:
                    first_begin = int(first_begin_str)
                    first_length = int(first_length_str)
                    # Set second range to start inside first range (ensure positive)
                    overlap_begin = first_begin + first_length - 10 if first_length > 10 else first_begin + 1
                    range_mappings[1].set('origin_begin', str(overlap_begin))
                    logging.info(f'Created overlapping range at origin_begin={overlap_begin}')
                    modified = True
            else:
                logging.info(f'Not enough range_mappings found: {len(range_mappings)}')

        if not modified:
            pytest.skip('Metadata does not contain suitable range_mappings to create overlap')

        tree.write(xml_file)

        # Use pre-allocated binary file from fixture
        binary_file = binary_metadata_file
        logging.info(f'Using pre-allocated binary file: {binary_file} (5MB)')

        # thin_restore should reject this
        logging.info(f'Running thin_restore with overlapping ranges: {xml_file} -> {binary_file}')
        restore_result = dmpd.thin_restore(input=str(xml_file), output=str(binary_file))
        logging.info(f'thin_restore stdout: {restore_result.stdout}')
        logging.info(f'thin_restore stderr: {restore_result.stderr}')
        assert not restore_result.succeeded, 'thin_restore should reject overlapping range mappings'
        logging.info(f'thin_restore correctly rejected overlapping ranges, exit_status: {restore_result.exit_status}')
