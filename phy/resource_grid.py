from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np

from .dmrs import dmrs_pattern
from .frame_structure import FrameAllocation
from .numerology import NumerologyConfig
from .reference_signals import comb_positions, qpsk_reference_sequence
from .types import SpatialLayout, TensorViewSpec


@dataclass(slots=True)
class ChannelMapping:
    positions: np.ndarray
    bits_capacity: int
    modulation: str


class ResourceGrid:
    """Single-slot active-subcarrier resource grid with layer/port/RX views."""

    def __init__(
        self,
        numerology: NumerologyConfig,
        allocation: FrameAllocation,
        spatial_layout: SpatialLayout | None = None,
    ) -> None:
        self.numerology = numerology
        self.allocation = allocation
        self.spatial_layout = spatial_layout or SpatialLayout()
        grid_shape = (numerology.symbols_per_slot, numerology.active_subcarriers)
        self.layer_grid = np.zeros(
            (self.spatial_layout.num_layers, *grid_shape),
            dtype=np.complex128,
        )
        self.port_grid = np.zeros(
            (self.spatial_layout.num_ports, *grid_shape),
            dtype=np.complex128,
        )
        self.rx_grid_tensor = np.zeros(
            (self.spatial_layout.num_rx_antennas, *grid_shape),
            dtype=np.complex128,
        )

    @property
    def shape(self) -> tuple[int, int]:
        return self.grid.shape

    @property
    def grid(self) -> np.ndarray:
        return self.port_grid[0]

    @grid.setter
    def grid(self, value: np.ndarray) -> None:
        self.port_grid[0, :, :] = np.asarray(value, dtype=np.complex128)

    def layer_view(self, layer: int = 0) -> np.ndarray:
        return self.layer_grid[int(layer)]

    def port_view(self, port: int = 0) -> np.ndarray:
        return self.port_grid[int(port)]

    def rx_view(self, rx_ant: int = 0) -> np.ndarray:
        return self.rx_grid_tensor[int(rx_ant)]

    def tensor_view_specs(self) -> dict[str, TensorViewSpec]:
        return {
            "layer_grid": TensorViewSpec(
                name="layer_grid",
                axes=("layer", "symbol", "subcarrier"),
                shape=tuple(int(dim) for dim in self.layer_grid.shape),
                description="Layer-domain resource grid before precoding and port mapping.",
            ),
            "port_grid": TensorViewSpec(
                name="port_grid",
                axes=("port", "symbol", "subcarrier"),
                shape=tuple(int(dim) for dim in self.port_grid.shape),
                description="Antenna-port resource grid after layer-to-port mapping.",
            ),
            "rx_grid_tensor": TensorViewSpec(
                name="rx_grid_tensor",
                axes=("rx_ant", "symbol", "subcarrier"),
                shape=tuple(int(dim) for dim in self.rx_grid_tensor.shape),
                description="Per-receive-antenna FFT grid.",
            ),
        }

    def tensor_view_specs_as_dict(self) -> dict[str, dict[str, object]]:
        return {name: spec.as_dict() for name, spec in self.tensor_view_specs().items()}

    def pdcch_positions(self) -> np.ndarray:
        return self.search_space_positions()

    def coreset_positions(self) -> np.ndarray:
        positions = []
        for symbol in self.allocation.pdcch_symbols:
            if not (0 <= symbol < self.numerology.symbols_per_slot):
                continue
            for sc in range(self.allocation.coreset_subcarriers):
                positions.append((symbol, sc))
        return np.asarray(positions, dtype=int)

    def search_space_positions(self) -> np.ndarray:
        coreset = self.coreset_positions()
        if not coreset.size:
            return np.zeros((0, 2), dtype=int)
        stride = max(1, int(self.allocation.search_space_stride))
        offset = int(self.allocation.search_space_offset) % stride
        mask = (np.arange(coreset.shape[0]) % stride) == offset
        selected = coreset[mask]
        if not selected.size:
            selected = coreset[:1]
        return selected.astype(int, copy=False)

    def dmrs_positions(self) -> np.ndarray:
        positions = []
        for symbol in self.allocation.dmrs_symbols:
            if symbol < self.allocation.pdsch_start_symbol:
                continue
            subcarriers, _ = dmrs_pattern(self.numerology.active_subcarriers, dmrs_symbol=symbol)
            for sc in subcarriers:
                positions.append((symbol, sc))
        return np.asarray(positions, dtype=int)

    def csi_rs_positions(self) -> np.ndarray:
        return comb_positions(
            self.numerology.active_subcarriers,
            symbols=list(self.allocation.csi_rs_symbols),
            comb=int(self.allocation.rs_comb),
            offset=int(self.allocation.csi_rs_subcarrier_offset),
        )

    def srs_positions(self) -> np.ndarray:
        return comb_positions(
            self.numerology.active_subcarriers,
            symbols=list(self.allocation.srs_symbols),
            comb=int(self.allocation.rs_comb),
            offset=int(self.allocation.srs_subcarrier_offset),
        )

    def ptrs_positions(self, *, direction: str = "downlink", channel_type: str = "data") -> np.ndarray:
        direction = str(direction).lower()
        channel_type = str(channel_type).lower()
        if direction == "uplink":
            if channel_type not in {"data", "pusch"}:
                return np.zeros((0, 2), dtype=int)
            allowed_symbols = set(self.allocation.pusch_symbols(self.numerology))
        else:
            if channel_type not in {"data", "pdsch"}:
                return np.zeros((0, 2), dtype=int)
            allowed_symbols = set(self.allocation.pdsch_symbols(self.numerology))
        positions = comb_positions(
            self.numerology.active_subcarriers,
            symbols=[symbol for symbol in self.allocation.ptrs_symbols if symbol in allowed_symbols],
            comb=int(self.allocation.rs_comb),
            offset=int(self.allocation.ptrs_subcarrier_offset),
        )
        if not positions.size:
            return positions
        reserved = {tuple(position) for position in self.dmrs_positions().tolist()}
        if direction == "downlink":
            reserved.update(tuple(position) for position in self.csi_rs_positions().tolist())
        else:
            reserved.update(tuple(position) for position in self.srs_positions().tolist())
        filtered = [tuple(position) for position in positions.tolist() if tuple(position) not in reserved]
        return np.asarray(filtered, dtype=int) if filtered else np.zeros((0, 2), dtype=int)

    def ssb_positions(self) -> np.ndarray:
        positions = []
        ssb_subcarriers = min(self.allocation.ssb_subcarriers, self.numerology.active_subcarriers)
        for symbol in self.allocation.ssb_symbols:
            if not (0 <= symbol < self.numerology.symbols_per_slot):
                continue
            for sc in range(ssb_subcarriers):
                positions.append((symbol, sc))
        return np.asarray(positions, dtype=int) if positions else np.zeros((0, 2), dtype=int)

    def pss_positions(self) -> np.ndarray:
        symbols = self.allocation.ssb_symbols
        if not symbols:
            return np.zeros((0, 2), dtype=int)
        return np.asarray([(symbols[0], sc) for sc in range(min(self.allocation.ssb_subcarriers, self.numerology.active_subcarriers))], dtype=int)

    def sss_positions(self) -> np.ndarray:
        symbols = self.allocation.ssb_symbols
        if len(symbols) < 3:
            return np.zeros((0, 2), dtype=int)
        symbol = symbols[min(2, len(symbols) - 1)]
        return np.asarray([(symbol, sc) for sc in range(min(self.allocation.ssb_subcarriers, self.numerology.active_subcarriers))], dtype=int)

    def pbch_dmrs_positions(self) -> np.ndarray:
        symbols = self.allocation.ssb_symbols
        if len(symbols) < 2:
            return np.zeros((0, 2), dtype=int)
        pbch_dmrs_symbols = [symbols[1]]
        if len(symbols) >= 4:
            pbch_dmrs_symbols.append(symbols[3])
        return comb_positions(
            min(self.allocation.ssb_subcarriers, self.numerology.active_subcarriers),
            symbols=pbch_dmrs_symbols,
            comb=4,
            offset=int(self.allocation.pbch_dmrs_subcarrier_offset),
        )

    def pbch_positions(self) -> np.ndarray:
        symbols = self.allocation.ssb_symbols
        if len(symbols) < 2:
            return np.zeros((0, 2), dtype=int)
        pbch_symbols = [symbols[1]]
        if len(symbols) >= 4:
            pbch_symbols.append(symbols[3])
        pbch_positions = []
        reserved = {tuple(position) for position in self.pbch_dmrs_positions().tolist()}
        ssb_subcarriers = min(self.allocation.ssb_subcarriers, self.numerology.active_subcarriers)
        for symbol in pbch_symbols:
            for sc in range(ssb_subcarriers):
                if (symbol, sc) not in reserved:
                    pbch_positions.append((symbol, sc))
        return np.asarray(pbch_positions, dtype=int) if pbch_positions else np.zeros((0, 2), dtype=int)

    def pdsch_positions(self) -> np.ndarray:
        positions = []
        reserved = {tuple(position) for position in self.dmrs_positions().tolist()}
        reserved.update(tuple(position) for position in self.csi_rs_positions().tolist())
        reserved.update(tuple(position) for position in self.ptrs_positions(direction="downlink", channel_type="data").tolist())
        for symbol in self.allocation.pdsch_symbols(self.numerology):
            for sc in range(self.numerology.active_subcarriers):
                if (symbol, sc) not in reserved:
                    positions.append((symbol, sc))
        return np.asarray(positions, dtype=int)

    def pusch_positions(self) -> np.ndarray:
        positions = []
        reserved = {tuple(position) for position in self.dmrs_positions().tolist()}
        reserved.update(tuple(position) for position in self.srs_positions().tolist())
        reserved.update(tuple(position) for position in self.ptrs_positions(direction="uplink", channel_type="data").tolist())
        for symbol in self.allocation.pusch_symbols(self.numerology):
            for sc in range(self.numerology.active_subcarriers):
                if (symbol, sc) not in reserved:
                    positions.append((symbol, sc))
        return np.asarray(positions, dtype=int)

    def pucch_positions(self) -> np.ndarray:
        positions = []
        for symbol in self.allocation.pucch_symbols(self.numerology):
            for sc in range(self.numerology.active_subcarriers):
                positions.append((symbol, sc))
        return np.asarray(positions, dtype=int)

    def prach_positions(self) -> np.ndarray:
        positions = []
        subcarriers = min(self.allocation.prach_subcarriers, self.numerology.active_subcarriers)
        for symbol in self.allocation.prach_symbols(self.numerology):
            for sc in range(subcarriers):
                positions.append((symbol, sc))
        return np.asarray(positions, dtype=int)

    def control_re_mask(self) -> np.ndarray:
        mask = np.zeros(self.shape, dtype=np.uint8)
        positions = self.pdcch_positions()
        if positions.size:
            mask[positions[:, 0], positions[:, 1]] = 1
        return mask

    def coreset_re_mask(self) -> np.ndarray:
        mask = np.zeros(self.shape, dtype=np.uint8)
        positions = self.coreset_positions()
        if positions.size:
            mask[positions[:, 0], positions[:, 1]] = 1
        return mask

    def search_space_re_mask(self) -> np.ndarray:
        mask = np.zeros(self.shape, dtype=np.uint8)
        positions = self.search_space_positions()
        if positions.size:
            mask[positions[:, 0], positions[:, 1]] = 1
        return mask

    def dmrs_re_mask(self) -> np.ndarray:
        mask = np.zeros(self.shape, dtype=np.uint8)
        positions = self.dmrs_positions()
        if positions.size:
            mask[positions[:, 0], positions[:, 1]] = 1
        return mask

    def data_re_mask(self, *, direction: str = "downlink") -> np.ndarray:
        mask = np.zeros(self.shape, dtype=np.uint8)
        positions = self.pusch_positions() if str(direction).lower() == "uplink" else self.pdsch_positions()
        if positions.size:
            mask[positions[:, 0], positions[:, 1]] = 1
        return mask

    def re_masks(self, *, direction: str = "downlink") -> Dict[str, np.ndarray]:
        return {
            "control": self.control_re_mask(),
            "coreset": self.coreset_re_mask(),
            "search_space": self.search_space_re_mask(),
            "dmrs": self.dmrs_re_mask(),
            "data": self.data_re_mask(direction=direction),
            "prach": self.prach_re_mask(),
            "csi_rs": self.csi_rs_re_mask(),
            "srs": self.srs_re_mask(),
            "ptrs": self.ptrs_re_mask(direction=direction),
            "ssb": self.ssb_re_mask(),
        }

    def prach_re_mask(self) -> np.ndarray:
        mask = np.zeros(self.shape, dtype=np.uint8)
        positions = self.prach_positions()
        if positions.size:
            mask[positions[:, 0], positions[:, 1]] = 1
        return mask

    def mapping_for(self, channel_type: str, bits_per_symbol: int, modulation: str, *, direction: str = "downlink") -> ChannelMapping:
        channel_type = channel_type.lower()
        direction = str(direction).lower()
        if direction == "uplink":
            if channel_type == "prach":
                positions = self.prach_positions()
            else:
                positions = self.pucch_positions() if channel_type in {"control", "pucch"} else self.pusch_positions()
        elif channel_type in {"pbch", "broadcast"}:
            positions = self.pbch_positions()
        elif channel_type in {"control", "pdcch"}:
            positions = self.pdcch_positions()
        else:
            positions = self.pdsch_positions()
        return ChannelMapping(
            positions=positions,
            bits_capacity=positions.shape[0] * bits_per_symbol * max(int(self.spatial_layout.num_layers), 1),
            modulation=modulation,
        )

    def csi_rs_re_mask(self) -> np.ndarray:
        mask = np.zeros(self.shape, dtype=np.uint8)
        positions = self.csi_rs_positions()
        if positions.size:
            mask[positions[:, 0], positions[:, 1]] = 1
        return mask

    def srs_re_mask(self) -> np.ndarray:
        mask = np.zeros(self.shape, dtype=np.uint8)
        positions = self.srs_positions()
        if positions.size:
            mask[positions[:, 0], positions[:, 1]] = 1
        return mask

    def ptrs_re_mask(self, *, direction: str = "downlink", channel_type: str = "data") -> np.ndarray:
        mask = np.zeros(self.shape, dtype=np.uint8)
        positions = self.ptrs_positions(direction=direction, channel_type=channel_type)
        if positions.size:
            mask[positions[:, 0], positions[:, 1]] = 1
        return mask

    def ssb_re_mask(self) -> np.ndarray:
        mask = np.zeros(self.shape, dtype=np.uint8)
        positions = self.ssb_positions()
        if positions.size:
            mask[positions[:, 0], positions[:, 1]] = 1
        return mask

    def map_symbols(
        self,
        symbols: np.ndarray,
        positions: np.ndarray,
        *,
        layer: int = 0,
        port: int = 0,
    ) -> None:
        positions = np.asarray(positions, dtype=int)
        count = min(symbols.size, positions.shape[0])
        if count <= 0:
            return
        self.layer_grid[layer, positions[:count, 0], positions[:count, 1]] = symbols[:count]
        self.port_grid[port, positions[:count, 0], positions[:count, 1]] = symbols[:count]

    def map_layer_streams(
        self,
        layer_symbols: np.ndarray,
        positions: np.ndarray,
        *,
        port_symbols: np.ndarray | None = None,
    ) -> None:
        layer_matrix = np.asarray(layer_symbols, dtype=np.complex128)
        if layer_matrix.ndim != 2:
            raise ValueError("layer_symbols must have shape (layer, symbol_index).")
        positions = np.asarray(positions, dtype=int)
        max_layers = min(layer_matrix.shape[0], self.layer_grid.shape[0])
        if max_layers <= 0 or positions.size == 0:
            return
        for layer_index in range(max_layers):
            count = min(layer_matrix.shape[1], positions.shape[0])
            if count > 0:
                self.layer_grid[layer_index, positions[:count, 0], positions[:count, 1]] = layer_matrix[layer_index, :count]
        if port_symbols is None:
            port_matrix = layer_matrix
        else:
            port_matrix = np.asarray(port_symbols, dtype=np.complex128)
            if port_matrix.ndim != 2:
                raise ValueError("port_symbols must have shape (port, symbol_index).")
        max_ports = min(port_matrix.shape[0], self.port_grid.shape[0])
        for port_index in range(max_ports):
            count = min(port_matrix.shape[1], positions.shape[0])
            if count > 0:
                self.port_grid[port_index, positions[:count, 0], positions[:count, 1]] = port_matrix[port_index, :count]

    def extract_symbols(self, positions: np.ndarray, *, domain: str = "port", index: int = 0) -> np.ndarray:
        positions = np.asarray(positions, dtype=int)
        domain_name = str(domain).lower()
        if domain_name == "layer":
            view = self.layer_view(index)
        elif domain_name == "rx":
            view = self.rx_view(index)
        else:
            view = self.port_view(index)
        return view[positions[:, 0], positions[:, 1]]

    def insert_dmrs(self, slot: int = 0, *, port: int = 0) -> Dict[str, np.ndarray]:
        inserted = []
        port_view = self.port_view(port)
        for symbol in self.allocation.dmrs_symbols:
            if symbol < self.allocation.pdsch_start_symbol:
                continue
            subcarriers, sequence = dmrs_pattern(self.numerology.active_subcarriers, dmrs_symbol=symbol, slot=slot)
            port_view[symbol, subcarriers] = sequence
            inserted.extend([(symbol, sc) for sc in subcarriers])
        position_array = np.asarray(inserted, dtype=int) if inserted else np.zeros((0, 2), dtype=int)
        return {
            "positions": position_array,
            "symbols": port_view[position_array[:, 0], position_array[:, 1]]
            if inserted
            else np.array([], dtype=np.complex128),
            "port": int(port),
        }

    def insert_csi_rs(self, slot: int = 0, *, port: int = 0, seed: int = 73) -> Dict[str, np.ndarray]:
        positions = self.csi_rs_positions()
        if not positions.size:
            return {"positions": np.zeros((0, 2), dtype=int), "symbols": np.array([], dtype=np.complex128), "port": int(port)}
        port_view = self.port_view(port)
        symbols = []
        for symbol in sorted({int(value) for value in positions[:, 0].tolist()}):
            symbol_mask = positions[:, 0] == symbol
            symbol_positions = positions[symbol_mask]
            sequence = qpsk_reference_sequence(symbol_positions.shape[0], slot=slot, symbol=symbol, seed=int(seed))
            port_view[symbol_positions[:, 0], symbol_positions[:, 1]] = sequence
            symbols.append(sequence)
        return {
            "positions": positions.copy(),
            "symbols": np.concatenate(symbols) if symbols else np.array([], dtype=np.complex128),
            "port": int(port),
        }

    def insert_srs(self, slot: int = 0, *, port: int = 0, seed: int = 73) -> Dict[str, np.ndarray]:
        positions = self.srs_positions()
        if not positions.size:
            return {"positions": np.zeros((0, 2), dtype=int), "symbols": np.array([], dtype=np.complex128), "port": int(port)}
        port_view = self.port_view(port)
        symbols = []
        for symbol in sorted({int(value) for value in positions[:, 0].tolist()}):
            symbol_mask = positions[:, 0] == symbol
            symbol_positions = positions[symbol_mask]
            sequence = qpsk_reference_sequence(symbol_positions.shape[0], slot=slot, symbol=symbol, seed=int(seed) + 1000)
            port_view[symbol_positions[:, 0], symbol_positions[:, 1]] = sequence
            symbols.append(sequence)
        return {
            "positions": positions.copy(),
            "symbols": np.concatenate(symbols) if symbols else np.array([], dtype=np.complex128),
            "port": int(port),
        }

    def insert_ptrs(
        self,
        slot: int = 0,
        *,
        port: int = 0,
        seed: int = 73,
        direction: str = "downlink",
        channel_type: str = "data",
    ) -> Dict[str, np.ndarray]:
        positions = self.ptrs_positions(direction=direction, channel_type=channel_type)
        if not positions.size:
            return {"positions": np.zeros((0, 2), dtype=int), "symbols": np.array([], dtype=np.complex128), "port": int(port)}
        port_view = self.port_view(port)
        symbols = []
        for symbol in sorted({int(value) for value in positions[:, 0].tolist()}):
            symbol_mask = positions[:, 0] == symbol
            symbol_positions = positions[symbol_mask]
            sequence = qpsk_reference_sequence(symbol_positions.shape[0], slot=slot, symbol=symbol, seed=int(seed) + 2000)
            port_view[symbol_positions[:, 0], symbol_positions[:, 1]] = sequence
            symbols.append(sequence)
        return {
            "positions": positions.copy(),
            "symbols": np.concatenate(symbols) if symbols else np.array([], dtype=np.complex128),
            "port": int(port),
        }

    def insert_ssb(self, slot: int = 0, *, port: int = 0, seed: int = 73) -> Dict[str, np.ndarray]:
        port_view = self.port_view(port)
        pss_positions = self.pss_positions()
        sss_positions = self.sss_positions()
        pbch_dmrs_positions = self.pbch_dmrs_positions()
        if not (pss_positions.size or sss_positions.size or pbch_dmrs_positions.size):
            return {
                "positions": np.zeros((0, 2), dtype=int),
                "symbols": np.array([], dtype=np.complex128),
                "pss_positions": np.zeros((0, 2), dtype=int),
                "sss_positions": np.zeros((0, 2), dtype=int),
                "pbch_dmrs_positions": np.zeros((0, 2), dtype=int),
                "pbch_dmrs_symbols": np.array([], dtype=np.complex128),
                "port": int(port),
            }

        def _bpsk(length: int, seed_offset: int) -> np.ndarray:
            qpsk = qpsk_reference_sequence(length, slot=slot, symbol=seed_offset, seed=int(seed) + seed_offset)
            return np.sign(np.real(qpsk)).astype(np.float64).astype(np.complex128)

        pss_symbols = _bpsk(pss_positions.shape[0], 3000) if pss_positions.size else np.array([], dtype=np.complex128)
        sss_symbols = _bpsk(sss_positions.shape[0], 4000) if sss_positions.size else np.array([], dtype=np.complex128)
        pbch_dmrs_symbols = (
            qpsk_reference_sequence(pbch_dmrs_positions.shape[0], slot=slot, symbol=5000, seed=int(seed) + 5000)
            if pbch_dmrs_positions.size
            else np.array([], dtype=np.complex128)
        )
        if pss_positions.size:
            port_view[pss_positions[:, 0], pss_positions[:, 1]] = pss_symbols
        if sss_positions.size:
            port_view[sss_positions[:, 0], sss_positions[:, 1]] = sss_symbols
        if pbch_dmrs_positions.size:
            port_view[pbch_dmrs_positions[:, 0], pbch_dmrs_positions[:, 1]] = pbch_dmrs_symbols
        all_positions = np.concatenate(
            [array for array in (pss_positions, sss_positions, pbch_dmrs_positions) if array.size],
            axis=0,
        )
        all_symbols = np.concatenate(
            [array for array in (pss_symbols, sss_symbols, pbch_dmrs_symbols) if array.size]
        )
        return {
            "positions": all_positions,
            "symbols": all_symbols,
            "pss_positions": pss_positions.copy(),
            "sss_positions": sss_positions.copy(),
            "pbch_dmrs_positions": pbch_dmrs_positions.copy(),
            "pbch_dmrs_symbols": pbch_dmrs_symbols.copy(),
            "port": int(port),
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
