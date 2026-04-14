from __future__ import annotations

from typing import Dict

import numpy as np


def apply_cfo(waveform: np.ndarray, cfo_hz: float, sample_rate: float) -> np.ndarray:
    if abs(cfo_hz) < 1e-12:
        return waveform
    view = np.asarray(waveform, dtype=np.complex128)
    time = np.arange(view.shape[-1]) / sample_rate
    return view * np.exp(1j * 2.0 * np.pi * cfo_hz * time)


def apply_sto(waveform: np.ndarray, sto_samples: int) -> np.ndarray:
    if sto_samples == 0:
        return waveform
    view = np.asarray(waveform)
    if sto_samples > 0:
        pad_shape = (*view.shape[:-1], sto_samples)
        return np.concatenate([np.zeros(pad_shape, dtype=view.dtype), view], axis=-1)
    return view[..., abs(sto_samples) :]


def apply_phase_noise(waveform: np.ndarray, std_per_sample: float, rng: np.random.Generator) -> np.ndarray:
    if std_per_sample <= 0:
        return waveform
    view = np.asarray(waveform, dtype=np.complex128)
    phase = np.cumsum(rng.normal(0.0, std_per_sample, size=view.shape), axis=-1)
    return view * np.exp(1j * phase)


def apply_iq_imbalance(waveform: np.ndarray, gain_imbalance_db: float, phase_imbalance_deg: float = 2.0) -> np.ndarray:
    if abs(gain_imbalance_db) < 1e-12:
        return waveform
    gain = 10 ** (gain_imbalance_db / 20.0)
    phase = np.deg2rad(phase_imbalance_deg)
    i = waveform.real * gain
    q = waveform.imag * np.exp(1j * phase).real
    return i + 1j * q


def apply_impairments(waveform: np.ndarray, config: Dict, sample_rate: float, rng: np.random.Generator) -> np.ndarray:
    channel_cfg = config.get("channel", {})
    distorted = apply_sto(waveform, int(channel_cfg.get("sto_samples", 0)))
    distorted = apply_cfo(distorted, float(channel_cfg.get("cfo_hz", 0.0)), sample_rate)
    distorted = apply_phase_noise(distorted, float(channel_cfg.get("phase_noise_std", 0.0)), rng)
    distorted = apply_iq_imbalance(distorted, float(channel_cfg.get("iq_imbalance_db", 0.0)))
    return distorted
