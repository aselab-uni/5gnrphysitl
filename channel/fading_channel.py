from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np

from .doppler import apply_doppler_rotation
from .pathloss import apply_path_loss, free_space_path_loss_db, log_normal_shadowing_db
from .tapped_delay_line import TdlProfile, get_tdl_profile


@dataclass(slots=True)
class FadingResult:
    waveform: np.ndarray
    impulse_response: np.ndarray
    frequency_response: np.ndarray


class FadingChannel:
    def __init__(self, config: Dict, sample_rate: float, fft_size: int, seed: int | None = None) -> None:
        self.config = config
        self.sample_rate = float(sample_rate)
        self.fft_size = int(fft_size)
        self.rng = np.random.default_rng(seed)

    def build_impulse_response(self) -> np.ndarray:
        channel_cfg = self.config.get("channel", {})
        profile_name = str(channel_cfg.get("profile", "static_near"))
        fading_type = str(channel_cfg.get("fading_type", channel_cfg.get("model", "rayleigh")))
        delay_spread_s = float(channel_cfg.get("delay_spread_s", 0.0))
        k_factor_db = float(channel_cfg.get("k_factor_db", 6.0))

        profile: TdlProfile = get_tdl_profile(profile_name=profile_name, delay_spread_s=delay_spread_s)
        taps = profile.sample_taps(fading_type=fading_type, rng=self.rng, k_factor_db=k_factor_db)
        sample_delays = np.round(profile.delays_s * self.sample_rate).astype(int)
        impulse = np.zeros(max(int(sample_delays.max()) + 1, 1), dtype=np.complex128)
        for tap, delay in zip(taps, sample_delays):
            impulse[delay] += tap
        return impulse

    def frequency_response_from_impulse(self, impulse: np.ndarray) -> np.ndarray:
        return np.fft.fftshift(np.fft.fft(impulse, self.fft_size))

    def apply(self, waveform: np.ndarray) -> FadingResult:
        impulse = self.build_impulse_response()
        view = np.asarray(waveform, dtype=np.complex128)
        if view.ndim == 1:
            output = np.convolve(view, impulse, mode="full")[: view.size]
        else:
            output = np.stack(
                [np.convolve(row, impulse, mode="full")[: row.size] for row in view],
                axis=0,
            )

        channel_cfg = self.config.get("channel", {})
        output = apply_doppler_rotation(
            output,
            doppler_hz=float(channel_cfg.get("doppler_hz", 0.0)),
            sample_rate=self.sample_rate,
            initial_phase=float(self.rng.uniform(0.0, 2.0 * np.pi)),
        )

        carrier_cfg = self.config.get("carrier", {})
        distance_m = float(channel_cfg.get("distance_m", 100.0))
        carrier_frequency_hz = float(carrier_cfg.get("center_frequency_hz", 3.5e9))
        shadowing_db = log_normal_shadowing_db(float(channel_cfg.get("shadowing_std_db", 0.0)), self.rng)
        path_loss_db = float(channel_cfg.get("path_loss_db", 0.0)) + free_space_path_loss_db(distance_m, carrier_frequency_hz) + shadowing_db
        output = apply_path_loss(output, total_loss_db=path_loss_db)

        frequency_response = self.frequency_response_from_impulse(impulse)
        total_gain = 10 ** (-path_loss_db / 20.0)
        return FadingResult(
            waveform=output,
            impulse_response=impulse * total_gain,
            frequency_response=frequency_response * total_gain,
        )
