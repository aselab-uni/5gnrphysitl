from __future__ import annotations

import numpy as np


def free_space_path_loss_db(distance_m: float, carrier_frequency_hz: float) -> float:
    distance_m = max(distance_m, 1.0)
    carrier_frequency_hz = max(carrier_frequency_hz, 1.0)
    c = 299_792_458.0
    return float(20.0 * np.log10(4.0 * np.pi * distance_m * carrier_frequency_hz / c))


def log_normal_shadowing_db(std_db: float, rng: np.random.Generator) -> float:
    if std_db <= 0:
        return 0.0
    return float(rng.normal(0.0, std_db))


def apply_path_loss(waveform: np.ndarray, total_loss_db: float) -> np.ndarray:
    gain = 10 ** (-total_loss_db / 20.0)
    return waveform * gain
