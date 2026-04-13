from __future__ import annotations

import numpy as np


def comb_positions(
    num_subcarriers: int,
    *,
    symbols: list[int],
    comb: int = 4,
    offset: int = 0,
) -> np.ndarray:
    step = max(1, int(comb))
    start = int(offset) % step
    positions = []
    for symbol in symbols:
        for subcarrier in range(start, int(num_subcarriers), step):
            positions.append((int(symbol), int(subcarrier)))
    return np.asarray(positions, dtype=int) if positions else np.zeros((0, 2), dtype=int)


def qpsk_reference_sequence(
    length: int,
    *,
    slot: int,
    symbol: int,
    seed: int,
) -> np.ndarray:
    size = max(int(length), 0)
    if size == 0:
        return np.array([], dtype=np.complex128)
    rng = np.random.default_rng(int(seed) + 257 * int(slot) + 17 * int(symbol))
    bits = rng.integers(0, 2, size=(size, 2), dtype=np.uint8)
    i = 1.0 - 2.0 * bits[:, 0].astype(np.float64)
    q = 1.0 - 2.0 * bits[:, 1].astype(np.float64)
    return ((i + 1j * q) / np.sqrt(2.0)).astype(np.complex128)
