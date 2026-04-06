from __future__ import annotations

import numpy as np

from phy.modulation import ModulationMapper


def test_qpsk_hard_roundtrip() -> None:
    mapper = ModulationMapper("QPSK")
    bits = np.array([0, 0, 0, 1, 1, 1, 1, 0], dtype=np.uint8)
    symbols = mapper.map_bits(bits)
    recovered = mapper.hard_demodulate(symbols)
    assert np.array_equal(bits, recovered)


def test_llr_shape_matches_input() -> None:
    mapper = ModulationMapper("16QAM")
    bits = np.random.default_rng(1).integers(0, 2, size=40, dtype=np.uint8)
    symbols = mapper.map_bits(bits)
    llrs = mapper.demap_llr(symbols, noise_variance=1e-3)
    assert llrs.shape == bits.shape
