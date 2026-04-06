from __future__ import annotations

import numpy as np


def equalize(
    rx_symbols: np.ndarray,
    channel_estimate: np.ndarray,
    noise_variance: float,
    mode: str = "mmse",
) -> np.ndarray:
    mode = mode.lower()
    if mode == "zf":
        return rx_symbols / np.where(np.abs(channel_estimate) < 1e-9, 1.0, channel_estimate)
    denominator = np.abs(channel_estimate) ** 2 + max(float(noise_variance), 1e-9)
    return np.conj(channel_estimate) * rx_symbols / denominator
