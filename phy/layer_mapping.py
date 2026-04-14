from __future__ import annotations

from typing import Iterable

import numpy as np


def layer_map_symbols(symbols: np.ndarray, num_layers: int) -> np.ndarray:
    num_layers = max(int(num_layers), 1)
    view = np.asarray(symbols, dtype=np.complex128).reshape(-1)
    if num_layers == 1:
        return view.reshape(1, -1).copy()
    if view.size == 0:
        return np.zeros((num_layers, 0), dtype=np.complex128)
    per_layer = int(np.ceil(view.size / num_layers))
    padded = np.pad(view, (0, per_layer * num_layers - view.size))
    layer_matrix = padded.reshape(per_layer, num_layers).T
    return layer_matrix.astype(np.complex128, copy=True)


def combine_layer_symbols(layer_symbols: np.ndarray | Iterable[np.ndarray], total_symbols: int | None = None) -> np.ndarray:
    if isinstance(layer_symbols, np.ndarray):
        matrix = np.asarray(layer_symbols, dtype=np.complex128)
    else:
        streams = [np.asarray(stream, dtype=np.complex128).reshape(-1) for stream in layer_symbols]
        if not streams:
            return np.array([], dtype=np.complex128)
        max_len = max(stream.size for stream in streams)
        matrix = np.zeros((len(streams), max_len), dtype=np.complex128)
        for index, stream in enumerate(streams):
            matrix[index, : stream.size] = stream
    if matrix.ndim == 1:
        combined = matrix.reshape(-1)
    elif matrix.size == 0:
        combined = np.array([], dtype=np.complex128)
    else:
        combined = matrix.T.reshape(-1)
    if total_symbols is None:
        return combined
    return combined[: max(int(total_symbols), 0)]


def expand_positions_for_layers(positions: np.ndarray, num_layers: int, total_symbols: int | None = None) -> np.ndarray:
    position_view = np.asarray(positions, dtype=int)
    if position_view.ndim != 2 or position_view.shape[1] != 2:
        return np.zeros((0, 2), dtype=int)
    repeated = np.repeat(position_view, max(int(num_layers), 1), axis=0)
    if total_symbols is None:
        return repeated
    return repeated[: max(int(total_symbols), 0)]
