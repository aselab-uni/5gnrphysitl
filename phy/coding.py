from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np


CRC_DEFINITIONS = {
    "crc8": (8, 0x07),
    "crc16": (16, 0x1021),
}


def _int_to_bits(value: int, width: int) -> np.ndarray:
    return np.array([(value >> shift) & 1 for shift in range(width - 1, -1, -1)], dtype=np.uint8)


def crc_remainder(bits: np.ndarray, crc_type: str) -> np.ndarray:
    width, polynomial = CRC_DEFINITIONS[crc_type]
    register = 0
    mask = (1 << width) - 1
    padded = np.concatenate([bits.astype(np.uint8), np.zeros(width, dtype=np.uint8)])
    for bit in padded:
        msb = (register >> (width - 1)) & 1
        register = ((register << 1) & mask) | int(bit)
        if msb:
            register ^= polynomial
    return _int_to_bits(register, width)


def attach_crc(bits: np.ndarray, crc_type: str) -> np.ndarray:
    return np.concatenate([bits.astype(np.uint8), crc_remainder(bits, crc_type)])


def check_crc(bits_with_crc: np.ndarray, crc_type: str) -> Tuple[np.ndarray, bool]:
    width, _ = CRC_DEFINITIONS[crc_type]
    payload = bits_with_crc[:-width]
    remainder = bits_with_crc[-width:]
    expected = crc_remainder(payload, crc_type)
    return payload, bool(np.array_equal(remainder, expected))


