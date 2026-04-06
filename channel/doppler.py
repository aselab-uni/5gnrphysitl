from __future__ import annotations

import numpy as np


def apply_doppler_rotation(
    waveform: np.ndarray,
    doppler_hz: float,
    sample_rate: float,
    initial_phase: float = 0.0,
) -> np.ndarray:
    if abs(doppler_hz) < 1e-12:
        return waveform
    time = np.arange(waveform.size) / sample_rate
    return waveform * np.exp(1j * (2.0 * np.pi * doppler_hz * time + initial_phase))
