from __future__ import annotations

from copy import deepcopy


def deep_merge(base: dict, override: dict) -> dict:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def validate_config(config: dict) -> dict:
    numerology = config.get("numerology", {})
    if int(numerology.get("n_rb", 1)) * 12 >= int(numerology.get("fft_size", 1)):
        raise ValueError("n_rb * 12 must stay below fft_size to keep guard bands and DC.")

    modulation = str(config.get("modulation", {}).get("scheme", "QPSK")).upper()
    if modulation not in {"QPSK", "16QAM", "64QAM", "256QAM"}:
        raise ValueError(f"Unsupported modulation scheme: {modulation}")

    return config