def _circular_rate_match(bits: np.ndarray, target_length: int, rv: int) -> np.ndarray:
    if bits.size == 0:
        return bits
    start = (rv * max(bits.size // 4, 1)) % bits.size
    indices = (np.arange(target_length) + start) % bits.size
    return bits[indices]


def _circular_rate_recover(llrs: np.ndarray, mother_length: int, rv: int) -> np.ndarray:
    if mother_length == 0:
        return np.array([], dtype=np.float64)
    start = (rv * max(mother_length // 4, 1)) % mother_length
    recovered = np.zeros(mother_length, dtype=np.float64)
    indices = (np.arange(llrs.size) + start) % mother_length
    np.add.at(recovered, indices, llrs)
    return recovered


def _next_power_of_two(value: int) -> int:
    return 1 << max(1, int(np.ceil(np.log2(max(2, value)))))


def _polar_weight(index: int, n_bits: int) -> float:
    beta = 2 ** 0.25
    return sum(((index >> bit) & 1) * (beta**bit) for bit in range(n_bits))


def _reliability_order(length: int) -> np.ndarray:
    n_bits = int(np.log2(length))
    scores = np.array([_polar_weight(index, n_bits) for index in range(length)])
    return np.argsort(scores)


def _polar_transform(u: np.ndarray) -> np.ndarray:
    x = u.copy()
    step = 1
    while step < x.size:
        for start in range(0, x.size, 2 * step):
            left = slice(start, start + step)
            right = slice(start + step, start + 2 * step)
            x[left] ^= x[right]
        step *= 2
    return x


def _f_function(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.sign(a) * np.sign(b) * np.minimum(np.abs(a), np.abs(b))


def _g_function(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
    return b + (1.0 - 2.0 * c.astype(np.float64)) * a


def _sc_decode(llr: np.ndarray, frozen: np.ndarray) -> np.ndarray:
    if llr.size == 1:
        if frozen[0]:
            return np.array([0], dtype=np.uint8)
        return np.array([0 if llr[0] >= 0 else 1], dtype=np.uint8)

    half = llr.size // 2
    left = _sc_decode(_f_function(llr[:half], llr[half:]), frozen[:half])
    right = _sc_decode(_g_function(llr[:half], llr[half:], left), frozen[half:])
    return np.concatenate([left ^ right, right]).astype(np.uint8)


@dataclass(slots=True)
class CodingMetadata:
    channel_type: str
    crc_type: str
    payload_length: int
    rate_matched_length: int
    mother_length: int
    redundancy_version: int
    interleaver: np.ndarray | None = None
    repetition_factor: int = 1
    polar_length: int | None = None
    info_positions: np.ndarray | None = None


class NrLdpcInspiredCoder:
    """Simplified rate-compatible data-channel coder.

    This is not a standards-compliant LDPC implementation. It preserves the
    processing stages expected in an NR-like PHY chain.
    """

    def __init__(self, target_rate: float = 0.5, crc_type: str = "crc16", seed: int = 0) -> None:
        self.target_rate = float(target_rate)
        self.crc_type = crc_type
        self.seed = int(seed)

    def encode(
        self,
        payload_bits: np.ndarray,
        target_length: int,
        redundancy_version: int = 0,
    ) -> Tuple[np.ndarray, CodingMetadata]:
        payload_crc = attach_crc(np.asarray(payload_bits, dtype=np.uint8), self.crc_type)
        repetition_factor = max(2, int(np.ceil(1.0 / max(self.target_rate, 1e-3))))
        mother = np.tile(payload_crc, repetition_factor)
        rng = np.random.default_rng(self.seed + payload_crc.size + redundancy_version)
        interleaver = rng.permutation(mother.size)
        interleaved = mother[interleaver]
        rate_matched = _circular_rate_match(interleaved, target_length=target_length, rv=redundancy_version)
        metadata = CodingMetadata(
            channel_type="data",
            crc_type=self.crc_type,
            payload_length=payload_bits.size,
            rate_matched_length=target_length,
            mother_length=mother.size,
            redundancy_version=redundancy_version,
            interleaver=interleaver,
            repetition_factor=repetition_factor,
        )
        return rate_matched.astype(np.uint8), metadata

    def decode(self, llrs: np.ndarray, metadata: CodingMetadata) -> Tuple[np.ndarray, bool]:
        recovered = _circular_rate_recover(llrs=np.asarray(llrs, dtype=np.float64), mother_length=metadata.mother_length, rv=metadata.redundancy_version)
        deinterleaved = np.zeros_like(recovered)
        assert metadata.interleaver is not None
        deinterleaved[metadata.interleaver] = recovered
        combined = deinterleaved.reshape(metadata.repetition_factor, -1).sum(axis=0)
        hard = (combined < 0).astype(np.uint8)
        payload, crc_ok = check_crc(hard, metadata.crc_type)
        return payload[: metadata.payload_length], crc_ok


class PolarLikeControlCoder:
    """Small-block control-channel coder using a simplified polar transform."""

    def __init__(self, target_rate: float = 0.25, crc_type: str = "crc8") -> None:
        self.target_rate = float(target_rate)
        self.crc_type = crc_type

    def encode(
        self,
        payload_bits: np.ndarray,
        target_length: int,
        redundancy_version: int = 0,
    ) -> Tuple[np.ndarray, CodingMetadata]:
        payload_crc = attach_crc(np.asarray(payload_bits, dtype=np.uint8), self.crc_type)
        polar_length = _next_power_of_two(max(payload_crc.size, int(np.ceil(payload_crc.size / max(self.target_rate, 1e-3)))))
        reliability = _reliability_order(polar_length)
        info_positions = np.sort(reliability[-payload_crc.size :])
        u = np.zeros(polar_length, dtype=np.uint8)
        u[info_positions] = payload_crc
        mother = _polar_transform(u)
        rate_matched = _circular_rate_match(mother, target_length=target_length, rv=redundancy_version)
        metadata = CodingMetadata(
            channel_type="control",
            crc_type=self.crc_type,
            payload_length=payload_bits.size,
            rate_matched_length=target_length,
            mother_length=mother.size,
            redundancy_version=redundancy_version,
            polar_length=polar_length,
            info_positions=info_positions,
        )
        return rate_matched.astype(np.uint8), metadata

    def decode(self, llrs: np.ndarray, metadata: CodingMetadata) -> Tuple[np.ndarray, bool]:
        recovered = _circular_rate_recover(llrs=np.asarray(llrs, dtype=np.float64), mother_length=metadata.mother_length, rv=metadata.redundancy_version)
        assert metadata.polar_length is not None
        assert metadata.info_positions is not None
        frozen = np.ones(metadata.polar_length, dtype=bool)
        frozen[metadata.info_positions] = False
        u_hat = _sc_decode(recovered, frozen)
        payload_crc = u_hat[metadata.info_positions]
        payload, crc_ok = check_crc(payload_crc, metadata.crc_type)
        return payload[: metadata.payload_length], crc_ok


def build_channel_coder(channel_type: str, config: Dict) -> object:
    coding_cfg = config.get("coding", {})
    if channel_type.lower() in {"control", "pdcch", "pbch"}:
        return PolarLikeControlCoder(
            target_rate=float(coding_cfg.get("control_rate", 0.25)),
            crc_type=str(coding_cfg.get("control_crc", "crc8")),
        )
    return NrLdpcInspiredCoder(
        target_rate=float(coding_cfg.get("target_rate", 0.5)),
        crc_type=str(coding_cfg.get("crc", "crc16")),
        seed=int(config.get("simulation", {}).get("seed", 0)),
    )
