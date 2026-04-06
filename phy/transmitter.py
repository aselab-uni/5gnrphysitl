from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np

from .coding import CodingMetadata, build_channel_coder
from .frame_structure import FrameAllocation, build_default_allocation
from .modulation import ModulationMapper, bits_per_symbol
from .numerology import NumerologyConfig
from .resource_grid import ChannelMapping, ResourceGrid
from .scrambling import scramble_bits


@dataclass(slots=True)
class TxMetadata:
    channel_type: str
    numerology: NumerologyConfig
    allocation: FrameAllocation
    payload_bits: np.ndarray
    coded_bits: np.ndarray
    scrambling_sequence: np.ndarray
    coding_metadata: CodingMetadata
    modulation: str
    mapper: ModulationMapper
    mapping: ChannelMapping
    dmrs: Dict[str, np.ndarray]
    tx_grid: np.ndarray
    tx_symbols: np.ndarray
    sample_rate: float


@dataclass(slots=True)
class TxResult:
    waveform: np.ndarray
    metadata: TxMetadata


class NrTransmitter:
    def __init__(self, config: Dict) -> None:
        self.config = config
        self.seed = int(config.get("simulation", {}).get("seed", 0))
        self.rng = np.random.default_rng(self.seed)
        self.numerology = NumerologyConfig.from_dict(config["numerology"])
        self.allocation = build_default_allocation(self.numerology, config)

    def _generate_payload(self, channel_type: str) -> np.ndarray:
        if channel_type.lower() in {"control", "pdcch"}:
            size = int(self.config.get("control_channel", {}).get("payload_bits", 128))
        else:
            size = int(self.config.get("transport_block", {}).get("size_bits", 1024))
        return self.rng.integers(0, 2, size=size, dtype=np.uint8)

    def _ofdm_modulate(self, grid: ResourceGrid) -> np.ndarray:
        waveform = []
        for symbol in range(self.numerology.symbols_per_slot):
            bins = grid.active_to_ifft_bins(grid.grid[symbol])
            time_symbol = np.fft.ifft(bins, n=self.numerology.fft_size)
            cp = time_symbol[-self.numerology.cp_length :]
            waveform.append(np.concatenate([cp, time_symbol]))
        return np.concatenate(waveform).astype(np.complex128)

    def transmit(self, channel_type: str = "data", payload_bits: np.ndarray | None = None) -> TxResult:
        channel_type = channel_type.lower()
        payload = np.asarray(payload_bits, dtype=np.uint8) if payload_bits is not None else self._generate_payload(channel_type)

        modulation_name = str(
            self.config.get("modulation", {}).get(
                "scheme",
                self.config.get("control_channel", {}).get("modulation", "QPSK")
                if channel_type in {"control", "pdcch"}
                else "QPSK",
            )
        ).upper()
        mapper = ModulationMapper(modulation_name)

        grid = ResourceGrid(self.numerology, self.allocation)
        mapping = grid.mapping_for(
            channel_type=channel_type,
            bits_per_symbol=bits_per_symbol(modulation_name),
            modulation=modulation_name,
        )

        coder = build_channel_coder(channel_type=channel_type, config=self.config)
        coded_bits, coding_metadata = coder.encode(payload_bits=payload, target_length=mapping.bits_capacity)
        scrambling_cfg = self.config.get("scrambling", {})
        scrambled_bits, scrambling_sequence = scramble_bits(
            coded_bits,
            nid=int(scrambling_cfg.get("nid", 1)),
            rnti=int(scrambling_cfg.get("rnti", 0x1234)),
            q=0 if channel_type in {"data", "pdsch"} else 1,
        )
        tx_symbols = mapper.map_bits(scrambled_bits)
        grid.map_symbols(tx_symbols, mapping.positions)
        dmrs = grid.insert_dmrs(slot=0)
        waveform = self._ofdm_modulate(grid)

        return TxResult(
            waveform=waveform,
            metadata=TxMetadata(
                channel_type=channel_type,
                numerology=self.numerology,
                allocation=self.allocation,
                payload_bits=payload,
                coded_bits=coded_bits,
                scrambling_sequence=scrambling_sequence,
                coding_metadata=coding_metadata,
                modulation=modulation_name,
                mapper=mapper,
                mapping=mapping,
                dmrs=dmrs,
                tx_grid=grid.grid.copy(),
                tx_symbols=tx_symbols,
                sample_rate=self.numerology.sample_rate,
            ),
        )
