from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np

from .types import SpatialLayout


@dataclass(slots=True, frozen=True)
class PrecoderSpec:
    mode: str
    matrix: np.ndarray


def build_precoder(config: Mapping[str, Any] | None, spatial_layout: SpatialLayout) -> PrecoderSpec:
    precoding_cfg = dict(config.get("precoding", {})) if config else {}
    mode = str(precoding_cfg.get("mode", "identity")).lower()
    num_layers = int(spatial_layout.num_layers)
    num_ports = int(spatial_layout.num_ports)

    if mode == "identity":
        matrix = np.zeros((num_ports, num_layers), dtype=np.complex128)
        diagonal = min(num_ports, num_layers)
        matrix[np.arange(diagonal), np.arange(diagonal)] = 1.0 + 0.0j
        return PrecoderSpec(mode="identity", matrix=matrix)

    if mode == "dft":
        row_index = np.arange(num_ports, dtype=np.float64)[:, None]
        col_index = np.arange(num_layers, dtype=np.float64)[None, :]
        matrix = np.exp(-1j * 2.0 * np.pi * row_index * col_index / max(num_ports, 1))
        matrix /= np.sqrt(max(num_layers, 1))
        return PrecoderSpec(mode="dft", matrix=matrix.astype(np.complex128))

    raise ValueError(f"Unsupported precoding.mode: {mode}")


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
