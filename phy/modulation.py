from __future__ import annotations

from functools import lru_cache
from typing import Dict, Tuple

import numpy as np


def bits_per_symbol(modulation: str) -> int:
    mapping = {"QPSK": 2, "16QAM": 4, "64QAM": 6, "256QAM": 8}
    try:
        return mapping[modulation.upper()]
    except KeyError as exc:
        raise ValueError(f"Unsupported modulation scheme: {modulation}") from exc


def _bits_to_int(bits: np.ndarray) -> int:
    value = 0
    for bit in bits:
        value = (value << 1) | int(bit)
    return value


def _gray_to_binary(value: int) -> int:
    result = value
    while value > 0:
        value >>= 1
        result ^= value
    return result


def _qam_levels(order_per_axis: int) -> np.ndarray:
    return np.arange(-(order_per_axis - 1), order_per_axis, 2, dtype=np.float64)


@lru_cache(maxsize=8)
def constellation_table(modulation: str) -> Tuple[np.ndarray, np.ndarray]:
    modulation = modulation.upper()
    bits = bits_per_symbol(modulation)
    order = 1 << bits
    order_per_axis = int(np.sqrt(order))
    bits_per_axis = bits // 2
    levels = _qam_levels(order_per_axis)

    labels = np.zeros((order, bits), dtype=np.uint8)
    points = np.zeros(order, dtype=np.complex128)

    for symbol_index in range(order):
        bit_label = np.array(
            [(symbol_index >> shift) & 1 for shift in range(bits - 1, -1, -1)],
            dtype=np.uint8,
        )
        i_gray = _bits_to_int(bit_label[:bits_per_axis])
        q_gray = _bits_to_int(bit_label[bits_per_axis:])
        i_index = _gray_to_binary(i_gray)
        q_index = _gray_to_binary(q_gray)
        labels[symbol_index] = bit_label
        points[symbol_index] = levels[i_index] + 1j * levels[q_index]

    points /= np.sqrt(np.mean(np.abs(points) ** 2))
    return points, labels


class ModulationMapper:
    """Gray-labeled QAM mapper and max-log soft demapper."""

    def __init__(self, modulation: str) -> None:
        self.modulation = modulation.upper()
        self.bits_per_symbol = bits_per_symbol(self.modulation)
        self.constellation, self.labels = constellation_table(self.modulation)
        self._label_to_symbol: Dict[Tuple[int, ...], complex] = {
            tuple(label.tolist()): symbol for label, symbol in zip(self.labels, self.constellation)
        }

    def map_bits(self, bits: np.ndarray) -> np.ndarray:
        bits = np.asarray(bits, dtype=np.uint8)
        padding = (-bits.size) % self.bits_per_symbol
        if padding:
            bits = np.pad(bits, (0, padding), mode="constant")
        groups = bits.reshape(-1, self.bits_per_symbol)
        symbols = np.zeros(groups.shape[0], dtype=np.complex128)
        for index, group in enumerate(groups):
            symbols[index] = self._label_to_symbol[tuple(group.tolist())]
        return symbols

    def demap_llr(self, symbols: np.ndarray, noise_variance: float) -> np.ndarray:
        noise_variance = max(float(noise_variance), 1e-9)
        metrics = np.abs(symbols[:, None] - self.constellation[None, :]) ** 2 / noise_variance
        llrs = np.zeros((symbols.size, self.bits_per_symbol), dtype=np.float64)
        for bit_index in range(self.bits_per_symbol):
            mask0 = self.labels[:, bit_index] == 0
            mask1 = ~mask0
            llrs[:, bit_index] = np.min(metrics[:, mask1], axis=1) - np.min(metrics[:, mask0], axis=1)
        return llrs.reshape(-1)

    def hard_demodulate(self, symbols: np.ndarray) -> np.ndarray:
        metrics = np.abs(symbols[:, None] - self.constellation[None, :]) ** 2
        nearest = np.argmin(metrics, axis=1)
        return self.labels[nearest].reshape(-1)
