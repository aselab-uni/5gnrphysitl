from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

import numpy as np


def bit_error_rate(reference: np.ndarray, detected: np.ndarray) -> float:
    if reference.size == 0:
        return 0.0
    count = min(reference.size, detected.size)
    return float(np.mean(reference[:count] != detected[:count]))


def block_error_rate(crc_ok: bool) -> float:
    return 0.0 if crc_ok else 1.0


def error_vector_magnitude(reference: np.ndarray, measured: np.ndarray) -> float:
    if reference.size == 0:
        return 0.0
    denominator = np.mean(np.abs(reference) ** 2)
    if denominator <= 0:
        return 0.0
    return float(np.sqrt(np.mean(np.abs(measured - reference) ** 2) / denominator))


def estimate_snr_db(reference: np.ndarray, error: np.ndarray) -> float:
    signal_power = float(np.mean(np.abs(reference) ** 2))
    noise_power = float(np.mean(np.abs(error) ** 2))
    if noise_power <= 0:
        return float("inf")
    return float(10.0 * np.log10(signal_power / noise_power))


def throughput_bps(decoded_bits: int, slot_duration_s: float, crc_ok: bool) -> float:
    if slot_duration_s <= 0 or not crc_ok:
        return 0.0
    return float(decoded_bits / slot_duration_s)


def spectral_efficiency_bps_hz(throughput: float, bandwidth_hz: float) -> float:
    if bandwidth_hz <= 0:
        return 0.0
    return float(throughput / bandwidth_hz)


@dataclass(slots=True)
class LinkKpiSummary:
    ber: float
    bler: float
    evm: float
    throughput_bps: float
    spectral_efficiency_bps_hz: float
    estimated_snr_db: float
    crc_ok: bool
    channel_estimation_mse: float | None = None
    synchronization_error_samples: float | None = None
    extra: Dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, float]:
        payload = {
            "ber": self.ber,
            "bler": self.bler,
            "evm": self.evm,
            "throughput_bps": self.throughput_bps,
            "spectral_efficiency_bps_hz": self.spectral_efficiency_bps_hz,
            "estimated_snr_db": self.estimated_snr_db,
            "crc_ok": float(self.crc_ok),
        }
        if self.channel_estimation_mse is not None:
            payload["channel_estimation_mse"] = self.channel_estimation_mse
        if self.synchronization_error_samples is not None:
            payload["synchronization_error_samples"] = self.synchronization_error_samples
        payload.update(self.extra)
        return payload
