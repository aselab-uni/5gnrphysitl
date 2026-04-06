from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(slots=True)
class NumerologyConfig:
    """Simplified OFDM numerology aligned with 5G NR concepts."""

    scs_khz: float
    fft_size: int
    cp_length: int
    n_rb: int
    symbols_per_slot: int = 14
    slots_per_frame: int = 10

    @property
    def subcarrier_spacing_hz(self) -> float:
        return self.scs_khz * 1e3

    @property
    def active_subcarriers(self) -> int:
        return self.n_rb * 12

    @property
    def sample_rate(self) -> float:
        return self.fft_size * self.subcarrier_spacing_hz

    @property
    def slot_length_samples(self) -> int:
        return self.symbols_per_slot * (self.fft_size + self.cp_length)

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "NumerologyConfig":
        return cls(
            scs_khz=float(config["scs_khz"]),
            fft_size=int(config["fft_size"]),
            cp_length=int(config["cp_length"]),
            n_rb=int(config["n_rb"]),
            symbols_per_slot=int(config.get("symbols_per_slot", 14)),
            slots_per_frame=int(config.get("slots_per_frame", 10)),
        )
