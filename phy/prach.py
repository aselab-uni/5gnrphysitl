from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def preamble_id_to_bits(preamble_id: int, width: int = 6) -> np.ndarray:
    value = max(0, int(preamble_id)) % (1 << int(width))
    return np.array([(value >> shift) & 1 for shift in range(width - 1, -1, -1)], dtype=np.uint8)


def bits_to_preamble_id(bits: np.ndarray, width: int = 6) -> int:
    view = np.asarray(bits, dtype=np.uint8).reshape(-1)[: int(width)]
    if view.size < int(width):
        view = np.pad(view, (0, int(width) - view.size))
    value = 0
    for bit in view:
        value = (value << 1) | int(bit)
    return int(value)


def zadoff_chu_sequence(length: int, root_sequence_index: int) -> np.ndarray:
    sequence_length = max(int(length), 1)
    root = max(1, int(root_sequence_index)) % sequence_length
    indices = np.arange(sequence_length, dtype=np.float64)
    return np.exp(-1j * np.pi * root * indices * (indices + 1.0) / sequence_length).astype(np.complex128)


def generate_prach_sequence(
    preamble_id: int,
    length: int,
    *,
    root_sequence_index: int = 25,
    cyclic_shift: int = 13,
) -> np.ndarray:
    base_sequence = zadoff_chu_sequence(length, root_sequence_index=root_sequence_index)
    shift = (int(preamble_id) * max(int(cyclic_shift), 1)) % max(int(length), 1)
    return np.roll(base_sequence, shift)


@dataclass(slots=True)
class PrachDetection:
    detected: bool
    detected_preamble_id: int
    metric: float
    candidate_metrics: np.ndarray


class PrachMapper:
    """Compatibility shim for GUI paths that expect a mapper-like object."""

    def __init__(self, sequence: np.ndarray) -> None:
        self.modulation = "PRACH"
        self.bits_per_symbol = 0
        self.constellation = np.asarray(sequence, dtype=np.complex128).reshape(-1)
        self.labels = np.zeros((0, 0), dtype=np.uint8)

    def map_bits(self, bits: np.ndarray) -> np.ndarray:  # pragma: no cover - PRACH bypasses bit mapping.
        return np.asarray(bits, dtype=np.complex128)

    def demap_llr(self, symbols: np.ndarray, noise_variance: float) -> np.ndarray:
        return np.array([], dtype=np.float64)

    def hard_demodulate(self, symbols: np.ndarray) -> np.ndarray:
        return np.array([], dtype=np.uint8)


def detect_prach_preamble(
    symbols: np.ndarray,
    *,
    num_preambles: int = 64,
    root_sequence_index: int = 25,
    cyclic_shift: int = 13,
    threshold: float = 0.45,
) -> PrachDetection:
    view = np.asarray(symbols, dtype=np.complex128).reshape(-1)
    candidate_count = max(1, int(num_preambles))
    if view.size == 0:
        return PrachDetection(
            detected=False,
            detected_preamble_id=0,
            metric=0.0,
            candidate_metrics=np.zeros(candidate_count, dtype=np.float64),
        )

    view_norm = np.linalg.norm(view)
    metrics = np.zeros(candidate_count, dtype=np.float64)
    if view_norm <= 0:
        return PrachDetection(
            detected=False,
            detected_preamble_id=0,
            metric=0.0,
            candidate_metrics=metrics,
        )

    for preamble_id in range(candidate_count):
        candidate = generate_prach_sequence(
            preamble_id,
            view.size,
            root_sequence_index=root_sequence_index,
            cyclic_shift=cyclic_shift,
        )
        denominator = np.linalg.norm(candidate) * view_norm + 1e-12
        metrics[preamble_id] = float(np.abs(np.vdot(candidate, view)) / denominator)

    detected_preamble_id = int(np.argmax(metrics))
    best_metric = float(metrics[detected_preamble_id])
    return PrachDetection(
        detected=bool(best_metric >= float(threshold)),
        detected_preamble_id=detected_preamble_id,
        metric=best_metric,
        candidate_metrics=metrics,
    )
