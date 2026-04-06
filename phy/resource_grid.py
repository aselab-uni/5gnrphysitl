from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np

from .dmrs import dmrs_pattern
from .frame_structure import FrameAllocation
from .numerology import NumerologyConfig


@dataclass(slots=True)
class ChannelMapping:
    positions: np.ndarray
    bits_capacity: int
    modulation: str


class ResourceGrid:
    """Single-slot active-subcarrier resource grid."""

    def __init__(self, numerology: NumerologyConfig, allocation: FrameAllocation) -> None:
        self.numerology = numerology
        self.allocation = allocation
        self.grid = np.zeros(
            (numerology.symbols_per_slot, numerology.active_subcarriers),
            dtype=np.complex128,
        )

    @property
    def shape(self) -> tuple[int, int]:
        return self.grid.shape

    def pdcch_positions(self) -> np.ndarray:
        positions = []
        for symbol in self.allocation.pdcch_symbols:
            for sc in range(self.allocation.control_subcarriers):
                positions.append((symbol, sc))
        return np.asarray(positions, dtype=int)

    def dmrs_positions(self) -> np.ndarray:
        positions = []
        for symbol in self.allocation.dmrs_symbols:
            if symbol < self.allocation.pdsch_start_symbol:
                continue
            subcarriers, _ = dmrs_pattern(self.numerology.active_subcarriers, dmrs_symbol=symbol)
            for sc in subcarriers:
                positions.append((symbol, sc))
        return np.asarray(positions, dtype=int)

    def pdsch_positions(self) -> np.ndarray:
        positions = []
        dmrs = {tuple(position) for position in self.dmrs_positions().tolist()}
        for symbol in self.allocation.pdsch_symbols(self.numerology):
            for sc in range(self.numerology.active_subcarriers):
                if (symbol, sc) not in dmrs:
                    positions.append((symbol, sc))
        return np.asarray(positions, dtype=int)

    def mapping_for(self, channel_type: str, bits_per_symbol: int, modulation: str) -> ChannelMapping:
        channel_type = channel_type.lower()
        if channel_type in {"control", "pdcch"}:
            positions = self.pdcch_positions()
        else:
            positions = self.pdsch_positions()
        return ChannelMapping(
            positions=positions,
            bits_capacity=positions.shape[0] * bits_per_symbol,
            modulation=modulation,
        )

    def map_symbols(self, symbols: np.ndarray, positions: np.ndarray) -> None:
        positions = np.asarray(positions, dtype=int)
        count = min(symbols.size, positions.shape[0])
        self.grid[positions[:count, 0], positions[:count, 1]] = symbols[:count]

    def extract_symbols(self, positions: np.ndarray) -> np.ndarray:
        positions = np.asarray(positions, dtype=int)
        return self.grid[positions[:, 0], positions[:, 1]]

    def insert_dmrs(self, slot: int = 0) -> Dict[str, np.ndarray]:
        inserted = []
        for symbol in self.allocation.dmrs_symbols:
            if symbol < self.allocation.pdsch_start_symbol:
                continue
            subcarriers, sequence = dmrs_pattern(self.numerology.active_subcarriers, dmrs_symbol=symbol, slot=slot)
            self.grid[symbol, subcarriers] = sequence
            inserted.extend([(symbol, sc) for sc in subcarriers])
        position_array = np.asarray(inserted, dtype=int) if inserted else np.zeros((0, 2), dtype=int)
        return {
            "positions": position_array,
            "symbols": self.grid[position_array[:, 0], position_array[:, 1]]
            if inserted
            else np.array([], dtype=np.complex128),
        }

    def active_to_ifft_bins(self, active_symbol: np.ndarray) -> np.ndarray:
        fft_bins = np.zeros(self.numerology.fft_size, dtype=np.complex128)
        shifted = np.zeros(self.numerology.fft_size, dtype=np.complex128)
        center = self.numerology.fft_size // 2
        left = self.numerology.active_subcarriers // 2
        right = self.numerology.active_subcarriers - left
        shifted[center - left : center] = active_symbol[:left]
        shifted[center + 1 : center + 1 + right] = active_symbol[left:]
        fft_bins[:] = np.fft.ifftshift(shifted)
        return fft_bins

    def ifft_bins_to_active(self, fft_bins: np.ndarray) -> np.ndarray:
        shifted = np.fft.fftshift(fft_bins)
        center = self.numerology.fft_size // 2
        left = self.numerology.active_subcarriers // 2
        right = self.numerology.active_subcarriers - left
        return np.concatenate(
            [
                shifted[center - left : center],
                shifted[center + 1 : center + 1 + right],
            ]
        )
