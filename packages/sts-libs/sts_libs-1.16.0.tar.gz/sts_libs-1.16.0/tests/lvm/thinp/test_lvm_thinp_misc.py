# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for miscellaneous thin provisioning functionality.

This module contains pytest tests for basic thin provisioning support
and segment type availability in LVM.
"""

from __future__ import annotations

from sts.utils.cmdline import run


class TestLvmThinpMisc:
    """Test cases for miscellaneous thin provisioning functionality."""

    def test_lvm_segment_types(self) -> None:
        """Test that thin and thin-pool segment types are supported.

        This test verifies LVM has thin provisioning capability by checking
        that both 'thin' and 'thin-pool' segment types are available.
        No fixtures needed as this only checks LVM capabilities.
        """
        # Check if thin segment type is supported
        result = run('lvm segtypes | grep -w "thin$"')
        assert result.succeeded, 'thin segment type should be supported'

        # Check if thin-pool segment type is supported
        result = run('lvm segtypes | grep -w "thin-pool$"')
        assert result.succeeded, 'thin-pool segment type should be supported'
