from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class AwgnResult:
    waveform: np.ndarray
    noise_variance: float


class AWGNChannel:
    def __init__(self, snr_db: float, seed: int | None = None) -> None:
        self.snr_db = float(snr_db)
        self.rng = np.random.default_rng(seed)

    def apply(self, waveform: np.ndarray) -> AwgnResult:
        signal_power = float(np.mean(np.abs(waveform) ** 2))
        snr_linear = 10 ** (self.snr_db / 10.0)
        noise_variance = signal_power / max(snr_linear, 1e-12)
        noise = np.sqrt(noise_variance / 2.0) * (
            self.rng.standard_normal(waveform.size) + 1j * self.rng.standard_normal(waveform.size)
        )
        return AwgnResult(waveform=waveform + noise, noise_variance=noise_variance)
