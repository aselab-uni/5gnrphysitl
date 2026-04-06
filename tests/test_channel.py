from __future__ import annotations

import numpy as np

from channel.awgn_channel import AWGNChannel
from channel.fading_channel import FadingChannel


def test_awgn_channel_preserves_shape() -> None:
    waveform = np.ones(1024, dtype=np.complex128)
    result = AWGNChannel(snr_db=20, seed=1).apply(waveform)
    assert result.waveform.shape == waveform.shape
    assert result.noise_variance > 0


def test_fading_channel_returns_impulse_response() -> None:
    config = {
        "carrier": {"center_frequency_hz": 3.5e9},
        "channel": {
            "profile": "pedestrian",
            "model": "rayleigh",
            "fading_type": "rayleigh",
            "delay_spread_s": 7.1e-7,
            "doppler_hz": 5.0,
            "distance_m": 100.0,
            "path_loss_db": 0.0,
            "shadowing_std_db": 0.0,
        },
    }
    waveform = np.ones(1024, dtype=np.complex128)
    result = FadingChannel(config, sample_rate=15.36e6, fft_size=512, seed=1).apply(waveform)
    assert result.waveform.shape == waveform.shape
    assert result.impulse_response.size >= 1
