from __future__ import annotations

import numpy as np


def estimate_symbol_timing(
    waveform: np.ndarray,
    fft_size: int,
    cp_length: int,
    search_window: int | None = None,
) -> int:
    search_window = int(search_window if search_window is not None else max(2 * cp_length, 1))
    best_metric = -np.inf
    best_offset = 0
    symbol_length = fft_size + cp_length
    for offset in range(max(search_window, 1)):
        if offset + symbol_length >= waveform.size:
            break
        metric = 0.0
        valid_symbols = 0
        for symbol_index in range(4):
            start = offset + symbol_index * symbol_length
            if start + symbol_length > waveform.size:
                break
            cp = waveform[start : start + cp_length]
            tail = waveform[start + fft_size : start + fft_size + cp_length]
            numerator = np.abs(np.vdot(cp, tail))
            denominator = np.sqrt(np.vdot(cp, cp).real * np.vdot(tail, tail).real) + 1e-12
            metric += numerator / denominator
            valid_symbols += 1
        if valid_symbols:
            metric /= valid_symbols
        if metric > best_metric:
            best_metric = metric
            best_offset = offset
    return best_offset


def estimate_cfo_from_cp(
    waveform: np.ndarray,
    fft_size: int,
    cp_length: int,
    sample_rate: float,
    symbols_to_average: int = 4,
) -> float:
    phases = []
    symbol_length = fft_size + cp_length
    for symbol_index in range(symbols_to_average):
        start = symbol_index * symbol_length
        end = start + symbol_length
        if end > waveform.size:
            break
        cp = waveform[start : start + cp_length]
        tail = waveform[start + fft_size : start + fft_size + cp_length]
        correlation = np.vdot(cp, tail)
        phases.append(np.angle(correlation))
    if not phases:
        return 0.0
    mean_phase = float(np.mean(phases))
    return mean_phase * sample_rate / (2.0 * np.pi * fft_size)


def correct_cfo(waveform: np.ndarray, cfo_hz: float, sample_rate: float) -> np.ndarray:
    if abs(cfo_hz) < 1e-12:
        return waveform
    time = np.arange(waveform.size) / sample_rate
    return waveform * np.exp(-1j * 2.0 * np.pi * cfo_hz * time)
