from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np

from .coding import CodingMetadata, build_channel_coder
from .frame_structure import FrameAllocation, build_default_allocation
from .modulation import ModulationMapper, bits_per_symbol
from .prach import PrachMapper, bits_to_preamble_id, generate_prach_sequence, preamble_id_to_bits
from .numerology import NumerologyConfig
from .resource_grid import ChannelMapping, ResourceGrid
from .scrambling import scramble_bits
from .types import SpatialLayout
from .uplink import apply_transform_precoding


@dataclass(slots=True)
class TxMetadata:
    direction: str
    channel_type: str
    numerology: NumerologyConfig
    allocation: FrameAllocation
    spatial_layout: SpatialLayout
    transform_precoding_enabled: bool
    payload_bits: np.ndarray
    coded_bits: np.ndarray
    scrambled_bits: np.ndarray
    scrambling_sequence: np.ndarray
    coding_metadata: CodingMetadata
    modulation: str
    mapper: object
    mapping: ChannelMapping
    dmrs: Dict[str, np.ndarray]
    csi_rs: Dict[str, np.ndarray]
    srs: Dict[str, np.ndarray]
    tensor_view_specs: Dict[str, Dict[str, object]]
    modulation_symbols: np.ndarray
    tx_layer_grid: np.ndarray
    tx_port_grid: np.ndarray
    tx_grid_data: np.ndarray
    tx_grid: np.ndarray
    tx_symbols: np.ndarray
    tx_port_waveforms: np.ndarray
    sample_rate: float
    prach_preamble_id: int | None = None
    prach_root_sequence_index: int | None = None
    prach_cyclic_shift: int | None = None
    prach_sequence: np.ndarray | None = None


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
        self.spatial_layout = SpatialLayout.from_config(config)

    def _generate_payload(self, channel_type: str) -> np.ndarray:
        if channel_type.lower() == "prach":
            prach_cfg = self.config.get("prach", {})
            width = int(prach_cfg.get("preamble_id_bits", 6))
            preamble_id = int(prach_cfg.get("preamble_id", 0))
            return preamble_id_to_bits(preamble_id, width=width)
        if channel_type.lower() in {"control", "pdcch", "pucch"}:
            size = int(self.config.get("control_channel", {}).get("payload_bits", 128))
        else:
            size = int(self.config.get("transport_block", {}).get("size_bits", 1024))
        return self.rng.integers(0, 2, size=size, dtype=np.uint8)

    def _ofdm_modulate_view(self, active_grid: np.ndarray) -> np.ndarray:
        waveform = []
        for symbol in range(self.numerology.symbols_per_slot):
            bins = ResourceGrid(self.numerology, self.allocation, spatial_layout=self.spatial_layout).active_to_ifft_bins(
                active_grid[symbol]
            )
            time_symbol = np.fft.ifft(bins, n=self.numerology.fft_size)
            cp = time_symbol[-self.numerology.cp_length :]
            waveform.append(np.concatenate([cp, time_symbol]))
        return np.concatenate(waveform).astype(np.complex128)

    def _ofdm_modulate(self, grid: ResourceGrid) -> np.ndarray:
        port_waveforms = [
            self._ofdm_modulate_view(grid.port_view(port_index)) for port_index in range(grid.port_grid.shape[0])
        ]
        return np.stack(port_waveforms, axis=0) if port_waveforms else np.zeros((0, 0), dtype=np.complex128)

    def _transmit_prach(self, *, direction: str, payload: np.ndarray) -> TxResult:
        grid = ResourceGrid(self.numerology, self.allocation, spatial_layout=self.spatial_layout)
        prach_cfg = self.config.get("prach", {})
        preamble_id = bits_to_preamble_id(payload, width=int(prach_cfg.get("preamble_id_bits", 6)))
        mapping = grid.mapping_for(
            channel_type="prach",
            bits_per_symbol=1,
            modulation="PRACH",
            direction=direction,
        )
        prach_sequence = generate_prach_sequence(
            preamble_id,
            max(int(mapping.positions.shape[0]), 1),
            root_sequence_index=int(prach_cfg.get("root_sequence_index", 25)),
            cyclic_shift=int(prach_cfg.get("cyclic_shift", 13)),
        )
        if mapping.positions.shape[0]:
            grid.map_symbols(prach_sequence, mapping.positions)
        tx_grid_data = grid.grid.copy()
        port_waveforms = self._ofdm_modulate(grid)
        waveform = port_waveforms[0].copy() if port_waveforms.size else np.array([], dtype=np.complex128)
        coding_metadata = CodingMetadata(
            channel_type="prach",
            crc_type="crc8",
            payload_length=int(payload.size),
            rate_matched_length=int(payload.size),
            mother_length=int(payload.size),
            redundancy_version=0,
            tb_crc_width=0,
            code_block_count=1,
            code_block_payload_lengths=(int(payload.size),),
            code_block_with_crc_lengths=(int(payload.size),),
            mother_block_lengths=(int(payload.size),),
            transport_block_with_crc=payload.copy(),
            code_block_payloads=(payload.copy(),),
            code_blocks_with_crc=(payload.copy(),),
            mother_code_blocks=(payload.copy(),),
        )
        empty_dmrs = {
            "positions": np.zeros((0, 2), dtype=int),
            "symbols": np.array([], dtype=np.complex128),
            "port": 0,
        }
        empty_rs = {
            "positions": np.zeros((0, 2), dtype=int),
            "symbols": np.array([], dtype=np.complex128),
            "port": 0,
        }
        return TxResult(
            waveform=waveform,
            metadata=TxMetadata(
                direction=direction,
                channel_type="prach",
                numerology=self.numerology,
                allocation=self.allocation,
                spatial_layout=self.spatial_layout,
                transform_precoding_enabled=False,
                payload_bits=payload,
                coded_bits=payload.copy(),
                scrambled_bits=payload.copy(),
                scrambling_sequence=np.zeros(payload.size, dtype=np.uint8),
                coding_metadata=coding_metadata,
                modulation="PRACH",
                mapper=PrachMapper(prach_sequence),
                mapping=mapping,
                dmrs=empty_dmrs,
                csi_rs=empty_rs.copy(),
                srs=empty_rs.copy(),
                tensor_view_specs=grid.tensor_view_specs_as_dict(),
                modulation_symbols=prach_sequence.copy(),
                tx_layer_grid=grid.layer_grid.copy(),
                tx_port_grid=grid.port_grid.copy(),
                tx_grid_data=tx_grid_data,
                tx_grid=grid.grid.copy(),
                tx_symbols=prach_sequence.copy(),
                tx_port_waveforms=port_waveforms.copy(),
                sample_rate=self.numerology.sample_rate,
                prach_preamble_id=int(preamble_id),
                prach_root_sequence_index=int(prach_cfg.get("root_sequence_index", 25)),
                prach_cyclic_shift=int(prach_cfg.get("cyclic_shift", 13)),
                prach_sequence=prach_sequence.copy(),
            ),
        )

    def transmit(self, channel_type: str = "data", payload_bits: np.ndarray | None = None) -> TxResult:
        channel_type = channel_type.lower()
        direction = str(self.config.get("link", {}).get("direction", "downlink")).lower()
        if direction not in {"downlink", "uplink"}:
            raise ValueError(f"Unsupported link.direction: {direction}")

        payload = np.asarray(payload_bits, dtype=np.uint8) if payload_bits is not None else self._generate_payload(channel_type)
        if channel_type == "prach":
            return self._transmit_prach(direction=direction, payload=payload)
        transform_precoding_enabled = bool(self.config.get("uplink", {}).get("transform_precoding", False)) and direction == "uplink" and channel_type in {"data", "pusch"}

        modulation_name = str(
            self.config.get("modulation", {}).get(
                "scheme",
                self.config.get("control_channel", {}).get("modulation", "QPSK")
                if channel_type in {"control", "pdcch", "pucch"}
                else "QPSK",
            )
        ).upper()
        mapper = ModulationMapper(modulation_name)

        grid = ResourceGrid(self.numerology, self.allocation, spatial_layout=self.spatial_layout)
        mapping = grid.mapping_for(
            channel_type=channel_type,
            bits_per_symbol=bits_per_symbol(modulation_name),
            modulation=modulation_name,
            direction=direction,
        )

        coder = build_channel_coder(channel_type=channel_type, config=self.config)
        coded_bits, coding_metadata = coder.encode(payload_bits=payload, target_length=mapping.bits_capacity)
        scrambling_cfg = self.config.get("scrambling", {})
        scrambled_bits, scrambling_sequence = scramble_bits(
            coded_bits,
            nid=int(scrambling_cfg.get("nid", 1)),
            rnti=int(scrambling_cfg.get("rnti", 0x1234)),
            q=0 if channel_type in {"data", "pdsch", "pusch"} else 1,
        )
        modulation_symbols = mapper.map_bits(scrambled_bits)
        tx_symbols = apply_transform_precoding(modulation_symbols) if transform_precoding_enabled else modulation_symbols.copy()
        grid.map_symbols(tx_symbols, mapping.positions)
        tx_grid_data = grid.grid.copy()
        reference_cfg = self.config.get("reference_signals", {})
        insert_csi_rs = bool(reference_cfg.get("enable_csi_rs", True)) and direction == "downlink" and channel_type in {"data", "pdsch", "control", "pdcch"}
        insert_srs = bool(reference_cfg.get("enable_srs", True)) and direction == "uplink" and channel_type in {"data", "pusch"}
        csi_rs = (
            grid.insert_csi_rs(slot=0, seed=int(reference_cfg.get("sequence_seed", 73)))
            if insert_csi_rs
            else {"positions": np.zeros((0, 2), dtype=int), "symbols": np.array([], dtype=np.complex128), "port": 0}
        )
        srs = (
            grid.insert_srs(slot=0, seed=int(reference_cfg.get("sequence_seed", 73)))
            if insert_srs
            else {"positions": np.zeros((0, 2), dtype=int), "symbols": np.array([], dtype=np.complex128), "port": 0}
        )
        dmrs = grid.insert_dmrs(slot=0)
        port_waveforms = self._ofdm_modulate(grid)
        waveform = port_waveforms[0].copy()

        return TxResult(
            waveform=waveform,
            metadata=TxMetadata(
                direction=direction,
                channel_type=channel_type,
                numerology=self.numerology,
                allocation=self.allocation,
                spatial_layout=self.spatial_layout,
                transform_precoding_enabled=transform_precoding_enabled,
                payload_bits=payload,
                coded_bits=coded_bits,
                scrambled_bits=scrambled_bits,
                scrambling_sequence=scrambling_sequence,
                coding_metadata=coding_metadata,
                modulation=modulation_name,
                mapper=mapper,
                mapping=mapping,
                dmrs=dmrs,
                csi_rs=csi_rs,
                srs=srs,
                tensor_view_specs=grid.tensor_view_specs_as_dict(),
                modulation_symbols=modulation_symbols,
                tx_layer_grid=grid.layer_grid.copy(),
                tx_port_grid=grid.port_grid.copy(),
                tx_grid_data=tx_grid_data,
                tx_grid=grid.grid.copy(),
                tx_symbols=tx_symbols,
                tx_port_waveforms=port_waveforms.copy(),
                sample_rate=self.numerology.sample_rate,
            ),
        )
