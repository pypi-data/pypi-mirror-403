# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Functional tests for VdoCalculateSize utility."""

import logging

import pytest

from sts.vdo import VdoCalculateSize


@pytest.mark.usefixtures('_vdo_test')
class TestVdoCalculateSize:
    """Test VdoCalculateSize command wrapper."""

    def test_basic_calculation(self) -> None:
        """Test basic VDO size calculation."""
        calc = VdoCalculateSize(
            physical_size='10G',
            logical_size='20G',
        )
        result = calc.calculate()
        logging.info(f'Basic calculation result:\n{result.stdout}')
        assert result.succeeded
        assert result.rc == 0

    @pytest.mark.parametrize('slab_bits', [13, 17, 19, 23])
    def test_with_valid_slab_bits(self, slab_bits: int) -> None:
        """Test calculation with valid slab_bits values."""
        calc = VdoCalculateSize(
            physical_size='100G',
            logical_size='200G',
            slab_bits=slab_bits,
        )
        result = calc.calculate()
        logging.info(f'Calculation with slab_bits={slab_bits}:\n{result.stdout}')
        assert result.succeeded
        assert result.rc == 0

    @pytest.mark.parametrize('slab_size', ['128M', '512M', '2G', '8G'])
    def test_with_slab_size(self, slab_size: str) -> None:
        """Test calculation with slab_size instead of slab_bits."""
        calc = VdoCalculateSize(
            physical_size='100G',
            logical_size='200G',
            slab_size=slab_size,
        )
        result = calc.calculate()
        logging.info(f'Calculation with slab_size={slab_size}:\n{result.stdout}')
        assert result.succeeded
        assert result.rc == 0

    @pytest.mark.parametrize('index_memory_size', [0.25, 0.5, 0.75, 1, 2])
    def test_with_valid_index_memory_size(self, index_memory_size: float) -> None:
        """Test calculation with valid index_memory_size values."""
        calc = VdoCalculateSize(
            physical_size='100G',
            logical_size='200G',
            index_memory_size=index_memory_size,
        )
        result = calc.calculate()
        logging.info(f'Calculation with index_memory_size={index_memory_size}:\n{result.stdout}')
        assert result.succeeded
        assert result.rc == 0

    def test_with_sparse_index(self) -> None:
        """Test calculation with sparse index enabled."""
        calc = VdoCalculateSize(
            physical_size='100G',
            logical_size='200G',
            sparse_index=True,
        )
        result = calc.calculate()
        logging.info(f'Calculation with sparse_index:\n{result.stdout}')
        assert result.succeeded
        assert result.rc == 0

    @pytest.mark.parametrize('block_map_cache_size', [1024, 32768, 65536])
    def test_with_block_map_cache_size(self, block_map_cache_size: int) -> None:
        """Test calculation with block_map_cache_size."""
        calc = VdoCalculateSize(
            physical_size='100G',
            logical_size='200G',
            block_map_cache_size=block_map_cache_size,
        )
        result = calc.calculate()
        logging.info(f'Calculation with block_map_cache_size={block_map_cache_size}:\n{result.stdout}')
        assert result.succeeded
        assert result.rc == 0

    def test_full_options(self) -> None:
        """Test calculation with all options (from man page example)."""
        calc = VdoCalculateSize(
            physical_size='600G',
            logical_size='2T',
            slab_bits=22,
            index_memory_size=1,
            block_map_cache_size=32768,
        )
        result = calc.calculate()
        logging.info(f'Full options calculation:\n{result.stdout}')
        assert result.succeeded
        assert result.rc == 0

    def test_sparse_index_with_memory(self) -> None:
        """Test calculation with sparse index and memory size."""
        calc = VdoCalculateSize(
            physical_size='500G',
            logical_size='1T',
            sparse_index=True,
            index_memory_size=0.5,
        )
        result = calc.calculate()
        logging.info(f'Sparse index with memory:\n{result.stdout}')
        assert result.succeeded
        assert result.rc == 0

    @pytest.mark.parametrize('slab_bits', [0, 12, 24, 100])
    def test_invalid_slab_bits(self, slab_bits: int) -> None:
        """Test calculation with invalid slab_bits values."""
        calc = VdoCalculateSize(
            physical_size='100G',
            logical_size='200G',
            slab_bits=slab_bits,
        )
        result = calc.calculate()
        logging.info(f'Invalid slab_bits={slab_bits} rc={result.rc}, stderr={result.stderr}')
        # Command should fail with invalid values
        assert result.failed
        assert result.rc != 0

    @pytest.mark.parametrize('index_memory_size', [0.1, 0.33, -1])
    def test_invalid_index_memory_size(self, index_memory_size: float) -> None:
        """Test calculation with invalid index_memory_size values."""
        calc = VdoCalculateSize(
            physical_size='100G',
            logical_size='200G',
            index_memory_size=index_memory_size,
        )
        result = calc.calculate()
        logging.info(f'Invalid index_memory_size={index_memory_size} rc={result.rc}, stderr={result.stderr}')
        # Command should fail with invalid values
        assert result.failed
        assert result.rc != 0

    def test_physical_size_only(self) -> None:
        """Test calculation with only physical_size fails (logical_size required)."""
        calc = VdoCalculateSize(physical_size='100G')
        result = calc.calculate()
        logging.info(f'Physical size only: rc={result.rc}, stderr={result.stderr}')
        # Both --logical-size and --physical-size are required
        assert result.failed
        assert result.rc != 0

    def test_logical_size_only(self) -> None:
        """Test calculation with only logical_size fails (physical_size required)."""
        calc = VdoCalculateSize(logical_size='200G')
        result = calc.calculate()
        logging.info(f'Logical size only: rc={result.rc}, stderr={result.stderr}')
        # Both --logical-size and --physical-size are required
        assert result.failed
        assert result.rc != 0

    def test_class_constants(self) -> None:
        """Verify class constants are accessible for reference."""
        assert VdoCalculateSize.MIN_SLAB_BITS == 13
        assert VdoCalculateSize.MAX_SLAB_BITS == 23
        assert VdoCalculateSize.DEFAULT_SLAB_BITS == 19
        assert 0.25 in VdoCalculateSize.VALID_INDEX_MEMORY_SIZES
        assert 0.5 in VdoCalculateSize.VALID_INDEX_MEMORY_SIZES
        assert 0.75 in VdoCalculateSize.VALID_INDEX_MEMORY_SIZES
