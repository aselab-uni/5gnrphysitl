from __future__ import annotations

from typing import Dict

import numpy as np


def ls_estimate_from_dmrs(
    rx_grid: np.ndarray,
    dmrs_positions: np.ndarray,
    dmrs_symbols: np.ndarray,
) -> Dict[str, np.ndarray]:
    """Least-squares DMRS estimate with linear interpolation over time/frequency."""

    symbols, subcarriers = rx_grid.shape
    estimate = np.ones((symbols, subcarriers), dtype=np.complex128)

    if dmrs_positions.size == 0:
        return {"h_dmrs": estimate.copy(), "h_full": estimate}

    unique_symbols = np.unique(dmrs_positions[:, 0])
    dmrs_full = np.zeros((unique_symbols.size, subcarriers), dtype=np.complex128)
    for row_index, symbol in enumerate(unique_symbols):
        symbol_mask = dmrs_positions[:, 0] == symbol
        symbol_positions = dmrs_positions[symbol_mask, 1]
        symbol_dmrs = dmrs_symbols[symbol_mask]
        h_ls = rx_grid[symbol, symbol_positions] / np.where(symbol_dmrs == 0, 1.0, symbol_dmrs)
        dmrs_full[row_index].real = np.interp(np.arange(subcarriers), symbol_positions, h_ls.real)
        dmrs_full[row_index].imag = np.interp(np.arange(subcarriers), symbol_positions, h_ls.imag)

    if unique_symbols.size == 1:
        estimate[:] = dmrs_full[0]
    else:
        for subcarrier in range(subcarriers):
            estimate[:, subcarrier].real = np.interp(
                np.arange(symbols), unique_symbols, dmrs_full[:, subcarrier].real
            )
            estimate[:, subcarrier].imag = np.interp(
                np.arange(symbols), unique_symbols, dmrs_full[:, subcarrier].imag
            )

    return {"h_dmrs": dmrs_full, "h_full": estimate}


def channel_mse(estimate: np.ndarray, reference: np.ndarray) -> float:
    if estimate.shape != reference.shape:
        return float("nan")
    return float(np.mean(np.abs(estimate - reference) ** 2))
