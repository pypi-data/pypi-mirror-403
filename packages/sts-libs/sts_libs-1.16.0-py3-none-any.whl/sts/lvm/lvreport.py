# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""LVM Logical Volume report handling.

This module provides the LVReport dataclass for parsing and storing Logical Volume information from lvs JSON output.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from sts.utils.cmdline import run


@dataclass
class LVReport:
    """Logical Volume report data.

    This class provides detailed information about a Logical Volume from 'lvs -o lv_all --reportformat json'.
    Contains all available LV attributes that can be queried.

    Args:
        name: LV name (optional, used for fetching, can be discovered)
        vg: Volume group name (optional, used for fetching, can be discovered)
        prevent_update: Flag to prevent updates from report (defaults to False)

        All lv_* fields: LV attributes from lvs output
        raw_data: Complete raw data from lvs output
    """

    # Control fields
    name: str | None = None
    vg: str | None = None
    prevent_update: bool = field(default=False)

    # Core LV identification
    lv_uuid: str | None = None
    lv_name: str | None = None
    lv_full_name: str | None = None
    lv_path: str | None = None
    lv_dm_path: str | None = None
    vg_name: str | None = None

    # Size and layout information
    lv_size: str | None = None
    lv_metadata_size: str | None = None
    seg_count: str | None = None
    lv_layout: str | None = None
    lv_role: str | None = None

    # Status and attributes
    lv_attr: str | None = None
    lv_active: str | None = None
    lv_active_locally: str | None = None
    lv_active_remotely: str | None = None
    lv_active_exclusively: str | None = None
    lv_permissions: str | None = None
    lv_suspended: str | None = None

    # Device information
    lv_major: str | None = None
    lv_minor: str | None = None
    lv_kernel_major: str | None = None
    lv_kernel_minor: str | None = None
    lv_read_ahead: str | None = None
    lv_kernel_read_ahead: str | None = None

    # Pool and thin provisioning
    pool_lv: str | None = None
    pool_lv_uuid: str | None = None
    data_lv: str | None = None
    data_lv_uuid: str | None = None
    metadata_lv: str | None = None
    metadata_lv_uuid: str | None = None
    data_percent: str | None = None
    metadata_percent: str | None = None

    # Snapshot information
    origin: str | None = None
    origin_uuid: str | None = None
    origin_size: str | None = None
    snap_percent: str | None = None

    # RAID information
    raid_mismatch_count: str | None = None
    raid_sync_action: str | None = None
    raid_write_behind: str | None = None
    raid_min_recovery_rate: str | None = None
    raid_max_recovery_rate: str | None = None

    # Cache information
    cache_total_blocks: str | None = None
    cache_used_blocks: str | None = None
    cache_dirty_blocks: str | None = None
    cache_read_hits: str | None = None
    cache_read_misses: str | None = None
    cache_write_hits: str | None = None
    cache_write_misses: str | None = None
    kernel_cache_settings: str | None = None
    kernel_cache_policy: str | None = None

    # VDO information
    vdo_operating_mode: str | None = None
    vdo_compression_state: str | None = None
    vdo_index_state: str | None = None
    vdo_used_size: str | None = None
    vdo_saving_percent: str | None = None

    # Write cache information
    writecache_block_size: str | None = None
    writecache_total_blocks: str | None = None
    writecache_free_blocks: str | None = None
    writecache_writeback_blocks: str | None = None
    writecache_error: str | None = None

    # Configuration and policy
    lv_allocation_policy: str | None = None
    lv_allocation_locked: str | None = None
    lv_autoactivation: str | None = None
    lv_when_full: str | None = None
    lv_skip_activation: str | None = None
    lv_fixed_minor: str | None = None

    # Timing and host information
    lv_time: str | None = None
    lv_time_removed: str | None = None
    lv_host: str | None = None

    # Health and status checks
    lv_health_status: str | None = None
    lv_check_needed: str | None = None
    lv_merge_failed: str | None = None
    lv_snapshot_invalid: str | None = None

    # Miscellaneous
    lv_tags: str | None = None
    lv_profile: str | None = None
    lv_lockargs: str | None = None
    lv_modules: str | None = None
    lv_historical: str | None = None
    kernel_discards: str | None = None
    copy_percent: str | None = None
    sync_percent: str | None = None

    # Device table status
    lv_live_table: str | None = None
    lv_inactive_table: str | None = None
    lv_device_open: str | None = None

    # Hierarchical relationships
    lv_parent: str | None = None
    lv_ancestors: str | None = None
    lv_full_ancestors: str | None = None
    lv_descendants: str | None = None
    lv_full_descendants: str | None = None

    # Conversion and movement
    lv_converting: str | None = None
    lv_merging: str | None = None
    move_pv: str | None = None
    move_pv_uuid: str | None = None
    convert_lv: str | None = None
    convert_lv_uuid: str | None = None

    # Mirror information
    mirror_log: str | None = None
    mirror_log_uuid: str | None = None

    # Synchronization
    lv_initial_image_sync: str | None = None
    lv_image_synced: str | None = None

    # Integrity
    raidintegritymode: str | None = None
    raidintegrityblocksize: str | None = None
    integritymismatches: str | None = None
    kernel_metadata_format: str | None = None

    # Segment information (from seg_all)
    segtype: str | None = None
    stripes: str | None = None
    data_stripes: str | None = None
    stripe_size: str | None = None
    region_size: str | None = None
    chunk_size: str | None = None
    seg_start: str | None = None
    seg_start_pe: str | None = None
    seg_size: str | None = None
    seg_size_pe: str | None = None
    seg_tags: str | None = None
    seg_pe_ranges: str | None = None
    seg_le_ranges: str | None = None
    seg_metadata_le_ranges: str | None = None
    devices: str | None = None
    metadata_devices: str | None = None
    seg_monitor: str | None = None

    # Additional segment fields
    reshape_len: str | None = None
    reshape_len_le: str | None = None
    data_copies: str | None = None
    data_offset: str | None = None
    new_data_offset: str | None = None
    parity_chunks: str | None = None
    thin_count: str | None = None
    discards: str | None = None
    cache_metadata_format: str | None = None
    cache_mode: str | None = None
    zero: str | None = None
    transaction_id: str | None = None
    thin_id: str | None = None
    cache_policy: str | None = None
    cache_settings: str | None = None
    integrity_settings: str | None = None

    # VDO segment settings
    vdo_compression: str | None = None
    vdo_deduplication: str | None = None
    vdo_minimum_io_size: str | None = None
    vdo_block_map_cache_size: str | None = None
    vdo_block_map_era_length: str | None = None
    vdo_use_sparse_index: str | None = None
    vdo_index_memory_size: str | None = None
    vdo_slab_size: str | None = None
    vdo_ack_threads: str | None = None
    vdo_bio_threads: str | None = None
    vdo_bio_rotation: str | None = None
    vdo_cpu_threads: str | None = None
    vdo_hash_zone_threads: str | None = None
    vdo_logical_threads: str | None = None
    vdo_physical_threads: str | None = None
    vdo_max_discard: str | None = None
    vdo_header_size: str | None = None
    vdo_use_metadata_hints: str | None = None
    vdo_write_policy: str | None = None

    # Raw data storage for any additional fields
    raw_data: dict[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        """Initialize the report."""
        # If name and vg are provided, fetch the report data
        if self.name and self.vg:
            self.refresh()

    def refresh(self) -> bool:
        """Refresh LV report data from system.

        Updates all fields with the latest information from lvs command.

        Returns:
            bool: True if refresh was successful, False otherwise
        """
        # If prevent_update is True, skip refresh
        if self.prevent_update:
            logging.debug('Refresh skipped due to prevent_update flag')
            return True

        if not self.name or not self.vg:
            logging.error('LV name and VG name required for refresh')
            return False

        # Run lvs command with JSON output including segment information
        result = run(f'lvs -a -o lv_all,seg_all {self.vg}/{self.name} --reportformat json')
        if result.failed or not result.stdout:
            logging.error(f'Failed to get LV report data for {self.vg}/{self.name}')
            return False

        try:
            report_data = json.loads(result.stdout)
            return self._update_from_report(report_data)
        except json.JSONDecodeError:
            logging.exception('Failed to parse LV report JSON')
            return False

    def _update_from_report(self, report_data: dict[str, Any]) -> bool:
        """Update LV information from report data.

        Args:
            report_data: Complete report data from lvs JSON

        Returns:
            bool: True if update was successful, False otherwise
        """
        if self.prevent_update:
            logging.debug('Update from report skipped due to prevent_update flag')
            return True

        if not isinstance(report_data, dict) or 'report' not in report_data:
            logging.error('Invalid LV report format')
            return False

        reports = report_data.get('report', [])
        if not isinstance(reports, list) or not reports:
            logging.error('No reports found in LV data')
            return False

        # Get the first report
        report = reports[0]
        if not isinstance(report, dict) or 'lv' not in report:
            logging.error('Invalid report structure')
            return False

        lvs = report.get('lv', [])
        if not isinstance(lvs, list) or not lvs:
            logging.warning(f'No LV data found for {self.vg}/{self.name}')
            return False

        # Get the first (and should be only) LV
        lv_data = lvs[0]
        if not isinstance(lv_data, dict):
            logging.error('Invalid LV data structure')
            return False

        # Update all fields from the data
        self.raw_data = lv_data.copy()

        # Map all known fields
        for field_name in self.__dataclass_fields__:
            if field_name not in ('raw_data', 'name', 'vg', 'prevent_update') and field_name in lv_data:
                setattr(self, field_name, lv_data[field_name])

        # Update our name and vg from the data if not set
        if not self.name and self.lv_name:
            self.name = self.lv_name
        if not self.vg and self.vg_name:
            self.vg = self.vg_name

        # Extract VG name from full name if available
        if self.lv_full_name and not self.vg_name and '/' in self.lv_full_name:
            self.vg_name = self.lv_full_name.split('/')[0]

        return True

    @classmethod
    def get_all(cls, vg: str | None = None) -> list[LVReport]:
        """Get reports for all logical volumes.

        Args:
            vg: Optional volume group to filter by

        Returns:
            List of LVReport instances
        """
        reports: list[LVReport] = []

        # Build command
        cmd = 'lvs -a -o lv_all,seg_all --reportformat json'
        if vg:
            cmd += f' {vg}'

        result = run(cmd)
        if result.failed or not result.stdout:
            return reports

        try:
            report_data = json.loads(result.stdout)

            if 'report' in report_data and isinstance(report_data['report'], list):
                for report in report_data['report']:
                    if not isinstance(report, dict) or 'lv' not in report:
                        continue

                    for lv_data in report.get('lv', []):
                        if not isinstance(lv_data, dict):
                            continue

                        # Create report with prevent_update=True to avoid double refresh
                        lv_report = cls(prevent_update=True)
                        lv_report.raw_data = lv_data.copy()

                        # Map all known fields
                        for field_name in cls.__dataclass_fields__:
                            if field_name not in ('raw_data', 'name', 'vg', 'prevent_update') and field_name in lv_data:
                                setattr(lv_report, field_name, lv_data[field_name])

                        # Set name and vg from the data
                        lv_report.name = lv_report.lv_name
                        lv_report.vg = lv_report.vg_name

                        # Extract VG name from full name if needed
                        if lv_report.lv_full_name and not lv_report.vg_name and '/' in lv_report.lv_full_name:
                            lv_report.vg_name = lv_report.lv_full_name.split('/')[0]
                            if not lv_report.vg:
                                lv_report.vg = lv_report.vg_name

                        reports.append(lv_report)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logging.warning(f'Failed to parse LV reports: {e}')

        return reports
