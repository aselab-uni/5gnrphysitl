from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .numerology import NumerologyConfig


@dataclass(slots=True)
class FrameAllocation:
    """Resource allocation abstraction for a single slot."""

    control_symbols: int
    pdsch_start_symbol: int
    pusch_start_symbol: int
    pucch_symbol_count: int
    prach_symbol_count: int
    prach_subcarriers: int
    csi_rs_symbols: List[int]
    srs_symbols: List[int]
    rs_comb: int
    csi_rs_subcarrier_offset: int
    srs_subcarrier_offset: int
    dmrs_symbols: List[int]
    control_subcarriers: int

    @property
    def pdcch_symbols(self) -> List[int]:
        return list(range(self.control_symbols))

    def pdsch_symbols(self, numerology: NumerologyConfig) -> List[int]:
        return [
            symbol
            for symbol in range(self.pdsch_start_symbol, numerology.symbols_per_slot)
            if symbol not in self.dmrs_symbols
        ]

    def pusch_symbols(self, numerology: NumerologyConfig) -> List[int]:
        return [
            symbol
            for symbol in range(self.pusch_start_symbol, numerology.symbols_per_slot)
            if symbol not in self.dmrs_symbols
        ]

    def pucch_symbols(self, numerology: NumerologyConfig) -> List[int]:
        count = max(1, min(self.pucch_symbol_count, numerology.symbols_per_slot))
        start = numerology.symbols_per_slot - count
        return [
            symbol
            for symbol in range(start, numerology.symbols_per_slot)
            if symbol not in self.dmrs_symbols
        ]

    def prach_symbols(self, numerology: NumerologyConfig) -> List[int]:
        count = max(1, min(self.prach_symbol_count, numerology.symbols_per_slot))
        return [
            symbol
            for symbol in range(count)
            if symbol not in self.dmrs_symbols
        ]


def build_default_allocation(numerology: NumerologyConfig, config: dict) -> FrameAllocation:
    frame_cfg = config.get("frame", {})
    reference_cfg = config.get("reference_signals", {})
    control_symbols = int(frame_cfg.get("control_symbols", 2))
    pdsch_start_symbol = int(frame_cfg.get("pdsch_start_symbol", control_symbols))
    pusch_start_symbol = int(frame_cfg.get("pusch_start_symbol", pdsch_start_symbol))
    pucch_symbol_count = int(frame_cfg.get("pucch_symbol_count", control_symbols))
    prach_symbol_count = int(frame_cfg.get("prach_symbol_count", 1))
    csi_rs_symbols = list(frame_cfg.get("csi_rs_symbols", [12])) if bool(reference_cfg.get("enable_csi_rs", True)) else []
    srs_symbols = list(frame_cfg.get("srs_symbols", [13])) if bool(reference_cfg.get("enable_srs", True)) else []
    rs_comb = int(frame_cfg.get("rs_comb", 4))
    csi_rs_subcarrier_offset = int(frame_cfg.get("csi_rs_subcarrier_offset", 1))
    srs_subcarrier_offset = int(frame_cfg.get("srs_subcarrier_offset", 2))
    dmrs_symbols = list(frame_cfg.get("dmrs_symbols", [2, 11]))
    control_subcarriers = int(
        frame_cfg.get("control_subcarriers", min(72, numerology.active_subcarriers))
    )
    prach_subcarriers = int(
        frame_cfg.get("prach_subcarriers", min(72, numerology.active_subcarriers))
    )
    return FrameAllocation(
        control_symbols=control_symbols,
        pdsch_start_symbol=pdsch_start_symbol,
        pusch_start_symbol=pusch_start_symbol,
        pucch_symbol_count=pucch_symbol_count,
        prach_symbol_count=prach_symbol_count,
        prach_subcarriers=max(12, min(prach_subcarriers, numerology.active_subcarriers)),
        csi_rs_symbols=[symbol for symbol in csi_rs_symbols if 0 <= symbol < numerology.symbols_per_slot],
        srs_symbols=[symbol for symbol in srs_symbols if 0 <= symbol < numerology.symbols_per_slot],
        rs_comb=max(1, rs_comb),
        csi_rs_subcarrier_offset=max(0, csi_rs_subcarrier_offset),
        srs_subcarrier_offset=max(0, srs_subcarrier_offset),
        dmrs_symbols=[symbol for symbol in dmrs_symbols if 0 <= symbol < numerology.symbols_per_slot],
        control_subcarriers=max(12, min(control_subcarriers, numerology.active_subcarriers)),
    )
