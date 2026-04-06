from __future__ import annotations

import numpy as np

from phy.kpi import bit_error_rate, error_vector_magnitude


def test_bit_error_rate_zero_for_equal_sequences() -> None:
    bits = np.array([0, 1, 1, 0], dtype=np.uint8)
    assert bit_error_rate(bits, bits.copy()) == 0.0


def test_evm_zero_for_identical_symbols() -> None:
    symbols = np.array([1 + 1j, -1 - 1j], dtype=np.complex128)
    assert error_vector_magnitude(symbols, symbols.copy()) == 0.0
