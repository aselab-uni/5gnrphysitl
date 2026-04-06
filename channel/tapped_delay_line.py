from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np


BASE_PROFILES: Dict[str, Tuple[np.ndarray, np.ndarray]] = {
    "static_near": (np.array([0.0]), np.array([0.0])),
    "cell_edge": (np.array([0.0, 80e-9, 220e-9]), np.array([0.0, -4.0, -8.0])),
    "pedestrian": (np.array([0.0, 110e-9, 410e-9, 710e-9]), np.array([0.0, -2.0, -5.0, -9.0])),
    "vehicular": (np.array([0.0, 220e-9, 440e-9, 880e-9, 1760e-9]), np.array([0.0, -1.0, -3.0, -7.0, -11.0])),
    "indoor": (np.array([0.0, 50e-9, 90e-9, 180e-9]), np.array([0.0, -3.0, -6.0, -9.0])),
    "urban_los": (np.array([0.0, 120e-9, 350e-9, 800e-9]), np.array([0.0, -1.5, -5.0, -8.0])),
    "urban_nlos": (np.array([0.0, 150e-9, 450e-9, 1100e-9, 1800e-9]), np.array([0.0, -2.0, -4.5, -8.5, -12.0])),
    "severe_fading": (np.array([0.0, 200e-9, 500e-9, 1200e-9, 2500e-9]), np.array([0.0, -1.0, -3.0, -7.0, -13.0])),
}


@dataclass(slots=True)
class TdlProfile:
    delays_s: np.ndarray
    powers_db: np.ndarray

    @property
    def powers_linear(self) -> np.ndarray:
        linear = 10 ** (self.powers_db / 10.0)
        return linear / np.sum(linear)

    def sample_taps(
        self,
        fading_type: str,
        rng: np.random.Generator,
        k_factor_db: float = 6.0,
    ) -> np.ndarray:
        powers = np.sqrt(self.powers_linear)
        fading_type = fading_type.lower()
        if fading_type in {"rician", "los"}:
            k_linear = 10 ** (k_factor_db / 10.0)
            los = np.sqrt(k_linear / (k_linear + 1.0))
            nlos = np.sqrt(1.0 / (k_linear + 1.0))
            gaussian = (
                rng.standard_normal(powers.size) + 1j * rng.standard_normal(powers.size)
            ) / np.sqrt(2.0)
            taps = powers * (los + nlos * gaussian)
            taps[0] = powers[0] * (los + nlos * gaussian[0])
            return taps
        gaussian = (
            rng.standard_normal(powers.size) + 1j * rng.standard_normal(powers.size)
        ) / np.sqrt(2.0)
        return powers * gaussian


def get_tdl_profile(profile_name: str, delay_spread_s: float | None = None) -> TdlProfile:
    delays, powers = BASE_PROFILES.get(profile_name.lower(), BASE_PROFILES["static_near"])
    delays = delays.copy()
    if delay_spread_s and delay_spread_s > 0 and delays.max() > 0:
        delays *= delay_spread_s / delays.max()
    return TdlProfile(delays_s=delays, powers_db=powers.copy())
