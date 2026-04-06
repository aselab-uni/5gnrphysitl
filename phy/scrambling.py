from __future__ import annotations

import numpy as np


def nr_gold_sequence(length: int, cinit: int) -> np.ndarray:
    x1 = np.zeros(length + 31, dtype=np.uint8)
    x2 = np.zeros(length + 31, dtype=np.uint8)
    x1[:31] = np.array([1] + [0] * 30, dtype=np.uint8)
    for index in range(31):
        x2[index] = (cinit >> index) & 1

    for index in range(length):
        x1[index + 31] = (x1[index + 3] + x1[index]) & 1
        x2[index + 31] = (x2[index + 3] + x2[index + 2] + x2[index + 1] + x2[index]) & 1

    return (x1[31:] + x2[31:]) & 1


def cinit_from_ids(nid: int, rnti: int, q: int = 0) -> int:
    return ((rnti & 0xFFFF) << 15) ^ ((nid & 0x3FF) << 4) ^ (q & 0xF)


def scramble_bits(bits: np.ndarray, nid: int, rnti: int, q: int = 0) -> tuple[np.ndarray, np.ndarray]:
    sequence = nr_gold_sequence(bits.size, cinit_from_ids(nid=nid, rnti=rnti, q=q))
    return bits ^ sequence, sequence


def descramble_llrs(llrs: np.ndarray, sequence: np.ndarray) -> np.ndarray:
    signs = 1.0 - 2.0 * sequence.astype(np.float64)
    return llrs * signs
