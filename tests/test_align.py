from raviewer.src.core import (align_image)
import pytest


def test_align():
    """Test verifying if adding/skipping data works properly"""
    data_buffer = bytearray([0] * 64)
    aligned_buffer = align_image(data_buffer, 8, 16)
    assert aligned_buffer == bytearray([16] * 8) + data_buffer

    aligned_buffer = align_image(data_buffer, -8)
    assert aligned_buffer == data_buffer[8:]
