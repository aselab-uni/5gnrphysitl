from __future__ import annotations

from typing import Tuple

import numpy as np


def _gold_sequence(length: int, cinit: int) -> np.ndarray:
    x1 = np.zeros(length + 31, dtype=np.uint8)
    x2 = np.zeros(length + 31, dtype=np.uint8)
    x1[:31] = np.array([1] + [0] * 30, dtype=np.uint8)
    for index in range(31):
        x2[index] = (cinit >> index) & 1

    for index in range(length):
        x1[index + 31] = (x1[index + 3] + x1[index]) & 1
        x2[index + 31] = (x2[index + 3] + x2[index + 2] + x2[index + 1] + x2[index]) & 1
    return (x1[31:] + x2[31:]) & 1


def generate_dmrs_sequence(length: int, nid: int, slot: int = 0) -> np.ndarray:
    bits = _gold_sequence(length * 2, cinit=((nid & 0xFFFF) << 5) ^ slot)
    i_bits = bits[0::2].astype(np.int8)
    q_bits = bits[1::2].astype(np.int8)
    qpsk = (1 - 2 * i_bits) + 1j * (1 - 2 * q_bits)
    return qpsk.astype(np.complex128) / np.sqrt(2.0)


def comb2_indices(num_subcarriers: int, offset: int = 0) -> np.ndarray:
    return np.arange(offset, num_subcarriers, 2, dtype=int)


def dmrs_pattern(num_subcarriers: int, dmrs_symbol: int, slot: int = 0) -> Tuple[np.ndarray, np.ndarray]:
    offset = (slot + dmrs_symbol) & 1
    indices = comb2_indices(num_subcarriers, offset=offset)
    sequence = generate_dmrs_sequence(indices.size, nid=slot + 1, slot=slot)
    return indices, sequence
