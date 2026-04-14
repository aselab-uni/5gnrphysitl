from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np

from .types import SpatialLayout


@dataclass(slots=True, frozen=True)
class PrecoderSpec:
    mode: str
    matrix: np.ndarray


def build_precoder_matrix(mode: str, num_ports: int, num_layers: int) -> np.ndarray:
    resolved_mode = str(mode).lower()
    port_count = int(num_ports)
    layer_count = int(num_layers)

    if resolved_mode == "identity":
        matrix = np.zeros((port_count, layer_count), dtype=np.complex128)
        diagonal = min(port_count, layer_count)
        matrix[np.arange(diagonal), np.arange(diagonal)] = 1.0 + 0.0j
        return matrix

    if resolved_mode == "dft":
        row_index = np.arange(port_count, dtype=np.float64)[:, None]
        col_index = np.arange(layer_count, dtype=np.float64)[None, :]
        matrix = np.exp(-1j * 2.0 * np.pi * row_index * col_index / max(port_count, 1))
        matrix /= np.sqrt(max(layer_count, 1))
        return matrix.astype(np.complex128)

    raise ValueError(f"Unsupported precoding.mode: {resolved_mode}")


def build_precoder(config: Mapping[str, Any] | None, spatial_layout: SpatialLayout) -> PrecoderSpec:
    precoding_cfg = dict(config.get("precoding", {})) if config else {}
    mode = str(precoding_cfg.get("mode", "identity")).lower()
    num_layers = int(spatial_layout.num_layers)
    num_ports = int(spatial_layout.num_ports)
    return PrecoderSpec(mode=mode, matrix=build_precoder_matrix(mode, num_ports=num_ports, num_layers=num_layers))


def apply_precoder(layer_symbols: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    layer_view = np.asarray(layer_symbols, dtype=np.complex128)
    precoder = np.asarray(matrix, dtype=np.complex128)
    if layer_view.ndim != 2:
        raise ValueError("layer_symbols must have shape (layer, symbol_index).")
    if precoder.ndim != 2:
        raise ValueError("precoder matrix must be 2-D.")
    if layer_view.shape[0] != precoder.shape[1]:
        raise ValueError("layer_symbols and precoder matrix have incompatible layer dimensions.")
    return precoder @ layer_view


def recover_layers_from_ports(port_symbols: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    port_view = np.asarray(port_symbols, dtype=np.complex128)
    precoder = np.asarray(matrix, dtype=np.complex128)
    if port_view.ndim != 2:
        raise ValueError("port_symbols must have shape (port, symbol_index).")
    if precoder.ndim != 2:
        raise ValueError("precoder matrix must be 2-D.")
    if port_view.shape[0] != precoder.shape[0]:
        raise ValueError("port_symbols and precoder matrix have incompatible port dimensions.")
    recovery = np.linalg.pinv(precoder)
    return recovery @ port_view
